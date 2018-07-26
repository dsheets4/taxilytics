import os
import logging
import pandas as pd

# Allow multi-processing on Windows.
from django_util import setup
setup.windows_multiprocessing_with_django()

from entity.models import Organization

from .taxi_common import create_datadefinition, remove_impossible
from .taxiloader import TaxiLoader


logger = logging.getLogger(__name__)


class Shenzhen(TaxiLoader):
    header_names = (
        'common_id',
        'timestamp',
        'passenger',
        'speed',
        'heading',
        'latitude',
        'longitude'
    )
    units_row = (
        # 'string',
        # 'unix time',
        'bool',
        'km/h',
        'degrees',
        'degrees',
        'degrees'
    )
    types_row = (
        # 'string',
        # 'unix time',
        'boolean',
        'float',
        'float',
        'double precision',
        'double precision'
    )
    data_metadata = create_datadefinition(
        header_names[2:],
        units=units_row,
        types=types_row,
        origin=['recorded'] * len(types_row)
    )

    def __init__(self, organization=None, **kwargs):
        if organization is None:
            organization, created = Organization.objects.get_or_create(
                name='Shenzhen',
                timezone='Asia/Shanghai'
            )
            if created:
                logger.info('Organization {} created'.format(organization.name))
        super().__init__(organization, **kwargs)

    def accept(self, input_resource):
        filename, extension = os.path.splitext(input_resource)
        return (
            os.path.isfile(input_resource) and
            extension == '.good'
        )

    def resource_to_dataframe(self, input_resource, **kwargs):
        df = pd.read_csv(
            input_resource,
            index_col=['common_id', 'timestamp'],
            parse_dates=['timestamp'],
            names=self.header_names,
            usecols=[0,1,2,3,4,5,6],  # Omit road and road id columns
            converters={
                'common_id': lambda p: p.strip()[2:]  # Cleans the corrupted unicode from the front.
            }
        )
        df.index = df.index.set_levels(
            df.index.levels[1].tz_localize('Asia/Shanghai'),  # .tz_convert('UTC')
            level=1
        )
        df = remove_impossible(df)  # Remove rows with data that is impossible
        df = df[~df.index.duplicated()]
        # df = remove_safe_dups(df)  # Remove rows where all data is the same
        return df


class Shenzhen2011(TaxiLoader):
    header_names = [
        'common_id',
        'longitude',
        'latitude',
        'timestamp',
        'speed',
        'heading',
        'unknown',
        'passenger'
    ]
    units_row = (
        # 'string',
        'degrees',
        'degrees',
        # 'unix time',
        'km/h',
        'degrees',
        'bool',
        'bool',
    )
    types_row = (
        # 'string',  # common_id
        'double precision',  # longitude
        'double precision',  # latitude
        # 'timestamp',   # timestamp
        'float',  # speed
        'float',  # heading
        'boolean',  # unknown
        'boolean'  # passenger
    )
    data_metadata = create_datadefinition(
        header_names[1:3] + header_names[4:],
        units=units_row,
        types=types_row,
        origin=['recorded'] * len(types_row)
    )

    def __init__(self, organization=None, **kwargs):
        if organization is None:
            organization, created = Organization.objects.get_or_create(
                name='Shenzhen2011',
                timezone='Asia/Shanghai'
            )
            if created:
                logger.info('Organization {} created'.format(organization.name))
        super().__init__(organization, **kwargs)

    def accept(self, input_resource):
        return os.path.isfile(input_resource)

    def resource_to_dataframe(self, input_resource, **kwargs):
        df = pd.read_csv(
            input_resource,
            index_col=['common_id', 'timestamp'],
            names=self.header_names,
        )
        df.index = df.index.set_levels(
            pd.to_datetime((df.index.levels[1].values*1e9).astype(int)).tz_localize('Asia/Shanghai'),
            level=1
        )
        df = remove_impossible(df)  # Remove rows with data that is impossible
        df = df[~df.index.duplicated()]
        # df = remove_safe_dups(df)  # Remove rows where all data is the same
        return df