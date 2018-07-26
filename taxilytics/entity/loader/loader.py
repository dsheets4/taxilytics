from django.db import connection


mapping = {
    'trip': {
        'entity_trip': ['id', 'start_datetime', 'duration', 'geometry', 'archive_uri', 'metadata']
    }
}
class StreamLoader:
    def load(self, loader, mapping):
        with connection.cursor() as cursor:
            for loader_table, db_table in mapping:
                with loader.table(loader_table) as stream:
                    cursor.copy_expert(
                        """
                        COPY {}({})
                        FROM STDOUT
                        DELIMITER '{}'
                        """.format(db_table, stream.fields, stream.delimiter),
                        file=stream
                    )

class DataFrameLoader:
    def load(self, loader, mapping):
        pass
