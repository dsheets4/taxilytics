from django.core.management.base import BaseCommand

from streetcube.build.regions import run


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-l', '--leaf-size',
            dest='leaf_size',
            metavar='leaf_size',
            help='Number of streets contained in each region.',
            default=500,
        )

    def handle(self, *args, **options):
        run(options['leaf_size'])
