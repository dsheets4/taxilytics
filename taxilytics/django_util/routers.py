from django.conf.urls import url

from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from .views import viewset_decorator_proxy, apply_decorators


class DecoratedViewsetRouter(DefaultRouter):
    """
    Apply the provided decorators to each registered viewset.
    decorators can be a single decorator or an iterable of decorators
    """

    def __init__(self, decorators, *args, **kwargs):
        self.decorators = decorators

        super().__init__(*args, **kwargs)

    def get_urls(self):
        """
        Largely based on Default
        """
        urls = []

        if self.include_root_view:
            root_url = url(
                r'^$',
                apply_decorators(self.get_api_root_view(), self.decorators),
                name=self.root_view_name)
            urls.append(root_url)

        # We modify the registry but only need to do so temporarily for the
        # call to SimpleRouter.get_urls
        temp_registry = self.registry
        self.registry = [
            (
                prefix,
                viewset_decorator_proxy(viewset, self.decorators),
                base_name
            )
            for prefix, viewset, base_name in temp_registry
        ]
        # Note that it's super(DefaultRouter) so it calls SimpleRouter.
        default_urls = super(DefaultRouter, self).get_urls()
        urls.extend(default_urls)
        self.registry = temp_registry

        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls)

        return urls
