from django.contrib import admin

from topic.models import TopicModelConfig, TopicModel


def recalculate_topic_model(modeladmin, request, queryset):
    # Calling save will recalculate the model and update time stamps.
    for tm in queryset:
        tm._load_model(regen=True)
        tm.save()  # Force the time stamp update
recalculate_topic_model.short_description = "Recalculate selected topic models"


# Register your models here.
@admin.register(TopicModelConfig)
class TopicModelConfigAdmin(admin.ModelAdmin):
    pass


@admin.register(TopicModel)
class TopicModelAdmin(admin.ModelAdmin):
    readonly_fields = ('slug', 'modified', 'created')
    actions = [recalculate_topic_model, ]
