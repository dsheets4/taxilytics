from django_util.renderers import MapRenderer


class ClusterMapRenderer(MapRenderer):
    context = {
        'dataObj': {
            'className': 'Rest',
            'args': {
            }
        },
        'appType': 'cluster',
        'options': {
            'queryOp': 'intersects',
        }
    }
