import logging
import traceback
from datetime import datetime
from multiprocessing import Pool
import pickle
import binascii
import json

from django.db import connection

import util

from loader.create_id import create_id
from loader.loaders import Loader
from taxi.dataframe_processing import (
    remove_implausible,
    create_linestring,
)

from entity.models import Organization, Entity, DataDefinition
from .taxi_common import (
    roadmatch_query, roadmatch_query_tripdata, roadmatch_def_name, roadmatch_key, roadmatch_metadata,
    TripStream, TripDataStream
)

logger = logging.getLogger(__name__)


class TaxiLoader(Loader):
    roadmatch_increment = 50000  # Number of trips road matched in each UPDATE
    roadmatch_increment_tripdata = 15000  # Number of trips road matched in each UPDATE

    def __init__(self, organization, verbosity=1, debug=None):
        if isinstance(organization, str):
            organization, created = Organization.objects.get_or_create(name=organization)
            if created:
                logger.info('Organization {} created'.format(organization.name))
        if not isinstance(organization, Organization):
            raise Exception('No associated Organization object')

        self.verbosity = verbosity
        self.debug = debug
        self.organization = organization

    def resource_to_dataframe(self, input_resource):
        """ Convert the input_resource (usually a file or directory) to a dataframe """
        raise NotImplementedError(
            'Classes deriving from TaxiLoader must define {}'.format(
                self.resource_to_dataframe.__name__
            )
        )

    def accept(self, input_resource):
        """ Return true if the input resource can be read by this loader. """
        raise NotImplementedError(
            'Classes deriving from TaxiLoader must define {}'.format(
                self.accept.__name__
            )
        )

    def get_datadefinition(self):
        """ This is a generic implementation, more complex versions are possible. """
        data_def, _ = DataDefinition.objects.get_or_create(
            short_name='{} Recorded Data'.format(self.__class__.__name__),
            definition=self.data_metadata
        )
        return data_def

    def dataframe_stream(self, trip_stream):
        """ Streams the dataframe to the database, which is much faster than using the ORM. """
        start_time = datetime.now()
        logger.info('Streaming Trips from {}.'.format(trip_stream.input_resource))
        with connection.cursor() as cursor:
            cursor.copy_expert(
                """
                COPY entity_trip({})
                FROM STDOUT
                DELIMITER '{}'
                """.format(trip_stream.columns(), trip_stream.delimiter),
                file=trip_stream
            )
            num_trips = cursor.rowcount
            logger.info('Streaming TripDatas from {}.'.format(trip_stream.input_resource))
            tripdata_stream = trip_stream.tripdatastream()
            cursor.copy_expert(
                """
                COPY entity_tripdata({})
                FROM STDOUT
                DELIMITER '{}'
                """.format(tripdata_stream.columns(), tripdata_stream.delimiter),
                file=tripdata_stream
            )
            # logger.info('Streaming TripDataArrays from {}.'.format(trip_stream.input_resource))
            # tripdata_streamarray = trip_stream.tripdatastreamarray()
            # cursor.copy_expert(
            #     """
            #     COPY entity_tripdatadecimal({})
            #     FROM STDOUT
            #     DELIMITER '{}'
            #     """.format(tripdata_streamarray.columns(), tripdata_streamarray.delimiter),
            #     file=tripdata_streamarray
            # )
            num_tripdatas = cursor.rowcount
            logger.info('(df): Loaded {} containing {} trips and {} tripdatas in {}.'.format(
                trip_stream.input_resource,
                num_trips, num_tripdatas,
                datetime.now()-start_time
            ))

    def clean(self, workers):
        """ This get run at the end of the loading phase after ALL input_resources have been loaded """
        self.roadmatch_tripdata(workers)

    def roadmatch(self, workers):
        """ Standard multi-processing execution for road matching trips. """
        job_args = []
        with connection.cursor() as cursor:
            start_time = datetime.now()

            roadmatch_def, _ = DataDefinition.objects.get_or_create(
                short_name=roadmatch_def_name,
                definition=roadmatch_metadata
            )

            logger.info('Roadmatch(metadata): Querying for id range to generate parallel partitions')
            cursor.execute(
                "SELECT id FROM entity_trip WHERE NOT metadata ? '{}' ORDER BY id;".format(
                    roadmatch_key
                ))
            job_id = 0
            total_trips = 0
            id_list_chunk = cursor.fetchmany(self.roadmatch_increment)
            while len(id_list_chunk) > 0:
                job_id += 1
                total_trips += len(id_list_chunk)
                job_args.append((id_list_chunk[0][0], id_list_chunk[-1][0], job_id))
                id_list_chunk = cursor.fetchmany(self.roadmatch_increment)
            logger.info(
                'Start roadmatch for {} trips in increments of {} with {} workers over {} jobs.'.format(
                    total_trips, self.roadmatch_increment, workers, job_id
            ))
        connection.close()
        pool = Pool(processes=workers)
        results = pool.starmap(roadmatch_query, job_args)
        pool.close()
        pool.join()
        results = sum(results)
        logger.info('Roadmatch: {} rows in {}'.format(results, datetime.now()-start_time))

    def roadmatch_tripdata(self, workers, roadmatch_func=roadmatch_query_tripdata):
        """ Standard multi-processing execution for roadmatching trips. """
        job_args = []
        with connection.cursor() as cursor:
            start_time = datetime.now()

            roadmatch_short_name = 'Road Match Data'
            roadmatch_def, _ = DataDefinition.objects.get_or_create(
                short_name=roadmatch_short_name,
                definition=roadmatch_metadata
            )

            # TODO: There should be more scalable ways to find the newly added trips.
            #       This queries all the trips and tripdata and finds records without associated
            #       roadmatch data.  However, when inserting data, the IDs being retreived here
            #       had been streamed through the application.  This approach is good for recovery,
            #       for example if the application doesn't complete roadmatching on the data ingest.
            logger.info('Roadmatch(tripdata): Querying for id range to generate parallel partitions')
            cursor.execute(
                """
                    SELECT t.id, td.trip_id
                    FROM entity_trip AS t
                    LEFT JOIN entity_tripdata AS td ON t.id = td.trip_id
                    GROUP BY t.id, td.trip_id
                    HAVING sum(
                        CASE WHEN definition_id = (
                            SELECT dd.id
                            FROM entity_datadefinition AS dd
                            WHERE dd.id={roadmatch_def_id}
                        ) THEN 1 ELSE 0 END
                    ) = 0
                    ORDER BY t.id
                """.format(roadmatch_def_id=roadmatch_def.id)
            )

            job_id = 0
            total_trips = 0
            id_list_chunk = cursor.fetchmany(self.roadmatch_increment_tripdata)
            while len(id_list_chunk) > 0:
                job_id += 1
                total_trips += len(id_list_chunk)
                job_args.append((id_list_chunk[0][0], id_list_chunk[-1][0], job_id))
                id_list_chunk = cursor.fetchmany(self.roadmatch_increment_tripdata)
            logger.info(
                'Start roadmatch tripdata for {} trips in increments of {} with {} workers over {} jobs.'.format(
                    total_trips, self.roadmatch_increment_tripdata, workers, job_id
            ))
        connection.close()
        pool = Pool(processes=workers)
        results = pool.starmap(roadmatch_func, job_args)
        pool.close()
        pool.join()
        results = sum(results)
        logger.info('Roadmatch: {} rows in {}'.format(results, datetime.now()-start_time))

    def process(self, input_resource, workers=8):
        self.dataframe_stream(
            TaxiTripStream(
                input_resource,
                self,
                self.get_datadefinition(),
                workers
            )
        )


