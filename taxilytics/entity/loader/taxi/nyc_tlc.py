import os
import re
import logging
import pandas as pd
from datetime import datetime
from collections import namedtuple
import subprocess
from textwrap import dedent

from django.db import connection

from util import make_enum

from entity.models import Organization

from .taxi_common import (
    remove_impossible, roadmatch_query_tripdata,
)
from .taxiloader import TaxiLoader

from entity.models import DataDefinition


logger = logging.getLogger(__name__)


VendorEnum = make_enum(
    'Unknown',
    'Creative Mobile Technologies, LLC',  # CMT
    'VeriFone Inc.',  # VTS
    'Digital Dispatch Systems Inc.',  # DDS
)

RateCodeEnum = make_enum(
    'Unknown',
    'Standard rate',
    'JFK',
    'Newark',
    'Nassau or Westchester',
    'Negotiated fare',
    'Group ride',
)

PaymentEnum = make_enum(
    'Unknown',
    'Credit card',
    'Cash',
    'No charge',
    'Dispute',
    'Unknown',
    'Voided trip',
)


tripdata_definition = {
    'longitude': {
        'units': 'Degrees',
        'desc': 'WGS-84 Longitude',
        'origin': 'recorded'
    },
    'latitude': {
        'units': 'Degrees',
        'desc': 'WGS-84 Latitude',
        'origin': 'recorded'
    },
    'heading': {
        'units': 'Degrees',
        'desc': 'This field is not valid but required.',
        'origin': 'derived'
    },
}


def nyc_roadmatch(start, end, job_id=None):
    start_time = datetime.now()

    tripdata_def = DataDefinition.objects.get(
        short_name="NYC Trip Data",
        definition=tripdata_definition
    )

    # Generate a trip data for each point.
    with connection.cursor() as cursor:
        cursor.execute(
            """
                WITH extracted AS (
                    WITH dump AS (
                        SELECT id, start_datetime as starttime, ((ST_DumpPoints(geometry)).geom) as pt
                        FROM entity_trip
                        WHERE id BETWEEN {start} AND {end}
                    )
                    SELECT
                        id,
                        array_agg((starttime + ST_Z(pt)* interval '1 second')) as ts,
                        array_agg(ST_X(pt)) as longitude,
                        array_agg(ST_Y(pt)) as latitude,
                        '{{NaN,NaN}}'::float[] as heading
                    FROM dump
                    WHERE
                        id NOT IN (SELECT trip_id FROM entity_tripdata WHERE definition_id={def_id})
                    GROUP BY id
                )
                INSERT INTO entity_tripdata(trip_id, _dataframe, metadata, definition_id) (
                    SELECT
                        id as trip_id,
                        pd_create_df(
                            pd_create_series(ts, longitude, 'longitude'),
                            pd_create_series(ts, latitude, 'latitude'),
                            pd_create_series(ts, heading, 'heading')
                        ) as _dataframe,
                        '{{}}'::jsonb as metadata,
                        {def_id} as definition_id
                    FROM extracted
                )
            """.format(start=start, end=end, def_id=tripdata_def.id)
        )
        logger.info('{}Created {} TripDatas in {} for id range {}:{}.'.format(
            'Job({}): '.format(job_id) if job_id is not None else '',
            cursor.rowcount, datetime.now() - start_time,
            start, end
        ))

        return cursor.rowcount


