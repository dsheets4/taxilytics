import os
import subprocess
import logging

from django.conf import settings


logger = logging.getLogger(__name__)


config = {
    'loader_executable': '/home/dingbat/src/taxi/osm2pgrouting/build/osm2pgrouting',
    'schema': 'public'
}
config.update(settings.ROUTING)
common_args = [
        config['executable'],
        '--conf', config['conf'],
        '--dbname', settings.DATABASES['default']['NAME'],
        '--username', settings.DATABASES['default']['USER'],
    ]


def load_osm_dir(osm_data):
    create_append = '--clean'

    def process(input_file_name):
        logger.info("Processing file {}.".format(input_file_name))
        subprocess.check_call(common_args + [create_append, '--file', input_file_name])

    if os.path.isdir(osm_data):
        for (root, dirs, files) in os.walk(osm_data):
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext == '.osm':
                    full_file_name = os.path.join(osm_data, f)
                    process(full_file_name)
                    create_append = ''
    elif os.path.isfile(osm_data):
        process(osm_data)



def forwards_func(apps, schema_editor):
    data_dir = settings.OSM_DATA
    if isinstance(data_dir, list):
        for d in data_dir:
            load_osm_dir(d)
    else:
        load_osm_dir(data_dir)


def reverse_func(apps, schema_editor):
    schema_editor.execute('DROP TABLE {}.osm_nodes CASCADE'.format(config['schema']))
    schema_editor.execute('DROP TABLE {}.osm_relations CASCADE'.format(config['schema']))
    schema_editor.execute('DROP TABLE {}.osm_way_classes CASCADE'.format(config['schema']))
    schema_editor.execute('DROP TABLE {}.osm_way_types CASCADE'.format(config['schema']))
    schema_editor.execute('DROP TABLE {}.relations_ways CASCADE'.format(config['schema']))
    schema_editor.execute('DROP TABLE {}.ways CASCADE'.format(config['schema']))
    schema_editor.execute('DROP TABLE {}.ways_vertices_pgr CASCADE'.format(config['schema']))
