WITH needs_corrected AS (
	SELECT
		id,
		trip_id,
		definition_id
	FROM entity_tripdata AS td
	WHERE definition_id = 6 AND temp_find_funk_time(_dataframe)
	LIMIT 1000
)
UPDATE entity_tripdata AS td
SET _dataframe=temp_fix_ts(td._dataframe)
FROM needs_corrected as nc
WHERE nc.id=td.id



                SELECT
                    trip_id,
                    array_agg(definition_id)
                FROM entity_tripdata AS td
                GROUP BY trip_id
                HAVING sum(
                    CASE WHEN definition_id = (
                        SELECT dd.id
                        FROM entity_datadefinition AS dd
                        WHERE short_name='Road Match Data'
                    ) THEN 1 ELSE 0 END
                ) = 0
                LIMIT 1


SELECT TIMESTAMP '2001-02-16 20:38:40' AT TIME ZONE 'Asia/Shanghai';
SELECT timezone('Asia/Shanghai', TIMESTAMP '2001-02-16 20:38:40')