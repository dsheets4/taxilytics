from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from . import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
# When using a model on two separate ViewSets, basename is required
router.register(r'st', views.StreetViewSet, 'st')


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'cubesets', views.cube_sets, name='cubesets'),
    url(r'test', views.TestView.as_view(), name='test'),
    url(r'cube', views.CubeView.as_view(), name='cube'),
]
