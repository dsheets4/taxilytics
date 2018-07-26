import re
import os
from datetime import timezone, datetime, timedelta

import scipy.io as sio
import pandas as pd

from django.contrib.gis.geos import GEOSGeometry

from entity.loader.common import Loader
from entity.models import Entity, Trip, TripData


SEC_TO_MICROSEC = 1000000

RE_FROM_FILENAME = re.compile(
    '(\d{3})(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})'
)
id_idx = 1
year_idx = 2
mon_idx = 3
day_idx = 4
hour_idx = 5
min_idx = 6


def _acquire_time_sync_idx(gmt_sec_param):
    prev_data = gmt_sec_param[0]
    sync_idx = prev_idx = 0
    sync_strength = 0
    for x in range(len(gmt_sec_param)):
        if x == 0:
            continue
        data = gmt_sec_param[x]
        # When the value of the data changes compare the difference
        # in the time stamps to see if it matches the difference in
        # values.  When it does, track the prev_t as correlation_t
        # and keep going until the correlation strength exceeds the
        # threshold.
        if not data == prev_data:
            if data < prev_data:
                delta_d = 60 - prev_data + data
            else:
                delta_d = data - prev_data

            if delta_d == 6:
                if sync_strength == 0:
                    sync_idx = prev_idx
                sync_strength += 1
                if sync_strength > 5:
                    break
            else:
                sync_strength = 0
            prev_data = data
            prev_idx = x

    return sync_idx


class Nasa(Loader):

    def __init__(self, **kwargs):
        pass

    def process_file(self, filename, user):

        trip = Trip()
        trip.archive_uri = filename
        trip.metadata['original_name'] = os.path.splitext(
            os.path.split(filename)[1])[0]

        filename_data = re.match(
            RE_FROM_FILENAME,
            trip.metadata['original_name']
        )

        # Open the file
        mat = sio.loadmat(
            filename,
            squeeze_me=True,
            struct_as_record=False
        )

        # Find where the recording rate syncs with the recorded GPS time.
        sync_idx = _acquire_time_sync_idx(mat['GMT_SEC'].data)
        if sync_idx is None:
            sync_idx = 0  # But load the data.

            trip.metadata['time_sync'] = False
        else:
            trip.metadata['time_sync'] = True

        try:
            sync_time = datetime(
                year=mat['DATE_YEAR'].data[sync_idx],
                month=mat['DATE_MONTH'].data[sync_idx],
                day=mat['DATE_DAY'].data[sync_idx],
                hour=mat['GMT_HOUR'].data[sync_idx],
                minute=mat['GMT_MINUTE'].data[sync_idx],
                second=mat['GMT_SEC'].data[sync_idx],
                tzinfo=timezone.utc
            )
            trip.metadata['time_source'] = 'GMT'
        except(KeyError, ValueError):
            # Not all flights have a StartTimeVec.
            if 'StartTimeVec' in mat:
                t = mat['StartTimeVec']
                sync_time = datetime(
                    year=t[0],
                    month=t[1],
                    day=t[2],
                    hour=t[3],
                    minute=t[4],
                    second=t[5],
                    tzinfo=timezone.utc
                )
                trip.metadata['time_source'] = 'StartTimeVec'
            else:
                if filename_data:
                    sync_time = datetime(
                        year=int(filename_data.group(year_idx)),
                        month=int(filename_data.group(mon_idx)),
                        day=int(filename_data.group(day_idx)),
                        hour=int(filename_data.group(hour_idx)),
                        minute=int(filename_data.group(min_idx)),
                        tzinfo=timezone.utc
                    )
                    trip.metadata['time_source'] = 'Filename'
                else:
                    raise

        # In microseconds
        sync_offset = (1 / mat['GMT_SEC'].Rate) * SEC_TO_MICROSEC * sync_idx
        start_time = sync_time - timedelta(microseconds=sync_offset)
        end_time = start_time

        # Organize the data by rate and create a time index for each rate.
        d = {}  # Time series data
        m = {}  # Meta data
        for p in mat:
            param = mat[p]
            if isinstance(param, sio.matlab.mio5_params.mat_struct):
                if param.Rate not in d:
                    d[param.Rate] = {
                        'p': {},
                        't': pd.date_range(
                            start_time,
                            periods=len(param.data),
                            freq='{}U'.format(
                                int(SEC_TO_MICROSEC * (1.0 / param.Rate))
                            ),
                            tz=timezone.utc,
                            name='timestamp'
                        ),
                        'm': {},
                    }
                    if d[param.Rate]['t'][-1] > end_time:
                        end_time = d[param.Rate]['t'][-1].to_datetime()
                d[param.Rate]['p'][p] = param.data
                d[param.Rate]['m'][p] = {
                    'rate': param.Rate,
                    'units': param.Units if len(param.Units) > 0 else None,
                    'alpha': param.Alpha,
                    'description': param.Description
                }
            else:
                if isinstance(param, bytes):
                    param = param.decode('utf-8')
                m[p] = param

        # Create a dataframe per data rate.
        common_id = filename_data.group(id_idx) if filename_data else None
        params = {}
        for k, v in d.items():
            rate_params = v
            params[k] = {
                'df': pd.DataFrame(rate_params['p'], index=rate_params['t']),
                'meta': rate_params['m']
            }
            if 'ACID' in params[k]['df'].columns:
                common_id = params[k]['df']['ACID'].value_counts().index[0]

        # Retrieve or create the entity for this trajectory.
        try:
            entity = Entity.objects.get(
                common_id=common_id,
                owner=user
            )
        except Entity.DoesNotExist:
            entity = Entity()
            entity.common_id = common_id
            entity.physical_id = common_id  # Not really what is wanted.
            entity.owner = user
            entity.loader_config = {
                'module': __name__,
            }
            entity.save()

        trip.entity = entity
        trip.metadata.update(m)
        trip.start_datetime = start_time
        trip.duration = end_time - start_time
        pos = params[1]['df'][['LONP', 'LATP']].join(
            params[4]['df'][['ALT']],
            how='inner'
        )
        # All positional values valid and within the USA for the data
        # Occasionally the data goes to 0.351562 and/or zero, especially at
        # at the end of the flight.
        f = ~(
            ((pos['LONP'] >= -0.4) & (pos['LONP'] <= 0.4)) |
            ((pos['LATP'] >= -0.4) & (pos['LATP'] <= 0.4))
        )
        pos = pos[f]
        positions = [
            '{} {} {}'.format(p[1].LONP, p[1].LATP, p[1].ALT)
            for p in pos.iterrows()
            if not (p[1].LONP == 0 or p[1].LATP == 0)
        ]
        trip.geometry = GEOSGeometry('SRID=4326;LINESTRING Z ({})'.format(
            ','.join(positions)
        ))
        trip.save()

        for k, v in params.items():
            tripdata = TripData()
            tripdata.dataframe = v['df']
            tripdata.metadata = v['meta']
            tripdata.trip = trip
            tripdata.save()
