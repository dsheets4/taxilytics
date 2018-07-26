from rest_framework import viewsets, renderers, pagination

from django_util.permissions import default_permissions
from django_util.views import LoginRequiredMixin, EmptyQueryWhenNoArgsMixin

from .models import (
    PlanetOsmPoint,
    PlanetOsmLine,
    PlanetOsmPolygon,
)
from .filters import (
    PlanetOsmPointFilterSet,
    PlanetOsmLineFilterSet,
    PlanetOsmPolygonFilterSet,
)
from .serializers import (
    PlanetOsmPointSerializer,
    PlanetOsmLineSerializer,
    PlanetOsmPolygonSerializer,
)

from .renderers import OsmMapRenderer


class OsmCursorPagination(pagination.CursorPagination):
    ordering = 'gid'
    page_size = 1000


class PlanetOsmPointViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    """ TBD """
    queryset = PlanetOsmPoint.objects.all()  # @UndefinedVariable
    serializer_class = PlanetOsmPointSerializer
    filter_class = PlanetOsmPointFilterSet
    permission_classes = default_permissions
    renderer_classes = (
        renderers.JSONRenderer,
        OsmMapRenderer,
    )
    pagination_class = OsmCursorPagination


class PlanetOsmLineViewSet(LoginRequiredMixin, EmptyQueryWhenNoArgsMixin, viewsets.ModelViewSet):
    """ TBD """
    queryset = PlanetOsmLine.objects.filter(highway__isnull=False)  # @UndefinedVariable
    serializer_class = PlanetOsmLineSerializer
    filter_class = PlanetOsmLineFilterSet
    permission_classes = default_permissions
    renderer_classes = (
        renderers.JSONRenderer,
        OsmMapRenderer,
        renderers.BrowsableAPIRenderer,
    )
    pagination_class = OsmCursorPagination


class PlanetOsmPolygonViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    """ TBD """
    queryset = PlanetOsmPolygon.objects.all()  # @UndefinedVariable
    serializer_class = PlanetOsmPolygonSerializer
    filter_class = PlanetOsmPolygonFilterSet
    permission_classes = default_permissions
    renderer_classes = (
        renderers.JSONRenderer,
        OsmMapRenderer,
    )
    pagination_class = OsmCursorPagination
