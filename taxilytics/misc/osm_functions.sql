-- DROP FUNCTION IF EXISTS osm_road_match_point_hdg(geometry);
DROP FUNCTION IF EXISTS osm_road_match_line_hdg(geometry);
DROP FUNCTION IF EXISTS osm_road_match_line(geometry);
DROP FUNCTION IF EXISTS osm_road_match_hdg(geometry, double precision);
DROP FUNCTION IF EXISTS osm_road_match(geometry);
DROP FUNCTION IF EXISTS osm_hdg_test(double precision,double precision,double precision);
DROP FUNCTION IF EXISTS osm_poi_match(double precision,double precision);
DROP TYPE IF EXISTS osm_road_matches;
DROP TYPE IF EXISTS point_dump;

-- Type returned from the osm_road_match* functions.
CREATE TYPE osm_road_matches as (
	gid integer,
	osm_id bigint,
	dist double precision,
	road_seg_hdg double precision,
	name text,
	highway text,
	oneway text,
	ref text,
	tags hstore,
	way geometry
	--, segment geometry
);

-- Type used in loop dumping geometry points.
CREATE TYPE point_dump as (
	pid integer,
	geom geometry
);

-- Finds the closest OSM lines with vehicular roadway attributes.
CREATE OR REPLACE FUNCTION osm_road_match(point geometry)
  RETURNS SETOF osm_road_matches AS
$BODY$
DECLARE
	seg_length float;
BEGIN
	point := ST_Transform(point, 3857);
	seg_length = .001;
	RETURN QUERY WITH index_query AS (
	    SELECT 
		l.gid, l.osm_id, 
		ST_Distance(l.way, $1) as dist,
		degrees(ST_Azimuth( -- Calculates the north heading of the road segment nearest the query point.
			ST_Line_Interpolate_Point(l.way, GREATEST(ST_Line_Locate_Point(l.way, $1)-seg_length, CAST(0 AS FLOAT))),
			ST_Line_Interpolate_Point(l.way, LEAST(ST_Line_Locate_Point(l.way, $1)+seg_length, CAST(1 AS FLOAT)))
		)) as road_seg_hdg,
		l.name, l.highway, l.oneway, l.ref, l.tags, l.way
	    from planet_osm_line as l 
	    where l.highway IN (
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
		    'turning_circle')
		ORDER BY l.way <-> $1
		LIMIT 5
	) 
	SELECT * 
	FROM index_query 
	ORDER BY dist 
	LIMIT 5;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


-- Return true if the headings match within a predefined tolerance.
CREATE OR REPLACE FUNCTION osm_hdg_test(
    traj_hdg double precision,
    road_hdg double precision,
    tolerance double precision)
  RETURNS boolean AS
$BODY$
BEGIN
	RETURN 
		(road_hdg BETWEEN
			CASE WHEN ($1 - tolerance) < 0 THEN 0 ELSE $1 - tolerance END
			AND
			CASE WHEN ($1 + tolerance) >= 360 THEN 360 ELSE $1 + tolerance END
		)
		OR -- Edge case when the road heading and trajectory heading are on opposite sides of the 360/0 degree wrap-around
		(road_hdg BETWEEN
			CASE WHEN ($1 + tolerance) >= 360 THEN 0 ELSE $1 - tolerance + 360 END
			AND
			CASE WHEN ($1 - tolerance) < 0 THEN 360 ELSE $1 + tolerance - 360 END
		)
	;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


-- Find the closest road with matching heading.
CREATE OR REPLACE FUNCTION osm_road_match_hdg(point geometry, tolerance double precision DEFAULT 60)
  RETURNS SETOF osm_road_matches AS
$BODY$
BEGIN
	RETURN QUERY select *
	from osm_road_match($1) as r -- , ST_M(point) as hdg
	where
		CASE
			-- -1 means that the order of points is opposite direction of travel
			WHEN r.oneway = '-1' THEN
				osm_hdg_test(ST_M(point), (CAST(r.road_seg_hdg AS INT) + 180) % 360, tolerance)
			WHEN r.oneway = 'yes' THEN
				osm_hdg_test(ST_M(point), r.road_seg_hdg, tolerance)
			ELSE -- Case when the road is two-way (or more accurately, not one-way)
				osm_hdg_test(ST_M(point), (CAST(r.road_seg_hdg AS INT) + 180) % 360, tolerance)
				OR
				osm_hdg_test(ST_M(point), r.road_seg_hdg, tolerance)
		END
	;
