from django_util.serializers import GeoFeatureModelSerializerWithCrs

from .models import Area


class AreaSerializer(GeoFeatureModelSerializerWithCrs):

    class Meta:
        model = Area
        geo_field = 'geometry'