class NycTlc(TaxiLoader):
    roadmatch_increment = 100000  # With only two per trip, can do quite a few at a time.

    # These are defined in the derived classes
    pickup_datetime_label = ''
    dropoff_datetime_label = ''
    taxi_type = ''
    file_prefix = ''
    organization_name = ''

    # These are shared among derived classes
    data_metadata = {
        'vendorid': {
            'units': VendorEnum().reverse_mapping,
            'desc': 'A code indicating the TPEP/LPEP provider that provided the record.',
            'origin': 'recorded'
        },
        'pickup_datetime': {
            'units': 'datetime',
            'desc': 'ISO8601 date and time format pickup time of the trip in EDT.',
            'origin': 'recorded'
        },
        'dropoff_datetime': {
            'units': 'datetime',
            'desc': 'ISO8601 date and time format dropoff time of the trip in EDT.',
            'origin': 'recorded'
        },
        'passenger_count': {
            'units': 'integer',
            'desc': 'The number of passengers in the vehicle.  This is a driver-entered value.',
            'origin': 'recorded'
        },
        'trip_distance': {
            'units': 'miles',
            'desc': 'The elapsed trip distance in miles reported by the taximeter.',
            'origin': 'recorded'
        },
        'pickup_longitude': {
            'units': 'WGS-84',
            'desc': 'GPS Longitude when the meter was engaged.',
            'origin': 'recorded'
        },
        'pickup_latitude': {
            'units': 'WGS-84',
            'desc': 'GPS Latitude when the meter was engaged.',
            'origin': 'recorded'
        },
        'ratecodeid': {
            'units': RateCodeEnum().reverse_mapping,
            'desc': 'The final rate code in effect at the end of the trip.',
            'origin': 'recorded'
        },
        'store_and_fwd_flag': {
            'units': 'Boolean',
            'desc': (
                'This flag indicates whether the trip record was held in vehicle '
                'memory before sending to the vendor, aka “store and forward", '
                'because the vehicle did not have a connection to the server.'
            ),
            'origin': 'recorded'
        },
        'dropoff_longitude': {
            'units': 'WGS-84',
            'desc': 'GPS Longitude when the meter was disengaged.',
            'origin': 'recorded'
        },
        'dropoff_latitude': {
            'units': 'WGS-84',
            'desc': 'GPS Latitude when the meter was disengaged.',
            'origin': 'recorded'
        },
        'payment_type': {
            'units': PaymentEnum().reverse_mapping,
            'desc': 'A numeric code signifying how the passenger paid for the trip.',
            'origin': 'recorded',
        },
        'fare_amount': {
            'units': 'USD',
            'desc': 'The time-and-distance fare calculated by the meter.',
            'origin': 'recorded',
        },
        'extra': {
            'units': 'USD',
            'desc': 'Miscellaneous extras and surcharges. Currently, this only includes the $0.50 and $1 rush hour and overnight charges.',
            'origin': 'recorded',
        },
        'mta_tax': {
            'units': 'USD',
            'desc': '$0.50 MTA tax that is automatically triggered based on the metered rate in use.',
            'origin': 'recorded',
        },
        'tip_amount': {
            'units': 'USD',
            'desc': 'Tip amount – This field is automatically populated for credit card tips. Cash tips are not included.',
            'origin': 'recorded',
        },
        'tolls_amount': {
            'units': 'USD',
            'desc': 'Total amount of all tolls paid in trip.',
            'origin': 'recorded',
        },
        'improvement_surcharge': {
            'units': 'USD',
            'desc': '$0.30 improvement surcharge assessed trips at the flag drop. The improvement surcharge began being levied in 2015.',
            'origin': 'recorded',
        },
        'total_amount': {
            'units': 'USD',
            'desc': 'The total amount charged to passengers. Does not include cash tips.',
            'origin': 'recorded',
        },
    }

    derived_metadata = {
        'gid': {
            'units': 'unique id',
            'desc': 'OSM database ID for the matched geometry',
            'origin': 'derived'
        },
        'dist': {
            'units': 'meters',
            'desc': 'Distance from the sample point to the gid',
            'origin': 'derived'
        },
    }

    def __init__(self, organization=None, **kwargs):
        if organization is None:
            organization, created = Organization.objects.get_or_create(
                name='NycTlc',
                timezone='America/New_York'
            )
            if created:
                logger.info('Organization {} created'.format(organization.name))
        super().__init__(organization, **kwargs)
        self.road_match_columns = [
            'pickup_longitude', 'pickup_latitude',
            'dropoff_longitude', 'dropoff_latitude'
        ]
        self.input_resource = None
        self.config = None

        tripdata_def, _ = DataDefinition.objects.get_or_create(
            short_name="NYC Trip Data",
            definition=tripdata_definition
        )

    def get_config(self, input_resource):
        filename = os.path.basename(input_resource)
        for cfg in nyc_config:
            if cfg.pattern.match(filename):
                return cfg
        return None

    def accept(self, input_resource):
        if os.path.isfile(input_resource):
            if self.get_config(input_resource) is not None:
                return True
        return False

    def common_columns(self, name, config):
        if name == config.pickup_datetime_label:
            name = 'pickup_datetime'
        elif name == config.dropoff_datetime_label:
            name = 'dropoff_datetime'
        return name.lower()

    def resource_to_dataframe(self, input_resource):
        config = self.get_config(input_resource)
        df = pd.read_csv(
            input_resource,
            parse_dates=[config.pickup_datetime_label, config.dropoff_datetime_label]
        )

        # Lower case makes yellow and green taxis have more common column names.
        df.columns = [self.common_columns(c, config) for c in df.columns]

        df['store_and_fwd_flag'] = df['store_and_fwd_flag'].map({'Y': True, 'N': False})

        # Based on the existence of times such as between 2 and 3AM on 3/8/2015, the timestamp
        # is not in normal America/New York timezone, since that time does not exist.  Therefore
        # the times are being cast to UTC as there is no information on what timezone is actually
        # being employed by the data.
        df['pickup_datetime'] = (
            # pd.Index(df['pickup_datetime']).tz_localize('America/New_York')
            pd.Index(df['pickup_datetime']).tz_localize('UTC')
        )
        df['dropoff_datetime'] = (
            # pd.Index(df['dropoff_datetime']).tz_localize('America/New_York')
            pd.Index(df['dropoff_datetime']).tz_localize('UTC')
        )
        df = remove_impossible(df, 'pickup_longitude', 'pickup_latitude')
        df = remove_impossible(df, 'dropoff_longitude', 'dropoff_latitude')

        # Many of the pickup and dropoff points are exactly the same.
        good_gps_points = (
            (df['pickup_longitude'] != df['dropoff_longitude']) |
            (df['pickup_latitude'] != df['dropoff_latitude'])
        )
        df = df[good_gps_points]

        return df

    def process(self, input_resource, _=None):
        # NOTE: Most process methods are implemented using the DataFrame streams. However, it
        #       is MUCH faster to pipe the data through awk and stream it directly than it is
        #       to read the dataframe.  This is possible here because each data file input row
        #       is one trip whereas other formats require pre-processing to create the trips,
        #       which is provided by pandas.  Also, the TripData relation is generated from the
        #       DataFrame but NYC data omits by only providing pickup and dropoff points.
        # self.dataframe_stream(NycTlcTripStream(input_resource))
        self.awk_stream(input_resource)

    def awk_stream(self, input_resource):
        start_time = datetime.now()
        config = self.get_config(input_resource)
        self.input_resource = input_resource

        # Here a stream is setup to pipe the data file through awk for preprocessing and format
        # conversion and then the stdout is piped to postgres for data loading via COPY FROM.
        ifilename = os.path.abspath(input_resource)
        ps_awk = subprocess.Popen(
            [
                'awk',
                '-v', 'f={}'.format(ifilename),
                awk_template.format(**config.columns),
                ifilename
            ],
            stdout=subprocess.PIPE
        )

        # This connects the stream output from awk into the database upload.
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION TIME ZONE 'America/New_York';")
            cursor.copy_expert(
                """
                    COPY entity_trip(id, start_datetime, duration, geometry, archive_uri, metadata)
                    FROM STDOUT DELIMITER '|'
                """,
                file=ps_awk.stdout
            )
            ps_awk.wait(100)
            logger.info('(awk) Loaded {} containing {} records in {}.'.format(
                input_resource,
                cursor.rowcount,
                datetime.now()-start_time
            ))

    def clean(self, workers=None):
        """
        Cleans the data that was added to the database.  Used to provide clean functions when the stream
        input can't properly filter records.  This is called before restoring database constraints as
        well and should provide integrity checks and restoration.
        """
        start = datetime.now()

        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM entity_trip
                WHERE
                    NOT ST_GeomFromText('POLYGON((-180 -90, 180 -90, 180 90, -180 90, -180 -90))') ~ geometry
                    OR
                    NOT ST_IsValid(geometry)
                """.replace('\n', ' '))
            logger.info('Removed {} invalid rows in {} during clean operation'.format(
                cursor.rowcount, datetime.now()-start
            ))

        self.roadmatch_tripdata(workers, nyc_roadmatch)


awk_template = dedent("""\
    BEGIN {{ FS = ","; OFS = "|"}}
    {{
        if ( NR == 1 ) {{
            next
        }}
        if (/^\s*$/ ) {{ next; }}
        if ( {pu_lon} == "0" || {pu_lat} == "0" || {do_lon} == "0" || {do_lat} == "0" ) {{
            print "Invalid position " FILENAME "(" NR "): " $0 > "/dev/stderr"
            next
        }}
        match($2, /^([0-9]{{4}})-([0-9]{{2}}).*/, ymd)
        t1 = gensub(/[-:]/," ","g",$2);
        t2 = gensub(/[-:]/," ","g",$3);
        d1=mktime(t1);
        d2=mktime(t2);
        if ( d2-d1 > 1000000 ) {{
            print "Invalid timestamp " FILENAME "(" NR "): " $0 > "/dev/stderr"
            next
        }}
        gsub(/\r/, "", $NF);

        if( $1==1 || $1=="CMT" ) vendor="Creative Mobile Technologies, LLC";
        else if( $1==2 || $1=="VTS" ) vendor="VeriFone Inc.";
        else if( $1=="DDS" ) vendor="Digital Dispatch Systems Inc.";
        else vendor=$1;

        py = toupper({pay_type})
        if( py=="2" || py=="CASH" || py=="CAS" || py=="CSH" ) payment="Cash"
        else if( py=="1" || py=="CRD" || py=="CRE" || py=="CREDIT" ) payment="Credit"
        else if( py=="3" ) payment="No Charge"
        else if( py=="4" ) payment="Dispute"
        else if( py=="5" ) payment="Unknown"
        else if( py=="6" ) payment="Voided Trip"
        else payment={pay_type}

        if( {rate_code}==1 ) rate="Standard rate"
        else if( {rate_code}==2 ) rate="JFK"
        else if( {rate_code}==3 ) rate="Newark"
        else if( {rate_code}==4 ) rate="Nassau or Westchester"
        else if( {rate_code}==5 ) rate="Negotiated fare"
        else if( {rate_code}==6 ) rate="Group ride"
        else rate={rate_code}

        if( {trip_type}==1 ) tt="Street-hail"
        else if( {trip_type}==2 ) tt="Dispatch"
        else tt={trip_type}

        if( {store_fwd_flag}=="Y" ) sf="true";
        else sf="false";

        row_id=sprintf("%d", ((ymd[1]-2000)*100+ymd[2])) sprintf("%015d", FNR)

        print row_id, $2, d2-d1, "SRID=4326;LINESTRING(" {pu_lon} " " {pu_lat} " 0," {do_lon} " " {do_lat} " " d2-d1 ")", FILENAME"?line="NR, \\
            "{{"\\
                "\\"vendor\\":" "\\""vendor"\\"" \\
                ",\\"trip_distance\\":" sprintf("%g", {trip_dist}) \\
                ",\\"passenger_count\\":" {passenger_count} \\
                ",\\"rate\\":"  "\\""rate"\\"" \\
                ",\\"fare_amount\\":" sprintf("%.2f", {fare_amount}) \\
                ",\\"mta_tax\\":" sprintf("%.2f", {mta_tax}) \\
                ",\\"tip_amount\\":" sprintf("%.2f", {tip_amount}) \\
                ",\\"tolls_amount\\":" sprintf("%.2f", {tolls_amount}) \\
                ",\\"ehail_fee\\":" sprintf("%.2f", {ehail_fee}) \\
                ",\\"extra\\":" sprintf("%.2f", {extra}) \\
                ",\\"improvement_surcharge\\":" sprintf("%.2f", {imp_charge}) \\
                ",\\"total_amount\\":" sprintf("%.2f", {total_amount}) \\
                ",\\"payment_type\\":" "\\""payment"\\"" \\
                ",\\"store_and_fwd_flag\\":" sf \\
                ",\\"trip_type\\":" "\\""tt"\\"" \\
                ",\\"taxi_type\\": \\"{taxi_type}\\"" \\
            "}}"
    }}
