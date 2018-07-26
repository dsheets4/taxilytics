from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from . import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'trip', views.TripViewSet)
# When using a model on two separate ViewSets, basename is required
router.register(r'tripgeo', views.TripMapViewSet, 'tripgeo')
router.register(r'tripdata', views.TripDataViewSet)
router.register(r'entity', views.EntityViewSet)
router.register(r'organization', views.OrganizationViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
]
