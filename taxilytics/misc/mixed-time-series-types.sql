SELECT * FROM entity_trip LIMIT 10;

INSERT INTO entity_tripdatadecimal (columns, ts, "values", trip_id) VALUES (
	'{"val1","val2"}',
	'{"2011-01-01 00:01:00", "2011-01-01 00:02:00"}',
	'{1.1, 2.2}',
	1501000000000000002
);

INSERT INTO entity_tripdataint (columns, ts, "values", trip_id) VALUES (
	'{"val3","val4"}',
	'{"2011-01-01 00:01:00", "2011-01-01 00:02:00"}',
	'{3, 4}',
	1501000000000000002
);

INSERT INTO entity_tripdatadecimal (columns, ts, "values", trip_id) VALUES (
	'{"val5","val6"}',
	'{"2011-01-01 00:01:00", "2011-01-01 00:02:00"}',
	'{"5555", "6666"}',
	1501000000000000002
);

SELECT * FROM entity_tripdatacommon
SELECT * FROM entity_tripdataint
SELECT * FROM entity_tripdatadecimal
SELECT * FROM entity_tripdatastring