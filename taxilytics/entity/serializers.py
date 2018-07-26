import json
from dateutil import parser as timeparser
from datetime import timedelta

from django.contrib.gis.geos import GeometryCollection, Point

from rest_framework import serializers

from django_util.serializers import (
    GeoFeatureModelSerializerWithCrs,
    HyperlinkedRelatedListField,
)
from .models import Organization, Entity, Trip, TripData


class DataFrameSlicer(object):

    def query_params(self):
        q = self.context['request'].query_params
        params = q.get('params', None)
        return params.split(',') if params else params

    def slice(self, obj):
        q = self.context['request'].query_params

        start_time = q.get('start_time', None)
        if start_time is not None:
            start_time = timeparser.parse(start_time)

        duration = q.get('duration', None)
        if duration is not None:
            duration = timedelta(seconds=int(duration))

        params = q.get('params', None)
        if params:
            params = params.split(',')

        return obj.dataframe_filter(
            params=params,
            times=(start_time, duration)
        )

    def has_query(self):
        try:
            q = self.context['request'].query_params
            params = q.get('params', '')
            start_time = q.get('start_time', None)

            return len(params) > 0 or start_time is not None
        except KeyError:
            return False


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    entities = HyperlinkedRelatedListField(
        view_name='entity-list',
        query_name='organization_id',
        read_only=True
    )

    class Meta:
        model = Organization
        fields = (
            'url', 'name', 'entities',
            'metadata'
        )


class EntitySerializer(serializers.HyperlinkedModelSerializer):
    trips = HyperlinkedRelatedListField(
        view_name='trip-list',
        query_name='common_id',
        lookup_field='common_id',
        read_only=True
    )
    metadata = serializers.DictField()
    organization = OrganizationSerializer()

    class Meta:
        model = Entity
        fields = (
            'url', 'organization', 'common_id', 'physical_id', 'metadata',
            'trips'
        )


class TripSerializerFieldsMixin(object):
    """ Class to abstract the common fields for the Trip Serializers """

    def get_common_id(self, obj):
        return obj.label

    def get_physical_id(self, obj):
        return obj.entity.physical_id if obj.entity else obj.label


class TripSerializer(serializers.HyperlinkedModelSerializer,
                     DataFrameSlicer, TripSerializerFieldsMixin):
    metadata = serializers.DictField()
    data = serializers.SerializerMethodField()
    common_id = serializers.SerializerMethodField()
    physical_id = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            'url', 'common_id', 'physical_id',
            'start_datetime', 'duration',
            'metadata',
            'data',
        )
        # prefetch_fields = ('entity',)
        preselect_fields = ('entity',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Selectively choose to serialize the dataframe.
        # * When a list is requested the dataframe is not serialized
        # * When a single item is requested, dataframe is left in play
        try:
            action = self.context['view'].action
        except (KeyError, AttributeError):
            action = None

        if action == 'list' and not self.has_query():
            self.fields.pop('data')

    def get_data(self, obj):
        """
        Using the TripDataSerializer as a field on this serializer would be
        an elegant way of including the TripData.  However, when doing that
        the context is not passed so it becomes a non-starter.  This method
        accomplished the same thing but creates a serializer with context.
        """
        data_set = []

        for sub_obj in obj.tripdata_set.all():
            sub_df = TripDataSerializer(sub_obj, context=self.context)
            d = sub_df.data
            if (d.get('paramlist', None) is not None or
                    d.get('dataframe', None) is not None):
                data_set.append(sub_df.data)

        return data_set


class TripGeoSerializer(GeoFeatureModelSerializerWithCrs,
                        TripSerializerFieldsMixin):
    id = serializers.SerializerMethodField()
    metadata = serializers.DictField()
    info = serializers.SerializerMethodField()
    common_id = serializers.SerializerMethodField()
    physical_id = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()

    class Meta(GeoFeatureModelSerializerWithCrs.Meta):
        model = Trip
        geo_field = 'geometry'
        fields = (
            'id', 'info',
            'common_id', 'physical_id', 'start_datetime', 'duration',
            'metadata'
        )
        prefetch_fields = ('entity',)

    def __init__(self, *args, id_prefix='', **kwargs):
        self.id_prefix = id_prefix
        super().__init__(*args, **kwargs)

    def get_id(self, obj):
        return '%s%d' % (self.id_prefix, obj.id)

    def get_geometry(self, obj):
        # TODO: Might need to reduce geometry for bigger trajectories.
        # simpler = obj.geometry.simplify(
        #     tolerance=0.0,
        #     preserve_topology=False
        # )
        # geo = json.loads(simpler.json)
        geocol = GeometryCollection([
            g for g in [
                Point(obj.geometry[0]),
                obj.geometry,
                Point(obj.geometry[-1])
            ] if g is not None
        ])
        geostr = geocol.geojson
        return json.loads(geostr)

    def get_info(self, obj):
        return {
            'type': obj._meta.app_label,
            'id': obj.id,
        }


class TripDataSerializer(serializers.HyperlinkedModelSerializer,
                         DataFrameSlicer):
    """
    Serializes the dataframe managed by the model.  This serializer is most
    useful when used by TripSerializer since stand-alone it doesn't provide
    enough fields to properly associate the data.
    """
    trip = serializers.HyperlinkedRelatedField(
        view_name='trip-detail',
        read_only=True
    )
    dataframe = serializers.SerializerMethodField()
    paramlist = serializers.SerializerMethodField()
    definition = serializers.SerializerMethodField()
    metadata = serializers.DictField()

    class Meta:
        model = TripData
        fields = (
            'url', 'trip',
            'paramlist',
            'metadata',
            'definition', 'dataframe',  # Pandas DataFrame
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Selectively choose to serialize the dataframe.
        # * When a list is requested the dataframe is not serialized
        # * When a single item is requested, dataframe is left in play
        try:
            action = self.context['view'].action
        except (KeyError, AttributeError):
            action = None

        if action == 'retrieve' or self.has_query():
            self.fields.pop('paramlist')
        else:
            self.fields.pop('dataframe')
            self.fields.pop('metadata')

    def get_dataframe(self, obj):
        return self.slice(obj)

    def get_paramlist(self, obj):
        return obj.paramlist()

    def get_definition(self, obj):
        params = self.query_params()
        if params:
            definition = {}
            for p in params:
                try:
                    definition[p] = obj.definition.definition[p]
                except KeyError:
                    pass
            return definition

        return obj.definition.definition
