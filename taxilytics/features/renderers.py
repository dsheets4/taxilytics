from django_util.renderers import MapRenderer


class FeatureMapRenderer(MapRenderer):
    context = {
        'dataObj': {
            'className': 'Rest',
            'args': {
            }
        },
        'appType': 'feature',
        'options': {
            'queryOp': 'intersects',
        }
    }