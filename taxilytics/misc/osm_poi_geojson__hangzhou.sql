-- In pgadmin use File->Export with the following options to export a json file
--    - Uncheck columns names
--    - Use 'No Quoting'
WITH poi_points AS (
	SELECT row_to_json(f) AS feature FROM (
	   SELECT
	      'Feature' AS type,
	      ST_AsGeoJSON(ST_Transform(way,4326))::json AS geometry,
	      row_to_json(
		(SELECT l FROM (SELECT
			gid AS id,
			osm_id,
			CASE WHEN tags->'name:en' <> '' THEN tags->'name:en'
			     WHEN tags->'name:zh_pinyin' <> '' THEN tags->'name:zh_pinyin'
			     ELSE name END AS name,
			string_to_array(concat_ws(',',
				p.amenity,
				p.aerialway,
				(CASE WHEN p.shop = 'yes' THEN 'shop' ELSE p.shop END),
				p.sport,
				p.tourism,
				p.historic,
				p.landuse,
				p.leisure,
				(CASE WHEN p.building = 'yes' OR p.building = 'entrance' THEN '' ELSE p.building END),
				p.military,
				p.office,
				p.public_transport
			), ',') AS poi_tags,
			(CASE WHEN array_length(akeys(tags), 1) > 0 THEN CAST(p.tags AS json) ELSE NULL END) AS extra
		) AS l)) AS properties
	   FROM planet_osm_point as p
	   WHERE
		(
			p.amenity IS NOT NULL OR
			p.aerialway IS NOT NULL OR
			p.shop IS NOT NULL OR
			p.sport IS NOT NULL OR
			p.tourism IS NOT NULL OR
			p.landuse IS NOT NULL OR
			p.leisure IS NOT NULL OR
			(p.building IS NOT NULL AND p.building <> 'yes' OR p.building <> 'entrance') OR
			p.military IS NOT NULL OR
			p.office IS NOT NULL OR
			(p.poi IS NOT NULL AND p.poi <> '') OR  -- POI seems to always be blank.
			p.public_transport IS NOT NULL
		) AND
		ST_Contains(ST_Transform(
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
			3857), way)
	) AS f
)
SELECT row_to_json(fc) AS hangzhou_pois FROM (
	SELECT
		'FeatureCollection' AS type,
		json_agg(feature) AS features FROM poi_points
	) AS fc