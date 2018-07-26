import os
import subprocess
import pandas as pd
from contextlib import contextmanager

from loader.loaders import Loader, DataFrameLoader, StreamLoader

from taxi.nyctlc.config import get_config, awk_template


class NycTlcLoader(Loader):
    def __init__(self, input_resource):
        super().__init__(input_resource)

    @classmethod
    def accept(cls, input_resource, create_object=True):
        if os.path.isfile(input_resource):
            config = get_config(input_resource)
            if config is not None:
                if create_object:
                    return cls(input_resource=input_resource, config=config)
                else:
                    return True


class NycTlcStream(StreamLoader, NycTlcLoader):
    """ Only works when awk is available, which is generally *nix hosts. """
    delimiter = '|'
    table_fields = {
        'trip': ['id', 'start_datetime', 'duration', 'geometry', 'archive_uri', 'metadata']
    }

    def __init__(self, input_resource, config=None):
        self.config = config or get_config(input_resource)
        self.awk_script_template = awk_template
        super().__init__(input_resource=input_resource)

    @contextmanager
    def stream(self, table):
        if table in self.table_fields:
            ps_awk = subprocess.Popen(
                [
                    'awk',
                    '-v', 'f={}'.format(self.input_resource),
                    self.awk_script_template.format(
                        output_delim=self.delimiter,
                        **self.config.awk_format_dict
                    ),
                    self.input_resource
                ],
                stdout=subprocess.PIPE
            )
            yield ps_awk.stdout
            ps_awk.wait(100)


class NycTlcDataFrame(DataFrameLoader, NycTlcLoader):
    def __init__(self, input_resource, config=None):
        self.config = config or get_config(input_resource)
        super().__init__(input_resource,
                         parse_func=pd.read_csv,
                         parse_args=self.config.dataframe_parse_args,
                         postprocess_functions=self.config.dataframe_postprocess)
