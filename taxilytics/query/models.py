import logging
from datetime import datetime

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from django_util import validators
from entity.query import (
    AttributeQueryMixin, AttributeQSetMixin,
    TemporalQueryMixin, TemporalQSetMixin,
    SpatialQueryMixin, SpatialQSetMixin,
    TripQueryMixin,
    TRAJECTORY_SEGMENT_CHOICES, SPATIAL_OPERATOR_CHOICES
)
from features.models import Area


logger = logging.getLogger(__name__)


class AttributeQueryObjectManager(models.Manager, AttributeQSetMixin):
    pass


class TemporalQueryObjectManager(models.Manager, TemporalQSetMixin):
    pass


class SpatialQueryObjectManager(models.Manager, SpatialQSetMixin):
    pass


class Attribute(models.Model, AttributeQueryMixin):
    objects = AttributeQueryObjectManager()
    name = models.CharField(max_length=64)
    attribute = JSONField(
        null=True,
        blank=True,
        validators=[validators.JsonValidator()]
    )

    def __str__(self):
        return self.name


def _get_datetime(d, t):
    if d is None:
        return str(t)
    if t is None:
        return str(d)
    return str(datetime.combine(d, t))


class Temporal(models.Model, TemporalQueryMixin):
    objects = TemporalQueryObjectManager()
    name = models.CharField(max_length=64)
    start_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return '{} ({}-{})'.format(
            self.name,
            _get_datetime(self.start_date, self.start_time),
            _get_datetime(self.end_date, self.end_time),
        )


class Spatial(models.Model, SpatialQueryMixin):
    objects = SpatialQueryObjectManager()
    segment = models.CharField(max_length=11, choices=TRAJECTORY_SEGMENT_CHOICES)
    operator = models.CharField(max_length=20, choices=SPATIAL_OPERATOR_CHOICES)
    area = models.ForeignKey(Area, null=True, blank=True)

    def __str__(self):
        return '{} {} {}'.format(
            self.get_segment_display(),
            self.get_operator_display(),
            self.area,
        )

    @property
    def geometry(self):
        return self.area.geometry


class TripQuery(models.Model, TripQueryMixin):
    name = models.CharField(max_length=64)
    attribute = models.ManyToManyField(Attribute, blank=True)
    temporal = models.ManyToManyField(Temporal, blank=True)
    spatial = models.ManyToManyField(Spatial, blank=True)
    limit = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return '%s%s' % (
            self.name,
            ' - limit %s' % self.limit if self.limit is not None else ''
        )

    def filters(self, *args):
        return (
            Temporal.objects.q_set(self.temporal.all()),
            Attribute.objects.q_set(self.attribute.all()),
            Spatial.objects.q_set(self.spatial.all())
        )