import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime

# Allow multi-processing on Windows.
from django_util import setup
setup.windows_multiprocessing_with_django()

from django.db import connection


logger = logging.getLogger(__name__)


def sample_df(df, rows=5):
    """ Returns N rows as a sample of the passed in dataframe. """
    return df.sample(rows).sort_index()


def human_size(num, suffix=''):
    """ Given a number in bytes, format it to the nearest size increment.  e.g. 1024 is 1K """
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def create_datadefinition(header_names, **kwargs):
    """ Combines two lists into the data definition for the recorded data.
    :param header_names:
    :param kwargs: Keywords of label and list elements
    :return: datadefinition
    """
    data_metadata = {}
    for i, hdr_label in enumerate(header_names):
        data_metadata[hdr_label] = {}
        for kw, val in kwargs.items():
            data_metadata[hdr_label][kw] = val[i]
    return data_metadata



roadmatch_metadata = {
    'gid': {
        'units': 'unique id',
        'desc': 'OSM geometry ID for the matched street',
        'origin': 'derived'
    },
    # 'dist': {
    #     'units': 'meters',
    #     'desc': 'Distance from the sample point to the gid',
    #     'origin': 'derived'
    # },
    # 'delta_hdg': {
    #     'units': 'degrees',
    #     'desc': 'Difference in heading from the trajectory to road segment.  Positive right, negative left',
    #     'origin': 'derived'
    # }
}


roadmatch_key = 'roadmatch'
roadmatch_def_name = 'Road Match Data'


def roadmatch_query(start, end, job_id=None):
    start_time = datetime.now()
    with connection.cursor() as cursor:
        ranges = 'AND id BETWEEN {} AND {}'.format(start, end)
        cursor.execute("""
            WITH roadmatch_metadata AS (
                WITH expanded_json_keys AS (
                    WITH roadmatch_all AS (
                        SELECT
                            id
                            , osm_roadmatch_line(geometry) as matches
                            , metadata
                        FROM entity_trip
                        WHERE
                            NOT metadata ? '{roadmatch_key}'
                            {ranges}
                    )
                    SELECT id, j1.key, j1.value FROM roadmatch_all, jsonb_each(metadata) as j1
                    UNION
                    SELECT id, '{roadmatch_key}', to_json(roadmatch_all.matches)::jsonb FROM roadmatch_all
                )
                SELECT
                    id,
                    json_object_agg(key, value)::jsonb as metadata
                FROM expanded_json_keys
                GROUP BY id
            )
            UPDATE entity_trip
            SET metadata=roadmatch_metadata.metadata
            FROM roadmatch_metadata
            WHERE entity_trip.id=roadmatch_metadata.id
        """.format(roadmatch_key=roadmatch_key, ranges=ranges).replace('\n', ' '))
        logger.info('{}Roadmatched {} in {} for id range {}:{}.'.format(
            'Job({}): '.format(job_id) if job_id is not None else '',
            cursor.rowcount, datetime.now() - start_time,
            start, end
        ))
        return cursor.rowcount