class TaxiTripDataStream(TripDataStream):
    """
    Transforms the general input_resource format of a series of columns representing points
    for numerous taxis into a stream compatible with psycopg2's copy_expert function.  This
    class is for adding TripData instances.
    """
    def __init__(self, df, data_def):
        super().__init__(df)
        self.data_def = data_def

    def stream_process(self, trip_id, df):
        try:
            del df['passenger']  # Stored more efficiently as metadata
            metadata = {}
            data = (
                trip_id,
                self.data_def.id,
                json.dumps(metadata),
                # Postgres interprets strings lead with \x as hex strings.
                "\\\\x{}".format(binascii.hexlify(pickle.dumps(df)).decode('utf-8'))
            )
            return data
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.warning('Failed to load data for trip {} due to:\n{}'.format(
                trip_id,
                traceback.format_exc()
            ))
            return None


class TaxiTripDataStreamArray(TripDataStream):
    """
    Transforms the general input_resource format of a series of columns representing points
    for numerous taxis into a stream compatible with psycopg2's copy_expert function.  This
    class is for adding TripData instances.
    """
    def __init__(self, df, data_def):
        super().__init__(df)
        self.data_def = data_def

    def stream_process(self, trip_id, df):
        try:
            try:
                del df['passenger']  # Stored more efficiently as metadata
            except KeyError:
                pass
            data = (
                trip_id,
                # self.data_def.id,
                '{{{}}}'.format(','.join(df.index.strftime("'%Y-%m-%d %H:%M:%S'"))),
                '{{{}}}'.format(','.join(df.columns)),
                '{{{{{}}}'.format(df.to_csv(header=False, index=False, line_terminator='},{')[:-2])
            )
            return data
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.warning('Failed to load data for trip {} due to:\n{}'.format(
                trip_id,
                traceback.format_exc()
            ))
            return None

    def columns(self):
        return 'trip_id, ts, columns, values'


