-- CREATE TABLE entity_tripdatadecimal2 (
--     LIKE entity_tripdatadecimal
--     INCLUDING ALL
-- );


TRUNCATE entity_tripdatadecimal RESTART IDENTITY
TRUNCATE entity_tripdatadecimal2 RESTART IDENTITY

-- Format 1 - entity_tripdatadecimal with FULL data.
INSERT INTO entity_tripdatadecimal (columns, ts, values, trip_id) (
	WITH rows AS (
		WITH joined_df AS (
		    SELECT
			t.entity_id,
		        trip_id,
			pd_join(array_agg(_dataframe)) AS df,
			array_agg(definition_id) as definitions
		    FROM entity_tripdata AS td
		    INNER JOIN entity_trip AS t ON t.id = trip_id
-- 		    WHERE
-- 			-- t.entity_id >= {eid1} AND t.entity_id <= {eid2}
-- 			t.entity_id >= 1 AND t.entity_id <= 2
		    GROUP BY t.entity_id, trip_id
		)
		SELECT
		    entity_id,
		    trip_id,
		    df.ts,
		    ARRAY[
			df.longitude,
			df.latitude,
			df.speed,
			df.heading,
			CASE WHEN df.state THEN 1.0 ELSE 0.0 END,
			df.osm
		    ] as vals
		FROM
		    joined_df as td,
		    pd_df_to_record(df) AS df(
			ts timestamp with time zone,
			longitude double precision,
			latitude double precision,
			speed float,
			heading float,
			state boolean,
			osm float
		    )
		WHERE
		    definitions @> ARRAY[1,2]
	)
	SELECT
		ARRAY['latitude','longitude','speed','heading','state','osm'] as columns,
		array_agg(ts) as ts,
		array_agg(vals) as values,
		trip_id
	FROM rows
	GROUP BY trip_id
	ORDER BY ts
)



-- Format 1 - entity_tripdatadecimal
SELECT
-- DELETE
FROM entity_tripdatadecimal
WHERE "columns" @> '{osm}'::varchar[]

INSERT INTO entity_tripdatadecimal (columns, ts, values, trip_id) (
	SELECT
	    ARRAY['osm'] as columns,
	    array_agg(df.ts) as ts,
	    array_agg(ARRAY[df.osm]) as values,
	    trip_id
	FROM
	    entity_tripdata,
	    pd_df_to_record(_dataframe) AS df(
		ts timestamp with time zone,
		osm float
	    )
	WHERE
	    definition_id = 2
	    AND df.osm != FLOAT 'NaN'
	GROUP BY id
)

-- Format 2 - entity_tripdatadecimal2
INSERT INTO entity_tripdatadecimal2 (columns, ts, values, trip_id) (
	SELECT
	    ARRAY['osm'] as columns,
	    array_agg(df.ts) as ts,
	    ARRAY[array_agg(df.osm)] as values,
	    trip_id
	FROM
	    entity_tripdata,
	    pd_df_to_record(_dataframe) AS df(
		ts timestamp with time zone,
		osm float
	    )
	WHERE
	    definition_id = 2
	    AND df.osm != FLOAT 'NaN'
	GROUP BY id
)


-- ****************************************************************************
-- ****************************************************************************
-- ****************************************************************************


-- Format 1 - entity_tripdatadecimal
-- SELECT *
DELETE
FROM entity_tripdatadecimal
WHERE "columns" @> '{latitude,longitude,speed,heading,state}'::varchar[]
-- LIMIT 5

INSERT INTO entity_tripdatadecimal (columns, ts, values, trip_id) (
	WITH rows AS (
		WITH base AS (
			SELECT *
			FROM entity_tripdata
			WHERE definition_id = 1
		)
		SELECT
			df.ts as ts,
			ARRAY[
				df.longitude,
				df.latitude,
				df.speed,
				df.heading,
				CASE WHEN df.state THEN 1.0 ELSE 0.0 END
			] as vals,
			trip_id
		FROM
		    base,
		    pd_df_to_record(_dataframe) AS df(
			ts timestamp with time zone,
			longitude double precision,
			latitude double precision,
			speed float,
			heading float,
			state boolean
		    )
	)
	SELECT
		ARRAY['latitude','longitude','speed','heading','state'] as columns,
		array_agg(ts) as ts,
		array_agg(vals) as values,
		trip_id
	FROM rows
	GROUP BY trip_id
	ORDER BY ts
)

-- Format 2 - entity_tripdatadecimal2
SELECT *
-- DELETE
FROM entity_tripdatadecimal2
WHERE "columns" @> '{latitude,longitude,speed,heading,state}'::varchar[]
LIMIT 5

INSERT INTO entity_tripdatadecimal2 (columns, ts, values, trip_id) (
	SELECT
	    ARRAY['latitude','longitude','speed','heading','state'] as columns,
	    array_agg(df.ts) as ts,
	    ARRAY[
		array_agg(df.longitude),
		array_agg(df.latitude),
		array_agg(df.speed),
		array_agg(df.heading),
		array_agg(CASE WHEN df.state THEN 1.0 ELSE 0.0 END)
	    ] as values,
	    trip_id
	FROM
	    entity_tripdata,
	    pd_df_to_record(_dataframe) AS df(
		ts timestamp with time zone,
		longitude double precision,
		latitude double precision,
		speed float,
		heading float,
		state boolean
	    )
	WHERE
	    definition_id = 1
	GROUP BY id
)



