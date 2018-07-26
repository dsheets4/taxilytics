from math import radians
import numpy as np
import pandas as pd

from django.contrib.gis.geos import LineString


def make_timezone_aware(df, ts_col, timezone='UTC'):
    df[ts_col] = (
        pd.Index(df[ts_col]).tz_localize(timezone, ambiguous='NaT')
    )
    return df


def map_column(df, column, mapping):
    df[column] = df[column].map(mapping)
    return df


def remove_column(df, column):
    del df[column]
    return df


def remove_non_moving(df, pu_lon, pu_lat, do_lon, do_lat):
    good_gps_points = (
        (df[pu_lon] != df[do_lon]) |
        (df[pu_lat] != df[do_lat])
    )
    return df[good_gps_points]


def vector_haversine(df_lon_from, df_lat_from, df_lon_to, df_lat_to):
    """
    :param df_lon_from: Vector of longitude in radians values representing the starting point
    :param df_lat_from: Vector of latitude in radians values representing the starting point
    :param df_lon_to: Vector of longitude in radians values representing the ending point
    :param df_lat_to: Vector of latitude in radians values representing the ending point
    :return:
    """
    dlon = df_lon_to - df_lon_from
    dlat = df_lat_to - df_lat_from
    a = np.sin(dlat/2) * np.sin(dlat/2) + np.cos(df_lat_from) * np.cos(df_lat_to) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    dist_meters = 6371.0 * c
    return dist_meters


def remove_safe_dups(d):
    """
    :param d: The dataframe to check, must have indicies of taxi ID and timetstamp
    :return: The dataframe with the exact duplicate rows removed
    """
    dups_data = d.duplicated()
    dups_index = d.index.duplicated()
    dups = dups_data & dups_index
    return d[~dups]


def check_dups(d):
    """
    :param d: The dataframe to check, must have indicies of taxi ID and timetstamp
    :return: True if there are duplicates in the index
    """
    return d.index.duplicated().any()


def remove_impossible(taxi, lon_label='longitude', lat_label='latitude'):
    """ Removes GPS points that are impossible for a taxi """
    # The filter
    good_gps_points = (
        (taxi[lon_label] != 0) &
        (taxi[lon_label] <= 180) &
        (taxi[lon_label] >= -180) &
        (taxi[lat_label] != 0) &
        (taxi[lat_label] <= 90) &
        (taxi[lat_label] >= -90)
    )

    return taxi[good_gps_points]


def remove_implausible(d, implausible_mps=50):
    """
    Removes points from the dataframe that are implausible based on the great circle
    speed requried to travel between the two points.
    :param d: Pandas dataframe with latitude, longitude, and timestamp index
    :param implausible_mps: An implausible speed for the data to travel
    :return:
    """
    # Great circle distance between consecutive GPS samples
    lon = d.longitude.map(radians)
    lat = d.latitude.map(radians)

    dist = vector_haversine(lon, lat, lon.shift(1), lat.shift(1))
    dist.iloc[0] = 0

    # Time difference the distance was traveled.
    times = dist.index.to_series()
    time_delta_prev = (times - times.shift(1)).astype('timedelta64[s]')
    time_delta_prev.iloc[0] = 0

    # Calculate meters per second
    mps = dist / time_delta_prev
    mps.iloc[0] = 0

    next_mps = mps.shift(-1)
    next_mps.iloc[-1] = 0

    dist_delta = pd.DataFrame({
        'prev_mps': mps,
        'next_mps': next_mps,
    })

    # Speed greater than 50 meters per second is not likely and indicative of GPS error
    filter_implausible_speed = (
        (dist_delta['prev_mps'] < implausible_mps) &
        (dist_delta['next_mps'] < implausible_mps)
    )

    filtered = d[filter_implausible_speed]
    # print('Implausible removing', len(taxi) - len(filtered), 'points')

    return filtered


def create_linestring(taxi_df, x='longitude', y='latitude'):
    positions = taxi_df[[x, y]]
    start_time = taxi_df.index[0]
    tuples = [
        tuple((x[0][0], x[0][1], (x[1]-start_time).total_seconds()))
        for x in zip(positions.values, taxi_df.index)
    ]
    if len(tuples) == 1:
        tuples = (tuples[0], tuples[0])
    return LineString(tuples, srid=4326)
