import logging
import geojson

from django.core.serializers import serialize

from rest_framework import serializers

from entity.models import Trip
from entity.serializers import TripGeoSerializer
from query.serializers import TripQuerySerializer

from .models import (
    ClusterConfig,
    ClusterModel,
)


logger = logging.getLogger(__name__)


class ClusterConfigSerializer(serializers.HyperlinkedModelSerializer):
    arguments = serializers.DictField()

    class Meta:
        model = ClusterConfig
        fields = (
            'url',  'algorithm',  'arguments'
        )


class ClusterModelSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.SerializerMethodField()
    config = ClusterConfigSerializer(read_only=True)
    query = serializers.SerializerMethodField()
    clusters = serializers.SerializerMethodField()
    next = serializers.HyperlinkedIdentityField(
        view_name='clustermodel-results',
    )

    class Meta:
        model = ClusterModel
        fields = (
            'name', 'url', 'next', 'created', 'modified',
            'config',
            'query', 'clusters',
        )

    def __init__(self, *args, clusters=False, **kwargs):
        super().__init__(*args, **kwargs)

        if not clusters:
            self.fields.pop('clusters')
            query = self.fields.pop('query')
            self.fields['results'] = query
        else:
            clusters = self.fields.pop('clusters')
            self.fields['results'] = clusters
            self.fields.pop('next')

    def get_name(self, obj):
        return str(obj)

    def get_query(self, obj):
        def area_to_geojson(a):
            fc = serialize('geojson', [a])
            fc = geojson.loads(fc)
            return fc['features'][0]
        return [geojson.FeatureCollection(
            features=[
                area_to_geojson(s.area) for s in obj.data.spatial.all()
            ],
            properties={
                'name': str(obj)
            },
            crs={
                'type': 'name',
                'properties': {
                    'name': 'EPSG:4326',
                }
            },
        )]

    def get_features(self, obj, cluster_num):
        trip_ids = []
        # TODO: Iterating the queryset again doesn't seem efficient.
        #       I think django will have cached the queryset if TripQuery is
        #       reusing the QuerySet object.
        for i, trip in enumerate(obj.data.q()):
            if obj.model.labels[i] == cluster_num:
                trip_ids.append(trip.id)

        qs = Trip.objects.filter(id__in=trip_ids)
        return TripGeoSerializer(
            qs, id_prefix='Cluster%d_' % cluster_num, many=True
        ).data

    def get_clusters(self, obj):
        q = self.context['request'].query_params
        json_data = []

        clusters = q.get('clusters', None)
        if clusters is None:
            display_clusters = list(range(obj.model.n_clusters))
            display_clusters.append(-1)  # Used for noise
        else:
            display_clusters = clusters.split(',')
            display_clusters = [int(i) for i in display_clusters]

        for i in display_clusters:
            json_data.append(
                self.get_features(obj, i)
            )

        return json_data
