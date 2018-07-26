from datetime import datetime, timezone


epoch = datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)  # 2000-01-01 00:00:00
extra_id_bits = 12
entity_id_bits = 16
max_bits = 63


def create_id(extra_id, entity_id, start_time):
    return (
        (extra_id << (max_bits-extra_id_bits)) +
        (entity_id << (max_bits-extra_id_bits-entity_id_bits)) +
        int((start_time.tz_convert(timezone.utc) - epoch).total_seconds() * 100)
    )