-- WITH initial AS (
-- 	SELECT
-- 		t.entity_id,
-- 		tdd.trip_id,
-- 		columns,
-- 		ts,
-- 		values
-- 	FROM
-- 		entity_tripdatadecimal AS tdd
-- 	INNER JOIN entity_trip AS t on t.id = tdd.trip_id
-- 	WHERE
-- 		-- t.entity_id >= {eid1} AND t.entity_id <= {eid2}
-- 		t.entity_id >= 1 AND t.entity_id <= 1
-- 	LIMIT 5
-- )
-- SELECT *
-- FROM
-- 	initial,
-- 	unnest(values)



CREATE OR REPLACE FUNCTION unnest_2d_1d(anyarray)
  RETURNS SETOF anyarray AS
$func$
SELECT array_agg($1[d1][d2])
FROM   generate_subscripts($1,1) d1
    ,  generate_subscripts($1,2) d2
GROUP  BY d1
ORDER  BY d1
$func$
LANGUAGE sql IMMUTABLE;







-- Format 1 - Queries
-- Expands the data structure where the 2D array is the inner arrays are all the values at a given timestamp
-- and the outer array contains the progress of values over time.
-- WITH level1 AS (
-- 	WITH tbl AS (
-- 		SELECT
-- 			ts,
-- 			columns as cols,
-- 			values as vals2d
-- 		FROM entity_tripdatadecimal
-- 		LIMIT 10
-- 	)
-- 	SELECT
-- 		ts.val as ts,
-- 		cols,
-- 		vals1d.val as vals1d
-- 	FROM
-- 		tbl,
-- 		unnest(ts) WITH ORDINALITY as ts(val, idx)
-- 	LEFT JOIN LATERAL unnest_2d_1d(vals2d) WITH ORDINALITY as vals1d(val, idx) ON ts.idx = vals1d.idx
-- )
-- SELECT
-- 	ts,
-- 	col.val,
-- 	val.val
-- FROM level1, unnest(cols) WITH ORDINALITY AS col(val, idx)
-- LEFT JOIN LATERAL unnest(vals1d) WITH ORDINALITY AS val(val, idx) ON col.idx = val.idx
-- ORDER BY ts

WITH level1 AS (
	WITH tbl AS (
		SELECT
			ts,
			columns as cols,
			values as vals2d
		FROM entity_tripdatadecimal
		WHERE
			columns @> ARRAY['osm']::varchar[]
			AND values @> ARRAY[625233.0, 1674417.0]
		LIMIT 100
	)
	SELECT
		ts.val as ts,
		cols,
		vals1d.val as vals1d
	FROM
		tbl,
		unnest(ts) WITH ORDINALITY as ts(val, idx)
	LEFT JOIN LATERAL unnest_2d_1d(vals2d) WITH ORDINALITY as vals1d(val, idx) ON ts.idx = vals1d.idx
)
SELECT
	ts,
	col.val,
	val.val
FROM level1, unnest(cols) WITH ORDINALITY AS col(val, idx)
LEFT JOIN LATERAL unnest(vals1d) WITH ORDINALITY AS val(val, idx) ON col.idx = val.idx
ORDER BY ts


-- Format 2 - Queries
-- Expands the data structure where the 2D array is the inner arrays are all values of a given parameter
-- over time and the outer array contains the multiple parameters.
-- WITH level1 AS (
-- 	WITH tbl AS (
-- 		SELECT
-- 			ARRAY['a','b'] as ts,
-- 			ARRAY['val1','val2'] as cols,
-- 			ARRAY[ARRAY[1,2],ARRAY[3,4]] as vals2d
-- 	)
-- 	SELECT
-- 		ts,
-- 		col.val as col,
-- 		vals1d.val as vals1d
-- 	FROM tbl, unnest_2d_1d(vals2d) WITH ORDINALITY as vals1d(val, idx)
-- 	LEFT JOIN LATERAL unnest(cols) WITH ORDINALITY AS col(val, idx) ON vals1d.idx = col.idx
-- )
-- SELECT
-- 	ts.val as ts,
-- 	col,
-- 	val.val as val
-- FROM level1, unnest(ts) WITH ORDINALITY AS ts(val, idx)
-- LEFT JOIN LATERAL unnest(vals1d) WITH ORDINALITY AS val(val, idx) ON ts.idx = val.idx
-- ORDER BY ts;

WITH level1 AS (
	WITH tbl AS (
		SELECT
			ts,
			columns as cols,
			values as vals2d
		FROM entity_tripdatadecimal2
		LIMIT 1
	)
	SELECT
		ts,
		col.val as col,
		vals1d.val as vals1d
	FROM tbl, unnest_2d_1d(vals2d) WITH ORDINALITY as vals1d(val, idx)
	LEFT JOIN LATERAL unnest(cols) WITH ORDINALITY AS col(val, idx) ON vals1d.idx = col.idx
)
SELECT
	ts.val as ts,
	col,
	val.val as val
FROM level1, unnest(ts) WITH ORDINALITY AS ts(val, idx)
LEFT JOIN LATERAL unnest(vals1d) WITH ORDINALITY AS val(val, idx) ON ts.idx = val.idx
ORDER BY ts;
