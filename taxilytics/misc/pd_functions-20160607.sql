-- DROP EXTENSION IF EXISTS plpython3u CASCADE;
-- DROP DOMAIN pd_df;
-- DROP DOMAIN pd_series;

CREATE EXTENSION IF NOT EXISTS plpython3u;
CREATE DOMAIN pd_df bytea;
CREATE DOMAIN pd_series bytea;


-- ############################################################################
-- 146: pd_series_from_df
-- ############################################################################
-- DROP FUNCTION IF EXISTS pd_series_from_df(df_bytes bytea, column_name text)
CREATE OR REPLACE FUNCTION pd_series_from_df(df_bytes bytea, column_name text)
        RETURNS pd_series
AS $$
        import pandas as pd
        import pickle
        df = pickle.loads(df_bytes)
        return pickle.dumps(df[column_name])
$$ LANGUAGE plpython3u;

-- SELECT pd_series_from_df(_dataframe, 'speed') as speed
-- FROM entity_tripdata LIMIT 5;


-- ############################################################################
-- 146: pd_series_record
-- ############################################################################
-- DROP TYPE IF EXISTS pd_series_record CASCADE;
CREATE TYPE pd_series_record as (
	ts timestamp with time zone,
	val float
);
-- DROP FUNCTION IF EXISTS pd_series_to_record(ps pd_series)
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
-- SELECT
-- 	s.ts, s.val as speed
-- FROM entity_tripdata, pd_series_to_record(pd_series_from_df(_dataframe, 'speed')) as s
-- LIMIT 5;


-- ############################################################################
-- 146: pd_df_to_record
-- ############################################################################
-- DROP FUNCTION IF EXISTS pd_df_to_record(df_bytes bytea);
CREATE OR REPLACE FUNCTION pd_df_to_record(df_bytes bytea)
        RETURNS SETOF RECORD
AS $$
        import pandas as pd
        import pickle
        df = pickle.loads(df_bytes)
        df['ts'] = df.index
        return df.to_dict(orient='records')
$$ LANGUAGE plpython3u;
-- -- Example: The benefit here is that the types are individually definable
-- SELECT td.trip_id, df.*
-- FROM entity_tripdata as td, pd_df_to_record(_dataframe) AS df(
-- 	ts timestamp with time zone,
-- 	longitude double precision,
-- 	latitude double precision,
-- 	speed float,
-- 	heading float,
-- 	state boolean)
-- LIMIT 50;
-- -- For single values, still faster to use the series to strip the data.
-- SELECT td.trip_id, s.ts, s.val as speed
-- FROM entity_tripdata as td, pd_series_to_record(pd_series_from_df(_dataframe, 'speed')) as s
-- LIMIT 50;
-- -- At three parameters, this is slower than using pd_df_to_record.
-- SELECT
-- 	td.trip_id, s.ts, s.val as speed, lat.val as latitude, lon.val as longitude
-- FROM
-- 	entity_tripdata as td,
-- 	pd_series_to_record(pd_series_from_df(_dataframe, 'speed')) as s,
-- 	pd_series_to_record(pd_series_from_df(_dataframe, 'longitude')) as lon,
-- 	pd_series_to_record(pd_series_from_df(_dataframe, 'latitude')) as lat
-- LIMIT 50;

-- ############################################################################
-- 146: pd_columns
-- ############################################################################
-- DROP TYPE IF EXISTS pd_column_record CASCADE;
CREATE TYPE pd_column_record as (
	col_name text,
	col_type text
);

-- DROP FUNCTION IF EXISTS pd_columns(df_bytes bytea);
CREATE OR REPLACE FUNCTION pd_columns(df_bytes bytea)
        RETURNS SETOF pd_column_record
AS $$
        import pandas as pd
        import pickle
        df = pickle.loads(df_bytes)
        return zip(df.columns, df.dtypes)
$$ LANGUAGE plpython3u;

