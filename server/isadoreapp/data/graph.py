#   Copyright 2010-2019 Dan Elliott, Russell Valentine
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from isadoreapp import app
from flask import request, abort, Response
from isadoreapp.authentication import authorized
from isadoreapp.cache import noCache
import isadoreapp.util as util
import logging
import json
import pytz
from isadoreapp.data import graph_data
from isadoreapp.data import plot
import matplotlib

matplotlib.use('Agg')

TEMP_READ_TYPE_ID = 10
HUM_READ_TYPE_ID = 11

TOP_BIN_SECTION = 13
BOTTOM_BIN_SECTION = 14


# @param width The width in pixels of the drawing area, or at least approximate.
# @return best sample size in default_subsample or 0.
def get_best_sample_period(width, begin_datetime, end_datetime, conn=None):
    if not conn:
        conn = util.getConn()
    minutes = (end_datetime - begin_datetime).total_seconds() / 60.0
    minutes_per_pixel = minutes / float(width)
    cur = conn.cursor()
    # Find closest subsample.
    cur.execute("SELECT subsample from default_subsample WHERE subsample < %s ORDER BY subsample desc LIMIT 1",
                (minutes_per_pixel,))
    row = cur.fetchone()
    if not row:
        if minutes <= (10 * 60):
            # samplePeriod = 0
            # TODO: 0 is not support with are multipel bin seciton data junk
            sample_period = 5
        else:
            sample_period = 5
    else:
        sample_period = row[0]
    cur.close()
    return sample_period


@app.route('/resources/data/graphp', methods=["GET"])
@authorized('User')
@noCache()
def graphp():
    fill_id = request.values.get('fill_id', None)
    if not fill_id:
        abort(400, 'Currently only support fillId argument.')
    try:
        fill_id = int(fill_id)
    except ValueError:
        abort(400, 'Invalid parameter fill_id')
    try:
        display_tz = pytz.timezone(request.values.get("display_tz"))
    except:
        return abort(400, 'invalid display_tz')

    png_data = graphp2(fill_id, display_tz)
    if not png_data:
        abort(500, 'Internal server error: Failed to make plot.')

    return Response(png_data, mimetype='image/png')


def graphp2(fill_id, display_tz):
    conn = util.getConn()
    general = util.getRowFromTableById('general_config', 1, conn=conn)
    query = []

    options = {}
    options['axisColors'] = [['#FF0000', '#0000FF']]
    options['axisLabels'] = [['Temperature (F)', 'Humidity (%)']]
    options['dataAxisMap'] = [[0, 0, 1, 1]]
    options['minMaxAreas'] = [[1, 1, 1, 1]]

    fill = util.getRowFromTableById("fill", fill_id, conn=conn)
    #    bin = util.getRowFromTableById('bin', fill['bin_id'], conn=conn)
    #    topSection = util.getRowFromTableById("bin_section", TOP_BIN_SECTION, conn=conn)
    #    bottomSection = util.getRowFromTableById("bin_section", BOTTOM_BIN_SECTION, conn=conn)

    begin_datetime = fill["air_begin_datetime"]
    if not begin_datetime:
        abort(404, 'Fill has not started air.')
    if not fill["air_end_datetime"]:
        end_datetime = util.getDateFromParam("now")
    else:
        end_datetime = fill["air_end_datetime"]
    if general['inletoutlet']:
        query.append(['inlet', [TEMP_READ_TYPE_ID]])
        query.append(['outlet', [TEMP_READ_TYPE_ID]])
        query.append(['inlet', [HUM_READ_TYPE_ID]])
        query.append(['outlet', [HUM_READ_TYPE_ID]])
        options['seriesLabels'] = [['inlet temp', 'outlet temp', 'inlet RH', 'outlet RH']]
    else:
        query.append(['sensor', [TOP_BIN_SECTION, TEMP_READ_TYPE_ID]])
        query.append(['sensor', [BOTTOM_BIN_SECTION, TEMP_READ_TYPE_ID]])
        query.append(['sensor', [TOP_BIN_SECTION, HUM_READ_TYPE_ID]])
        query.append(['sensor', [BOTTOM_BIN_SECTION, HUM_READ_TYPE_ID]])
        options['seriesLabels'] = [['top temp', 'bottom temp', 'top RH', 'bottom RH']]

    if general['emchrs_per_point']:
        query.append(['maxtemp', []])
        options['seriesLabels'][0].append('target temp')
        options['dataAxisMap'][0].append(0)
        options['minMaxAreas'][0].append(0)

    # 600 x 400 was size of old graph
    graph_dims = (600, 400)

    # Auto sample period
    sample_period = get_best_sample_period(graph_dims[0] / 5, begin_datetime, end_datetime, conn=conn)
    logging.debug("Sample period: " + str(sample_period))
    # samplePeriod=120

    our_graph_data = graph_data.graph_data_struct(fill['bin_id'], query, sample_period, begin_datetime, end_datetime)

    p = plot.Plotter(our_graph_data, None, options, graph_dims, display_tz)
    return p.getPNGBuffer()


