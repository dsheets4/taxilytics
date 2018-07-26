
SET SESSION timezone TO 'Asia/Shanghai';


WITH trunc AS (
	SELECT date_trunc('month', start_datetime) as time_inc
	FROM entity_trip
	WHERE
	start_datetime > '2011-01-01 00:00:00' AND
	start_datetime <= '2012-01-01 00:00:00'
)
SELECT time_inc, count(*)
FROM trunc
GROUP BY time_inc
ORDER BY time_inc;


SELECT count(*) --DELETE
FROM entity_trip
WHERE
	(
	start_datetime >= '2011-11-13 00:00:00' --AND duration < interval '00:00:01'
	)
	AND
	(
	start_datetime < '2011-11-30 00:00:00' --AND duration < interval '00:00:01'
	)