street_query = """
    WITH street_data AS (
        WITH cube_data AS (
                SELECT
                    st.street_id,
                    json_agg(st.time_inc) as times,
                    json_agg((st.measures->>'cnt')::int) as cnt,
                    json_agg(round((st.measures->>'fare_sum')::numeric,2)) as fare_sum,
                    json_agg(round((st.measures->>'pass_sum')::numeric,3)) as pass_sum,
                    json_agg(round((st.measures->>'dist_sum')::numeric,3)) as dist_sum
                FROM streetcube_streetcell as st
                WHERE
                    st.street_id IS NOT NULL
                    AND st.time_inc IS NOT NULL
                    AND st.street_id > {start_id}
                    AND st.time_inc > '2009-01-01' AND st.time_inc < '2017-01-01'
                GROUP BY st.street_id
                ORDER BY st.street_id
        )
        SELECT
            cube_data.*,
            classes.name AS street_category,
            streets.name,
            ST_Transform(streets.the_geom, 3857) as the_geom
        FROM cube_data
        LEFT JOIN ways AS streets ON streets.gid = cube_data.street_id
        LEFT JOIN osm_way_classes AS classes ON classes.class_id = streets.class_id
        {filter}
        {limit}
    )
    SELECT
        max(street_data.street_id) as max_id,
        json_object_agg(
            street_data.street_id,
            json_build_object(
                'geo', json_build_object(
                    'id', street_data.street_id,
                    'type', 'Feature',
                    'geometry', ST_AsGeoJson(the_geom)::json,
                    'properties', json_build_object(
                        'highway', street_category,
                        'name', street_data.name
                    )
                ),
                'times', times,
                'cnt', cnt,
                'fare_sum', fare_sum,
                'pass_sum', pass_sum,
                'dist_sum', dist_sum
            )
        ) as cube
    FROM street_data
"""
