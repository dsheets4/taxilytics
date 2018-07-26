from rest_framework import viewsets, renderers
from rest_framework.response import Response

from django_util.views import LoginRequiredMixin, HtmlJsonRetrieveModelMixin

from entity.models import Trip
from entity.serializers import TripGeoSerializer
from entity.renderers import EntityTripMapRenderer

from .models import (
    Attribute,
    Temporal,
    Spatial,
    TripQuery,
)
from .serializers import (
    AttributeSerializer,
    TemporalSerializer,
    SpatialSerializer,
    TripQuerySerializer,
)


# Create your views here.
class AttributeViewSet(viewsets.ModelViewSet):
    """
    Type something in the doc string here and it appears on the web page.
    A HTML snippet to display a map can be found with the map endpoint.
    """
    queryset = Attribute.objects.filter()
    serializer_class = AttributeSerializer


class TemporalViewSet(viewsets.ModelViewSet):
    """
    Type something in the doc string here and it appears on the web page.
    A HTML snippet to display a map can be found with the map endpoint.
    """
    queryset = Temporal.objects.filter()
    serializer_class = TemporalSerializer


class SpatialViewSet(viewsets.ModelViewSet):
    """
    Type something in the doc string here and it appears on the web page.
    A HTML snippet to display a map can be found with the map endpoint.
    """
    queryset = Spatial.objects.filter()
    serializer_class = SpatialSerializer


class TripQueryViewSet(LoginRequiredMixin, HtmlJsonRetrieveModelMixin, viewsets.ModelViewSet):
    """
    This viewset provides the BrowsableAPI when getting a list so that it shows all the saved
    queries as a list.  When retrieving an individual query it will show the map to plot out
    all the trips that the query finds.
    """
    queryset = TripQuery.objects.all()
    serializer_class = TripQuerySerializer
    renderer_classes = (
        renderers.JSONRenderer,
    )

    def get_serializer_class(self):
        if self.action == 'list':
            return TripQuerySerializer
        elif self.action == 'retrieve':
            return TripGeoSerializer
        else:
            return super().get_serializer_class()

    def get_renderers(self):
        my_renderers = super().get_renderers()
        if self.action == 'list':
            my_renderers.append(renderers.BrowsableAPIRenderer())
        elif self.action == 'retrieve':
            my_renderers.append(EntityTripMapRenderer())
        return my_renderers

    def create_response(self, queryset):
        # Below is the general DRF implementation of retrieve but using the
        # passed in Trip queryset instead.
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        if request.accepted_media_type == 'text/html':
            data = {
                'next': request._request.build_absolute_uri()
            }
            return Response(data)
        else:
            # The query app defines queries for the trip model so getting details
            # returns a query set of Trip models.
            return self.create_response(self.get_object().q(
                qs=(
                    Trip.objects
                        .all()  # @UndefinedVariable
                )
            ))