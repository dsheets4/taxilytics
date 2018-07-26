from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from . import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'area', views.AreaViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
