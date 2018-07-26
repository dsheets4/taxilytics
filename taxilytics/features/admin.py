from django.contrib import admin

from django_util.admin import GeoAdmin

from .models import Area


# Register your models here.

admin.site.register(Area, GeoAdmin)
