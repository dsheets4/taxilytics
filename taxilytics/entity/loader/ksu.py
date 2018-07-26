import io
import os
import logging
import re

import pandas as pd
import numpy as np

from django.contrib.gis.geos import GEOSGeometry

from entity.loader.common import Loader
from entity.models import Entity, Trip, TripData


logger = logging.getLogger(__name__)

RE_FROM_FILENAME = re.compile(
    '.*_(\d{2})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_(.*)$'
)
year_idx = 1
mon_idx = 2
day_idx = 3
hour_idx = 4
min_idx = 5
sec_idx = 6
airfield_idx = 7


class Ksu(Loader):

    def __init__(self, **kwargs):
        pass

    def process_file(self, filename, organization, verbosity=1, debug=None):
        (common_id, file) = os.path.split(filename)
        common_id = os.path.split(common_id)[1]
        m = re.match(RE_FROM_FILENAME, os.path.splitext(file)[0])

        try:
            entity = Entity.objects.get(
                common_id=common_id,
                organization=organization
            )
        except Entity.DoesNotExist:
            entity = Entity()
            entity.common_id = common_id
            entity.physical_id = common_id  # Not really what is wanted.
            entity.organization = organization
            entity.loader_config = {
                'module': __name__,
            }
            entity.save()

        trip = Trip()
        trip.entity = entity
        trip.archive_uri = filename
        trip.metadata = {
            'airfield': m.group(airfield_idx) if m else '',
        }

        with open(filename, 'r', encoding='latin_1') as f:
            # Extract the flight level metadata
            properties = f.readline().replace(' ', '').split(',')
            for meta in properties:
                if '=' in meta:
                    kv = meta.split('=')
                    trip.metadata[kv[0]] = kv[1].replace('"', '')

            # Units
            # Note that the first 3 columns are combined into a timestamp by
            # pandas below
            unit_values = f.readline().replace(' ', '').replace('\n', '')
            unit_values = unit_values.split(',')[3:]

            # The data files have an unfortunate habit of just ending
            # midstream.  However, if the last line is chopped then pandas
            # can't successfully read the data.
            filedata = f.read()
            k = filedata.rfind('\n')
            buff = io.StringIO(filedata[:k])

            # This block reads the rest of the file.
            name_ts = 'timestamp'
            df = pd.read_csv(
                buff,
                parse_dates={name_ts: ['Lcl Date', 'Lcl Time', 'UTCOfst']},
                skipinitialspace=True,
                index_col=name_ts,
            )

            try:
                ts = df[df['GPSfix'] == '3D'].index.tolist()[0]
                sync_idx = int(np.where(df['GPSfix'] == '3D')[0][0])
                index = [
                    (ts - pd.DateOffset(seconds=sync_idx - i))
                    for i in range(sync_idx)
                ] + df.index.tolist()[sync_idx:]
                df.index = pd.DatetimeIndex(index)
                trip.metadata['Time Sync'] = True
            except IndexError:
                # Happens if no GPS fix is ever received
                sync_idx = None
                logger.warning('Flight does not GPS sync: {}'.format(
                    filename)
                )
                trip.metadata['Time Sync'] = False

        try:
            ts = df[df['GPSfix'] == '3D'].index.tolist()[0]
            sync_idx = int(np.where(df['GPSfix'] == '3D')[0][0])
            index = [
                (ts - pd.DateOffset(seconds=sync_idx - i))
                for i in range(sync_idx)
            ] + df.index.tolist()[sync_idx:]
            df.index = pd.DatetimeIndex(index)
            trip.metadata['Time Sync'] = True
        except IndexError:
            # Happens if no GPS fix is ever received
            sync_idx = None
            logger.warning('Flight does not GPS sync: {}'.format(filename))
            trip.metadata['Time Sync'] = False

        df = df.tz_localize('UTC')

        pos_gen = df[['Longitude', 'Latitude', 'AltGPS']].dropna().iterrows()
        positions = [
            '{} {} {}'.format(d[1][0], d[1][1], d[1][2])
            for d in pos_gen
        ]
        trip.geometry = GEOSGeometry(
            'SRID=4326;LINESTRING Z ({})'.format(','.join(positions))
        )

        start_datetime = df.index[0].to_datetime()
        trip.start_datetime = start_datetime
        trip.duration = df.index[-1] - df.index[0]

        trip.save()

        data = TripData()
        data.metadata['units'] = dict(zip(
            df.columns,
            unit_values
        ))
        data.dataframe = df
        data.trip = trip
        data.save()
