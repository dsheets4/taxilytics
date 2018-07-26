from django.conf import settings


CLUSTER_SETTINGS = {
    # Name of the cache that will be used by the topic app
    'CACHE': None,

    # Seconds that topic data from trip queries is saved in the cache
    'QUERY_CACHE_TIME': 3600,
}

CLUSTER_SETTINGS.update(
    getattr(settings, 'CLUSTER_SETTINGS', {})
)
