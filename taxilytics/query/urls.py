from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from . import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'tripquery', views.TripQueryViewSet)
router.register(r'attribute', views.AttributeViewSet)
router.register(r'temporal', views.TemporalViewSet)
router.register(r'spatial', views.SpatialViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
