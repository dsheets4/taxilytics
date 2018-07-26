from django.contrib import admin


from .models import (
    Attribute,
    Temporal,
    Spatial,
    TripQuery
)


def copy_model(modeladmin, request, queryset):
    # Calling save will recalculate the model and update time stamps.
    for tm in queryset:
        tm.id = None
        tm.save()
copy_model.short_description = "Copy selected models"

# Register your models here.

admin.site.register(Temporal)
admin.site.register(Attribute)
admin.site.register(Spatial)


@admin.register(TripQuery)
class TripQueryAdmin(admin.ModelAdmin):
    actions = [copy_model, ]
    filter_horizontal = [
        'temporal',
        'attribute',
        'spatial',
    ]