from datetime import datetime

from rest_framework import serializers

from .models import (
    Attribute,
    Temporal,
    Spatial,
    TripQuery
)
from features.serializers import AreaSerializer


class AttributeSerializer(serializers.HyperlinkedModelSerializer):
    attribute = serializers.DictField()

    class Meta:
        model = Attribute


class TemporalSerializer(serializers.HyperlinkedModelSerializer):
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()

    class Meta:
        model = Temporal
        fields = (
            'name', 'start', 'end'
        )

    def get_start(self, obj):
        return datetime.combine(obj.start_date, obj.start_time)

    def get_end(self, obj):
        return datetime.combine(obj.end_date, obj.end_time)


class SpatialSerializer(serializers.HyperlinkedModelSerializer):
    area = AreaSerializer(read_only=True)

    class Meta:
        model = Spatial


class TripQuerySerializer(serializers.HyperlinkedModelSerializer):
    attribute = AttributeSerializer(many=True, read_only=True)
    temporal = TemporalSerializer(many=True, read_only=True)
    spatial = SpatialSerializer(many=True, read_only=True)

    class Meta:
        model = TripQuery
        fields = [
            'name', 'url', 'attribute', 'temporal', 'spatial', 'limit'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Selectively choose to serialize the dataframe.
        # * When a list is requested the dataframe is not serialized
        # * When a single item is requested, dataframe is left in play
        try:
            action = self.context['view'].action
        except (KeyError, AttributeError):
            action = None

        if action == 'list':
            self.fields.pop('attribute')
            self.fields.pop('temporal')
            self.fields.pop('spatial')
