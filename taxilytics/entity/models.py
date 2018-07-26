import pickle
import pytz
from io import BytesIO

import pandas as pd
from pandas.compat import pickle_compat as pc

from django.db import models
from django.contrib.gis.db import models as geomodels
from django.contrib.postgres.fields import JSONField  #, ArrayField

from django_util import validators

from entity.functions import Array


# Create your models here.
def _prep_dataframe(df):
    """
    Performs operations on the DataFrame prior to it's merge
    """
    return df


timezones = {}
for tz in pytz.all_timezones:
    split_tz = tz.split('/')
    if split_tz[0] not in timezones:
        timezones[split_tz[0]] = []
    if len(split_tz) > 1:
        remaining = split_tz[1:]
        timezones[split_tz[0]].append((tz,'/'.join(remaining)))
    else:
        timezones[split_tz[0]].append((tz,tz))


class Organization(models.Model):
    name = models.CharField(max_length=64)
    timezone = models.CharField(
        max_length=64,
        null=True,
        choices=((k, timezones[k]) for k in sorted(timezones.keys()))
    )
    metadata = JSONField(
        default={},
        validators=[validators.JsonValidator()],
        blank=True
    )

    def __str__(self):
        return self.name


class EntityManager(models.Manager):
    """
    Manager for Entity objects.  It primarily defines the natural keys but
    is useful for other features such as default query functions.
    """
    def get_by_natural_key(self, physical_id):
        return self.get(
            physical_id=physical_id
        )


class Entity(models.Model):
    """
    Represents a physical entity that can generate trajectories (aka Trips).
    It allows association of multiple trips to a single resource for better
    data connectivity and relationships.
    """
    objects = EntityManager()
    organization = models.ForeignKey(Organization, null=True)
    common_id = models.CharField(
        max_length=16,
        db_index=True,
        help_text='Commonly used identifier (e.g. Tail Number, License plate'
    )
    physical_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text='Unique id following the physical resource (e.g. VIN)'
    )
    metadata = JSONField(
        default={},
        validators=[validators.JsonValidator()],
        blank=True
    )

    class Meta:
        # It seems tail numbers are more unique
        unique_together = ('physical_id',)  # 'common_id')
        verbose_name_plural = 'entities'

    def __str__(self):
        return self.common_id

    def natural_key(self):
        return self.physical_id

    def combine_trip_data(self, prepare=_prep_dataframe, trip_filter=None):
        trips = self.trip_set.all()
        if trip_filter:
            trips = trips.filter(trip_filter)
        qs = TripData.objects.filter(trip__in=trips)
        return TripManager.combine_trip_data(qs, prepare)


class TripManager(geomodels.GeoManager):

    # def get_queryset(self):
    #     return EstCountGeoQuerySet(self.model, using=self.db)

    def get_by_natural_key(self, entity, start_datetime):
        """ Allows use of natural keys with dumpdata. """
        return self.get(
            entity=entity,
            start_datetime=start_datetime
        )

    def with_passenger(self):
        return self.filter(metadata__jcontains={'passenger': True})

    @staticmethod
    def combine_trip_data(trip_qs, prepare=_prep_dataframe):
        trip_qs = (trip_qs
              .values('trip_id')  #  Limits the fields by not returning ORM object
              .annotate(df_list=Array('_dataframe'))  # Will GROUP BY when given aggregate
              )
        df = pd.concat([
                prepare(pd.concat([pickle.loads(d) for d in trip['df_list']], axis=1))
                for trip in trip_qs
        ])
        return df


class Trip(geomodels.Model):
    """
    Represents a partition of the movement of an Entity.  It represents the
    base atomic element of most analysis.  Although some analysis will dissect
    further into the TripData or specific points, the results are often
    associated back to the Trip.  When different granularity is required, the
    partitioning is usually modified and a new set of trips created.
    """
    objects = TripManager()
    # Not all taxi data associates with an single physical taxi
    id = geomodels.BigIntegerField(primary_key=True)
    entity = geomodels.ForeignKey(Entity, blank=True, null=True)
    start_datetime = geomodels.DateTimeField(db_index=True)
    duration = geomodels.DurationField()
    geometry = geomodels.LineStringField(dim=3, null=True)
    metadata = JSONField(
        default={},
        validators=[validators.JsonValidator()],
        blank=True,
        # db_index=True - Defined by migration so it uses a GIST instead of BTREE index
    )
    archive_uri = geomodels.CharField(max_length=1024)

    class Meta:
        # ordering = ['-start_datetime']  # Newer trips listed first
        # Trip IDs are generated as a function of entity and start_datetime as well as
        # another ID that enforce this unique_together in the PK.
        # unique_together = ('entity', 'start_datetime')
        pass

    def __str__(self):
        return '%s|%s' % (
            self.label,
            self.start_datetime.isoformat()
        )

    @property
    def label(self):
        return self.entity.common_id if self.entity else ('Trip(%s)' % self.id)

    def natural_key(self):
        return self.entity, self.start_datetime

    @property
    def organization(self):
        return self.entity.organization

    def dataframe_filter(self, params=None, times=(None, None), interpolate=None):
        df_list = list(
            tripdata for tripdata in self.__iter__(params=params, times=times, interpolate=interpolate)
        )
        return df_list

    def __iter__(self, params=None, times=(None, None), interpolate=None):
        # TODO: Best ways to carve up a data frame.
        #       Is it faster to return a series when only one parameter requested?
        #       How will the code calling this most often iterate the results?
        for tripdata in self.tripdata_set.all():
            data = tripdata.dataframe_filter(params=params, times=times)
            if data is None:
                continue
            if interpolate:
                data = data.interpolate(method=interpolate)

            yield data