class TaxiTripStream(TripStream):
    """
    Transforms the general input_resource format of a series of columns representing points
    for numerous taxis into a stream compatible with psycopg2's copy_expert function.  This
    class is for adding Trip instances.
    """
    def __init__(self, filename, loader, data_def, workers):
        super().__init__(loader, filename, workers=workers)
        self.archive_uri = filename
        self.tripdata = []
        self.data_def = data_def

        # Because we can't query during the COPY FROM operation, and it's
        # better to do as much work up front anyway, pre-group the taxis
        # according to their entities.
        self.df.sort_index(inplace=True)
        taxi_partitions = self.df.groupby(level='common_id', sort=False)

        self.taxis = []
        for common_id, data in taxi_partitions:
            # Get the entity representing this taxi
            entity, _ = Entity.objects.get_or_create(
                common_id=common_id,
                physical_id=common_id,
                organization=self.loader.organization
            )

            # TODO: Determine if this makes a copy of the data, if so, run the filtering here.
            self.taxis.append((entity, data))

    def iterate(self, df):
        for entity, data in self.taxis:
            logger.debug('Processing taxi {}'.format(entity.common_id))

            # Clean data
            data.index = data.index.droplevel(0)
            data = remove_implausible(data)

            # Split into trips
            trips = (data.passenger.diff(1) != 0).astype('int').cumsum()
            trip_groups = data.groupby(trips, sort=False)

            complete = False  # First trip is marked incomplete
            for name, trip in trip_groups:
                yield self.stream_process(
                    entity,
                    trip,
                    meta={
                        'complete': complete
                    }
                )
                complete = True

    def stream_process(self, entity, data, meta={}):
        try:
            start_datetime = data.index[0]
            trip_id = create_id(
                self.loader.organization.id,
                entity.id,
                start_datetime
            )
            self.tripdata.append((trip_id, data))
            metadata = meta.copy()
            util.update_dict(
                metadata, {
                    'passenger': True if data['passenger'][0] else False,
                }
            )
            geometry = create_linestring(data)

            data = (
                trip_id,
                entity.id,
                start_datetime,
                data.index[0] - start_datetime,
                geometry,
                self.archive_uri,
                json.dumps(metadata),
            )
            return data
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.warning('Failed to load: {} due to:\n{}'.format(
                entity.id,
                traceback.format_exc()
            ))
            return None

    def tripdatastream(self):
        return TaxiTripDataStream(self.tripdata, self.data_def)

    def tripdatastreamarray(self):
        return TaxiTripDataStreamArray(self.tripdata, self.data_def)
