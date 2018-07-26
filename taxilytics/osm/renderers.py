from django_util.renderers import MapRenderer


class OsmMapRenderer(MapRenderer):
    context = {
        'dataObj': {
            'className': 'Rest',
            'args': {
            }
        },
        'appType': 'osm',
        'options': {
            'queryOp': 'intersects',
        }
    }
    title = 'OSM Data'