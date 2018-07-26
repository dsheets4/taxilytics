import re
import os
from textwrap import dedent
from collections import namedtuple
from functools import partial

from taxi.dataframe_processing import (
    map_column, remove_column,
    make_timezone_aware,
    remove_non_moving, remove_impossible
)

from .datadefinition import (
    DefaultLabels, timestamp_columns,
    PaymentEnum
)


# TODO: Portions of the NYCTLC awk script should be constructable via python code
#       For example, the VendorIdEnum could help generate the vendor variable assignment.
awk_template = dedent("""\
    BEGIN {{ FS = ","; OFS = "{output_delim}"}}
    {{
        if ( NR == 1 ) {{
            next
        }}
        if (/^\s*$/ ) {{ next; }}
        if ( {pu_lon} == "0" || {pu_lat} == "0" || {do_lon} == "0" || {do_lat} == "0" ||
            ({pu_lon} == {do_lon} && {pu_lat} == {do_lat}) ) {{
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

        print \\
            row_id, \\
            $2, \\
            d2-d1, \\
            "SRID=4326;LINESTRING(" {pu_lon} " " {pu_lat} " 0," {do_lon} " " {do_lat} " " d2-d1 ")", \\
            FILENAME"?line="NR, \\
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
    'pattern',
    'awk_format_dict',
    'dataframe_parse_args',
    'dataframe_postprocess',
])


common_processing = [
    # Based on the existence of times such as between 2 and 3AM on 3/8/2015, the timestamp
    # is not in normal 'America/New_York' timezone.  One guess is that during a trip the time
    # doesn't reset if it's used to calculate the fare.  Another is that the taxis use UTC.
    partial(make_timezone_aware, ts_col=DefaultLabels.pickup_time, timezone='America/New_York'),
    partial(make_timezone_aware, ts_col=DefaultLabels.dropoff_time, timezone='America/New_York'),
    partial(remove_impossible, lon_label=DefaultLabels.pickup_lon, lat_label=DefaultLabels.pickup_lat),
    partial(remove_impossible, lon_label=DefaultLabels.dropoff_lon, lat_label=DefaultLabels.dropoff_lat),
    partial(
        remove_non_moving,
        pu_lon=DefaultLabels.pickup_lon, pu_lat=DefaultLabels.pickup_lat,
        do_lon=DefaultLabels.dropoff_lon, do_lat=DefaultLabels.dropoff_lat
    ),
    # Filter trips that are less than N seconds
]


yellow_2009_2014_df_columns = [
    DefaultLabels.vendor_id,
    DefaultLabels.pickup_time, DefaultLabels.dropoff_time,
    DefaultLabels.passenger_count, DefaultLabels.trip_distance,
    DefaultLabels.pickup_lon, DefaultLabels.pickup_lat,
    DefaultLabels.rate_code_id, DefaultLabels.store_fwd,
    DefaultLabels.dropoff_lon, DefaultLabels.dropoff_lat,
    DefaultLabels.payment_type,
    DefaultLabels.fare_amt, DefaultLabels.extra, DefaultLabels.mta_tax, DefaultLabels.tip_amt,
    DefaultLabels.tolls_amt,
    DefaultLabels.total_amt,
]
yellow_2009_2014_awk_format_dict = {
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
}


# Mapping used for early data sets prior to the normalized ID as represented by PaymentEnum
pay_type_mapping = {
    'CRD': getattr(PaymentEnum(), 'Credit card'),
    'CRE': getattr(PaymentEnum(), 'Credit card'),
    'CREDIT': getattr(PaymentEnum(), 'Credit card'),
    'CASH': getattr(PaymentEnum(), 'Cash'),
    'CAS': getattr(PaymentEnum(), 'Cash'),
    'CSH': getattr(PaymentEnum(), 'Cash'),
}


def payment_type_normalize(df, pay_type_label):
    df[pay_type_label] = df[pay_type_label].astype(str).str.upper()
    return map_column(df, column=pay_type_label, mapping=pay_type_mapping)


# These abbreviations where used in the 2009 data then changed to the vendor_id in 2010
# Therefore, we map the abbreviation to the corresponding ID here to map to VendorIdEnum
vendor_mapping = {
    'CMT': 1,
    'VTS': 2,
    'DDS': 3
}

dataframe_parse_args = {
     'index_col': False,
     'header': 0,  # Replaces existing names using the 'names' argument
     'infer_datetime_format': True,
     'true_values': ['Y'],
     'false_values': ['N']
 }

nyc_config = [
    # yellow v1
    NycTlcConfig(
        pattern=re.compile('yellow_tripdata_(2009)'),
        awk_format_dict=yellow_2009_2014_awk_format_dict,
        dataframe_postprocess=common_processing + [
            partial(map_column, column=DefaultLabels.vendor_id, mapping=vendor_mapping),
            partial(payment_type_normalize, pay_type_label=DefaultLabels.payment_type),
        ],
        dataframe_parse_args=dict(
            dataframe_parse_args,
            names=yellow_2009_2014_df_columns,
            parse_dates=timestamp_columns
        ),
    ),
    # yellow v2
    NycTlcConfig(
        pattern=re.compile('yellow_tripdata_(201[0-4])'),
        awk_format_dict=yellow_2009_2014_awk_format_dict,
        dataframe_postprocess=common_processing + [
            partial(map_column, column=DefaultLabels.vendor_id, mapping=vendor_mapping),
            partial(payment_type_normalize, pay_type_label=DefaultLabels.payment_type),
        ],
        dataframe_parse_args=dict(
            dataframe_parse_args,
            names=yellow_2009_2014_df_columns,
            parse_dates=timestamp_columns
        ),
    ),
    # yellow v3
    NycTlcConfig(
        pattern=re.compile('yellow_tripdata_(2015|2016-(0[1-6]))'),
        awk_format_dict={
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
        dataframe_postprocess=common_processing + [
        ],
        dataframe_parse_args=dict(
            dataframe_parse_args,
            names=[
                DefaultLabels.vendor_id,
                DefaultLabels.pickup_time, DefaultLabels.dropoff_time,
                DefaultLabels.passenger_count, DefaultLabels.trip_distance,
                DefaultLabels.pickup_lon, DefaultLabels.pickup_lat,
                DefaultLabels.rate_code_id, DefaultLabels.store_fwd,
                DefaultLabels.dropoff_lon, DefaultLabels.dropoff_lat,
                DefaultLabels.payment_type,
                DefaultLabels.fare_amt, DefaultLabels.extra, DefaultLabels.mta_tax, DefaultLabels.tip_amt,
                DefaultLabels.tolls_amt, DefaultLabels.improvement_surcharge,
                DefaultLabels.total_amt,
            ],
            parse_dates=timestamp_columns,
        ),
    ),
    # # yellow v4
    # NycTlcConfig(
    #     pattern=re.compile('yellow_tripdata_2016-(0[7-9]|1[0-2])'),
    #     awk_format_dict={
    #         # Pickup and Dropoff locations change to areas, requires revision of data model
    #     },
    #     dataframe_postprocess=[],
    #     dataframe_parse_args=dict(
    #         dataframe_parse_args,
    #         names=[
    #         ],
    #         parse_dates=timestamp_columns,
    #     ),
    # ),
    # green v2
    NycTlcConfig(
        pattern=re.compile('green_tripdata_(2009|201[0-4])'),
        awk_format_dict={
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
        dataframe_postprocess=common_processing + [
            partial(remove_column, column='not_used'),
        ],
        dataframe_parse_args=dict(
            dataframe_parse_args,
            names=[
                DefaultLabels.vendor_id,
                DefaultLabels.pickup_time, DefaultLabels.dropoff_time,
                DefaultLabels.store_fwd, DefaultLabels.rate_code_id,
                DefaultLabels.pickup_lon, DefaultLabels.pickup_lat,
                DefaultLabels.dropoff_lon, DefaultLabels.dropoff_lat,
                DefaultLabels.passenger_count, DefaultLabels.trip_distance,
                DefaultLabels.fare_amt, DefaultLabels.extra, DefaultLabels.mta_tax, DefaultLabels.tip_amt,
                DefaultLabels.tolls_amt, DefaultLabels.ehail_fee,
                DefaultLabels.total_amt, DefaultLabels.payment_type, DefaultLabels.trip_type,
                # The data has an extra comma that will cause pandas to assume the first column is
                # intended as an index.  Thus, we add a column here to resolve that.
                'not_used'
            ],
            parse_dates=timestamp_columns,
        ),
    ),
    # green v3
    NycTlcConfig(
        pattern=re.compile('green_tripdata_(2015|2016-(0[1-6]))'),
        awk_format_dict={
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
        dataframe_postprocess=common_processing + [
            partial(remove_column, column='not_used'),
        ],
        dataframe_parse_args=dict(
            dataframe_parse_args,
            names=[
                DefaultLabels.vendor_id,
                DefaultLabels.pickup_time, DefaultLabels.dropoff_time,
                DefaultLabels.store_fwd, DefaultLabels.rate_code_id,
                DefaultLabels.pickup_lon, DefaultLabels.pickup_lat,
                DefaultLabels.dropoff_lon, DefaultLabels.dropoff_lat,
                DefaultLabels.passenger_count, DefaultLabels.trip_distance,
                DefaultLabels.fare_amt, DefaultLabels.extra, DefaultLabels.mta_tax, DefaultLabels.tip_amt,
                DefaultLabels.tolls_amt, DefaultLabels.ehail_fee, DefaultLabels.improvement_surcharge,
                DefaultLabels.total_amt, DefaultLabels.payment_type, DefaultLabels.trip_type,
                # The data has an extra comma that will cause pandas to assume the first column is
                # intended as an index.  Thus, we add a column here to resolve that.
                'not_used'
            ],
            parse_dates=timestamp_columns,
        ),
    ),
    # # green v4 - This version doesn't provide point locations
    # NycTlcConfig(
    #     pattern=re.compile('green_tripdata_2016-(0[7-9]|1[0-2])'),
    #     awk_format_dict={
    #         # Pickup and Dropoff locations change to areas, requires revision of data model
    #     },
    #     dataframe_postprocess=[],
    #     dataframe_parse_args=dict(
    #         dataframe_parse_args,
    #         names=[
    #         ],
    #         parse_dates=timestamp_columns,
    #     ),
    # ),
]


def get_config(input_resource):
    filename = os.path.basename(input_resource)
    for cfg in nyc_config:
        if cfg.pattern.match(filename):
            return cfg
    raise AttributeError('No configuration for {}'.format(input_resource))
