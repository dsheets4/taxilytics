from django.db.models import Func, Aggregate
from django.db.models import IntegerField
from django.contrib.gis.db.models import LineStringField
from django.contrib.postgres.fields import ArrayField
from django.contrib.gis.db import models


class NumPoints(Func):
    """
    Returns the number of points in a geometry field.
    Currently only supports postgis
    """
    function = 'ST_NPoints'

    def __init__(self, *expressions, **extra):
        super().__init__(*expressions, output_field=IntegerField(), **extra)


class Simplify(Func):
    """
    Simplifies the geometry using Visvalingam-Whyatt algorithm.  Requires
    postgis version 2.2.0 or greater.
    """
    function = 'ST_SimplifyVW'

    def __init__(self, *expressions, **extra):
        super().__init__(*expressions, output_field=LineStringField(), **extra)


class Cast(Func):
    template = "CAST(%(expressions)s as %(function)s)"


class Array(Aggregate):
    """
    Combines the fields in a group by into an array which is helpful for
    one to many relationships when aggregation is needed with individual values.
    """
    function = 'array_agg'

    def __init__(self, *expressions, **extra):
        super().__init__(
            *expressions,
            output_field=ArrayField(base_field=models.BinaryField()),
            **extra
        )