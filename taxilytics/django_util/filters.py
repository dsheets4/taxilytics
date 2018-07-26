import json
from django.contrib.gis.geos import GEOSGeometry
# Some filters, such as BaseInFilter, are not exposed at the top level of django_filters
from django_filters.filters import (
    Filter, BaseInFilter, NumberFilter, CharFilter, BooleanFilter, DateFromToRangeFilter
)

import util


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class DateRangeFilter(DateFromToRangeFilter):

    def filter(self, qs, value):
        if value.start is not None:
            qs = self.get_method(qs)(**{'%s__gte' % self.name: value.start})
        if value.stop is not None:
            qs = self.get_method(qs)(**{'%s__lte' % self.name: value.stop})

        return qs


class TextInFilter(BaseInFilter, CharFilter):
    pass


class IsNullFilter(BooleanFilter):
    def filter(self, qs, value):
        filter_args = {
            '%s__isnull' % self.name: value
        }
        return self.get_method(qs)(**filter_args)


class SpecificJsonFilter(Filter):
    """
    Used with django-pgjson's JsonBField.  It will generate the queryset
    syntax for a passed in value stored in the JsonBField according to the
    pgjson required syntax.
    """

    def __init__(self, key, *args, **kwargs):
        self.key = key
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        value = json.loads(value)
        return self.get_method(qs)(**{
            '%s__jcontains' % self.name: {self.key: value}
        })


class JsonFilter(Filter):
    """
    Used with django-pgjson's JsonBField.  It will generate the queryset
    syntax for a passed in value stored in the JsonBField according to the
    pgjson required syntax. It accepts arguments of the form key:value
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        filter_dict = json.loads(value)
        if len(filter_dict):
            return self.get_method(qs)(**{
                '%s__jcontains' % self.name: filter_dict
            })
        return qs


class GeoFilter(Filter):
    # TODO: GeoFilter could use a field_class to parse the 'op' param

    def __init__(self, *args, value_srid='3857', **kwargs):
        super().__init__(*args, **kwargs)
        self.value_srid = value_srid

    def filter(self, qs, value):
        op = self.parent.data.get('op', 'contained')
        value = value.replace('POLYGON', 'SRID=%s;MULTIPOLYGON(' % self.value_srid)
        value = value.replace('))', ')))')
        geometry = GEOSGeometry(value)
        srid = qs.model._meta.get_field(self.name).srid
        wgs = geometry.transform(srid, True)
        kwargs = {
            self.name + '__' + op: wgs
        }
        return self.get_method(qs)(**kwargs)
