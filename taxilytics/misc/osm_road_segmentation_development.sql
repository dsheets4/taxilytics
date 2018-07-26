-- ****************************************************************************
-- OSM defines intersections between two ways by declaring the same node 
-- in both.  Finding the intersections is important because it avoids
-- splitting roads at places such as an overpass where the roads intersect in
-- the 2D plane but do not actually connect in reality.
-- For all China data, takes about 7 minutes to run (with no index available)
-- ****************************************************************************
SELECT
	a.id as a_id,
	b.id as b_id,
	a.tags as a_tags,
	b.tags as b_tags,	
	ARRAY(SELECT UNNEST(a.nodes) INTERSECT SELECT UNNEST(b.nodes)) as intersecting_nodes
FROM
	planet_osm_ways as a,
	planet_osm_ways as b
-- INNER JOIN planet_osm_nodes as n ON intersecting_nodes=n.id
WHERE
	a.id != b.id
	AND
	-- @> is the subset operator
	a.tags @> ARRAY['highway']::text[]
	AND
	-- && is the overlap operator and checks for ANY overlap
	a.tags && ARRAY[
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
	]::text[]
	AND
	b.tags @> ARRAY['highway']::text[]
	AND
	b.tags && ARRAY[
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
	]::text[]
	AND
	a.nodes && b.nodes
LIMIT 100
;
