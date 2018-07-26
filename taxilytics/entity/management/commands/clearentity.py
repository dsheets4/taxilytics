import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from entity import models


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-n', '--organizationname',
            dest='organization',
            metavar='organization_name',
            help='Name of the organization that owns the entity.'
        )
        parser.add_argument(
            '-f', '--force',
            dest='force',
            action='store_true',
            default=False,
            help='Force removal, ignore missing, no prompts.'
        )
        parser.add_argument(
            '-t', '--trips',
            dest='trips',
            action='store_true',
            default=False,
            help='Remove trips and not entities.'
        )

    def handle(self, *args, **options):
        can_use_truncate = False
        if options.get('trips'):
            qset = models.Trip.objects
            relation = 'entity__organization'
            prompt = 'trajectories'
        else:
            qset = models.Entity.objects
            relation = 'organization'
            prompt = 'entities and related trajectories'

        if options.get('organization') is not None:
            try:
                organization = models.Organization.objects.get(name=options['organization'])
                qset = qset.filter(**{relation: organization})
                prompt = '{} for user "{}"'.format(prompt, options['organization'])
            except User.DoesNotExist:
                logger.critical(
                    'Organization {} does not exist'.format(options['organization']))
                return
        else:
            can_use_truncate = True

        count = qset.count()
        perform_delete = False
        if options['force']:
            perform_delete = True
        else:
            var = input('Remove {} {}? [Y/n]: '.format(count, prompt))
            if var == 'Y':
                perform_delete = True
            elif var == 'y':
                print('Use capital Y to accept deletion.')
            else:
                print('Operation aborted.')

        if perform_delete:
            if can_use_truncate:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        TRUNCATE {} RESTART IDENTITY CASCADE
                    """.format(qset.model._meta.db_table))
            else:
                qset.delete()

            logger.info('Deleted {} {}.'.format(count, prompt))
