from collections import namedtuple
from IPython.display import Markdown
from itertools import islice
from django.db import connection

cursor = connection.cursor()

num_results = 20  # Maximum results to print from a query


def format_results(results):
    if len(results) > 1:
        nl = '\n'
        col_sep = '|'
    else:
        nl = ''
        col_sep = ', '
    return Markdown(nl.join((
        col_sep.join(f for f in results[0]._fields),  # Header row
        col_sep.join(['-:'] * len(results[0]._fields)) if len(results) > 1 else ' = ',  # Alignment Row
        '\n'.join(col_sep.join(str(getattr(r, f)) if getattr(r, f) is not None else 'ANY' for f in r._fields) for r in results).rstrip())
    ))


def execute(q_str, max_results=num_results):
    cursor.execute(q_str)
    nt_result = namedtuple('Result', (col[0] for col in cursor.description))
    return [nt_result(*r) for r in islice(cursor, None, max_results)]
