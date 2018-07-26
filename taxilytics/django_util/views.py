from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets
from rest_framework.response import Response


class LoginRequiredMixin(object):
    """
    Requires the class based view has an authenticated user.  Place this
    mixin first in the list of inherited/mixed-in classes.
    """
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


def apply_decorators(view, decorators):
    if not isinstance(decorators, list):
        decorators = [decorators]
    for decorator in decorators:
        view = decorator(view)
    return view


class EmptyQueryWhenNoArgsMixin(object):

    def get_queryset(self):

        default_qs = super().get_queryset()
        if self.action == 'retrieve':
            return default_qs

        q = self.request.query_params
        if len(q) == 0 or (len(q) == 1 and (q.get(format, None) is not None)):
            return default_qs.none()

        return default_qs


def viewset_decorator_proxy(viewset, decorators):
    """
    Viewsets registered with a router require an as_view class method.  This
    class simply serves as a proxy for the given class and applies the
    decorators to as_view
    """
    class DecoratedViewsetProxy(viewset):

        @classmethod
        def as_view(cls, actions=None, **kwargs):
            view = apply_decorators(
                super().as_view(actions, **kwargs), decorators)
            return view

    return DecoratedViewsetProxy


class HtmlJsonListModelMixin(object):
    """
    List model but allow a separate html request to provide the HTML
    separate from any data.  That is, when requesting HTML, this will
    not query the data API at all.  When requesting anything else, the
    data API is accessed.
    """
    def list(self, request, *args, **kwargs):
        if request.accepted_media_type == 'text/html':
            data = {
                'next': self.get_html_data(request)
            }
            return Response(data)
        else:
            return super().list(request, *args, **kwargs)


class HtmlJsonRetrieveModelMixin(object):
    """
    Same as the HtmlJsonListModelMixin but for requesting details specific
    to a model.
    """
    def retrieve(self, request, *args, **kwargs):
        if request.accepted_media_type == 'text/html':
            data = {
                'next': self.get_html_data(request)
            }
            return Response(data)
        else:
            return super().retrieve(request, *args, **kwargs)

    def get_html_data(self, request):
        return request._request.build_absolute_uri()


class PrefetchRelatedMixin(object):
    def get_queryset(self):
        qs = super().get_queryset()
        pf_fields = getattr(self.get_serializer_class().Meta, 'prefetch_fields', None)
        if pf_fields is not None:
            qs = qs.prefetch_related(*pf_fields)
        ps_fields = getattr(self.get_serializer_class().Meta, 'preselect_fields', None)
        if ps_fields is not None:
            qs = qs.select_related(*ps_fields)
        return qs


class HtmlFrontJsonBackViewSet(HtmlJsonListModelMixin, HtmlJsonRetrieveModelMixin):
    pass