-- DROP FUNCTION IF EXISTS pd_column_names(df_bytes bytea);
CREATE OR REPLACE FUNCTION pd_column_names(df_bytes bytea)
        RETURNS text[]
AS $$
        import pandas as pd
        import pickle
        df = pickle.loads(df_bytes)
        return df.columns
$$ LANGUAGE plpython3u;

-- -- Using pd columns to get type and column name.
-- WITH one_data AS (
-- 	SELECT * FROM entity_tripdata LIMIT 1
-- )
-- SELECT cols.* FROM one_data, pd_columns(_dataframe) as cols;
-- 
-- WITH one_data AS (
-- 	SELECT * FROM entity_tripdata LIMIT 50
-- )
-- SELECT id, array_agg(cols.col_name)
-- FROM one_data, pd_columns(_dataframe) as cols
-- GROUP BY id;
-- 
-- WITH one_data AS (
-- 	SELECT * FROM entity_tripdata LIMIT 50
-- )
-- SELECT id, pd_column_names(_dataframe)
-- FROM one_data;
-- 
-- 
-- -- Getting the data definition related to the trip data as columns
-- WITH expanded_defs AS (
-- 	WITH one_data AS (
-- 		SELECT dd.definition
-- 		FROM entity_tripdata as td
-- 		INNER JOIN entity_datadefinition AS dd ON td.definition_id = dd.id
-- 		LIMIT 1
-- 	)
-- 	SELECT cols.* FROM one_data, jsonb_each(definition) AS cols
-- )
-- SELECT key, units, origin FROM expanded_defs, jsonb_to_record(value) AS (units text, origin text);


-- ############################################################################
-- 136: pd_stat
-- ############################################################################
-- DROP FUNCTION IF EXISTS pd_stat(df_bytes bytea, column_name text, stat_func text)
CREATE OR REPLACE FUNCTION pd_stat(ps pd_series, stat_func text)
        RETURNS float
AS $$
        import pandas as pd
        import pickle
        s = pickle.loads(ps)
        return getattr(s, stat_func)()
$$ LANGUAGE plpython3u;

-- -- Example: Statistic on a single column.
-- SELECT
-- 	trip_id,
-- 	pd_stat(pd_series_from_df(_dataframe, 'speed'), 'mean') as mean_speed
-- FROM entity_tripdata
-- LIMIT 5;
-- 
-- -- For all columns in the dataframe, calculate the mean.
-- SELECT
-- 	trip_id,
-- 	col_name,
-- 	mean
-- FROM
-- 	entity_tripdata,
-- 	pd_columns(_dataframe) as col_name,
-- 	pd_stat(pd_series_from_df(_dataframe, col_name), 'mean') AS mean
-- LIMIT 50;


-- ############################################################################
-- 139: pd_compare
-- ############################################################################
-- DROP FUNCTION IF EXISTS pd_compare(ps pd_series, op text, threshold float)
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

-- -- Example of calling compare
-- WITH one_data AS (
-- 	SELECT * FROM entity_tripdata LIMIT 1
-- )
-- SELECT trip_id, spd_comp.*
-- FROM
-- 	one_data,
-- 	pd_df_to_record(
-- 		pd_compare(pd_series_from_df(_dataframe, 'speed'), 'lt', 25)
-- 	) as spd_comp(
-- 		ts timestamp with time zone,
-- 		speed float,
-- 		"speed_lt_25" boolean
-- 	)
-- ;


-- ############################################################################
-- 137: pd_concat - Appends the given data frames
-- ############################################################################
-- DROP FUNCTION IF EXISTS pd_concat(df_bytes_array bytea[])
CREATE OR REPLACE FUNCTION pd_concat(df_bytes_array bytea[])
        RETURNS bytea
AS $$
        import pandas as pd
        import pickle
        df = pd.concat([pickle.loads(df_bytes) for df_bytes in df_bytes_array])
        return pickle.dumps(df)
$$ LANGUAGE plpython3u;

