import django_filters
from rest_framework.filters import FilterSet

from django_util.filters import DateRangeFilter, IsNullFilter

from .models import StreetCell


class StreetFilterSet(FilterSet):
    datetime = django_filters.DateTimeFromToRangeFilter(name='time_inc')
    date = DateRangeFilter(name='time_inc')
    # time = django_filters.TimeRangeFilter(name='time_inc')
    street_isnull = IsNullFilter(name='street')

    class Meta:
        model = StreetCell
        fields = [
            'street', 'time_inc',
            'datetime', 'date', # 'time',
            'street_isnull',
        ]
