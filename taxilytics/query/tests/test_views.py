from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.test import TestCase

# Create your tests here.

from entity.tests.common import (
    create_test_trip
)

from features.tests.common import (
    create_area
)

from query.tests.common import (
    create_attribute,
    create_temporal,
    create_spatial,
    create_tripquery,
)


class TripQueryViewSetTestCase(TestCase):

    def setUp(self):
        self.trip = create_test_trip()

        self.attribute = create_attribute(
            name="test_attribute", attr_value="key")
        self.temporal = create_temporal(
            "Test Now",
            datetime.now() - timedelta(seconds=30),
            datetime.now()
        )
        self.area = create_area(
            "test_area",
            MultiPolygon(Polygon([
                [114.11037681897618, 22.600637396001883],
                [114.1190457185114, 22.605035731566073],
                [114.12033317883824, 22.612166245994242],
                [114.11037681897618, 22.600637396001883]
            ]))
        )
        self.spatial = create_spatial('start_point', 'contained', self.area)
        self.limit = None
        self.tripquery = create_tripquery(
            "test_tripquery",
            self.attribute,
            self.temporal,
            self.spatial,
            self.limit
        )

    def test_tripquerylist(self):
        url = reverse('tripquery-list')
        self.client.get(url)

    def test_tripquerydetail(self):
        url = reverse(
            'tripquery-detail',
            kwargs={'pk': self.tripquery.id}
        )
        self.client.get(url)
