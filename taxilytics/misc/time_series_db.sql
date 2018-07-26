-- Get one column with a timestamp
SELECT
	td.trip_id, s.ts, s.val as speed
FROM entity_tripdata as td, pd_series_to_record(pd_series_from_df(_dataframe, 'speed')) as s
LIMIT 5;

-- Check that the trips have both the recorded data and the derived roadmatch data.
SELECT t.id, td.definition_id, _dataframe AS df
FROM entity_trip as t
INNER JOIN entity_tripdata as td ON t.id = td.trip_id
ORDER BY t.id
LIMIT 10

-- View the available column names.
WITH combined_data AS (
	SELECT t.id, pd_concat(array_agg(_dataframe)) AS df
	FROM entity_trip as t
	INNER JOIN entity_tripdata as td ON t.id = td.trip_id
	GROUP BY t.id
	LIMIT 10
)
SELECT cols.* FROM combined_data, pd_columns_each(df) as cols;

-- Calculate the average speed of each road.
WITH expanded AS (
	WITH combined_data AS (
		SELECT t.id, pd_join(array_agg(_dataframe)) AS df
		FROM entity_trip as t
		INNER JOIN entity_tripdata as td ON t.id = td.trip_id
		GROUP BY t.id
		LIMIT 10
	)
	SELECT
		id, ts, speed, osm
	FROM
		combined_data as c,
		pd_df_to_record(df) AS df(
			ts timestamp with time zone,
			longitude double precision,
			latitude double precision,
			speed float,
			heading float,
			state boolean,
			osm float
			)
)
SELECT osm, avg(speed)
FROM expanded
GROUP BY osm