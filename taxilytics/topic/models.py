import os
import logging
import functools

from django.db import connection
from django.template.defaultfilters import slugify
from django.db import models
from django.core.cache import caches

from django.contrib.postgres.fields import JSONField

import processing
from processing import topicmodeling  # To coordinate logger
import util

from django_util import validators
from query.models import TripQuery
from .settings import TOPIC_SETTINGS


logger = logging.getLogger(__name__)
topicmodeling.logger = logger


class TripToDocCached(object):

    def __call__(self, trip):
        """
        Turns the provided entity.Trip instance into a document for use in the
        topic model.  This abstracts this operation from the rest of the code.
        """
        doc = []
        for tripdata in trip.dataframe_filter(params=['gid']):
            td = tripdata['gid']
            doc.extend([str(gid) for gid in td])
        return doc


class TripToDocQuery(object):

    def __init__(self, query):
        self.query = query
        self.curr = connection.cursor()

    def __call__(self, trip):
        """
        Turns the provided entity.Trip instance into a document for use in the
        topic model.  This abstracts this operation from the rest of the code.
        """
        doc = []
        for tripdata in trip.tripdata_set.all():
            df = tripdata.dataframe[['longitude', 'latitude', 'heading']]
            doc.extend([self.exec_query(sample) for sample in df.iterrows()])
        return doc

    def exec_query(self, sample):
        #  if sample['valid'] == True:
        query_str = self.query.format(
            sample[1].longitude,
            sample[1].latitude,
            sample[1].heading,
            25  # hdg_tolerance
        )
        self.curr.execute(query_str)
        result = self.curr.fetchone()
        return str(result[0])


trip_to_road = TripToDocQuery(
    'select gid, dist '
    'from osm_road_match({}, {}) limit 1;'
)


trip_to_road_hdg = TripToDocQuery(
    'select gid, dist '
    'from osm_road_match_hdg({}, {}, {}, {}) limit 1;'
)


trip_to_poi = TripToDocQuery(
    'select gid, dist '
    'from osm_poi_match({}, {}) limit 10;'
)


trip_to_doc = TripToDocCached()
# trip_to_doc = trip_to_road_hdg


def trip_queryset_to_corpus(qs, obj_id):
    """
    Convenience function for calling trip_to_doc on a given queryset of
    entity.Trip instances.  It will cache the results since the operation
    can be time consuming.
    """
    if TOPIC_SETTINGS['CACHE'] is not None:
        key = 'query%s:corpus' % (obj_id)
        cache = caches[TOPIC_SETTINGS['CACHE']]
        corpus = cache.get(key)
        if corpus is None:
            logger.info('Cache miss on corpus for query %s with key %s' % (
                obj_id, key
            ))
        else:
            logger.info('Cache hit on corpus for query %s with key %s' % (
                obj_id, key
            ))

    if corpus is None:
        logger.info('Creating corpus from query %s' % obj_id)
        corpus = [trip_to_doc(trip) for trip in qs.all()]
        if TOPIC_SETTINGS['CACHE'] is not None:
            logger.info(
                'Saving corpus to cache: query=%s; %d seconds; key=%s' % (
                    obj_id, TOPIC_SETTINGS['QUERY_CACHE_TIME'], key)
            )
            cache.set(key, corpus, TOPIC_SETTINGS['QUERY_CACHE_TIME'])
    else:
        logger.info('Corpus %s revived from cache' % obj_id)

    return corpus


# Create your models here.

class TopicModelConfig(models.Model):
    """
    Stores the configuration for a particular model that can be applied
    to multiple sets of data to allow for general comparison of the model
    to multiple data sets.
    """
    IMPLEMENTATIONS = (
        ('MalletLda', 'LDA MALLET'),
        ('GensimLda', 'LDA Gensim'),
        # ('GensimTfIdf', 'TF/IDF'),
        ('GensimLsi', 'LSI'),
    )
    algorithm = models.CharField(max_length=16, choices=IMPLEMENTATIONS)
    num_topics = models.IntegerField(default=300)
    arguments = JSONField(
        default={},
        blank=True,
        null=True,
        validators=[validators.JsonValidator()],
        help_text='Additional arguments to pass to the topic model.'
    )

    def __str__(self):
        return '%s(%s)' % (
            self.get_algorithm_display(),
            self.num_topics
        )


class TopicModel(models.Model):
    """
    Represents the combination of the model configuration with a queryset
    to provide the data to create the model.
    """
    slug = models.SlugField()
    config = models.ForeignKey(TopicModelConfig)
    data = models.ForeignKey(TripQuery)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s on %s' % (
            self.config,
            self.data,
        )

    def __init__(self, *args, **kwargs):
        self._model = None
        super().__init__(*args, **kwargs)

    def set_slug(self):
        """
        Calculates the slug name from other properties on the model.
        """
        self.slug = slugify(str(self))
        slug_len = TopicModel._meta.get_field('slug').max_length
        if len(self.slug) > slug_len:
            post_fix = ''
            if self.id is not None:
                post_fix = '%d' % self.id
            self.slug = self.slug[:slug_len-1-len(post_fix)]
            self.slug = '%s%s' % (self.slug, post_fix)

    def save(self, *args, **kwargs):
        self.set_slug()
        post_process = False
        new_model = False
        if self.id is None:
            new_model = True
        super().save(*args, **kwargs)  # Also creates the id for new models
        if new_model:
            self._load_model()
            self.set_slug()
            super().save(*args, **kwargs)

    @property
    def model(self):
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self, regen=False):
        """
        Loads the topic model up from a stored state or calculates it if there
        is no saved model.
        One aspect of complexity is that the model is associated with a set of
        data in time (hence tracking the modified timestamp).  Thus, when the
        results of a query change as the base data changes, the model might be
        different if it were recalculated.  For our purposes, however, we
        consider the model good for as long as it is useful and instead provide
        the ability to recalculate the model or associated a different model
        with any downstream operations.
        """
        logger.info('Building Topic Model: {}'.format(
            str(self)
        ))
        model_cache_dir = os.path.join(TOPIC_SETTINGS['MODEL_DIR'], 'models', str(self.id))
        util.create_dir(model_cache_dir)
        query_cache_dir = os.path.join(TOPIC_SETTINGS['MODEL_DIR'], 'queries', str(self.data.id))
        util.create_dir(query_cache_dir)

        model_options = self.config.arguments
        model_options['name'] = str(self)
        model_options['num_topics'] = self.config.num_topics
        model_options['impl'] = self.config.algorithm
        model_options['mallet'] = TOPIC_SETTINGS['MALLET_DIR']

        doc_iter = functools.partial(
            trip_queryset_to_corpus,
            self.data.q(),
            self.data.id
        )

        library = processing.Library(
            doclib=doc_iter,
            cache_dir=query_cache_dir,
            # doclibs can be deleted from filesystem to trigger deletion
            # regen=regen
        )

        return processing.TopicModel(
            library=library,
            cache_dir=model_cache_dir,
            regen=regen,
            **model_options
        )
