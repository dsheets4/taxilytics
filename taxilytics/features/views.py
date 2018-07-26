from rest_framework import viewsets, renderers

from django_util.permissions import default_permissions
from django_util.views import LoginRequiredMixin

from .models import Area
from .serializers import AreaSerializer
from .renderers import FeatureMapRenderer


# Create your views here.

class AreaViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    """
    Type something in the doc string here and it appears on the web page.
    A HTML snippet to display a map can be found with the map endpoint.
    """
    queryset = Area.objects.filter()  # @UndefinedVariable
    serializer_class = AreaSerializer
    renderer_classes = (
        renderers.JSONRenderer,
        FeatureMapRenderer,
    )
    permission_classes = default_permissions