""")


NycTlcConfig = namedtuple('NycTlcConfig', [
    # Used for awk_stream
    'pattern',
    'columns',
    # Used for dataframe_stream
    'pickup_datetime_label',
    'dropoff_datetime_label',
    'taxi_type',
    'organization_name',
])


nyc_config = [
    # yellow v1
    NycTlcConfig(
        pattern=re.compile('yellow_tripdata_(2009|201[0-4])'),
        columns={
            'passenger_count': '$4',
            'trip_dist': '$5',
            'pu_lon': '$6',
            'pu_lat': '$7',
            'do_lon': '$10',
            'do_lat': '$11',
            'rate_code': '$8',
            'store_fwd_flag': '$9',
            'pay_type': '$12',
            'fare_amount': '$13',
            'extra': '$14',
            'mta_tax': '$15',
            'imp_charge': '0',
            'tip_amount': '$16',
            'tolls_amount': '$17',
            'ehail_fee': 0,
            'total_amount': '$18',
            'trip_type': "Unknown",
            'taxi_type': 'yellow',
            'fields': 18
        },
        pickup_datetime_label='pickup_datetime',  # Not correct for 2009
        dropoff_datetime_label='dropoff_datetime',   # Not correct for 2009
        taxi_type='yellow',
        organization_name='NycTlcYellow',
    ),
    # yellow v2
    NycTlcConfig(
        pattern=re.compile('yellow_tripdata_(2015|2016-(0[1-6]))'),
        columns={
            'passenger_count': '$4',
            'trip_dist': '$5',
            'pu_lon': '$6',
            'pu_lat': '$7',
            'do_lon': '$10',
            'do_lat': '$11',
            'rate_code': '$8',
            'store_fwd_flag': '$9',
            'pay_type': '$12',
            'fare_amount': '$13',
            'extra': '$14',
            'mta_tax': '$15',
            'imp_charge': '$18',
            'tip_amount': '$16',
            'tolls_amount': '$17',
            'ehail_fee': 0,
            'total_amount': '$19',
            'trip_type': "Unknown",
            'taxi_type': 'yellow',
            'fields': 19
        },
        pickup_datetime_label='tpep_pickup_datetime',
        dropoff_datetime_label='tpep_dropoff_datetime',
        taxi_type='yellow',
        organization_name='NycTlcYellow',
    ),
    # # yellow v3
    # NycTlcConfig(
    #     pattern=re.compile('yellow_tripdata_2016-(0[7-9]|1[0-2])'),
    #     columns={
    #         # Pickup and Dropoff locations change to areas, requires revision of data model
    #     },
    #     pickup_datetime_label='tpep_pickup_datetime',
    #     dropoff_datetime_label='tpep_dropoff_datetime',
    #     taxi_type='yellow',
    #     organization_name='NycTlcYellow',
    # ),
    # green v1
    NycTlcConfig(
        pattern=re.compile('green_tripdata_(2009|201[0-4])'),
        columns={
            'passenger_count': '$10',
            'trip_dist': '$11',
            'pu_lon': '$6',
            'pu_lat': '$7',
            'do_lon': '$8',
            'do_lat': '$9',
            'rate_code': '$5',
            'store_fwd_flag': '$4',
            'pay_type': '$19',
            'fare_amount': '$12',
            'extra': '$13',
            'mta_tax': '$14',
            'imp_charge': 0,
            'tip_amount': '$15',
            'tolls_amount': '$16',
            'ehail_fee': '$17',
            'total_amount': '$18',
            'trip_type': '$20',
            'taxi_type': 'green',
            'fields': 20
        },
        pickup_datetime_label='lpep_pickup_datetime',
        dropoff_datetime_label='Lpep_dropoff_datetime',
        taxi_type='green',
        organization_name='NycTlcGreen',
    ),
    # green v2
    NycTlcConfig(
        pattern=re.compile('green_tripdata_(2015|2016-(0[1-6]))'),
        columns={
            'passenger_count': '$10',
            'trip_dist': '$11',
            'pu_lon': '$6',
            'pu_lat': '$7',
            'do_lon': '$8',
            'do_lat': '$9',
            'rate_code': '$5',
            'store_fwd_flag': '$4',
            'pay_type': '$20',
            'fare_amount': '$12',
            'extra': '$13',
            'mta_tax': '$14',
            'imp_charge': '$18',
            'tip_amount': '$15',
            'tolls_amount': '$16',
            'ehail_fee': '$17',
            'total_amount': '$19',
            'trip_type': '$21',
            'taxi_type': 'green',
            'fields': 21
        },
        pickup_datetime_label='lpep_pickup_datetime',
        dropoff_datetime_label='Lpep_dropoff_datetime',
        taxi_type='green',
        organization_name='NycTlcGreen',
    ),
    # # green v3 - This version doesn't provide point locations
    # NycTlcConfig(
    #     pattern=re.compile('green_tripdata_2016-(0[7-9]|1[0-2])'),
    #     columns={
    #         # Pickup and Dropoff locations change to areas, requires revision of data model
    #     },
    #     pickup_datetime_label='lpep_pickup_datetime',
    #     dropoff_datetime_label='lpep_dropoff_datetime',
    #     taxi_type='green',
    #     organization_name='NycTlcGreen',
    # ),
]
