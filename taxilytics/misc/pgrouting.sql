-------------------------------------------------------------------------------
-- Provide troubleshooting output, which results in the pgrouting queries 
-- to provide reasons when they fail.
SET client_min_messages = 'notice';

SELECT version();
SELECT PostGIS_full_version();


-------------------------------------------------------------------------------
-- Database setup
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;


-- Need to re-evaluate the effectiveness of these
-- -- Create useful index for faster lookups.
-- -- Takes about 15 min on the NYC OSM data.
-- CREATE INDEX ways__the_geom__geohash ON ways (ST_GeoHash(the_geom,4326));
-- CLUSTER ways USING ways__the_geom__geohash;
-- 
-- DROP INDEX ways__the_geom__index


-------------------------------------------------------------------------------
-- Database validation
select pgr_analyzegraph('ways', 0.000001, 'the_geom', 'gid');

-- || -1|| reversed (1 way but geometry is reversed) ||
-- ||  0|| unknown ||
-- ||  1|| yes (direction is per geometry) ||
-- ||  2|| 2 way ||
-- ||  3|| reversible (one way street but direction changes on time) ||
select pgr_analyzeoneway('ways',
			 '{-1, 0, 2, 3}', '{0, 1, 2, 3}',
                         '{0, 1, 2, 3}',  '{-1, 0, 2, 3}',
                         true, 'one_way')

-- The network can be noded as intersections to get better routing.  The algorithm is looking at line segment intersections
-- and breaking lines when they intersect.  This happens even when the road segments don't have actual connectivity, such
-- as an overpass connecting with the road running under it.  All-in-all, the osm2pgrouting is using the OSM nodes, which
-- define common points in the road network.  The result is that it seems better to not use the pgr_nodeNetwork with the
-- OSM data loaded via osm2pgrouting.
--select pgr_nodeNetwork('ways', 0.001, 'gid');
--select pgr_createTopology('ways_noded', 0.000001);
--select pgr_analyzegraph('ways_noded', 0.000001);
--select pgr_analyzeoneway('ways_noded',
--			 '{-1, 0, 2, 3}', '{0, 1, 2, 3}',
--                         '{0, 1, 2, 3}',  '{-1, 0, 2, 3}',
--                         true, 'one_way')
--select * from ways limit 10
--select * from ways_noded limit 10
--select * from ways_vertices_pgr limit 10


-- Comparison of road segments with straight OSM data
SELECT count(plain.way) as count FROM planet_osm_line as plain          --  652782
SELECT count(routing.the_geom) as count FROM ways as routing  -- 1159372


-------------------------------------------------------------------------------
-- Routing
SELECT
	gid,
	source::int4,
	target::int4,
	cost,
	x1, y1, x2, y2,
	reverse_cost
FROM ways
WHERE ST_DWithin(ST_GeomFromText('LINESTRING(-73.956388 40.608035, -73.956389 40.608037)', 4326), the_geom, .01)


SELECT * FROM ways WHERE gid=960060 OR gid=962531


