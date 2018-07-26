import json
from datetime import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase

from .common import (
    create_user,
    create_entity,
    create_trip,
    create_tripdata,
)


class TripDataModelTestCase(TestCase):

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

        self.start_dt = datetime.now()  # Cache to avoid combine everywhere
        self.trip = create_trip(
            self.entity,
            start_dt=self.start_dt
        )

    def test_no_argument_request_list(self):
        """
        Requesting TripData as a list requires some filter arguments to prevent
        requesting too much data.
        """
        self.tripdata = create_tripdata(self.trip)
        self.client.login(username=self.username, password=self.username)
        url = reverse('tripdata-list')
        response = self.client.get(url)
        response_data_dict = json.loads(response.content.decode('utf-8'))
        # Response code should be good.
        self.assertEqual(response.status_code, 200)
        # The list should have data (no filters)
        self.assertDictContainsSubset(
            {'count': 1},
            response_data_dict,
        )
        # And the dataframe portion should not exist.
        d = response_data_dict['results'][0]
        with self.assertRaises(KeyError):
            d['dataframe']

    def test_no_argument_request_detail(self):
        """
        Requesting detail from a single TripData object without filter params
        should return the full detail.
        """
        tripdata = create_tripdata(self.trip)
        self.client.login(username=self.username, password=self.username)
        url = reverse(
            'tripdata-detail',
            kwargs={'pk': tripdata.id}
        )
        response = self.client.get(url)
        response_data_dict = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response_data_dict['dataframe'], None)