@app.route('/resources/data/graphq', methods=["GET"])
@authorized('User')
@noCache()
def graphq():
    try:
        bin_id = int(request.values.get("bin_id"))
    except ValueError:
        return abort(400, 'Invalid bin_id')
    try:
        query_top = json.loads(request.values.get("query_top"))
    except json.decoder.JSONDecodeError:
        return abort(400, 'invalid query_top')
    try:
        query_bottom = json.loads(request.values.get("query_bottom"))
    except json.decoder.JSONDecodeError:
        return abort(400, 'invalid query_bottom')

    try:
        display_tz = pytz.timezone(request.values.get("display_tz"))
    except json.decoder.JSONDecodeError:
        return abort(400, 'invalid display_tz')

    if len(query_top) == 0:
        query_top = None
    if len(query_bottom) == 0:
        query_bottom = None

    try:
        sample_period = request.values.get("sample_period")
        if sample_period:
            sample_period = int(sample_period)
    except ValueError:
        return abort(400, 'invalid sample_period parameter')

    try:
        begin_datetime = util.getDateFromParam(request.values.get("begin_datetime"))
        end_datetime = util.getDateFromParam(request.values.get("end_datetime"))
    except:
        return abort(400, 'invalid datetime parameter')

    if not begin_datetime or not end_datetime:
        abort(400, 'Missing datetime period')

    plot_options = request.values.get("plot_options")
    try:
        options = json.loads(plot_options)
    except Exception as e:
        logging.debug("plot_options=" + plot_options)
        logging.exception(e)
        return abort(400, 'Invalid plot_options')

    # Add hash to axisColor strings
    for i in range(0, len(options['axisColors'])):
        for j in range(0, len(options['axisColors'][i])):
            options['axisColors'][i][j] = '#' + options['axisColors'][i][j]

    if 'graphDims' in options:
        graph_dims = options['graphDims']
        if graph_dims[0] > 2000 or graph_dims[1] > 2000:
            abort(400, 'options.graphDims dims more than 2000x2000')
    else:
        graph_dims = (600, 400)

    logging.debug("graphDims=" + str(graph_dims))
    if not sample_period or sample_period <= 0:
        sample_period = get_best_sample_period(graph_dims[0] / 5, begin_datetime, end_datetime)

    logging.debug("sp=" + str(sample_period) + ", queryTop=" + str(query_top) + ", queryBottom=" + str(query_bottom))
    graph_data_top = None
    graph_data_bottom = None
    if query_top:
        graph_data_top = graph_data.graph_data_struct(bin_id, query_top, sample_period, begin_datetime, end_datetime)
        logging.debug("toplen = " + str(len(graph_data_top)))
    if query_bottom:
        graph_data_bottom = graph_data.graph_data_struct(bin_id, query_bottom, sample_period, begin_datetime,
                                                         end_datetime)
        logging.debug("botlen = " + str(len(graph_data_bottom)))

    if not query_top and query_bottom:
        # switch top and bottom
        graph_data_top = graph_data_bottom
        graph_data_bottom = None
        graphq_switch_options(options)

    for g in range(2):
        if 0 not in options['dataAxisMap'][g]:
            graphq_switch_axis(options, g)

    # degree symbol fix
    for g in range(len(options['axisLabels'])):
        for idx in range(len(options['axisLabels'][g])):
            options['axisLabels'][g][idx] = options['axisLabels'][g][idx].replace('&deg;', '$^\circ$')

    logging.debug("options=" + str(options))
    p = plot.Plotter(graph_data_top, graph_data_bottom, options, graph_dims, display_tz)
    return Response(p.getPNGBuffer(), mimetype='image/png')


def graphq_switch_options(options):
    options['axisColors'][0] = options['axisColors'][1]
    options['axisLabels'][0] = options['axisLabels'][1]
    options['dataAxisMap'][0] = options['dataAxisMap'][1]
    options['minMaxAreas'][0] = options['minMaxAreas'][1]
    options['seriesLabels'][0] = options['seriesLabels'][1]


def graphq_switch_axis(options, g):
    options['axisColors'][g][0] = options['axisColors'][g][1]
    options['axisLabels'][g][0] = options['axisLabels'][g][1]
    options['dataAxisMap'][g] = [0] * len(options['dataAxisMap'][g])
