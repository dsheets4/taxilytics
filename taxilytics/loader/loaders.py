import os


class Loader:
    table_fields = {}

    def __init__(self, input_resource):
        self.input_resource = os.path.abspath(input_resource)

    @classmethod
    def accept(cls, res):
        """ Returns true if the Loader accepts the provided input resource """
        raise NotImplementedError("{} needs to implement an 'accept' method for Loader".format(
            cls.__name__
        ))

    def tables(self):
        return self.table_fields.keys()

    def fields(self, table):
        return self.table_fields.get(table)


class StreamLoader(Loader):

    def stream(self, table):
        raise NotImplementedError(
            "{} needs to implement a 'stream' method for StreamLoader".format(
                self.__class__.__name__
            ))


class DataFrameLoader(Loader):
    def __init__(self, input_resource, parse_func, parse_args, postprocess_functions):
        super().__init__(input_resource)
        self.parse_func = parse_func
        self.parse_args = parse_args
        self.postprocess_functions = postprocess_functions

    def dataframe(self):
        df = self.parse_func(
            self.input_resource,
            **self.parse_args
        )

        for f in self.postprocess_functions:
            df = f(df)

        return df