class DataDefinition(models.Model):
    """ Defines a common datadefinition to share among common tripdata schema instances """
    short_name = models.CharField(max_length=32)
    definition = JSONField(
        default={},
        validators=[validators.JsonValidator()]
    )

    def __str__(self):
        return self.short_name


# class TripDataCommon(models.Model):
#     trip = models.ForeignKey(Trip, related_name="%(app_label)s_%(class)s_set")
#     ts = ArrayField(models.DateTimeField())
#
#     class Meta:
#         abstract = False
#
#     def commit_from_df(self, df):
#         pass
#
#
# class TripDataDecimal(TripDataCommon):
#     columns = ArrayField(models.CharField(max_length=64))
#     data = ArrayField(
#         ArrayField(
#             models.DecimalField(decimal_places=6, max_digits=20)
#         )
#     )
#
#
# class TripDataString(TripDataCommon):
#     columns = ArrayField(models.CharField(max_length=64))
#     data = ArrayField(
#         ArrayField(
#             models.CharField(max_length=256)
#         )
#     )
#
#
# class TripDataInt(TripDataCommon):
#     columns = ArrayField(models.CharField(max_length=64))
#     data = ArrayField(
#         ArrayField(
#             models.IntegerField()
#         )
#     )


class TripData(models.Model):
    """ Isolates the large binary data from the rest of the record. """
    trip = models.ForeignKey(Trip, related_name='tripdata_set')
    _dataframe = models.BinaryField()
    metadata = JSONField(
        default={},
        validators=[validators.JsonValidator()]
    )
    definition = models.ForeignKey(DataDefinition)

    class Meta:
        verbose_name_plural = 'Trip data'

    def __str__(self):
        return '%s|%s' % (
            str(self.trip),
            self.id
        )

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._db_to_dataframe()
        return instance

    def _dataframe_to_db(self):
        """
        This is basically the same code from pandas 0.18 pandas.io.pickle.to_pickle
        but keeping the bytes in memory.  Since that method does not allow passing the
        pickle in memory (only via file on file system) the logic is duplicated.
        """
        self._dataframe = pickle.dumps(self.dataframe, protocol=pickle.HIGHEST_PROTOCOL)

    def _db_to_dataframe(self):
        """
        This is basically pd.read_pickle but allowing in-memory objects and
        forcing python 3.  The idea is that pandas.read_pickle maintains some semblance
        of backward compatibility making this more robust.  The code this is derived from
        came from pandas 0.18 pandas.io.pickle.
        """
        fh = BytesIO(self._dataframe)
        encoding = 'latin1'
        try:
            self.dataframe =  pickle.load(fh)
        except (Exception) as e:
            try:
                # reg/patched pickle
                self.dataframe = pc.load(fh, encoding=encoding, compat=False)
            except:
                # compat pickle
                self.dataframe = pc.load(fh, encoding=encoding, compat=True)

    def save(self, *args, **kwargs):
        self._dataframe_to_db()
        super().save(*args, **kwargs)

    def dataframe_filter(self, params=None, times=(None, None)):
        """
        params is an iterable of parameters to retrieve
        times is a tuple of start_time, duration to retrieve
        """
        if times[0] is None and (params is None or len(params) == 0):
            return self.dataframe

        if times is not None and times[0] is not None:
            times = (times[0], times[0] + times[1])
        else:
            times = (None, None)

        params = params if params is not None else []
        if len(params) > 0:
            avail_params_set = set(self.paramlist())
            params = avail_params_set.intersection(params)
            if len(params) == 0:
                return None  # This dataframe does not contain desired params
            return self.dataframe.loc[times[0]:times[1], params]
        else:
            return self.dataframe.loc[times[0]:times[1], ]

    def paramlist(self):
        return self.dataframe.columns

    @property
    def organization(self):
        return self.trip.entity.organization


""" Looking to start defining the basic analysis. These should be in a separate django app"""
"""
* Develop python functions and configure the call using EventDefinition
  * Specific input arguments are defined for each EventDefinition.
  * Multiple EventDefinitions can call same function with different arguments.

class EventDefinition(models.Model):
    package = models.FilePathField()
    kwargs = JSONField(default={}, validators=[validators.JsonValidator()])
"""

"""
* EventDefinitions are pulled into groups by EventGroup
  * EventGroup to EventDefinitions is ManyToMany since a group can have
     multiple definitions and a definition can belong to multiple groups.
  * EventGroup to Entity is ManyToMany.

class EventGroup(models.Model):
    events = models.ManyToManyField(EventDefinition, related_name='groups')
    entities = models.ManyToManyField(Entity, related_name='groups')
"""

"""
* Events that produce hits are captured as EventOccurrences
  * These becomes the basis of further analysis
  * Analysis interfaces are structured to support start_time, duration requests
  * Will support the creation of a vector of events for more advanced analysis.
  * Parametric data is associated by storing a parameter name and querying it
    from the associated entity (via the trip) when requested.
  * Additionally derived information not saved to the trip can be metadata
class EventOccurrence(models.Model):
    definition = models.ForeignKey(EventDefinition)
    trip = models.ForeignKey(Trip)
    start_time = models.DateTimeField()
    duration = models.DurationField()
    # from django.contrib.postgres.fields import ArrayField
    params = ArrayField(models.CharField(max_length=64))
    metadata = JSONField(default={}, validators=[validators.JsonValidator()])
"""

"""
* When event analysis is run on an entity, it is tracked by EventExecution
  * Allows verifying analysis was run even if no EventOccurrence was found
  * Stores the execution results for later reporting and troubleshooting
class EventExecution(models.Model):
    entity = models.ForeignKey(Entity)
    definition = models.ForeignKey(EventDefinition)
    exec_time = models.DateTimeField()
    result = models.TextField()

"""
