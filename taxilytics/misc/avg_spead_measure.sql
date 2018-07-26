WITH combined_trip AS (
	WITH combined_data AS (
		SELECT
			s.trip_id,
			r.osm,
			s.ts,
			date_trunc('hour', s.ts) as time_inc,
			s.speed
		FROM (
			SELECT
				trip_id,
				s.ts,
				s.val as speed
			FROM
				entity_tripdata,
				pd_series_to_record(pd_series_from_df(_dataframe, 'speed')) as s
			WHERE
				definition_id = 1 --AND trip_id BETWEEN {lower_id} AND {upper_id}
		) AS s
		INNER JOIN (
			SELECT
				trip_id,
				r.ts,
				CAST(r.val AS BIGINT) as osm
			FROM
				entity_tripdata,
				pd_series_to_record(pd_series_from_df(_dataframe, 'osm')) as r
			WHERE
				definition_id = 2 --AND trip_id BETWEEN {lower_id} AND {upper_id}
		) AS r ON s.trip_id = r.trip_id AND s.ts = r.ts
		LIMIT 20
	)
	SELECT
		t.entity_id,
		c.*
	FROM combined_data as c
	INNER JOIN entity_trip as t ON t.id = c.trip_id
)
SELECT
	entity_id,
	osm,
	time_inc,
	json_build_object(
		'speed',
		json_build_object(
			'average',
			avg(speed),
			'count',
			count(speed)
		)
	)::jsonb as measures
FROM combined_trip
GROUP BY entity_id, osm, time_inc