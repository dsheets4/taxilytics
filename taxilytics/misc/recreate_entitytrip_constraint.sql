﻿ALTER TABLE entity_trip
DROP CONSTRAINT entity_trip_entity_id_d09f4a61_uniq

ALTER TABLE entity_trip
ADD CONSTRAINT entity_trip_entity_id_d09f4a61_uniq
UNIQUE (entity_id, start_datetime)