from rest_framework import filters

from django_util.filters import GeoFilter, NumberInFilter

from .models import PlanetOsmPoint, PlanetOsmLine, PlanetOsmPolygon


def make_osm_filterset(filter_model, model_fields=None, meta_fields=None):
    """ Most OSM models have the same fields """
    model_fields = model_fields or []
    meta_fields = meta_fields or {}

    class NewFilterSet(filters.FilterSet):
        gids = NumberInFilter(name='gid', lookup_type='in')
        geo = GeoFilter(name='way')

        class Meta:
            model = filter_model
            fields = ['gid', 'gids', 'geo'] + model_fields + list(meta_fields.keys())

    for k, v in meta_fields:
        setattr(NewFilterSet, k, v)

    return NewFilterSet


PlanetOsmPointFilterSet = make_osm_filterset(PlanetOsmPoint)

PlanetOsmLineFilterSet = make_osm_filterset(
    PlanetOsmLine,
    model_fields=['highway']
)

PlanetOsmPolygonFilterSet = make_osm_filterset(PlanetOsmPolygon)
