import logging
from django.contrib.postgres.fields.jsonb import JSONField
import django_filters

from django_util.filters import TextInFilter, JsonFilter, GeoFilter

from .models import Entity, Trip, TripData


logger = logging.getLogger(__name__)


def _make_entity_filterset(relation='', m=Entity):
    """
    Since many items are related to an Entity, and it's convenient to filter by
    criteria related to a trip, this function helps create new classes that
    allow various related objects to generate an appropriate filter.
    """
    class NewEntityFilterSet(django_filters.FilterSet):
        common_id = TextInFilter(name='%scommon_id' % relation)
        organization_id = django_filters.CharFilter(
            name='%sorganization__id' % relation
        )
        organization = django_filters.CharFilter(
            name='%sorganization__name' % relation
        )

        class Meta:
            model = m
            fields = ['common_id', 'organization']

    return NewEntityFilterSet


def _make_trip_filterset(relation='', m=Trip):
    """
    Since many items are related to a Trip, and it's convenient to filter by
    criteria related to a trip, this function helps create new classes that
    allow various related objects to generate an appropriate filter.
    """
    NewEntityFilterSet = _make_entity_filterset('%sentity__' % (
        relation
    ))

    class NewTripFilterSet(NewEntityFilterSet):
        filter_overrides = {
            JSONField: {
                'filter_class': JsonFilter,
            }
        }
        # metadata = JsonFilter(
        #     name='%smetadata' % relation
        # )
        date = django_filters.DateFromToRangeFilter(name='%sstart_datetime' % relation)
        time = django_filters.TimeRangeFilter(name='%sstart_timetime' % relation)
        geo = GeoFilter(name='geometry')

        class Meta:
            model = m
            fields = NewEntityFilterSet.Meta.fields + [
                'metadata', 'date', 'time', 'geo'
            ]

    return NewTripFilterSet


"""
Generate the default classes used to create filters so they aren't created
several times.
"""
EntityFilterSet = _make_entity_filterset()
TripFilterSet = _make_trip_filterset()
TripDataFilterSet = _make_trip_filterset('trip__', TripData)
