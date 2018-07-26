WITH data AS (
	SELECT
		t.id as trip_id, t.archive_uri as uri, TRUE as success, 1 as org
	FROM entity_trip as t
	LIMIT 10
),
insert_ds AS (
	INSERT INTO entity_datasource (uri, successful_load, organization_id)
	SELECT d.uri, d.success, d.org FROM data AS d
	ON CONFLICT DO NOTHING
	RETURNING entity_datasource.id AS ds_id
),
update_trip AS (
	UPDATE entity_trip as t2
	SET data_source_id = ds_id
	FROM data, insert_ds
	WHERE t2.id = data.trip_id
)
UPDATE entity_tripdata as td
SET data_source_id = ds_id
FROM data, insert_ds
WHERE td.trip_id = data.trip_id