-- The above code is faster.  Below we create additional rows in the output based on whether a single road segment can match multiple headings (one way vs. two way)
-- 	RETURN QUERY WITH roads_expanded as (
-- 		WITH roads AS (
-- 			SELECT *
-- 			FROM osm_road_match($1) as l
-- 			WHERE l.highway IN (
-- 				'motorway',
-- 				'trunk',
-- 				'primary',
-- 				'secondary',
-- 				'tertiary',
-- 				'unclassified',
-- 				'residential',
-- 				'service',
-- 				'motorway_link',
-- 				'trunk_link',
-- 				'primary_link',
-- 				'secondary_link',
-- 				'tertiary_link',
-- 				'living_street',
-- 				'road',
-- 				'turning_circle')
-- 		)
-- 		select * FROM roads
-- 		where (roads.oneway <> '-1' OR COALESCE(roads.oneway, '') = '')
-- 		UNION ALL
-- 		select
-- 			roads.gid,
-- 			roads.name,
-- 			roads.dist,
-- 			roads.road_seg_hdg,
-- 			roads.highway,
-- 			roads.oneway,
-- 			roads.ref,
-- 			roads.tags,
-- 			ST_Reverse(roads.way),
-- 			roads.osm_id
-- 			--, roads.segment geometryroads.gid, roads.osm_id, roads.highway, roads.oneway, roads.name, roads.ref, roads.tags, 
-- 		from roads
-- 		where (COALESCE(roads.oneway, '') = '' OR roads.oneway = 'no' OR roads.oneway = '-1')
-- 	)
-- 	select *
-- 	from roads_expanded as r -- , ST_M(point) as hdg
-- 	where osm_hdg_test(ST_M(point), r.road_seg_hdg, tolerance)
-- 	;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


-- Finds the closest points of interest that are destinations.
CREATE OR REPLACE FUNCTION osm_poi_match(
    IN lon double precision,
    IN lat double precision)
  RETURNS TABLE(dist double precision, gid integer, osm_id bigint, name text,
		amenity text,
		shop text,
		sport text,
		tourism text,
		historic text,
		landuse text,
		leisure text,
		building text,
		military text,
		office text,
		poi text,
		public_transport text,
		tags hstore, way geometry) AS
$BODY$
DECLARE
	point geometry;
BEGIN
	point := ST_Transform(ST_SetSRID(ST_Point($1, $2), 4326), 3857);
	RETURN QUERY WITH index_query as (
	   select 
		ST_Distance(o.way, point) as dist, o.gid, o.osm_id,
		CASE WHEN o.tags->'name:en' <> '' THEN o.tags->'name:en' ELSE o.name END,
		o.amenity,
		CASE WHEN o.shop = 'yes' THEN 'shop' ELSE o.shop END,
		o.sport,
		o.tourism,
		o.historic,
		o.landuse,
		o.leisure,
		-- building tends to inject a few non-useful tags such as 'yes' and 'entrance'
		CASE WHEN o.building = 'yes' OR o.building = 'entrance' THEN '' ELSE o.building END,
		o.military,
		o.office,
		o.poi,
		o.public_transport,
		o.tags, o.way
	   from planet_osm_point as o
	   where
		o.amenity IS NOT NULL OR
		o.shop IS NOT NULL OR
		o.sport IS NOT NULL OR
		o.tourism IS NOT NULL OR
		o.historic IS NOT NULL OR
		o.landuse IS NOT NULL OR
		o.leisure IS NOT NULL OR
		o.building IS NOT NULL OR
		o.military IS NOT NULL OR
		o.office IS NOT NULL OR
		-- POI seems to always be blank.
		--o.poi IS NOT NULL OR
		o.public_transport IS NOT NULL
	   order by o.way <#> point limit 20
	)
	select * from index_query order by dist;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


-- CREATE FUNCTION osm_road_match_point_hdg(IN pt geometry)
-- RETURNS SETOF osm_road_matches AS $$
-- BEGIN
-- 	RAISE NOTICE 'osm_road_match_hdg(%)', pt;
-- 	return QUERY SELECT * from osm_road_match_hdg(pt) LIMIT 1;
-- END;
-- $$ LANGUAGE plpgsql;


