from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(
    r'models', views.TopicModelList, 'topicmodel')
router.register(
    r'models', views.TopicModelDetail, 'topicmodel')
router.register(r'config', views.TopicModelConfigViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
