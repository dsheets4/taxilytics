
from query.models import (
    Attribute,
    Temporal,
    Spatial,
    TripQuery,
)


def create_attribute(name, **kwargs):
    return Attribute.objects.create(name=name, attribute=kwargs)


def create_temporal(name, start_datetime, end_datetime):
    return Temporal.objects.create(
        name=name,
        start_date=start_datetime.date(),
        start_time=start_datetime.time(),
        end_date=end_datetime.date(),
        end_time=end_datetime.time()
    )


def create_spatial(segment, operator, area):
    return Spatial.objects.create(
        segment=segment,
        operator=operator,
        area=area
    )


def create_tripquery(name, attribute, temporal, spatial, limit):
    tq = TripQuery.objects.create(
        name=name,
        # attribute=attribute,
        # temporal=temporal,
        # spatial=spatial,
        limit=limit
    )
    return tq
