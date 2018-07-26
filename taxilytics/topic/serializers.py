import geojson
import logging
from collections import namedtuple

from django.core.cache import caches

from rest_framework import serializers

from osm.models import PlanetOsmLine
from osm.serializers import PlanetOsmLineSerializer

from .settings import TOPIC_SETTINGS
from .models import (
    TopicModel,
    TopicModelConfig,
)


logger = logging.getLogger(__name__)


class TopicModelConfigSerializer(serializers.HyperlinkedModelSerializer):
    arguments = serializers.DictField()

    class Meta:
        model = TopicModelConfig
        fields = (
            'url', 'algorithm', 'num_topics', 'arguments'
        )


class TopicModelSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.SerializerMethodField()
    config = TopicModelConfigSerializer(read_only=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = TopicModel
        fields = (
            'url', 'name', 'config', 'created', 'modified',
            'results',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Bin = namedtuple('Bin', ['label', 'threshold', 'terms'])
        self.bins = (
            Bin('highest', 0.125, []),
            Bin('higher', 0.100, []),
            Bin('high', 0.075, []),
            Bin('medium', 0.050, []),
            Bin('low', 0.025, [])
        )
        # Don't serialize features when a list is being presented.
        try:
            action = self.context['view'].action
        except (KeyError, AttributeError):
            action = None

        if action == 'list':
            self.fields.pop('results')

    def get_name(self, obj):
        return str(obj)

    def create_contours(self, prefix, qs):
        logger.info('Calculating topic contours...')
        ch_bins = []
        for _ in self.bins:
            ch_bins.append(None)
        for road in qs:
            for i, v in enumerate(self.bins):
                if str(road.gid) in v.terms:
                    if ch_bins[i] is None:
                        ch_bins[i] = road.way
                    else:
                        ch_bins[i] = ch_bins[i].union(road.way)
                    break

        hulls = []
        combined = None
        for i, v in enumerate(ch_bins):
            if v is not None:
                if combined is None:
                    combined = v
                else:
                    combined = combined.union(v)
                ch = combined.convex_hull
                ch_json = geojson.loads(ch.json)
                ch_feature = geojson.Feature(
                    id='%s_CH_%s' % (prefix, self.bins[i].label),
                    geometry=ch_json,
                    properties={
                        'label': self.bins[i].label
                    }
                )
                hulls.append(ch_feature)
        return hulls

    def get_features(self, obj, topic_num, num_terms, get_contours=False):

        topic = obj.model.show_topic(topic_num, num_terms)
        name = "Topic{}".format(topic_num)
        terms = [int(term[1]) for term in topic]
        qs = PlanetOsmLine.objects.filter(  # @UndefinedVariable
            gid__in=terms
        )

        layer = None
        if TOPIC_SETTINGS['CACHE']:
            key = 'model%d"topic%d:features' % (obj.id, topic_num)
            cache = caches[TOPIC_SETTINGS['CACHE']]
            features = cache.get(key)
            if features is not None:
                layer = features

        if layer is None:
            logger.info(
                'Building features for topic %s (cache miss)' % (topic_num)
            )
            serializer = PlanetOsmLineSerializer(
                qs,
                id_prefix='%s_' % name,
                many=True
            )
            layer = serializer.data
            layer['id'] = topic_num
            if TOPIC_SETTINGS['CACHE']:
                cache.set(key, layer, TOPIC_SETTINGS['QUERY_CACHE_TIME'])
        else:
            logger.info(
                'Features for topic %s loaded from cache' % (topic_num)
            )

        # TODO: Consider the best way to display convex hulls on the map
        # Convex Hull for contour.  Consider putting the streets in bins
        # according to their probability and then generate the CH for the
        # highest probability bin first, then iteratively union the next
        # highest probability bin to generate additional contours.
        if get_contours:
            if TOPIC_SETTINGS['CACHE']:
                key = 'model%d"topic%d:contours' % (obj.id, topic_num)
                contours = cache.get(key)
            if contours is None:
                logger.info('Building contours for topic %s' % (topic_num))
                for term in topic:
                    # term[0] = probability; term[1] = term
                    for b in self.bins:
                        if term[0] > b.threshold:
                            b.terms.append(term[1])
                            break
                contours = self.create_contours(name, qs)
                if TOPIC_SETTINGS['CACHE']:
                    cache.set(key, layer, TOPIC_SETTINGS['QUERY_CACHE_TIME'])
            else:
                logger.info('Contours loaded from cache')

            layer['features'].extend(contours)

        return layer

    def get_results(self, obj):
        q = self.context['request'].query_params
        json_data = []

        num_display_roads = 5000 / obj.model.num_topics

        topics = q.get('topics', None)
        contours = q.get('contours', False)
        if topics is None:
            display_topics = range(obj.model.num_topics)
        else:
            display_topics = topics.split(',')
            display_topics = [int(i) for i in display_topics]

        for i in display_topics:
            json_data.append(
                self.get_features(obj, i, num_display_roads, contours)
            )

        return json_data
