import logging

import numpy

from django.db import models
from django.core.cache import caches
from django.contrib.postgres.fields import JSONField

import processing
from processing import clustering

from django_util import validators
from query.models import TripQuery
from topic.models import TopicModel, trip_queryset_to_corpus

from .settings import CLUSTER_SETTINGS


logger = logging.getLogger(__name__)
clustering.logger = logger


# Create your models here.

class ClusterConfig(models.Model):
    """
    Represents the cluster algorithm and algorithm inputs.
    """
    ALGORITHMS = (
        ('AffinityPropagation', 'Affinity Propagation'),
        ('DBSCAN', 'DBSCAN'),
        ('Agglomerative', 'Agglomerative'),
        ('Birch', 'Birch'),
        ('KMeans', 'k-Means'),
        ('MiniBatchKMeans', 'Mini Batch k-Means'),
        ('MeanShift', 'Mean Shift'),
        ('Spectral', 'Spectral'),
        ('Ward', 'Ward'),
    )

    algorithm = models.CharField(max_length=20, choices=ALGORITHMS)
    arguments = JSONField(
        default={},
        validators=[validators.JsonValidator()],
        blank=True,
        null=True,
        help_text='Additional arguments to pass to the specific cluster model'
    )

    def __str__(self):
        return '{} {}'.format(
            self.get_algorithm_display(),
            self.arguments,
        )


class ClusterModel(models.Model):
    """
    Defines an execution of the clustering data
    """
    config = models.ForeignKey(ClusterConfig)
    data = models.ForeignKey(TripQuery)
    topic_model = models.ForeignKey(TopicModel, null=True, blank=True)
    arguments = JSONField(
        blank=True,
        null=True,
        validators=[validators.JsonValidator()],
        help_text='Additional arguments for clustering'
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        self._model = None
        super().__init__(*args, **kwargs)

    def __str__(self):
        name = '%s with data (%s)' % (
            self.config,
            self.data,
        )
        if self.topic_model is not None:
            name = '%s on topic model (%s)' % (
                name,
                self.topic_model,
            )
        return name

    def geo_data(self, data):
        cluster_data = numpy.ndarray(shape=(len(data.q()), 4))
        for i, trip in enumerate(data.q()):
            geom_start = trip.start_point
            geom_end = trip.end_point
            cluster_data[i][0] = geom_start.coords[0]
            cluster_data[i][1] = geom_start.coords[1]
            cluster_data[i][2] = geom_end.coords[0]
            cluster_data[i][3] = geom_end.coords[1]

        return cluster_data

    def topic_data(self, data):
        cluster_data = numpy.zeros(
            shape=(len(data.q()), self.topic_model.model.num_topics)
        )

        if True or self.arguments.get('cluster_street_topics', None):
            # Find the most probable topic for each street in the data by
            # creating a corpus of single term documents with the term being
            # the street id and then inferring that with the model
            streets_corpus = []
            for trip in data.q():
                gid_df = trip.dataframe_filter(params=['gid'])[0]
                for gid in gid_df['gid']:
                    gid = str(gid)
                    if gid not in streets_corpus:
                        streets_corpus.append(gid)
            streets_corpus = [[street] for street in streets_corpus]
            inferred_streets = self.topic_model.model[streets_corpus]
            street_topics = {}
            for i, topic in enumerate(inferred_streets):
                topics = sorted(topic, key=lambda t: -t[1])
                street_topics[int(streets_corpus[i][0])] = topics[0]

            adj = 1
            # For each document, create an entry in the cluster data by
            # iterating through each street in the trajectory and incrementing
            # the topic that is most probable for that street.
            for i, trip in enumerate(data.q()):
                streets_df = trip.dataframe_filter(params=['gid'])[0]
                for gid in streets_df['gid']:
                    street_topic = street_topics[gid][0]
                    cluster_data[i][street_topic] += adj

                for s in range(len(cluster_data[i])):
                    cluster_data[i][s] /= (len(streets_df) * adj)
        else:
            # Infer the data associated with the cluster.
            inferred_corpus = self.topic_model.model[
                trip_queryset_to_corpus(data.q(), data.id)
            ]

            # Create cluster data base of inferred corpus
            for i, topics in enumerate(inferred_corpus):
                topics = sorted(topics, key=lambda t: t[1], reverse=True)

                for t in topics:
                    cluster_data[i][t[0]] = t[1]

        return cluster_data

    @property
    def model(self):

        # If the cluster model hasn't been accessed on this model yet, get it.
        if self._model is None:
            # First, attempt to get the model from the cache if available.
            if CLUSTER_SETTINGS['CACHE'] is not None:
                key = 'cluster:model%s' % (self.id)
                cache = caches[CLUSTER_SETTINGS['CACHE']]
                self._model = cache.get(
                    key, CLUSTER_SETTINGS['QUERY_CACHE_TIME'])

            # If the model was not in the cache then calculate it.
            if self._model is None:
                logger.info('Calculating cluster %s' % self)
                if self.topic_model is not None:
                    cluster_data = self.topic_data(self.data)
                else:
                    cluster_data = self.geo_data(self.data)

                self._model = processing.ClusterModel(
                    impl=self.config.algorithm,
                    **self.config.arguments
                )
                self._model.fit(cluster_data)

                if CLUSTER_SETTINGS['CACHE'] is not None:
                    # key is calculated above and cache retrieved above
                    cache.set(
                        key, self._model, CLUSTER_SETTINGS['QUERY_CACHE_TIME'])
            else:
                logger.info('Cluster pulled from cache')

        return self._model
