from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from django.contrib.auth.models import User
from django.contrib.gis.geos import LineString


from entity.models import (
    Entity,
    Trip,
    TripData
)


def create_user(name, password=None):
    password = password if password is not None else name
    user = User.objects.create_user(
        username=name,
        password=password
    )
    user.save()
    return user


def create_entity(owner, common_id, metadata=None):
    metadata = metadata if metadata is not None else {}

    entity = Entity(
        common_id=common_id,
        owner=owner,
        metadata=metadata
    )
    entity.save()
    return entity


# Create your tests here.
def create_trip(entity,
                start_dt=None,
                duration=None,
                geometry=None,
                metadata=None):

    start_datetime = start_dt if start_dt is not None else datetime.now()
    duration = duration if duration is not None else timedelta(seconds=1000)
    geometry = geometry if geometry is not None else LineString(
        [
            [-81.341629, 41.144818, -9999],
            [-81.341318, 41.144636, -9999],
            [-81.340926, 41.144963, -9999],
            [-81.341173, 41.145133, -9999],
            [-81.341463, 41.145068, -9999],
        ],
        srid=4326
    )
    metadata = metadata if metadata is not None else {}

    trip = Trip(
        entity=entity,
        metadata=metadata,
        geometry=geometry,
        start_datetime=start_datetime,
        duration=duration,
        archive_uri='TestData'
    )
    trip.save()

    return trip


def create_tripdata(trip, metadata=None, data=None, rows=10000, freq=100):

    if data is None:
        index = pd.date_range(
            trip.start_datetime,
            periods=rows,
            freq='{}L'.format(freq),
            tz=timezone.utc,
            name='timestamp'
        )
        data = pd.DataFrame(
            {
                'A': 1.,
                'B': pd.Series(
                    1, index=list(range(rows)), dtype='float32'
                ),
                'C': np.array([3] * rows, dtype='int32'),
                'D': 'foo'
            },
            index=index
        )

    tripdata = TripData(
        trip=trip,
        metadata={}
    )
    tripdata.dataframe = data
    tripdata.save()

    return tripdata


def create_test_trip(username='triptestcaseuser'):
    user = create_user(username)

    entity = create_entity(
        owner=user,
        common_id='query_test_id',
        metadata={
            'module': __name__,
        }
    )

    start_dt = datetime.now()
    trip = create_trip(
        entity,
        start_dt=start_dt
    )

    data = create_tripdata(trip)

    return {
        "user": user,
        "entity": entity,
        "trip": trip,
        "data": data
    }
