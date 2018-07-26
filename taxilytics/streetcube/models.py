from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField, ArrayField

from pgrouting.models import Ways


# Create your models here.
class TimeIncrement(models.Model):
    """
    This model defines a time increment to be used for qualifying data in
    analysis.
    """
    objects = models.GeoManager  # TrajCubeManager()
    full_time = models.DateTimeField(unique=True)  # Full time increment for ranged WHERE
    year = models.SmallIntegerField()  # Four digit year
    day_of_year = models.SmallIntegerField()  # Day number 1-366
    month = models.SmallIntegerField()  # Month number: 1-12
    day_of_month = models.SmallIntegerField()  # Day number: 1-31
    week = models.SmallIntegerField()  # Week number of the year. New week starts Mondays. 1-53
    day_of_week = models.SmallIntegerField()  # Zero on Monday: 0-6
    hour = models.SmallIntegerField()  # 0-23
    # True when normal working day (False on most weekends and holiday)
    workday = models.BooleanField()

    def __str__(self):
        return str(self.full_time)

    @staticmethod
    def truncate(dt):
        """
        Converts given time to the desired increment level.  Useful to allow
        grouping common times
        """
        return dt.replace(minute=0, second=0, microsecond=0)

    @staticmethod
    def datetime_to_lookup(dt):
        """ Creates the time cube dimension for the given time. """
        return {
            'full_time': dt,
            'year': dt.year,
            'day_of_year': dt.dayofyear,
            'month': dt.month,
            'day_of_month': dt.day,
            'week': dt.week,
            'day_of_week': dt.dayofweek,
            'hour': dt.hour,
            'workday': (dt.weekday() > 5)  # Need to cross-reference with holidays
        }


class RegionPartition(models.Model):
    geometry = models.MultiPolygonField(dim=2, srid=3857, null=True)
    name = models.CharField(max_length=64, null=True)
    items = ArrayField(models.BigIntegerField())  # street ids
    system = models.BooleanField()


class StreetCell(models.Model):
    objects = models.GeoManager
    street = models.ForeignKey(Ways, null=True)
    time_inc = models.DateTimeField(db_index=True, null=True)
    # In NOSQL fashion, this will store whatever values we desire from the provided
    # analysis functions.
    measures = JSONField()

    class Meta:
        unique_together = ('street', 'time_inc')

    def __str__(self):
        return 'street(%s), time(%s), measures=%s' % (
            self.street, self.time_inc, self.measures
        )

    def __repr__(self):
        return self.__str__()
