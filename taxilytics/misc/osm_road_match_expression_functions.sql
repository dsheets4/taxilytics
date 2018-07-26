
DROP FUNCTION IF EXISTS osm_roadmatch_line(geometry, int);
DROP FUNCTION IF EXISTS osm_roadmatch_point(geometry, int);


-- Finds the closest OSM lines with vehicular roadway attributes.
CREATE OR REPLACE FUNCTION osm_roadmatch_point(
    point geometry,
    initial_results integer DEFAULT 10)
RETURNS bigint AS $BODY$
DECLARE
	the_match bigint;
BEGIN
	point := ST_Transform(point, 3857);
	SELECT l.gid, ST_Distance(l.way, point) as dist
	INTO the_match
	FROM planet_osm_line as l 
	WHERE
		ST_DWithin(point, l.way, 20)
		AND
		l.highway IN (
			'motorway',
			'trunk',
			'primary',
			'secondary',
			'tertiary',
			'unclassified',
			'residential',
			'service',
			'motorway_link',
			'trunk_link',
			'primary_link',
			'secondary_link',
			'tertiary_link',
			'living_street',
			'road',
			'turning_circle'
		)
	ORDER BY dist
	LIMIT initial_results
	;
	RETURN the_match;
END $BODY$
LANGUAGE plpgsql VOLATILE;


CREATE FUNCTION osm_roadmatch_line(
	IN geometry,
	initial_results int DEFAULT 10)
RETURNS bigint[] AS $BODY$
DECLARE
	roadmatch bigint[];
BEGIN
	SELECT array_agg(osm_roadmatch_point((dp).geom, initial_results)) INTO roadmatch
	FROM (SELECT ST_DumpPoints($1) AS dp) As foo;
	RETURN roadmatch;
END $BODY$
LANGUAGE plpgsql VOLATILE;


-- -- Test queries
-- WITH roadmatch_metadata AS (
-- 	WITH expanded_json_keys AS (
-- 		WITH roadmatch_all AS (
-- 			SELECT
-- 				id
-- 				, osm_roadmatch_line(geometry) as matches
-- 				, metadata
-- 			FROM entity_trip
-- 			WHERE NOT metadata ? 'roadmatch'
-- 			LIMIT 20000
-- 		)
-- 		SELECT id, j1.key, j1.value FROM roadmatch_all, jsonb_each(metadata) as j1
-- 		UNION
-- 		SELECT id, 'roadmatch', to_json(roadmatch_all.matches)::jsonb FROM roadmatch_all
-- 	)
-- 	SELECT
-- 		id,
-- 		json_object_agg(key, value)::jsonb as metadata
-- 	FROM expanded_json_keys
-- 	GROUP BY id
-- )
-- UPDATE entity_trip
-- SET metadata=roadmatch_metadata.metadata
-- FROM roadmatch_metadata
-- WHERE entity_trip.id=roadmatch_metadata.id
-- ;
