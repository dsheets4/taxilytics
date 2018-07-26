import os
import subprocess
import logging

from django.conf import settings


logger = logging.getLogger(__name__)


def load_osm_dir(osm_dir):
    common_args = [
        'osm2pgsql',
        '--hstore',
        '--cache', '10000',
        '--number-processes', '8',
        '--database', settings.DATABASES['default']['NAME'],
        '-U', settings.DATABASES['default']['USER'],
        '--slim',
        '--proj', '3857'
    ]
    create_append = '--create'
    for (root, dirs, files) in os.walk(osm_dir):
        for f in files:
            full_file_name = os.path.join(osm_dir, f)
            logger.info("Processing file {}.".format(full_file_name))
            subprocess.check_call(common_args + [create_append, full_file_name])
            create_append = '--append'


def forwards_func(apps, schema_editor):
    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS hstore;")
    data_dir = settings.OSM_DATA
    if isinstance(data_dir, list):
        for d in data_dir:
            load_osm_dir(d)
    else:
        load_osm_dir(data_dir)


def reverse_func(apps, schema_editor):
    schema_editor.execute('DROP TABLE planet_osm_line CASCADE')
    schema_editor.execute('DROP TABLE planet_osm_nodes CASCADE')
    schema_editor.execute('DROP TABLE planet_osm_point CASCADE')
    schema_editor.execute('DROP TABLE planet_osm_polygon CASCADE')
    schema_editor.execute('DROP TABLE planet_osm_rels CASCADE')
    schema_editor.execute('DROP TABLE planet_osm_roads CASCADE')
    schema_editor.execute('DROP TABLE planet_osm_ways CASCADE')
    # schema_editor.execute("DROP EXTENSION IF EXISTS hstore;")
