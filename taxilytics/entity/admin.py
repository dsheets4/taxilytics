from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from .models import Organization, Entity, Trip, DataDefinition, TripData


# Register your models here.

@admin.register(Organization)
class EntityAdmin(admin.ModelAdmin):
    list_display = 'name', 'timezone',
    list_filter = 'name',
    search_fields = 'name',


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ('common_id', 'organization')
    list_filter = ('organization',)
    search_fields = ('common_id', 'organization__name')


class TripDataInline(admin.StackedInline):
    model = TripData
    extra = 0


@admin.register(Trip)
class TripAdmin(gis_admin.OSMGeoAdmin):
    list_display = ('label', 'start_datetime', 'duration')
    list_filter = ('start_datetime', 'entity__organization__name')
    search_fields = ('entity__common_id',)
    fieldsets = [
        ('ID',        {'fields': ['entity', 'archive_uri']}),
        ('Date/Time', {'fields': ['start_datetime', 'duration']}),
        ('Metadata',  {'fields': ['metadata']}),
    ]
    inlines = [TripDataInline]


@admin.register(DataDefinition)
class DataDefinitionAdmin(admin.ModelAdmin):
    pass