-- -- Concatenation via postgres and other pd functions
-- WITH entity_data AS (
-- 	SELECT entity_id, _dataframe
-- 	FROM entity_trip as t
-- 	INNER JOIN entity_tripdata as td ON t.id = td.trip_id
-- 	WHERE entity_id=7790
-- )
-- SELECT entity_id, df_records.*
-- FROM entity_data, pd_df_to_record(_dataframe) AS df_records(
-- 	ts timestamp with time zone,
-- 	longitude double precision,
-- 	latitude double precision,
-- 	speed float,
-- 	heading float,
-- 	state boolean
-- 	)
-- ORDER BY ts;
-- 
-- -- Combining the multiple dataframes into a single dataframe (via CTE)
-- WITH combined AS (
-- 	SELECT entity_id, pd_concat(array_agg(_dataframe)) AS df
-- 	FROM entity_trip as t
-- 	INNER JOIN entity_tripdata as td ON t.id = td.trip_id
-- 	WHERE entity_id=7790
-- 	GROUP BY entity_id
-- )
-- SELECT entity_id, df_records.*
-- FROM combined, pd_df_to_record(df) AS df_records(
-- 	ts timestamp with time zone,
-- 	longitude double precision,
-- 	latitude double precision,
-- 	speed float,
-- 	heading float,
-- 	state boolean
-- 	)
-- ORDER BY ts;


-- ############################################################################
-- 137: pd_join - Appends the given data frames
-- ############################################################################
-- DROP FUNCTION IF EXISTS pd_join(df_bytes_array bytea[])
CREATE OR REPLACE FUNCTION pd_join(df_bytes_array bytea[])
        RETURNS bytea
AS $$
        import pandas as pd
        import pickle
        df = pd.concat([pickle.loads(df_bytes) for df_bytes in df_bytes_array], axis=1)
        return pickle.dumps(df)
$$ LANGUAGE plpython3u;


-- ############################################################################
-- 138: pd_create_series
-- ############################################################################
-- DROP FUNCTION IF EXISTS pd_create_series(ts timestamp with time zone[], vals bigint[], name text)
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

CREATE OR REPLACE FUNCTION pd_create_series(ts timestamp with time zone[], vals double precision[], name text, timezone text DEFAULT 'America/New_York')
        RETURNS pd_series
AS $$
    import pandas as pd
    import pickle
    s = pd.Series(
        data=vals,
        index=ts,
        name=name
    )
    s.index = s.index.to_datetime().tz_convert(timezone)
    s.index.name = 'timestamp'
    return pickle.dumps(s)
$$ LANGUAGE plpython3u;

-- DROP FUNCTION IF EXISTS pd_create_df(VARIADIC series_data bytea[])
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


-- -- ############################################################################
-- -- 138: pd_group
-- -- ############################################################################
-- -- DROP FUNCTION IF EXISTS pd_group(df_bytes bytea, group_column text)
-- CREATE OR REPLACE FUNCTION pd_group(df_bytes bytea, group_column text)
--         RETURNS SETOF bytea
-- AS $$
--         import pandas as pd
--         import pickle
--         df = pickle.loads(df_bytes)
-- 
--         # Groupd by the indicated column then return the data frame by group
--         grp = df.groupby([split_column])
--         for 
-- 
--         return [(col_name, df[col_name].values) for col_name in group]
-- $$ LANGUAGE plpython3u;


-- ############################################################################
-- 138: pd_split
-- ############################################################################
-- -- DROP FUNCTION IF EXISTS pd_split(df_bytes bytea, df_split pd_df)
-- CREATE OR REPLACE FUNCTION pd_split(df_bytes bytea, df_split pd_df)
--         RETURNS SETOF bytea
-- AS $$
--         import pandas as pd
--         import pickle
--         df = pickle.loads(df_bytes)
-- 
--         return [(col_name, df[col_name].values) for col_name in group]
-- $$ LANGUAGE plpython3u;
-- 
-- SELECT trip_id, series.* FROM entity_tripdata, pd_each(_dataframe) as series LIMIT 5;
