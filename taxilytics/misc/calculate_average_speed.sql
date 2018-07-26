WITH combined_data AS (
	WITH joined_df AS (
		SELECT
			pd_join(array_agg(_dataframe)) AS df,
			array_agg(definition_id) as definitions
		FROM entity_tripdata AS td
		GROUP BY trip_id
	)
	SELECT
		df.osm,
		df.speed
	FROM
		joined_df as td,
		pd_df_to_record(df) AS df(
			ts timestamp with time zone,
			speed float,
			osm float
		)
	WHERE definitions @> ARRAY[1,2]
)
SELECT
	osm,
	count(speed),
	avg(speed)
FROM combined_data
GROUP BY osm