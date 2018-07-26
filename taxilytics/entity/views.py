from rest_framework import renderers, pagination, viewsets

from django_util.permissions import default_permissions
from django_util.views import (
    PrefetchRelatedMixin,
    EmptyQueryWhenNoArgsMixin,
    HtmlFrontJsonBackViewSet,
)

from entity.models import Organization, Entity, Trip, TripData
from entity.serializers import (
    OrganizationSerializer,
    EntitySerializer,
    TripSerializer,
    TripGeoSerializer,
    TripDataSerializer,
)
from entity.renderers import (
    EntityTripMapRenderer,
    DataFrameJsonRenderer,
    DataFrameCsvFileRenderer,
    DataFrameH5FileRenderer,
    DataFrameChartRenderer,
    DataFrameBytesFileRenderer,
)
from entity.filters import (
    EntityFilterSet,
    TripFilterSet,
    TripDataFilterSet,
)


# Create your views here.

class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides 'list' and 'detail' actions.
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = default_permissions


class EntityViewSet(viewsets.ModelViewSet):
    """
    Type something in the doc string here and it appears on the web page.
    """
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    filter_class = EntityFilterSet
    permission_classes = default_permissions


class TripCursorPagination(pagination.CursorPagination):
    ordering = 'start_datetime'
    page_size = 100


class TripViewSet(PrefetchRelatedMixin, EmptyQueryWhenNoArgsMixin, viewsets.ModelViewSet):
    """
    This endpoint provides operations to view and manage trip data with
    'list', 'create', 'retrieve', 'update' and 'destroy' actions.

    It is possible to retrieve the data in a variety of formats including:
    'json', 'csv', 'bytes', and 'png' using the format suffix paradigm.
    Specific parameters can be requested.
    Some formats offer additional structuring options.  Specific ranges of
    time can also be requested.

    Query arguments:

    * **common_id**: String value for the common identifier for the entity
    * **organization**: String value for the organization name
    * **organization_id**: Numeric ID for the organization
    * **date_0**: Set to a ISO8601 compliant lower range date string: YYYY-MM-DD
    * **date_1**: Set to a ISO8601 compliant upper range date string: YYYY-MM-DD
    * **time_0**: Set to a ISO8601 compliant lower range time string: HH:MM:SS
    * **time_1**: Set to a ISO8601 compliant upper range time string: HH:MM:SS
    * **metadata**: Use JSON to filter where ALL values exist.
    * **params**: CSV list of parameters to return.  Available parameters
      listed in *paramlist*.
      the first data point to return.
    * **duration**: Number of seconds to include in the response.
    * **orient**: *JSON format only*.  Allows 'split', 'index', and
      'records' providing different JSON structure

    Examples:

    1. Return only trips on 2011-12-10
       > ?date_0=2011-12-10
    1. Return trips between 2011-12-12 and 2011-12-14
       > ?date_0=2011-12-10&date_1=2011-12-14
    1. Return all trips that have a passenger and the roadmatch is complete
       > ?metadata={"passenger":true,"complete":true}
    1. Return a list of all available Latitude and Longitude parameters (will take some time on larger lists)
       > ?params=latitude,longitude
    """
    queryset = Trip.objects.all()  # @UndefinedVariable
    serializer_class = TripSerializer
    filter_class = TripFilterSet
    permission_classes = default_permissions
    renderer_classes = (
        DataFrameJsonRenderer,
        DataFrameCsvFileRenderer,
        DataFrameH5FileRenderer,
        DataFrameChartRenderer,
        DataFrameBytesFileRenderer,
        renderers.BrowsableAPIRenderer,
    )
    pagination_class = TripCursorPagination


class TripMapViewSet(HtmlFrontJsonBackViewSet, TripViewSet):
    serializer_class = TripGeoSerializer
    renderer_classes = (
        renderers.JSONRenderer,
        EntityTripMapRenderer,
        renderers.BrowsableAPIRenderer,
    )


class TripDataViewSet(viewsets.ModelViewSet):
    """
    Type something in the doc string here and it appears on the web page.
    A HTML snippet to display a map can be found with the map endpoint.
    """
    queryset = TripData.objects.all()  # @UndefinedVariable - It's there...
    serializer_class = TripDataSerializer
    filter_class = TripDataFilterSet
    permission_classes = default_permissions
