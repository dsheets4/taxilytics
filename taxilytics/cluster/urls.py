from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r'config', views.ClusterConfigViewSet)
router.register(r'cluster', views.ClusterModelViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
