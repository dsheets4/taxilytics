from rest_framework import serializers

from .models import StreetCell


class StreetSerializer(serializers.ModelSerializer):

    measures = serializers.DictField()

    class Meta:
        model = StreetCell
        fields = (
            'street', 'time_inc', 'measures'
        )
        # preselect_fields = ('entity', 'osm')
