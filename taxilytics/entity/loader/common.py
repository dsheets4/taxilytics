import logging
import traceback
from django.db import transaction


logger = logging.getLogger(__name__)


def commit_trip(row):
    try:
        with transaction.atomic():
            row['trip'].save()
        with transaction.atomic():
            for d in row['trip_data']:
                d.trip = row['trip']
                d.save()
        return True
    except (SystemError, KeyboardInterrupt):
        raise
    except BaseException:
        logger.warning('Failed to commit {} due to:\n{}'.format(
            row,
            traceback.format_exc()
        ))
    return False


def iterQueue(queue, sentinel):
    """Iterate over the values in queue until sentinel is reached."""
    while True:
        value = queue.get()
        if value != sentinel:
            yield value
        else:
            return