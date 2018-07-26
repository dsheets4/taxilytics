from django.contrib.gis import admin as geoadmin


def copy_model(modeladmin, request, queryset):
    # Calling save will recalculate the model and update time stamps.
    for model in queryset:
        model.id = None
        model.save()
copy_model.short_description = "Copy selected models"


class GeoAdmin(geoadmin.OSMGeoAdmin):
    openlayers_url = 'https://cdnjs.cloudflare.com/ajax/libs/openlayers/2.13.1/OpenLayers.js'
