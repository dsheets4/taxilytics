from django.contrib import admin

from django_util.admin import copy_model

from .models import ClusterConfig, ClusterModel


# Register your models here.

@admin.register(ClusterConfig)
class ClusterConfigAdmin(admin.ModelAdmin):
    actions = [copy_model, ]


@admin.register(ClusterModel)
class ClusterModelAdmin(admin.ModelAdmin):
    actions = [copy_model, ]
