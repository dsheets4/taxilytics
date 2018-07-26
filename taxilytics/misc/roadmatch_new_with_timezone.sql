-- SET LOCAL TIME ZONE 'Asia/Shanghai';
WITH tz_correlated AS (
	WITH matched_agg AS (
		WITH matched AS (
		    WITH needs_matched AS (
			SELECT
			    trip_id,
			    pd_join(array_agg(_dataframe)) AS df
			FROM entity_tripdata AS td
			GROUP BY trip_id
			HAVING sum(
			    CASE WHEN definition_id = (
				SELECT dd.id
				FROM entity_datadefinition AS dd
				WHERE short_name='Road Match Data'
			    ) THEN 1 ELSE 0 END
			) = 0
			LIMIT 1
		    )
		    SELECT
			trip_id,
			df.ts,
			osm_roadmatch_point(
			    ST_SetSRID(ST_MakePointM(df.longitude, df.latitude, df.heading),4326)
			) as osm
		    FROM
			needs_matched as td,
			pd_df_to_record(df) AS df(
				ts timestamp with time zone,
				longitude double precision,
				latitude double precision,
				heading float
			)
		)
	    SELECT
		trip_id,
		'{}'::jsonb as metadata,
		(SELECT id FROM entity_datadefinition WHERE short_name='Road Match Data') as definition_id,
		array_agg(ts) as ts,
		array_agg(osm) as osm
	    FROM matched AS td
	    GROUP BY trip_id
	)
	SELECT
		o.timezone,
		td.*
	FROM matched_agg AS td
	INNER JOIN entity_trip as t ON t.id = td.trip_id
	INNER JOIN entity_entity as e ON e.id = t.entity_id
	INNER JOIN entity_organization as o ON o.id = e.organization_id
)
INSERT INTO entity_tripdata(trip_id, metadata, definition_id, _dataframe)(
    SELECT
	trip_id,
	'{}'::jsonb as metadata,
	(SELECT id FROM entity_datadefinition WHERE short_name='Road Match Data') as definition_id,
	pd_create_df(pd_create_series(ts, osm, 'osm', timezone)) as _dataframe
    FROM tz_correlated
);

--SET SESSION TIME ZONE DEFAULT;