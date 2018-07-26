
WITH pick_drop AS (
	WITH od_rows AS (
		WITH od_pairs AS (
			WITH joined_df AS (
				SELECT
					trip_id,
					array_agg(pd_slice(_dataframe, NULL, NULL, 'end')) AS df,
					array_agg(definition_id) as definitions
				FROM entity_tripdata AS td
				INNER JOIN entity_trip AS t ON t.id = trip_id
				WHERE
					t.start_datetime >= '2011-12-19' AND
					t.start_datetime <  '2011-12-20'
					-- t.start_datetime >= '{start_date}' AND t.start_datetime < '{end_date}'
				GROUP BY trip_id
				ORDER BY trip_id
			)
			SELECT
			    trip_id,
			    array_agg(date_trunc('hour', df.ts)) as time_inc,
			    array_agg(df.osm::bigint) as osm,
			    ARRAY['pickup','dropoff']
			FROM
			    joined_df as td,
			    pd_join_record(df) AS df(
				id float,
				ts timestamp with time zone,
				osm float
			    )
			WHERE
			    definitions @> ARRAY[1,2]
			    AND df.osm != FLOAT 'NaN'
			GROUP BY trip_id
			ORDER BY trip_id
		)
		SELECT
			trip_id,
			time_inc[1] as pickup_time, time_inc[2] as dropoff_time,
			osm[1] as pickup_osm, osm[2] as dropoff_osm
		FROM od_pairs
	)
	(
		SELECT
			pickup_time as time_inc,
			pickup_osm as osm,
			json_build_object(
				'times', jsonb_agg(dropoff_time),
				'osm', jsonb_agg(dropoff_osm)
			) as measure,
			'dropoffs' as json_key
		FROM od_rows
		GROUP BY pickup_time, pickup_osm
	)
	UNION ALL
	(
		SELECT
			dropoff_time as time_inc,
			dropoff_osm as osm,
			json_build_object(
				'times', jsonb_agg(dropoff_time),
				'osm', jsonb_agg(dropoff_osm)
			) as measure,
			'pickups' as json_key
		FROM od_rows
		GROUP BY dropoff_time, dropoff_osm
	)
)
SELECT
	count(*),
	osm,
	time_inc,
	jsonb_object_agg(json_key, measure)
FROM pick_drop
GROUP BY time_inc, osm

-- SELECT * FROM entity_trip LIMIT 1;