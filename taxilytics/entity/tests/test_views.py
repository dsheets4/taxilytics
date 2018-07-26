from datetime import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase

from .common import (
    create_user,
    create_entity,
    create_trip,
)


class TripDataViewSetTestCase(TestCase):

    def setUp(self):
        self.username = 'triptestcaseuser'
        self.user = create_user(self.username)

        self.entity = create_entity(
            owner=self.user,
            common_id='test_common_id',
            metadata={
                'module': __name__,
            }
        )

        self.start_dt = datetime.now()
        self.trip = create_trip(
            self.entity,
            start_dt=self.start_dt
        )

    def test_no_login(self):
        response = self.client.get(reverse(
            'tripdata-detail',
            kwargs={'pk': 1}
        ))
        self.assertEqual(response.status_code, 403)

    def test_no_tripdata(self):
        self.client.login(username=self.username, password=self.username)
        response = self.client.get(reverse(
            'tripdata-detail',
            kwargs={'pk': 1}  # There's no data in the test database
        ))
        self.assertEqual(response.status_code, 404)
