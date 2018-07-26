-- 1. 
CREATE TABLE intersections AS
	SELECT DISTINCT    
		ST_Intersection(a.way, b.way) as geom
	FROM
		planet_osm_line as a,
		planet_osm_line as b
	WHERE
		ST_Touches(a.way, b.way)
		OR
		ST_Crosses(a.way, b.way)    
		AND
		a.gid != b.gid
		AND
		highway IS NOT NULL
	GROUP BY
		geom;

-- 2. 
CREATE TABLE rp_union AS
	SELECT *
	FROM ogrgeojson
	LEFT JOIN split_points ON ST_Intersects(planet_osm_line.wkb_geometry, split_points.geom)

-- 3.
CREATE TABLE rp_union1 AS
	SELECT
		id,
		highway,
		oneway,
		ST_LineMerge(ST_Union(f.wkb_geometry)) as lgeom,
		ST_Multi(ST_Union(f.geom)) as pgeom
	FROM rp_union As f
	GROUP BY id,highway,oneway;

-- 4. 
CREATE TABLE split_roads AS
	SELECT 
		id As oldId,
		highway,
		oneway,
		ST_GeomFromEWKB((ST_Dump(ST_Split(g.lgeom, g.pgeom))).geom) As geom
	FROM rp_union1 as g;

-- 5. 
SELECT UpdateGeometrySRID('split_roads','geom',4326); first mapping algorithm

-- 6. 
CREATE SEQUENCE my_ids6;
ALTER TABLE split_roads ADD id INT UNIQUE;
UPDATE split_roads SET id = NEXTVAL('my_ids6');