CREATE FUNCTION osm_road_match_line(IN line geometry)
RETURNS SETOF osm_road_matches AS $$
DECLARE
	pt point_dump%rowtype;
	-- count int := 0;
BEGIN
	-- RAISE NOTICE 'LineString: %', ST_AsGeoJson(line);
	for pt in
		SELECT
			(dp).path[1] As index,
			(dp).geom As pt
		FROM (
			SELECT ST_DumpPoints(line) as dp
		) AS foo
	loop
  		-- RAISE NOTICE 'Point: %', ST_AsGeoJson(pt.geom);
  		-- count := count + 1;
  		-- RAISE NOTICE 'Count: %', count;
		RETURN NEXT (SELECT osm_road_match(pt.geom) limit 1) as bar;
	end loop;
	return;
END;
$$ LANGUAGE plpgsql;


CREATE FUNCTION osm_road_match_line_hdg(IN line geometry)
RETURNS SETOF osm_road_matches AS $$
DECLARE
	pt point_dump%rowtype;
	-- count int := 0;
BEGIN
	-- RAISE NOTICE 'LineString: %', ST_AsGeoJson(line);
	for pt in
		SELECT
			(dp).path[1] As index,
			(dp).geom As pt
		FROM (
			SELECT ST_DumpPoints(line) as dp
		) AS foo
	loop
  		-- RAISE NOTICE 'Point: %', ST_AsGeoJson(pt.geom);
  		-- count := count + 1;
  		-- RAISE NOTICE 'Count: %', count;
		RETURN NEXT (SELECT osm_road_match_hdg(pt.geom) limit 1) as bar;
	end loop;
	return;
END;
$$ LANGUAGE plpgsql;



-- Test queries

-- Basic just find the closest road.
--select * from osm_road_match(114.099197, 22.559517) limit 5;

-- Basic query to road match but only returns roads that are close in heading.
-- Inputs are Longitude, latitude, trajectory_heading, tolerance
-- Where tolerance just means how much deviation in the heading is allowed to make a match
--select * from osm_road_match_hdg(114.099197, 22.559517, 270, 45) limit 50; -- at 270 degrees, should get 538968

-- This query is useful in that it provides a CSV of the points of interest such that when
-- one of the columns is null, it is omitted from the results.
--select  dist, gid, osm_id
--	,name ,
--	concat_ws(',',
--		amenity, shop, sport, tourism, historic,
--		landuse, leisure, building, military
--		,office
--		,public_transport
--	) as poi_type
--	,tags
--	,way
--	from osm_poi_match(114.099197, 22.559517) where dist < 1000 limit 100;


-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.23290300000001 22.705717 180.0)'));
-- SELECT * FROM osm_road_match(ST_GeomFromEWKT('SRID=4326;POINT M(114.2325360 22.7051830 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.231949 22.704483 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.231247 22.703283 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.230652 22.702217 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.230453 22.701883 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.22938500000001 22.700317000000002 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.2285 22.698816 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.227531 22.697517 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.22640200000001 22.695932 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.223785 22.691882999999997 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.223648 22.691601000000002 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.223381 22.690483 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.223381 22.690483 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.223381 22.690483 180.0)'));
-- SELECT * FROM osm_road_match_hdg(ST_GeomFromEWKT('SRID=4326;POINT M(114.223381 22.690483 180.0)'));

-- SELECT * FROM osm_road_match_line_hdg(ST_GeomFromEWKT('SRID=4326;LINESTRING M(114.23290300000001 22.705717 180.0, 114.23253600000001 22.705182999999998 180.0, 114.231949 22.704483 180.0, 114.231247 22.703283 180.0, 114.230652 22.702217 180.0, 114.230453 22.701883 180.0, 114.22938500000001 22.700317000000002 180.0, 114.2285 22.698816 180.0, 114.227531 22.697517 180.0, 114.22640200000001 22.695932 180.0, 114.223785 22.691882999999997 180.0, 114.223648 22.691601000000002 180.0, 114.223381 22.690483 180.0, 114.223381 22.690483 180.0, 114.223381 22.690483 180.0, 114.223381 22.690483 180.0)'));
