import logging

from django.db.models import Q, TimeField, DateField

from .models import Trip
from .functions import NumPoints, Cast


logger = logging.getLogger(__name__)


# (model_property, human_name)
TRAJECTORY_SEGMENT_CHOICES = (
    ('start_point', 'start point'),
    ('geometry', 'full trip'),
    ('end_point', 'end point'),
)


SPATIAL_OPERATOR_CHOICES = (
    ('contained', 'contained by'),
    ('intersects', 'intersects'),
    ('within', 'near'),
)


class AndQSetMixin(object):
    """
    Manager used to combine multiple query parameters into a single
    Q object for use in further queries.
    """
    @staticmethod
    def q_set(queries):
        _q = Q()
        for o in queries:
            _q &= o.q()
        return _q


class OrQSetMixin(object):
    """
    Manager used to combine multiple query parameters into a single
    Q object for use in further queries.
    """
    @staticmethod
    def q_set(queries):
        _q = Q()
        for o in queries:
            _q |= o.q()
        return _q


class AttributeQSetMixin(OrQSetMixin):
    pass


class TemporalQSetMixin(OrQSetMixin):
    pass


class SpatialQSetMixin(object):
    """
    Provides a method that, when given an iterable of SpatialQueryMixin
    objects, will generate a django query to extract trips.
    """
    @staticmethod
    def q_set(queries):
        _q_segments = {}

        for o in queries:
            if o.segment in _q_segments:
                _q_segments[o.segment] |= o.q()
            else:
                _q_segments[o.segment] = o.q()

        _q_combined = None
        for _q in _q_segments.values():
            if _q:
                if _q_combined:
                    _q_combined &= _q
                else:
                    _q_combined = _q

        return _q_combined or Q()


class AttributeQueryMixin(object):
    """
    Provides a single Q object representing an attribute query.  The target
    class must provide an attribute called:
        attribute
    """
    def q(self):
        return Q(metadata__jcontains=self.attribute)
    q.set_class = AttributeQSetMixin


class TemporalQueryMixin(object):
    """
    Provides a single Q object representing a time query.  The target class
    must provide one or more attributes to query on:
        start_date
        end_date
        start_time
        end_time
    """
    def q(self):
        args = {}
        if hasattr(self, 'start_date') and self.start_date:
            if hasattr(self, 'end_date') and self.end_date:
                args['start_date__range'] = [
                    self.start_date, self.end_date
                ]
            else:
                args['start_date'] = self.start_date

        if hasattr(self, 'start_time') and self.start_time:
            if hasattr(self, 'end_time') and self.end_time:
                args['start_time__range'] = [
                    self.start_time, self.end_time
                ]
            else:
                args['start_time'] = self.start_time

        return Q(**args)
    q.set_class = TemporalQSetMixin


class SpatialQueryMixin(object):
    """
    Provides a single Q object representing a Spatial Query.  The class
    must provide attributes for:
        segment = TRAJECTORY_SEGMENT_CHOICES[n][0]
        operator = SPATIAL_OPERATOR_CHOICES[n][0]
        geometry = GEOSGeometry
    """
    def q(self):
        args = {
            '{}__{}'.format(self.segment, self.operator): self.geometry
        }
        return Q(**args)
    q.set_class = SpatialQSetMixin


class TripQueryMixin(object):
    def q(self, *args, qs=None):
        """
        Takes in a list of QueryMixin classes and constructs a query.
        :param qs: Base django Trip QuerySet to start the filtering.
        :param args: List of QueryMixin classes
        :return: Filtered QuerySet
        """

        if qs is None:
            qs = (Trip.objects
                .all())  # @UndefinedVariable

        # TODO: Allow removal of abnormally large trajectories through inputs.
        #       Default to remove trips with abnormally large number of points
        #       since they seem to just be driving around (at least for taxis).
        max_points = 1000
        min_points = 4
        qs = (
            qs
            .annotate(  # @UndefinedVariable
                num_points=NumPoints('geometry'))
            .filter(num_points__lt=max_points)  # @UndefinedVariable
            .filter(num_points__gt=min_points)  # @UndefinedVariable
        )
        logger.warning(
            'TripQueryMixin filtering to only trips with num points {} < trip < {}'.format(
                min_points, max_points
            )
        )

        # TODO: Setup a means to create/call these functions through the API
        #       Refs #76 - Should include the TO DO above for num points as well.
        qs = qs.annotate(
            start_time=Cast(
                'start_datetime',
                function='time with time zone',
                output_field=TimeField()),
            start_date=Cast(
                'start_datetime',
                function='date',
                output_field=DateField())
        )
        qs = qs.filter(*self.filters(*args))

        if self.limit is not None:
            qs = qs[:self.limit]

        return qs

    def filters(self, *args):
        if len(args):
            return [args[0].q()]
        else:
            return [Q()]
