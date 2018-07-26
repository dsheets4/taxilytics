from datetime import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase

from .common import (
    create_user,
    create_entity,
    create_trip,
    create_tripdata,
)


class TripViewSetTestCase(TestCase):

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

    def format_json(self):
        tripdata = create_tripdata(self.trip)
        url = reverse(
            'trip-detail',
            kwargs={'pk': self.trip.id, 'format': 'json'}
        )
        response = self.client.get(
            url,
            data={'param': tripdata.dataframe.columns[0]}
        )
        self.assertEqual(response.accepted_media_type, 'application/json')

    def format_csv(self):
        tripdata = create_tripdata(self.trip)
        url = reverse(
            'trip-detail',
            kwargs={'pk': self.trip.id, 'format': 'csv'}
        )
        response = self.client.get(
            url,
            data={'param': tripdata.dataframe.columns[0]}
        )
        self.assertEqual(response.accepted_media_type, 'text/csv')

    def format_h5(self):
        tripdata = create_tripdata(self.trip)
        url = reverse(
            'trip-detail',
            kwargs={'pk': self.trip.id, 'format': 'h5'}
        )
        response = self.client.get(
            url,
            data={'param': tripdata.dataframe.columns[0]}
        )
        self.assertEqual(response.accepted_media_type, 'application/x-hdf')

    def format_bytes(self):
        tripdata = create_tripdata(self.trip)
        url = reverse(
            'trip-detail',
            kwargs={'pk': self.trip.id, 'format': 'bytes'}
        )
        response = self.client.get(
            url,
            data={'param': tripdata.dataframe.columns[0]}
        )
        self.assertEqual(
            response.accepted_media_type,
            'application/octet-stream'
        )

    def format_chart(self):
        tripdata = create_tripdata(self.trip)
        url = reverse(
            'trip-detail',
            kwargs={'pk': self.trip.id, 'format': 'png'}
        )
        response = self.client.get(
            url,
            data={'param': tripdata.dataframe.columns[0]}
        )
        self.assertEqual(response.accepted_media_type, 'image/png')

    # -------------------------------------------------------------------------
    # Format requests with login

    def test_format_json(self):
        self.client.login(username=self.username, password=self.username)
        self.format_json()

    def test_format_csv(self):
        self.client.login(username=self.username, password=self.username)
        self.format_csv()

    def test_format_h5(self):
        self.client.login(username=self.username, password=self.username)
        self.format_h5()

    def test_format_bytes(self):
        self.client.login(username=self.username, password=self.username)
        self.format_bytes()

    def test_format_chart(self):
        self.client.login(username=self.username, password=self.username)
        self.format_chart()

    # -------------------------------------------------------------------------
    # Format requests without login

    def test_format_json_not_logged_in(self):
        self.format_json()

    def test_format_csv_not_logged_in(self):
        self.format_csv()

    def test_format_h5_not_logged_in(self):
        self.format_h5()

    def test_format_bytes_not_logged_in(self):
        self.format_bytes()

    def test_format_chart_not_logged_in(self):
        self.format_chart()
