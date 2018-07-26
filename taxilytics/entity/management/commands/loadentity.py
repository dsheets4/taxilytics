import os
import logging
import traceback
from datetime import datetime

# On Linux multi-processing does a fork and all apps are setup as a result
# On Windows the behavior is a spawn so a new process is created and loaded
# therefore django must be setup to work properly.  This must be done before
# any django imports.
from django_util import setup
from django.core.management.base import BaseCommand, CommandError

import util

from entity import loader


logger = logging.getLogger(__name__)


def load_data(loader_instances, full_path, workers):
    for l in loader_instances:
        if l.accept(full_path):
            logger.debug('Loader {} resolved.'.format(l.__class__.__name__))
            try:
                l.process(full_path, workers)
                return l
            except (KeyboardInterrupt, SystemExit):
                logger.info('Load of {} aborted by user or system...'.format(
                    full_path,
                ))
                raise
            except BaseException as e:
                logger.error('Failed to load {} due to {}:\n{}'.format(
                    full_path,
                    e,
                    traceback.format_exc()
                ))
    return False


class Command(BaseCommand):
    help = 'Loads entity data into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'resource',
            metavar='URI',
            nargs='+',
            help=('Name of resource to load such as a file or directory.  '
                  'This can include a directory containing sub-directories with data '
                  'files and those will be loaded concurrently.'
                  )
        )
        parser.add_argument(
            "-d", "--debug",
            action="store_true",
            dest="debug",
            default=False,
            help="Enable behavior useful for debugging."
        )
        parser.add_argument(
            '-w', '--workers',
            metavar='WORKERS', type=int,
            default=10,  # Specific to development workstation
            help=('Number of workers to use per input data source, if and where applicable.')
        )

    def handle(self, *args, **options):
        start_time = datetime.now()
        logger.info('Command loadentity on {} started.'.format(options['resource']))

        try:
            loader_instances = [
                l(verbosity=options['verbosity'], debug=options['debug'])
                for l in loader.loader_classes
            ]
        except AttributeError:
            raise CommandError('Loader {} module not found.'.format(
                options['loader']
            ))

        for res in options['resource']:
            if os.path.isdir(res):
                loader_inst = load_data(loader_instances, res, options['workers'])
                if not loader_inst:
                    for (root, dirs, files) in os.walk(res):
                        # Create a copy of dirs, allowing manipulation of original in iteration.
                        for d in util.sort_nicely(dirs[:]):
                            full_path = os.path.join(root, d)
                            loader_inst = load_data(loader_instances, full_path, options['workers'])
                            if loader_inst:
                                dirs.remove(d)
                                loader_inst.clean(options['workers'])

                        # Check the files.
                        for f in util.sort_nicely(files):
                            full_path = os.path.join(root, f)
                            loader_inst = load_data(loader_instances, full_path, options['workers'])
                            if loader_inst:
                                loader_inst.clean(options['workers'])
                            else:
                                logger.warning('Failed to load {} under input {}'.format(
                                    full_path, res
                                ))
                else:
                    loader_inst.clean(options['workers'])
            elif os.path.isfile(res):
                loader_inst = load_data(loader_instances, res, options['workers'])
                if loader_inst:
                    loader_inst.clean(options['workers'])
                else:
                    logger.error('Failed to load {}'.format(res))
            else:
                logger.error('Input resource not found: {}'.format(res))
        logger.info('Command loadentity on {} completed in {}.'.format(
            options['resource'], datetime.now()-start_time
        ))
