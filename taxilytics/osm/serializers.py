from rest_framework import serializers

from django_util.serializers import GeoFeatureModelSerializerWithCrs

from .models import (
    PlanetOsmLine,
    PlanetOsmRoads,
    PlanetOsmPoint,
    PlanetOsmPolygon,
    PlanetOsmNodes,
    PlanetOsmRels,
    PlanetOsmWays
)


def _make_osm_geo_serializer(osm_model):
    class OsmSerializer(GeoFeatureModelSerializerWithCrs):
        info = serializers.SerializerMethodField()
        gid = serializers.SerializerMethodField()

        class Meta(GeoFeatureModelSerializerWithCrs.Meta):
            model = osm_model
            id_field = 'gid'
            geo_field = 'way'
            fields = (
                'gid', 'osm_id', 'info', 'name', 'highway',
            )

        def __init__(self, *args, id_prefix='', **kwargs):
            self.id_prefix = id_prefix
            super().__init__(*args, **kwargs)

        def get_gid(self, obj):
            return '%s%d' % (self.id_prefix, obj.gid)

        def get_name(self, obj):
            if not obj.name:
                print(type(obj.tags))

        def get_info(self, obj):
            return {
                'type': obj._meta.app_label,
                'id': obj.gid,
            }

    return OsmSerializer


PlanetOsmPointSerializer = _make_osm_geo_serializer(PlanetOsmPoint)
PlanetOsmLineSerializer = _make_osm_geo_serializer(PlanetOsmLine)
PlanetOsmPolygonSerializer = _make_osm_geo_serializer(PlanetOsmPolygon)
PlanetOsmRoadsSerializer = _make_osm_geo_serializer(PlanetOsmRoads)


class PlanetOsmNodesSerializer(serializers.HyperlinkedIdentityField):

    class Meta:
        model = PlanetOsmNodes
        fields = (
            'id',
        )


class PlanetOsmRelsSerializer(serializers.HyperlinkedIdentityField):

    class Meta:
        model = PlanetOsmRels
        fields = (
            'id',
        )


class PlanetOsmWaysSerializer(serializers.HyperlinkedIdentityField):

    class Meta:
        model = PlanetOsmWays
        fields = (
            'id',
        )
