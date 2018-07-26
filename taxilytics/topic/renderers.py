from rest_framework import renderers

from django_util.renderers import MapRenderer


class TopicJsonRenderer(renderers.JSONRenderer):
    media_type = 'application/json'
    format = 'json'
    charset = 'utf-8'


class TopicMapRenderer(MapRenderer):
    context = {
        'dataObj': {
            'className': 'Cube',
            'args': {
                'date': ['2011-12-01', '2011-12-30'],
                'pageSize': 7
            }
        },
        'appType': 'cube',
        'options': {
            'queryOp': 'intersects',
        }
    }
