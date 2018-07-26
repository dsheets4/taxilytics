from datetime import datetime, timedelta

from django.test import TestCase

from .common import (
    create_user,
    create_entity,
    create_trip,
    create_tripdata,
)


class TripDataModelTestCase(TestCase):

    def setUp(self):
        self.user = create_user('triptestcaseuser')

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

        self.tripdata = create_tripdata(self.trip)

    def assert_params(self, df, good_params, bad_params):
        for p in good_params:
            df[p]
        df[good_params]

        for p in bad_params:
            with self.assertRaises(KeyError):
                df[p]
        with self.assertRaises(KeyError):
            df[bad_params]

    def assert_times(self, df, start_time):
        df.loc[start_time, ]
        with self.assertRaises(KeyError):
            df[self.start_dt]

    def test_dataframe_filter_params(self):
        """
        Test to verify that the model filters parameters properly. This also
        does some additional verification for the time filter.
        """
        columns = self.tripdata.dataframe.columns
        remain_cols = columns[::2]
        remove_cols = columns[1::2]

        filtered_df = self.tripdata.dataframe_filter(params=remain_cols)

        self.assert_params(
            filtered_df,
            good_params=remain_cols,
            bad_params=remove_cols
        )

        # Supplemental to the time filter, make sure this works.  The time
        # filter removes this portion of the data so the test here passes
        # and the test below raises an exception as it should to verify the
        # operation appropriately.
        filtered_df.loc[self.start_dt, ]

    def test_dataframe_filter_times(self):
        start_time = self.start_dt + timedelta(seconds=10)
        duration = timedelta(seconds=30)
        filtered_df = self.tripdata.dataframe_filter(times=[
            start_time,
            duration
        ])

        self.assert_times(filtered_df, start_time)

        # Supplemental to the params filter test, this should work
        filtered_df[['B']]
        filtered_df[['C']]

    def test_dataframe_filter_times_params(self):
        columns = self.tripdata.dataframe.columns
        remain_cols = columns[1::2]
        remove_cols = columns[::2]

        start_time = self.start_dt + timedelta(seconds=10)
        duration = timedelta(seconds=30)
        filtered_df = self.tripdata.dataframe_filter(
            params=remain_cols,
            times=[start_time, duration]
        )

        self.assert_params(
            filtered_df,
            good_params=remain_cols,
            bad_params=remove_cols
        )
        self.assert_times(filtered_df, start_time)
