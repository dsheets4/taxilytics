import logging

from rest_framework import viewsets, renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from django_util.views import LoginRequiredMixin, HtmlFrontJsonBackViewSet

from .models import (
    ClusterConfig,
    ClusterModel,
)
from .serializers import (
    ClusterConfigSerializer,
    ClusterModelSerializer,
)
from .filters import ClusterConfigFilterSet, ClusterModelFilterSet
from .renderers import ClusterMapRenderer


logger = logging.getLogger(__name__)


# Create your views here.
class ClusterConfigViewSet(viewsets.ModelViewSet):
    """ TBD """
    queryset = ClusterConfig.objects.all()
    serializer_class = ClusterConfigSerializer
    filter_class = ClusterConfigFilterSet


class ClusterModelViewSet(LoginRequiredMixin, HtmlFrontJsonBackViewSet, viewsets.ModelViewSet):
    queryset = ClusterModel.objects.all()
    serializer_class = ClusterModelSerializer
    filter_class = ClusterModelFilterSet
    renderer_classes = (
        renderers.JSONRenderer,
    )

    def get_renderers(self):
        # When displaying a list the browsable API is used for HTML but for
        # details a map is displayed with the individual cluster results.
        my_renderers = super().get_renderers()
        if self.action == 'list':
            my_renderers.append(renderers.BrowsableAPIRenderer())
        elif self.action == 'retrieve':
            my_renderers.append(ClusterMapRenderer())
        return my_renderers

    @detail_route(methods=['get'])
    def results(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, clusters=True)
        return Response(serializer.data)
