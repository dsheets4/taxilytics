import logging

from rest_framework import viewsets, renderers, mixins

from django_util.views import HtmlFrontJsonBackViewSet, LoginRequiredMixin
from .models import (
    TopicModelConfig,
    TopicModel,
)
from .serializers import (
    TopicModelConfigSerializer,
    TopicModelSerializer,
)

from .renderers import TopicMapRenderer


logger = logging.getLogger(__name__)


# Create your views here.
class TopicModelConfigViewSet(viewsets.ModelViewSet):
    """ TBD """
    queryset = TopicModelConfig.objects.all()
    serializer_class = TopicModelConfigSerializer


class TopicModelList(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TopicModel.objects.filter()  # @UndefinedVariable
    serializer_class = TopicModelSerializer
    renderer_classes = (
        renderers.JSONRenderer,
        renderers.BrowsableAPIRenderer,
    )


class TopicModelDetail(LoginRequiredMixin, HtmlFrontJsonBackViewSet, viewsets.ModelViewSet):
    queryset = TopicModel.objects.filter()  # @UndefinedVariable
    serializer_class = TopicModelSerializer
    renderer_classes = (
        renderers.JSONRenderer,
        TopicMapRenderer,
    )
