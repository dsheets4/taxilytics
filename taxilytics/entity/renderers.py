import pickle
import io
import json
import uuid

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # noqa - Must set before pyplot import or crashes ensue
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from pandas.tools.plotting import scatter_matrix

from rest_framework import renderers
from rest_framework.exceptions import NotAcceptable

from django_util.renderers import MapRenderer


plt.style.use('ggplot')


def str_to_tuple(csv_str):
    if isinstance(csv_str, str):
        csv_str = csv_str.split(',')
        csv_str = map(lambda x: int(x), csv_str)
    return csv_str


def _merge_dataframes(df_dict):
    """ Merges a dictionary of DataFrames into a single DataFrame """
    return pd.DataFrame().join([v['dataframe'] for v in df_dict], how='outer')


def _dataframe_to_json(df, orient='columns'):
    # TODO: Add index to the returned JSON data for records and values
    #       The other orientations include index by default.  However,
    #       including index seems to kill python.
    # orient allows changing the format of the returned json
    #  split : multi-dim array, separate array labels columns, third has index
    #  records : list of objects one key per param
    #  index : like records but outer structure is object named by index
    #  columns : params are separate objects contains objects named by index
    #  values : just the values array
    return json.loads(df.to_json(
        date_format='iso',
        orient=orient
    ))


class EntityTripMapRenderer(MapRenderer):
    context = {
        'dataObj': {
            'className': 'Rest',
            'args': {
            }
        },
        'appType': 'entity',
        'options': {
            'queryOp': 'intersects',
        }
    }


class DataFrameCsvFileRenderer(renderers.BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, media_type=None, renderer_context=None):
        response = renderer_context['response']

        if response.exception:
            return data['detail']
        else:
            action = renderer_context['view'].action
            if action == 'list':
                raise NotAcceptable(
                    'Format not accepted on list. Select a specific object.'
                )
            elif action == 'retrieve':
                response = renderer_context['response']
                response['Content-Disposition'] = 'attachment; filename="%s-%s.csv"' % (
                    data['common_id'],
                    data['start_datetime']
                )
                df = _merge_dataframes(data['data'])
                return df.to_csv()


class DataFrameH5FileRenderer(renderers.BaseRenderer):
    media_type = 'application/x-hdf'  # Single Series Store
    format = 'h5'
    charset = None  # Don't encode text
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        response = renderer_context['response']

        if response.exception:
            response['Content-Disposition'] = 'attachment; filename="error.h5"'
            return None
        else:
            filename = uuid.uuid1().hex
            h5 = pd.HDFStore(
                filename,
                mode='w',
                driver="H5FD_CORE",
                driver_core_backing_store=0
            )

            action = renderer_context['view'].action
            if action == 'list':
                raise NotAcceptable(
                    'Format not accepted on list. Select a specific object.'
                )

            df = data['data']
            for i, d in enumerate(df):
                h5['df_%d' % i] = d['dataframe']

            response['Content-Disposition'] = 'attachment; filename="%s-%s.h5"' % (
                data['common_id'],
                data['start_datetime']
            )
            ret = h5._handle.get_file_image()
            h5.close()
        return ret


class DataFrameBytesFileRenderer(renderers.BaseRenderer):
    media_type = 'application/octet-stream'
    format = 'bytes'

    def render(self, data, media_type=None, renderer_context=None):
        action = renderer_context['view'].action
        response = renderer_context['response']

        if response.exception:
            response[
                'Content-Disposition'] = 'attachment; filename="error.bytes"'
            data = {
                'exception': data,
                'status': response.status_text,
                'code': response.status_code,
            }
        else:
            if action == 'list':
                raise NotAcceptable(
                    'Format not accepted on list. Select a specific object.'
                )

            response['Content-Disposition'] = 'attachment; filename="%s-%s.bytes"' % (
                data['common_id'],
                data['start_datetime']
            )
        return pickle.dumps(data)


class DataFrameJsonRenderer(renderers.JSONRenderer):
    media_type = 'application/json'
    format = 'json'
    charset = 'utf-8'

    def render(self, data, media_type=None, renderer_context=None):
        # Lists use data == OrderedDict with 'results' key is list of results
        # Single values use data == ReturnDict
        response = renderer_context['response']
        if not response.exception:
            datalist = data.get('data', [])
            for d in datalist:
                df = d['dataframe']  # If there's a dataframe, render.
                q = renderer_context['request'].query_params
                orient = q.get('orient', 'records')
                d['dataframe'] = _dataframe_to_json(df, orient)

        return super().render(data, media_type, renderer_context)


class DataFrameChartRenderer(renderers.BaseRenderer):
    media_type = 'image/png'
    format = 'png'
    charset = None  # Don't encode text
    render_style = 'binary'
    chart_types = ['line', 'scatter_matrix']

    def render(self, data, media_type=None, renderer_context=None):
        response = renderer_context['response']
        if not response.exception:
            action = renderer_context['view'].action
            if action == 'list':
                raise NotAcceptable(
                    'Format not accepted on list. Select a specific object.'
                )

            q_dict = renderer_context['request'].query_params.dict()

            # TODO: Figure out how to plot parameters at different rates.
            #       Merging the dataframes and interpolating gives something
            #       but it's not always accurate since the default
            #       interpolation may not apply to the parameter and then it
            #       injects indiscernable points into the plot.  however, most
            #       other methods result in a memory error.  e.g. The following
            #       usually creates multiple figures, e.g. in python notebook.
            #       for v in df.values():
            #           plt.figure()
            #           ax = v.plot()
            df = _merge_dataframes(data['data'])
            df = df.interpolate(method='time')
            # End code to get something of a plot.

            figsize = str_to_tuple(q_dict.get('figsize', (15, 10)))

            chart_type = q_dict.pop('type', None)
            if chart_type is None or chart_type == 'line':
                ax = df.plot(
                    figsize=figsize,
                    subplots=q_dict.get('subplots', False),
                    style=q_dict.get('style', None)
                )
                if isinstance(ax, np.ndarray):
                    ax = ax[0]
            elif chart_type == 'scatter_matrix':
                ax = scatter_matrix(
                    df,
                    figsize=figsize,
                    alpha=q_dict.get('alpha', 0.5),
                    diagonal=q_dict.get('diagonal', 'hist'),
                    style=q_dict.get('style', None)
                )[0][0]

            fig = ax.get_figure()
            canvas = FigureCanvas(fig)
            png_bytes = io.BytesIO()
            canvas.print_png(png_bytes)
            return png_bytes.getvalue()