def roadmatch_query_tripdata(start, end, job_id=None):
    start_time = datetime.now()
    with connection.cursor() as cursor:
        ranges = 'trip_id BETWEEN {} AND {}'.format(start, end)
        cursor.execute("""
            WITH matched_agg AS (
                WITH matched AS (
                    WITH needs_matched AS (
                        SELECT
                            trip_id,
                            pd_join(array_agg(_dataframe)) AS df
                        FROM entity_tripdata AS td
                        WHERE {ranges}
                        GROUP BY trip_id
                        HAVING sum(
                            CASE WHEN definition_id = (
                            SELECT dd.id
                            FROM entity_datadefinition AS dd
                            WHERE short_name='{roadmatch_def_name}'
                            ) THEN 1 ELSE 0 END
                        ) = 0
                    )
                    SELECT
                        trip_id,
                        df.ts,
                        osm_roadmatch_point(
                            ST_SetSRID(ST_MakePointM(df.longitude, df.latitude, df.heading),4326)
                        ) as osm
                    FROM
                        needs_matched as td,
                        pd_df_to_record(df) AS df(
                            ts timestamp with time zone,
                            longitude double precision,
                            latitude double precision,
                            heading float
                        )
                )
                SELECT
                    trip_id,
                    '{{}}'::jsonb as metadata,
                    (SELECT id FROM entity_datadefinition WHERE short_name='{roadmatch_def_name}') as definition_id,
                    array_agg(ts) as ts,
                    array_agg(osm) as osm
                FROM matched AS td
                WHERE osm IS NOT NULL
                GROUP BY trip_id
            )
            INSERT INTO entity_tripdata(trip_id, metadata, definition_id, _dataframe)(
                SELECT
                    trip_id,
                    metadata,
                    (SELECT id FROM entity_datadefinition WHERE short_name='{roadmatch_def_name}') as definition_id,
                    pd_create_df(pd_create_series(ts, osm, 'osm')) as _dataframe
                FROM matched_agg
            );
        """.format(roadmatch_def_name=roadmatch_def_name, ranges=ranges).replace('\n', ' '))
        logger.info('{}Roadmatched {} in {} for id range {}:{}.'.format(
            'Job {} '.format(job_id) if job_id is not None else '',
            cursor.rowcount, datetime.now() - start_time,
            start, end
        ))
        return cursor.rowcount


class TripDataStream(metaclass=ABCMeta):
    delimiter = '|'

    def __init__(self, df):
        self.df = df
        self.iterator = self.iterate(self.df)

    def iterate(self, df):
        """ Generator that iterates a list of (trip_id, dataframe) instances """
        for trip_id, data in self.df:
            yield self.stream_process(trip_id, data)

    def read(self, _=None):  # _ is size
        """
        This will be called by copy_expert, which passes in a size but only ever cares
        when the size is 0.
        """
        try:
            string = '%s\n' % self.delimiter.join([str(t) for t in next(self.iterator)])
            return string
        except StopIteration:
            return ''

    @abstractmethod
    def stream_process(self, trip_id, df):
        """
        Returns a tuple in the form (trip_id, definition_id, metadata, _dataframe)
        """
        raise NotImplementedError('Classes derived from TripStream must implement stream_process')

    def columns(self):
        return 'trip_id, definition_id, metadata, _dataframe'


class TripStream(metaclass=ABCMeta):
    delimiter = '|'
    end = '\n'

    def __init__(self, loader, filename, **kwargs):
        self.input_resource = filename
        self.loader = loader
        self.df = loader.resource_to_dataframe(filename, **kwargs)
        self.iterator = self.iterate(self.df)

    @abstractmethod
    def iterate(self, df):
        """
        Returns an iterator that provides data at the Trip perspective
        """
        raise NotImplementedError('Classes derived from TripStream must implement iterate')

    def read(self, size=None):
        try:
            string = self.delimiter.join([str(t) for t in next(self.iterator)]) + self.end
            return string
        except StopIteration:
            return ''

    @abstractmethod
    def stream_process(self, common_id, data, meta={}):
        """
        Returns a tuple in the form (id, start_datetime, duration, geometry, archive_uri, metadata)
        """
        raise NotImplementedError('Classes derived from TripStream must implement stream_process')

    @abstractmethod
    def tripdatastream(self):
        """
        Returns a TripDataStream associated with the same data used in this stream
        """
        raise NotImplementedError('Classes derived from TripStream must implement tripdatastream')

    @abstractmethod
    def tripdatastreamarray(self):
        """
        Returns a TripDataStream associated with the same data used in this stream
        """
        raise NotImplementedError('Classes derived from TripStream must implement tripdatastreamarray')

    def columns(self):
        return 'id, entity_id, start_datetime, duration, geometry, archive_uri, metadata'
