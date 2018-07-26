from django.db import connection
from datetime import datetime


def road_match(lon, lat, srid=4326):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM traj_RoadMatchPoint(ST_GeomFromText('POINT({} {})', {}))
        """.format(lon, lat, srid))
        return cursor.fetchone()[0]


def road_match_collection(points, batch_size=1000000, srid=4326):
    matches = []
    counter = 0

    def exec_query(geom):
        cursor.execute("""
            SELECT * FROM traj_RoadMatchCollection(ST_GeomFromText('{}', {}))
        """.format(geom, srid))
        matches.extend(s[0] for s in cursor.fetchall())

    with connection.cursor() as cursor:
        geometry = 'GEOMETRYCOLLECTION('
        points_added = 0
        for lon, lat in points.as_matrix():
            if not points_added == 0:
                geometry += ','
            geometry += 'POINT({} {})'.format(lon, lat)
            points_added += 1
            if points_added == batch_size:
                counter += points_added
                geometry += ')'
                exec_query(geometry)
                print('        ', datetime.now(), 'Matched {} points'.format(counter))
                geometry = 'GEOMETRYCOLLECTION('
                points_added = 0
        if points_added:
            geometry += ')'
            counter += points_added
            exec_query(geometry)
            print('    ', datetime.now(), 'Matched {} points'.format(counter))
    return matches


def route():
    pass
