from util import make_enum


class DefaultLabels:
    vendor_id = 'vendor_id'
    pickup_time = 'pickup_datetime'
    pickup_lon = 'pickup_lon'
    pickup_lat = 'pickup_lat'
    dropoff_time = 'dropoff_datetime'
    dropoff_lon = 'dropoff_lon'
    dropoff_lat = 'dropoff_lat'
    store_fwd = 'store_fwd'
    rate_code_id = 'rate_code'
    passenger_count = 'passenger_count'
    trip_distance = 'trip_distance'
    fare_amt = 'fare_amt'
    extra = 'extra'
    mta_tax = 'mta_tax'
    tip_amt = 'tip_amt'
    tolls_amt = 'tolls_amt'
    ehail_fee = 'ehail_fee'
    improvement_surcharge = 'improvement_surcharge'
    total_amt = 'total_amt'
    payment_type = 'payment_type'
    trip_type = 'trip_type'


timestamp_columns = [DefaultLabels.pickup_time, DefaultLabels.dropoff_time]


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

TripTypeEnum = make_enum(
    'Unknown',
    'Street-hail',
    'Dispatch',
)


# These are shared among derived classes
data_metadata = {
    DefaultLabels.vendor_id: {
        'units': VendorEnum().reverse_mapping,
        'desc': 'A code indicating the TPEP/LPEP provider that provided the record.',
        'origin': 'recorded'
    },
    DefaultLabels.pickup_time: {
        'units': 'datetime',
        'desc': 'ISO8601 date and time format pickup time of the trip in EDT.',
        'origin': 'recorded'
    },
    DefaultLabels.dropoff_time: {
        'units': 'datetime',
        'desc': 'ISO8601 date and time format dropoff time of the trip in EDT.',
        'origin': 'recorded'
    },
    DefaultLabels.passenger_count: {
        'units': 'integer',
        'desc': 'The number of passengers in the vehicle.  This is a driver-entered value.',
        'origin': 'recorded'
    },
    DefaultLabels.trip_distance: {
        'units': 'miles',
        'desc': 'The elapsed trip distance in miles reported by the taximeter.',
        'origin': 'recorded'
    },
    DefaultLabels.pickup_lon: {
        'units': 'WGS-84',
        'desc': 'GPS Longitude when the meter was engaged.',
        'origin': 'recorded'
    },
    DefaultLabels.pickup_lat: {
        'units': 'WGS-84',
        'desc': 'GPS Latitude when the meter was engaged.',
        'origin': 'recorded'
    },
    DefaultLabels.rate_code_id: {
        'units': RateCodeEnum().reverse_mapping,
        'desc': 'The final rate code in effect at the end of the trip.',
        'origin': 'recorded'
    },
    DefaultLabels.store_fwd: {
        'units': 'Boolean',
        'desc': (
            'This flag indicates whether the trip record was held in vehicle '
            'memory before sending to the vendor, aka “store and forward", '
            'because the vehicle did not have a connection to the server.'
        ),
        'origin': 'recorded'
    },
    DefaultLabels.dropoff_lon: {
        'units': 'WGS-84',
        'desc': 'GPS Longitude when the meter was disengaged.',
        'origin': 'recorded'
    },
    DefaultLabels.dropoff_lat: {
        'units': 'WGS-84',
        'desc': 'GPS Latitude when the meter was disengaged.',
        'origin': 'recorded'
    },
    DefaultLabels.payment_type: {
        'units': PaymentEnum().reverse_mapping,
        'desc': 'A numeric code signifying how the passenger paid for the trip.',
        'origin': 'recorded',
    },
    DefaultLabels.fare_amt: {
        'units': 'USD',
        'desc': 'The time-and-distance fare calculated by the meter.',
        'origin': 'recorded',
    },
    DefaultLabels.extra: {
        'units': 'USD',
        'desc': 'Miscellaneous extras and surcharges. Currently, this only includes the $0.50 and $1 rush hour and overnight charges.',
        'origin': 'recorded',
    },
    DefaultLabels.mta_tax: {
        'units': 'USD',
        'desc': '$0.50 MTA tax that is automatically triggered based on the metered rate in use.',
        'origin': 'recorded',
    },
    DefaultLabels.tip_amt: {
        'units': 'USD',
        'desc': 'Tip amount – This field is automatically populated for credit card tips. Cash tips are not included.',
        'origin': 'recorded',
    },
    DefaultLabels.tolls_amt: {
        'units': 'USD',
        'desc': 'Total amount of all tolls paid in trip.',
        'origin': 'recorded',
    },
    DefaultLabels.improvement_surcharge: {
        'units': 'USD',
        'desc': '$0.30 improvement surcharge assessed trips at the flag drop. The improvement surcharge began being levied in 2015.',
        'origin': 'recorded',
    },
    DefaultLabels.total_amt: {
        'units': 'USD',
        'desc': 'The total amount charged to passengers. Does not include cash tips.',
        'origin': 'recorded',
    },
    DefaultLabels.trip_type: {
        'units': TripTypeEnum.reverse_mapping,
        'desc': 'A code indicating whether the trip was a street-hail or a dispatch'
                'that is automatically assigned based on the metered rate in use but'
                'can be altered by the driver.',
        'origin': 'recorded',
    },
}