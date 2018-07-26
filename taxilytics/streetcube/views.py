import logging
from collections import OrderedDict
from json import loads
from django.core.cache import caches
from django.db import connection
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

from rest_framework import renderers, viewsets, status
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param

from django_util.permissions import default_permissions
from django_util.views import (
    LoginRequiredMixin,
    HtmlFrontJsonBackViewSet,
)

from util.general import hash_dict, update_dict

from .models import StreetCell, RegionPartition
from .filters import StreetFilterSet
from .serializers import StreetSerializer
from .renderers import ItemCubeMapRenderer, LinkCubeMapRenderer
from .queries import street_query


logger = logging.getLogger(__name__)
cache = caches['large-object']


# Create your views here.
operations = OrderedDict([
    ('intersects', 'ST_Intersects({geo_field}, {lookup})'),
    ('contains', 'ST_Contains({lookup}, {geo_field})'),
    # ('contained', '{lookup} @ {geo_field}'),
    ('bbcontains', '{lookup} ~ {geo_field}'),
    ('bboverlaps', '{lookup} && {geo_field}'),
    ('contains_properly', 'ST_ContainsProperly({lookup}, {geo_field})'),
    ('coveredby', 'ST_CoveredBy({geo_field}, {lookup})'),
    ('covers', 'ST_Covers({lookup}, {geo_field})'),
    ('crosses', 'ST_Crosses({lookup}, {geo_field})'),
    ('disjoint', 'ST_Disjoint({geo_field}, {lookup})'),
    ('equals', 'ST_Equals({geo_field}, {lookup})'),
    ('exact', '{geo_field} ~= {lookup}'),
    # ('isvalid', 'ST_IsValid({geo_field}, {lookup})'),
    ('overlaps', 'ST_Overlaps({geo_field}, {lookup})'),
    ('relate', 'ST_Relate({geo_field}, {lookup})'),
    ('touches', 'ST_Touches({geo_field}, {lookup})'),
    ('within', 'ST_Within({geo_field}, {lookup})'),
    ('left', '{geo_field} << {lookup}'),
    ('right', '{geo_field} >> {lookup}'),
    ('overlaps_left', '{geo_field} &< {lookup}'),
    ('overlaps_right', '{geo_field} &> {lookup}'),
    ('overlaps_above', '{geo_field} |&> {lookup}'),
    ('overlaps_below', '{geo_field} &<| {lookup}'),
    ('strictly_above', '{geo_field} |>> {lookup}'),
    ('strictly_below', '{geo_field} <<| {lookup}'),
])


def make_feature(region):
    return {
        'type': 'Feature',
        'geometry': loads(region.geometry.json),
        'properties': {
            'id': region.id,
            'name': region.name,
            'items': region.items,
            'sys': region.system,
        }
    }

cubeset_json = {
    'categories': [
        'motorway',
        'trunk',
        'primary',
        'secondary',
        'tertiary',
        'unclassified',
        'residential',
        'service',
        'motorway_link',
        'trunk_link',
        'primary_link',
        'secondary_link',
        'tertiary_link',
        'living_street',
        'road',
        # 'turning_circle'
    ],
    'operations': list(operations.keys()),
    'regions': {
        'type': 'FeatureCollection',
        'features': [],
        'crs': {
            'type': 'name',
            'properties': {
                'name': 'EPSG:3857'
            }
        },
    }
}


def cube_sets(request):
    cubeset_json['regions']['features'] = [
        make_feature(g) for g in RegionPartition.objects.filter(geometry__isnull=False)
    ]
    return JsonResponse(cubeset_json)


class TestView(LoginRequiredMixin, TemplateView):
    template_name = 'streetcube/test.html'


class CubeView(LoginRequiredMixin, TemplateView):
    template_name = 'streetcube/cube-view.html'


