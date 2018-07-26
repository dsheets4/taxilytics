import os

from django.conf import settings


TOPIC_SETTINGS = {
    # Defines where the calculated topic models will be cached.
    'MODEL_DIR': os.path.abspath(
        os.path.join(settings.BASE_DIR, '../topic_models')),

    # If mallet is not on the system path, this defines the location of the
    # mallet executable.  Required to use the MALLET LDA implementation.
    'MALLET_DIR': os.path.abspath(
        os.path.join(settings.BASE_DIR,
                     '../3rdparty/mallet/bin/mallet'
                     )),

    # Name of the cache that will be used by the topic app
    'CACHE': None,

    # Seconds that topic data from trip queries is saved in the cache
    'QUERY_CACHE_TIME': 43200,
}

TOPIC_SETTINGS.update(
    getattr(settings, 'TOPIC_SETTINGS', {})
)
