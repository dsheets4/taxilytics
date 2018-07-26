from django.db import connection
from django.contrib.gis.db.models import query


class EstimatedCountQuerySetMixin(object):

    def count(self, exact=False):
        """
        With bigger tables even getting the count is costly. This uses faster, less
        accurate approach unless specifically requested.  Note that if the table
        statistics are up to date this provides the same reply as count for postgres
        """
        # TODO: Est. Count Mixin to detect query criteria to return super().count() instead
        if exact or self.query.has_filters():
            return super().count()

        if self.query.is_empty():
            return 0

        # TODO: The total count portion of EstimatedCountQuerySetMixin is postgres specific
        #       Below is only good for a global count and not when lookup criteria are used
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT reltuples::BIGINT AS count FROM pg_class WHERE relname='{}'
                """.format(self.model._meta.db_table)
            )
            return cursor.fetchone()[0]  # fetch always returns tuples


class EstCountGeoQuerySet(EstimatedCountQuerySetMixin, query.GeoQuerySet):
    pass