class CacheCubeMixin(object):
    page_id = 'pageid'
    road_types = 'roads'
    region_id = 'region_id'
    region_name = 'region_name'
    build_region = 'build_region'
    geo_op = 'op'
    timeout = 30 * 24 * 60 * 60  # In seconds

    def set_query_param_defaults(self, q_params, in_place=True):
        q_params[self.page_id] = q_params.get(self.page_id) or 0
        q_params[self.road_types] = q_params.get(self.road_types) or ''
        q_params[self.region_id] = q_params.get(self.region_id) or ''
        q_params[self.region_name] = q_params.get(self.region_name) or ''

    def run_query(self, q_str, q_params, page_size=None):
        self.set_query_param_defaults(q_params)
        q_params[self.build_region] = q_params.get(self.build_region) or ''
        q_params[self.geo_op] = q_params.get(self.geo_op) or 'intersects'

        category = None
        region = None

        q_filter = ''
        connective = 'WHERE'
        if q_params[self.road_types]:
            q_filter += "{connective} highway IN ({roads})".format(
                connective=connective,
                roads=','.join("'{}'".format(t) for t in q_params[self.road_types].split(','))
            )
            category = q_params[self.road_types]
            connective = 'AND'
        if q_params[self.region_id]:
            q_filter += "{connective} streets.gid = ANY (SELECT unnest(items) FROM streetcube_regionpartition WHERE id={region_id})".format(
                connective=connective,
                region_id=q_params[self.region_id]
            )
            region = q_params[self.region_id]
            connective = 'AND'
        elif q_params[self.build_region]:
            sub_filter = "{connective} " + operations.get(q_params[self.geo_op])
            q_filter += sub_filter.format(
                connective=connective,
                geo_field='way',
                lookup="ST_GeomFromText('{polygon}', 3857)".format(
                    polygon=q_params[self.build_region]
                )
            )
            connective = 'AND'
        with connection.cursor() as c:
            query = q_str.format(
                start_id=q_params[self.page_id],
                limit='LIMIT {}'.format(page_size) if page_size else '',
                filter=q_filter
            )
            c.execute(query)
            data = c.fetchone()
            try:
                for v in data[1].values():
                    v['geo']['properties']['cubesets'] = {
                        'category': category,
                        'region': region
                    }
            except AttributeError:
                # When there are no results.
                logging.error('No results for {}'.format(category))
            return data

    def generate_request_key(self, q_params, media_type):
        return self.__class__.__name__ + ':' + hash_dict(update_dict(
            {
                'media_type': media_type,
            },
            q_params
        ))

    def list(self, request, *args, **kwargs):
        q_params = request.query_params.dict()
        self.set_query_param_defaults(q_params)
        key = self.generate_request_key(q_params, request.accepted_media_type)
        response = cache.get(key, version=self.version)
        if not response:  # Temporarily always recreate regions.
            logger.info('Generating cache data for "{}"'.format(key))
            data = self.run_query(self.get_query(request), q_params, self.page_size)
            osm_id = data[0]
            data = data[1]
            if data and len(data.keys()) > 0:
                if len(data.keys()) == self.page_size:
                    next_url = replace_query_param(request._request.build_absolute_uri(), self.page_id, osm_id)
                else:
                    next_url = None
                data = {
                    'results': data,
                    'next': next_url,
                }
            else:
                data = {
                    'results': {},
                    'next': None
                }
            response = Response(data)
            response = self.finalize_response(request, response, *args, **kwargs)
            response.render()  # Otherwise ContentNotRenderedError
            cache.set(key, response, timeout=self.timeout, version=self.version)
        return response

    def create(self, request, *args, **kwargs):
        q_params = request.POST.dict()
        logger.info('Building region "{}"'.format(q_params[self.region_name]))
        # Note: There is no page size enforced on region creation.
        osm_id, cubeset = self.run_query(self.get_query(request), q_params, None)
        streets = list(cubeset.keys())
        if len(streets) > self.page_size:
            logger.warning('Building region page size exceeds configured page size for region "{}"!'.format(
                q_params['region_name']
            ))

        region = RegionPartition()
        region.geometry = MultiPolygon(GEOSGeometry(q_params['build_region']))
        region.items = streets
        region.name = q_params['region_name']
        region.save()
        headers = {
            'Location': '{base_url}&{name_key}={name}'.format(
                base_url=request._request.build_absolute_uri(),
                name_key=self.region_name,
                name=q_params[self.region_name]
            )
        }
        data = {
            'results': cubeset,
            'next': None
        }
        q_params.pop(self.build_region)
        q_params.pop(self.geo_op)
        # Create a cache entry for the corresponding GET request
        key = self.generate_request_key(q_params, request.accepted_media_type)
        # response = Response(data)
        # response = self.finalize_response(request, response, *args, **kwargs)
        # response.render()  # Otherwise ContentNotRenderedError
        # cache.set(key, response, timeout=self.timeout, version=self.version)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def get_query(self, request):
        return self.query


class StreetViewSet(LoginRequiredMixin,
                    HtmlFrontJsonBackViewSet,
                    CacheCubeMixin,
                    viewsets.ModelViewSet):
    """
    Type something in the doc string here and it appears on the web page.
    A HTML snippet to display a map can be found with the map endpoint.
    """
    queryset = (StreetCell.objects
                .filter(time_inc__isnull=False)
                .filter(street__isnull=False)
                .order_by('-time_inc')
                )
    serializer_class = StreetSerializer
    filter_class = StreetFilterSet
    renderer_classes = (
        renderers.JSONRenderer,
        ItemCubeMapRenderer,
        renderers.BrowsableAPIRenderer,
    )
    permission_classes = default_permissions
    page_size = 300
    cube_type = 'cube_type'
    StreetType = 'street'

    version = 2
    street_query = street_query
    query_map = {
        StreetType: street_query,
    }

    def get_query(self, request):
        cube_type = request.query_params.get(self.cube_type, self.StreetType)
        return self.query_map.get(cube_type, self.StreetType)

    def get_html_data(self, request):
        return [
            replace_query_param(request._request.build_absolute_uri(), self.cube_type, self.StreetType),
            # replace_query_param(request._request.build_absolute_uri(), self.cube_type, self.TaxiType),
        ]
