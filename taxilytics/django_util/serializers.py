from rest_framework import serializers

from rest_framework_gis import serializers as serializers_gis


class HyperlinkedRelatedListField(serializers.HyperlinkedIdentityField):
    """
    Creates a link to a filtered list of related models.  This is useful
    when the number of related models is large and generation of an inline
    list, such as created by the default DRF serializers.HyperlinkRelated
    field.  Using this requires that the target list provides a filter
    matching the query_name value and taking the value on the object
    specified by the lookup field.  The provided view is used to lookup
    the URL and the query is added ?query_name=getattr(obj, lookup_field)
    """

    def __init__(self, query_name, view_name=None, **kwargs):
        self.query_name = query_name
        super().__init__(view_name, **kwargs)

    def get_url(self, obj, view_name, request, drf_format):
        # Unsaved objects will not yet have a valid URL.
        if obj.pk is None:
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {}  # {self.lookup_url_kwarg: lookup_value}
        url = self.reverse(
            view_name, kwargs=kwargs, request=request, format=drf_format)
        return url + '?%s=%s' % (self.query_name, lookup_value)


class GeoFeatureModelListSerializerWithCrs(
        serializers_gis.GeoFeatureModelListSerializer):
    """
    Overridden simply to provide the CRS.  Why isn't that a base feature???
    """

    def to_representation(self, data):
        ret = super().to_representation(data)

        try:
            geom_field = getattr(data[0], self.child.Meta.geo_field)
            crs = {
                'type': 'name',
                'properties': {
                    'name': 'EPSG:%d' % geom_field.srid,
                }
            }
            ret['crs'] = crs
        except (IndexError, AttributeError):
            pass

        return ret


class GeoFeatureModelSerializerWithCrs(
        serializers_gis.GeoFeatureModelSerializer):
    """
    Class connects the GeoFeatureModelListSerializerWithCrs with the model to
    make inclusion more natural
    """
    class Meta:
        list_serializer_class = GeoFeatureModelListSerializerWithCrs
