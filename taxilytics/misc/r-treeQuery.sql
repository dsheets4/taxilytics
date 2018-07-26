WITH results AS (
    WITH combined_data AS (
        WITH joined_df AS (
            SELECT
                t.entity_id,
                pd_join(array_agg(_dataframe)) AS df,
                array_agg(definition_id) as definitions
            FROM entity_tripdata AS td
            INNER JOIN entity_trip AS t ON t.id = trip_id
            WHERE t.entity_id >= 1 AND t.entity_id <= 1
            GROUP BY t.entity_id, trip_id
            LIMIT 10
        )
        SELECT
            entity_id,
            df.osm,
            date_trunc('hour', df.ts) as time_inc,
            df.speed
        FROM
            joined_df as td,
            pd_df_to_record(df) AS df(
                ts timestamp with time zone,
                speed float,
                osm float
            )
        WHERE
            definitions @> ARRAY[1,2]
            AND df.osm != FLOAT 'NaN'
    )
    SELECT
        osm::bigint,
--         ST_Extent(posm.way),
        entity_id,
        time_inc,
        '{}'::jsonb
    FROM combined_data as cd
--     INNER JOIN planet_osm_line as posm ON posm.gid = cd.osm
    GROUP BY entity_id, osm, time_inc
)
SELECT
	r.*,
	ST_Envelope(posm.way)
FROM results as r
INNER JOIN planet_osm_line as posm ON posm.gid = r.osm