SELECT * FROM pgr_astar(
	concat('	SELECT
			gid as id,
			source::int4,
			target::int4,
			cost,
			x1, y1, x2, y2,
			reverse_cost
		FROM ways
		WHERE ST_DWithin(ST_GeomFromText(',
		'''LINESTRING(-73.956388 40.608035, -73.956389 40.608037)''',
		', 4326), the_geom, .01)'
	),  -- sql text,
	50589, -- source node ID,
	727722, -- target node ID,
        true,  -- directed boolean,
        false   -- has_rcost boolean
);


DROP FUNCTION IF EXISTS traj_Route(integer, integer, double precision);
CREATE OR REPLACE FUNCTION traj_Route(src integer, tgt integer, within double precision DEFAULT 0.01)
  RETURNS SETOF pgr_costresult AS
$BODY$
DECLARE
	bbox geometry;
	s integer;
	t integer;
BEGIN
	WITH endpoints AS (
		SELECT the_geom FROM ways WHERE gid=src OR gid=tgt
	)
	SELECT ST_Extent(the_geom) INTO bbox FROM endpoints;

	SELECT source INTO s FROM ways WHERE gid=src;
	SELECT target INTO t FROM ways WHERE gid=tgt;

	RAISE NOTICE 'source(%)', s;
	RAISE NOTICE 'target(%)', t;
	
	RETURN QUERY SELECT * FROM pgr_astar(
		concat('	SELECT
				gid as id,
				source::int4,
				target::int4,
				cost,
				x1, y1, x2, y2,
				reverse_cost
			FROM ways
			WHERE ST_DWithin(ST_GeomFromText(''',
			ST_AsText(bbox),
			''', 4326), the_geom,', .01, ')'
		),  -- sql text,
		s, -- source node ID,
		t, -- target node ID,
		true,  -- directed boolean,
		false   -- has_rcost boolean
	);
END
$BODY$
LANGUAGE plpgsql VOLATILE;

SELECT * FROM traj_Route(960060, 962531)


-------------------------------------------------------------------------------
-- Map-matching (reverse geocode to the road)


-- Test type return values
SELECT 'geometry_collection' AS geometry, ST_GeometryType(ST_GeomFromText(
	'GEOMETRYCOLLECTION(POINT(-73.956388 40.608035),POINT(-73.957499 40.609147))', 4326)
	)  -- t
UNION
SELECT 'point' AS geometry, ST_GeometryType(ST_GeomFromText(
	'POINT(-73.956388 40.608035)', 4326)
	)  -- f
UNION
SELECT 'multi_point' AS geometry, ST_GeometryType(ST_GeomFromText(
	'MULTIPOINT((-73.956388 40.608035),(-73.957499 40.609147))', 4326)
	)  -- t
UNION
SELECT 'linestring' AS geometry, ST_GeometryType(ST_GeomFromText(
	'LINESTRING(-73.956388 40.608035,-73.957499 40.609147)', 4326)
	)  -- f
UNION
SELECT 'multi_linestring' AS geometry, ST_GeometryType(ST_GeomFromText(
	'MULTILINESTRING((-73.956388 40.608035,-73.957499 40.609147),(-73.956388 40.608035,-73.957499 40.609147))', 4326)
	)  -- t


-- Test what is considered a collection.
SELECT 'geometry_collection' AS geometry, ST_IsCollection(ST_GeomFromText(
	'GEOMETRYCOLLECTION(POINT(-73.956388 40.608035),POINT(-73.957499 40.609147))', 4326)
	)  -- t
UNION
SELECT 'point' AS geometry, ST_IsCollection(ST_GeomFromText(
	'POINT(-73.956388 40.608035)', 4326)
	)  -- f
UNION
SELECT 'multi_point' AS geometry, ST_IsCollection(ST_GeomFromText(
	'MULTIPOINT((-73.956388 40.608035),(-73.957499 40.609147))', 4326)
	)  -- t
UNION
SELECT 'linestring' AS geometry, ST_IsCollection(ST_GeomFromText(
	'LINESTRING(-73.956388 40.608035,-73.957499 40.609147)', 4326)
	)  -- f
UNION
SELECT 'multi_linestring' AS geometry, ST_IsCollection(ST_GeomFromText(
	'MULTILINESTRING((-73.956388 40.608035,-73.957499 40.609147),(-73.956388 40.608035,-73.957499 40.609147))', 4326)
	)  -- t


-- Test breaking down collections.
SELECT ST_AsText(geom) FROM ST_Dump(ST_GeomFromText('GEOMETRYCOLLECTION(POINT(-73.956388 40.608035),POINT(-73.957499 40.609147))', 4326))
SELECT ST_AsText(geom) FROM ST_Dump(ST_GeomFromText('MULTIPOINT((-73.956388 40.608035),(-73.957499 40.609147))', 4326))
SELECT ST_AsText(geom) FROM ST_Dump(ST_GeomFromText('MULTILINESTRING((-73.956388 40.608035,-73.957499 40.609147),(-73.956388 40.608035,-73.957499 40.609147))', 4326))
SELECT ST_AsText(geom) FROM ST_Dump(ST_GeomFromText('GEOMETRYCOLLECTION(POINT(-73.956388 40.608035),MULTIPOINT((-73.956388 40.608035),(-73.957499 40.609147)),MULTILINESTRING((-73.956388 40.608035,-73.957499 40.609147),(-73.956388 40.608035,-73.957499 40.609147)))', 4326))
-- Calling ST_Dump on non-collections just returns the same geometry.
SELECT ST_AsText(geom) FROM ST_Dump(ST_GeomFromText('POINT(-73.956388 40.608035)', 4326))
SELECT ST_AsText(geom) FROM ST_Dump(ST_GeomFromText('LINESTRING(-73.956388 40.608035,-73.957499 40.609147)', 4326))


-- Simple matching query outside of function for troubleshooting
WITH candidates AS (
	SELECT *
		, ST_GeomFromText('POINT(-73.956388 40.608035)', 4326) as point
		, 0.001 as seg_length
	FROM ways as n
	ORDER BY n.the_geom <#> ST_GeomFromText('POINT(-73.956388 40.608035)', 4326)
	LIMIT 10
)
SELECT
	*,
	ST_Distance(c.the_geom, point) as dist,
	degrees(ST_Azimuth( -- Calculates the north heading of the road segment nearest the query point.
		ST_LineInterpolatePoint(the_geom, GREATEST(ST_LineLocatePoint(the_geom, point)-seg_length, CAST(0 AS FLOAT))),
		ST_LineInterpolatePoint(the_geom, LEAST(ST_LineLocatePoint(the_geom, point)+seg_length, CAST(1 AS FLOAT)))
	)) as road_seg_hdg
FROM candidates AS c
ORDER BY dist
LIMIT 1;


-- -- Clean-up for changing function signatures
-- DROP FUNCTION traj_RoadMatch(geometry, double precision)
-- DROP TYPE IF EXISTS traj_RoadMatchRecord;


-- Function definition requires new type for return set
CREATE TYPE traj_RoadMatchRecord AS (
	gid bigint,
	class_id integer,
	length double precision,
	length_m double precision,
	name text,
	source bigint,
	target bigint,
	x1 double precision,
	y1 double precision,
	x2 double precision,
	y2 double precision,
	cost double precision,
	reverse_cost double precision,
	cost_s double precision,
	reverse_cost_s double precision,
	rule text,
	one_way integer,
	maxspeed_forward integer,
	maxspeed_backward integer,
	osm_id bigint,
	source_osm bigint,
	target_osm bigint,
	priority double precision,
	the_geom geometry
	,point geometry
	,seg_length double precision
	,dist double precision
	,road_seg_hdg double precision
);


-- It's faster to call the correct form directly if the calling code already has a uniform geometry
CREATE OR REPLACE FUNCTION traj_RoadMatchPoint(data_to_match geometry, segment_length double precision DEFAULT 0.001)
  RETURNS SETOF traj_RoadMatchRecord AS
$BODY$
DECLARE
BEGIN
	RETURN QUERY WITH candidates AS (
		SELECT *
		FROM ways as n
		ORDER BY n.the_geom <#> data_to_match
		LIMIT 10
	)
	SELECT
		*
		, data_to_match
		, segment_length
		, ST_Distance(c.the_geom, data_to_match) as dist
		, degrees(ST_Azimuth( -- Calculates the north heading of the road segment nearest the query point.
			ST_LineInterpolatePoint(the_geom, GREATEST(ST_LineLocatePoint(the_geom, data_to_match)-segment_length, CAST(0 AS FLOAT))),
			ST_LineInterpolatePoint(the_geom, LEAST(ST_LineLocatePoint(the_geom, data_to_match)+segment_length, CAST(1 AS FLOAT)))
		)) as road_seg_hdg
	FROM candidates AS c
	ORDER BY ST_Distance(c.the_geom, data_to_match)
	LIMIT 1;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION traj_RoadMatchCollection(data_to_match geometry, segment_length double precision DEFAULT 0.001)
  RETURNS SETOF traj_RoadMatchRecord AS
$BODY$
DECLARE
	g geometry;
BEGIN
	FOR g IN
		SELECT geom FROM ST_Dump(data_to_match)
	LOOP
		RETURN NEXT traj_RoadMatchPoint(g, segment_length);
	END LOOP;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION traj_RoadMatchLinestring(data_to_match geometry, segment_length double precision DEFAULT 0.001)
  RETURNS SETOF traj_RoadMatchRecord AS
$BODY$
DECLARE
	g geometry;
BEGIN
	FOR g IN
		SELECT geom FROM ST_DumpPoints(data_to_match)
	LOOP
		RETURN NEXT traj_RoadMatchPoint(g, segment_length);
	END LOOP;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


-- Generic road match function figures out the geometry type and returns a set of matches.
CREATE OR REPLACE FUNCTION traj_RoadMatch(data_to_match geometry, segment_length double precision DEFAULT 0.001)
  RETURNS SETOF traj_RoadMatchRecord AS
$BODY$
DECLARE
BEGIN
	IF ST_IsCollection(data_to_match) THEN
		RETURN QUERY SELECT * FROM traj_RoadMatchCollection(data_to_match, segment_length);
	ELSIF ST_GeometryType(data_to_match) = 'ST_LineString' THEN  -- Could also support Polygon but does that make sense?
		RETURN QUERY SELECT * FROM traj_RoadMatchLinestring(data_to_match, segment_length);
	ELSE
		RETURN QUERY SELECT * FROM traj_RoadMatchPoint(data_to_match, segment_length);
	END IF;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


-- Point test case
SELECT * FROM traj_RoadMatchPoint(ST_GeomFromText('POINT(-73.956388 40.608035)', 4326))  -- gid=960060
UNION
SELECT * FROM traj_RoadMatchPoint(ST_GeomFromText('POINT(-73.957499 40.609147)', 4326))  -- gid=962531

SELECT * FROM traj_RoadMatch(ST_GeomFromText('POINT(-73.956388 40.608035)', 4326))  -- gid=960060
UNION
SELECT * FROM traj_RoadMatch(ST_GeomFromText('POINT(-73.957499 40.609147)', 4326))  -- gid=962531


-- Geometry Collection test case
SELECT * FROM traj_RoadMatchCollection(
	ST_GeomFromText('GEOMETRYCOLLECTION(POINT(-73.956388 40.608035),POINT(-73.957499 40.609147))', 4326)
)

SELECT * FROM traj_RoadMatch(
	ST_GeomFromText('GEOMETRYCOLLECTION(POINT(-73.956388 40.608035),POINT(-73.957499 40.609147))', 4326)
)


-- Linestring test case
SELECT * FROM traj_RoadMatch(
	ST_GeomFromText('LINESTRING(-73.956388 40.608035,-73.957499 40.609147)', 4326)
)
