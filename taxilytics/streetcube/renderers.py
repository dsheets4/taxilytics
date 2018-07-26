from django_util.renderers import MapRenderer


class ItemCubeMapRenderer(MapRenderer):
    context = {
        'dataObj': {
            'className': 'Cube',
            'args': {
                'collectPages': False,
            }
        },
        'initialFilter': {
            'date': ['2011-12-01', '2011-12-30']
        },
        'appType': 'item_cube',
        'options': {
            'queryOp': 'intersects',
        }
    }
    title = 'Street-Taxi Cube'


class LinkCubeMapRenderer(MapRenderer):
    context = {
        'dataObj': {
            'className': 'Cube',
            'args': {
                'collectPages': True,
            }
        },
        'initialFilter': {
            'date': ['2011-12-01', '2011-12-30']
        },
        'appType': 'link_cube',
        'options': {
            'queryOp': 'intersects',
        }
    }
    title = 'Orig-Dest Cube'
