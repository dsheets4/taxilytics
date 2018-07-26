import os
import logging
import pandas as pd
from multiprocessing import Pool

import util

from entity.models import Organization

from .taxi_common import (
    create_datadefinition, remove_impossible,
)
from .taxiloader import TaxiLoader


logger = logging.getLogger(__name__)


def strip(text):
    try:
        return text.strip()
    except AttributeError:
        return text


def clean_plate(text):
    text = text.strip()
    if text.startswith('¿'):
        text = 'zhe' + text[1:]
    return text


def make_int(text):
    return int(make_float(text))


def make_float(text):
    return float(text.strip())


class Hangzhou(TaxiLoader):
    header_names = (
        # Message_id and taxi_id are specific to the original database.
        # 'message_id',
        # 'taxi_id',
        'common_id',
        'latitude',
        'longitude',
        # These fields px and py are always 0 in the data.
        # 'px',
        # 'py',
        'speed',
        'heading',
        'passenger',
        'state',
        'timestamp',  # 'speed_time',  # Better index time
        # 'db_time',
        # Can't use segments since the format uses [] and , and " in same field.
        # 'segments',  # Added by Farah (from research group)
    )

    units_row = (
        'degrees',  # latitude
        'degrees',  # longitude
        'km/h',  # speed
        'degrees',  # heading
        'bool',  # Loaded
        'bool',  # State
    )

    types_row = (
        'double precision',  # latitude
        'double precision',  # longitude
        'float',  # speed
        'float',  # heading
        'boolean',  # Loaded
        'boolean',  # State
    )

    data_metadata = create_datadefinition(
        header_names[1:-1],
        units=units_row,
        type=types_row,
        origin=['recorded'] * len(types_row)
    )

    def __init__(self, organization=None, **kwargs):
        if organization is None:
            organization, created = Organization.objects.get_or_create(
                name='Hangzhou',
                timezone='Asia/Shanghai'
            )
            if created:
                logger.info('Organization {} created'.format(organization.name))
        super().__init__(organization, **kwargs)

    def accept(self, input_resource):
        if os.path.isdir(input_resource):
            for (root, dirs, files) in os.walk(input_resource):
                if len(dirs) == 0 and len(files) > 0 and files[0].startswith('result_'):
                    return True
                else:
                    return False
        elif os.path.isfile(input_resource):
            filename = os.path.basename(input_resource)
            return filename.startswith('result_')
        return False

    def resource_to_dataframe(self, input_resource, workers=8):
        """
        Performs the multiple file data frame load using multiple processes.  A similar thing
        is possible with threading but the performance is nowhere near the same.
        :param input_resource:
        :param workers:
        :return:
        """
        data_files = []
        if os.path.isdir(input_resource):
            # With multiple files composing a single day we can load several in parallel
            # and then combine them in the Main Thread as the workers complete.
            for (root, dirs, files) in os.walk(input_resource):
                data_files += [os.path.join(root, f) for f in util.sort_nicely(files)]
                break  # Only goes one level deep so sub-dirs are ignored

            pool = Pool(processes=workers)
            df = pd.concat(
                pool.map(self.resource_to_dataframe_file, [f for f in data_files])
            )
            pool.close()
            pool.join()
        elif os.path.isfile(input_resource):
            df = self.resource_to_dataframe_file(input_resource)
        else:
            raise FileNotFoundError(input_resource)

        logger.info('DataFrame composition from {} complete'.format(input_resource))
        return df

    def resource_to_dataframe_file(self, filename):
        logger.info('Composing {} for DataFrame'.format(filename))
        df = pd.read_csv(
            filename,
            comment='[',  # Results in ignoring road matching
            index_col=['common_id', 'timestamp'],
            parse_dates=['timestamp'],  #'db_time'],
            names=self.header_names,
            usecols=[2, 3, 4, 7, 8, 9, 10, 11,],  # Omit unneeded columns
            skipinitialspace=True,
            converters={
                'common_id': clean_plate,  # Cleans the unicode first character.
                'speed': make_float,
                'heading': make_int,
            },
            dayfirst=True,
            # nrows=5000  # Useful for debugging when multiple big files are required.
        )
        df.index = df.index.set_levels(
            df.index.levels[1].tz_localize('Asia/Shanghai'),  # .tz_convert('UTC')
            level=1
        )
        df = remove_impossible(df)  # Remove rows with data that is impossible
        return df
