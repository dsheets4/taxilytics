"""taxilytics URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.conf import settings


admin.site.site_header = 'Trajectory Analytics Admin'


urlpatterns = [
    # rest framework doesn't handle using namespaces
    url(r'^entity/', include('entity.urls')),
    url(r'^features/', include('features.urls')),
    url(r'^query/', include('query.urls')),
    url(r'^trajcube/', include('streetcube.urls')),
    url(r'^topic/', include('topic.urls')),
    url(r'^cluster/', include('cluster.urls')),
    url(r'^osm/', include('osm.urls')),
    url(r'^favicon\.ico$', RedirectView.as_view(
        url='/static/favicon.ico',
        permanent=True
    )),
    url('^accounts/', include('django.contrib.auth.urls')),
    # url(r'^api-auth/', include(
    #     'rest_framework.urls',
    #     namespace='rest_framework'
    # )),
    url(r'^admin/', include(admin.site.urls)),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
