# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def read_sql(apps, schema_editor):
    contents = ''
    # schema_editor.execute('CREATE EXTENSION IF NOT EXISTS plpython3u;')
    with open('misc/pd_functions.sql') as f:
        for line in f:
            line = line.partition('--')[0]
            if len(line.strip()) > 0:
                contents += line
            if ';' in line:
                contents = contents.strip()
                print('Running: <{}>'.format(contents))
                schema_editor.execute(contents)
                contents = ''


class Migration(migrations.Migration):

    dependencies = [
        ('entity', '0001_initial'),
    ]

    operations = [
        # TODO: It would be better if this migration could read in the SQL from a file
        #       I tried that this the RunPython code here but it gives a syntax error even
        #       though running the (seemingly) same exact string hard-coded works fine.
        #migrations.RunPython(read_sql, atomic=False),
        migrations.RunSQL(
            'CREATE EXTENSION IF NOT EXISTS plpython3u;',
            ''
        ),
        migrations.RunSQL(
            'CREATE DOMAIN pd_df bytea;',
            'DROP DOMAIN pd_df'
        ),
        migrations.RunSQL(
            'CREATE DOMAIN pd_series bytea;',
            'DROP DOMAIN pd_series'
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_series_from_df(df_bytes bytea, column_name text)
                RETURNS pd_series
            AS $$
                import pandas as pd
                import pickle
                df = pickle.loads(df_bytes)
                return pickle.dumps(df[column_name])
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_series_from_df(bytea, text)"
        ),
        migrations.RunSQL(
            """
            CREATE TYPE pd_series_record as (
                ts timestamp with time zone,
                val float
            );
            """,
            "DROP TYPE pd_series_record;"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_series_to_record(ps pd_series)
                    RETURNS SETOF pd_series_record
            AS $$
                import pandas as pd
                import pickle
                s = pickle.loads(ps)
                class named_value:
                   def __init__ (self, n, v):
                      self.ts = n
                      self.val = v
                return (named_value(t,v) for t, v in s.iteritems())
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_series_to_record(pd_series)"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_df_to_record(df_bytes bytea, cols text[] DEFAULT ARRAY[]::text[])
                    RETURNS SETOF RECORD
            AS $$
                    import pandas as pd
                    import pickle
                    df = pickle.loads(df_bytes)
                    df['ts'] = df.index
                    if len(cols) > 0:
                        df = df[cols]
                    return df.to_dict(orient='records')
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_df_to_record(bytea, text[])"
        ),
        migrations.RunSQL(
            """
            CREATE TYPE pd_column_record as (
                col_name text,
                col_type text
            );
            """,
            "DROP TYPE pd_column_record;"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_columns_each(df_bytes bytea)
                RETURNS SETOF pd_column_record
            AS $$
                import pandas as pd
                import pickle
                df = pickle.loads(df_bytes)
                return zip(df.columns, df.dtypes)
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_columns_each(bytea)"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_column_names(df_bytes bytea)
                RETURNS text[]
            AS $$
                import pandas as pd
                import pickle
                df = pickle.loads(df_bytes)
                return df.columns
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_column_names(bytea)"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_stat(ps pd_series, stat_func text)
                RETURNS float
            AS $$
                import pandas as pd
                import pickle
                s = pickle.loads(ps)
                return getattr(s, stat_func)()
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_stat(pd_series, text)"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_compare(ps pd_series, op text, threshold float)
                    RETURNS pd_df
            AS $$
                valid_ops = ['lt', 'le', 'eq', 'ne', 'ge', 'gt']
                if op not in valid_ops:
                    raise Exception('Invalid pd_compare operator: Use one of {}'.format(valid_ops))
                import pandas as pd
                import pickle
                s = pickle.loads(ps)
                c = getattr(s, op)(threshold)
                c = c.to_frame(name='{}_{}_{}'.format(s.name, op, int(threshold)))
                c[s.name] = s
                return pickle.dumps(c)
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_compare(pd_series, text, float)"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_concat(df_bytes_array bytea[])
                RETURNS bytea
            AS $$
                import pandas as pd
                import pickle
                df = pd.concat([pickle.loads(df_bytes) for df_bytes in df_bytes_array])
                return pickle.dumps(df)
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_concat(bytea[])"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_join(df_bytes_array bytea[])
                RETURNS bytea
            AS $$
                import pandas as pd
                import pickle
                df = pd.concat([pickle.loads(df_bytes) for df_bytes in df_bytes_array], axis=1)
                return pickle.dumps(df)
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_join(bytea[])"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_create_series(ts timestamp with time zone[], vals bigint[], name text)
                    RETURNS pd_series
            AS $$
                import pandas as pd
                import pickle
                s = pd.Series(
                    data=vals,
                    index=ts,
                    name=name,
                    #dtype='int64'
                )
                s.dropna(inplace=True)
                s = s.astype('int64')
                s.index = s.index.to_datetime()
                return pickle.dumps(s)
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_create_series(timestamp with time zone[], bigint[], text)"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_create_series(ts timestamp with time zone[], vals boolean[], name text)
                    RETURNS pd_series
            AS $$
                import pandas as pd
                import pickle
                s = pd.Series(
                    data=vals,
                    index=ts,
                    name=name,
                    #dtype='int64'
                )
                s.dropna(inplace=True)
                s = s.astype('bool')
                return pickle.dumps(s)
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_create_series(timestamp with time zone[], boolean[], text)"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_create_series(ts timestamp with time zone[], vals double precision[], name text, timezone text DEFAULT '')
                    RETURNS pd_series
            AS $$
                import pandas as pd
                import pickle
                s = pd.Series(
                    data=vals,
                    index=ts,
                    name=name
                )
                if timezone:
                    s.index = s.index.to_datetime().tz_convert(timezone)
                s.index.name = 'timestamp'
                return pickle.dumps(s)
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_create_series(timestamp with time zone[], double precision[], text, text)"
        ),
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION pd_create_df(VARIADIC series_data bytea[])
                    RETURNS bytea
            AS $$
                import pandas as pd
                import pickle

                data_dict = {}
                for series_bytes in series_data:
                    s = pickle.loads(series_bytes)
                    data_dict[s.name] = s
                df = pd.DataFrame(data_dict)
                return pickle.dumps(df)
            $$ LANGUAGE plpython3u;
            """,
            "DROP FUNCTION pd_create_df(VARIADIC bytea[])"
        ),
    ]
