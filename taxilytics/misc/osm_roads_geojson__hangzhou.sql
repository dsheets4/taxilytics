SELECT row_to_json(f) AS feature FROM (
   SELECT
      'Feature' AS type,
      ST_AsGeoJSON(ST_Transform(way,4326))::json AS geometry,
      row_to_json((SELECT l FROM (SELECT gid AS id, highway, oneway, CASE WHEN tags->'name:en' <> '' THEN tags->'name:en' ELSE name END AS name) AS l)) AS properties
   FROM planet_osm_line
   WHERE
	highway IN (
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
		'turning_circle') AND
	ST_Intersects(way, ST_Transform(
		ST_GeomFromText('POLYGON((
			119.56558227539062 30.60458185864903,
			119.56558227539062 30.214927389558223,
			119.71758842468262 30.04002774575956,
			119.80367660522461 29.876727320355958,
			120.2285385131836 29.81657483511139,
			120.48585891723633 30.045080122817144,
			120.72395324707031 30.190003096851264,
			120.74446678161621 30.230056916247293,
			120.69906234741211 30.298555614147382,
			120.63846588134766 30.421199826754933,
			120.54765701293945 30.577392196458817,
			120.40191650390625 30.64712427164843,
			120.09429931640625 30.624673661761303,
			119.9985122680664 30.585077004647964,
			119.85054016113281 30.6093097168015,
			119.56558227539062 30.60458185864903))', 4326),
		3857))
) AS f;