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
from bottle import route  # @UnresolvedImport
from bottle import request, response, static_file, abort
from authentication import authorized
import util
import logging;
from datetime import time, timedelta
import random
import gzip
import json
from alarms import EMC


DEW_READ_TYPE_ID = 5
JFACTOR_READ_TYPE_ID = 6
GPRESSURE_READ_TYPE_ID = 7
TEMP_READ_TYPE_ID = 10
HUM_READ_TYPE_ID = 11
PRESSURE_READ_TYPE_ID = 14
WB_READ_TYPE_ID = 131

TOP_BIN_SECTION = 13
BOTTOM_BIN_SECTION = 14


@route('/resources/data/graph/selections/:id#[0-9]+#', method=["GET"])
@authorized('User')
# @confCache()
def data_graph_selections(id):
    true_bin = False
    selections = {}
    tops = []

    conn = util.getConn()
    binr = util.getRowFromTableById("bin", int(id), conn=conn)
    bin_sections = []
    bin_sections_names = []
    if not binr:
        abort(404, 'Bin not found')
    sql = """SELECT DISTINCT ON (read_type_id, bin_section_id)
            rt.id AS read_type_id, rt.short_name AS read_type_name, rt.units, bs.id AS bin_section_id,
            bs.name AS bin_section_name
        FROM
            reading_subsample rs, reading_data_subsample rds, read_type rt, bin_section bs
        WHERE
            rt.id = rds.read_type_id AND bs.id = rds.bin_section_id AND rds.bin_id = %s AND
            rds.reading_subsample_id = rs.id AND rs.id IN
            (SELECT id from reading_subsample where sample_period = 5 ORDER by datetime desc limit 100)"""
    cur = conn.cursor()
    cur.execute(sql, (id,))
    # TODO: Virtual Sensor detection (Dew, jfactor)
    for row in cur:
        read_type_id = row[0]
        read_type_name = row[1]
        units = row[2]
        bin_section_id = row[3]
        bin_section_name = row[4]
        if not bin_section_id in bin_sections:
            bin_sections.append(bin_section_id)
            bin_sections_names.append(bin_section_name)
        if not units in selections:
            selections[units] = []
        selections[units].append(
            [bin_section_name + ' ' + read_type_name, 'sensor', [bin_section_id, read_type_id]])
        if bin_section_id == TOP_BIN_SECTION:
            tops.append(read_type_id)
        if bin_section_id == BOTTOM_BIN_SECTION:
            if read_type_id in tops:
                true_bin = True
                selections[units].append(['Inlet ' + read_type_name, 'inlet', [read_type_id]])
                selections[units].append(['Outlet ' + read_type_name, 'outlet', [read_type_id]])
        #Guage pressure
        if read_type_id == PRESSURE_READ_TYPE_ID:
            if not "inH2O" in selections:
                selections["inH2O"] = []
            selections["inH2O"].append(
                [bin_section_name + ' ' + read_type_name, 'sensor', [bin_section_id, GPRESSURE_READ_TYPE_ID]])
            if bin_section_id == TOP_BIN_SECTION:
                tops.append(read_type_id)
            if bin_section_id == BOTTOM_BIN_SECTION:
                if read_type_id in tops:
                    selections["inH2O"].append(['Inlet ' + read_type_name, 'inlet', [GPRESSURE_READ_TYPE_ID]])
                    selections["inH2O"].append(['Outlet ' + read_type_name, 'outlet', [GPRESSURE_READ_TYPE_ID]])
    general = util.getRowFromTableById('general_config', 1, conn=conn)
    if true_bin:
        # Virtual Options
        if general['jfactor']:
            selections['Misc'] = [['jFactor', 'sensor', [TOP_BIN_SECTION, JFACTOR_READ_TYPE_ID]]]
        #selections['&deg;F'].append(['Max Temp', 'maxtemp', []])
        selections['&deg;F'].append(['Top Dew', 'sensor', [TOP_BIN_SECTION, DEW_READ_TYPE_ID]])
        selections['&deg;F'].append(['Bottom Dew', 'sensor', [BOTTOM_BIN_SECTION, DEW_READ_TYPE_ID]])
        selections['&deg;F'].append(['Inlet Dew', 'inlet', [DEW_READ_TYPE_ID]])
        selections['&deg;F'].append(['Outlet Dew', 'outlet', [DEW_READ_TYPE_ID]])
        selections['&deg;F'].append(['Top WB', 'sensor', [TOP_BIN_SECTION, WB_READ_TYPE_ID]])
        selections['&deg;F'].append(['Bottom WB', 'sensor', [BOTTOM_BIN_SECTION, WB_READ_TYPE_ID]])
        selections['&deg;F'].append(['Inlet WB', 'inlet', [WB_READ_TYPE_ID]])
        selections['&deg;F'].append(['Outlet WB', 'outlet', [WB_READ_TYPE_ID]])
    else:
        for i in range(len(bin_sections)):
            selections['&deg;F'].append([bin_sections_names[i]+' WB', 'sensor', [bin_sections[i], WB_READ_TYPE_ID]])

    rlist = []
    for key, value in selections.iteritems():
        rlist.append([key, value])
    return {'options': rlist}


def append_join(joins, j_from, j_id, bin_id, bin_section_id, read_type_id):
    label = gen_joinlabel(bin_section_id, read_type_id)
    if label not in joins:
        joins[label] = """ LEFT OUTER JOIN %s %s ON
            r.id = %s.%s AND %s.bin_id = %d AND %s.bin_section_id = %d
            AND %s.read_type_id = %d """ % (
            j_from, label, label, j_id, label, bin_id, label, bin_section_id, label, read_type_id)


def gen_joinlabel(bin_section_id, read_type_id):
    return 'bs%ds%d' % (bin_section_id, read_type_id)


"""
&deg;F    {subsection} {short_name}, Inlet {short_name}, Outlet {short_name}, Max Temp; short_name = 'Temp'|'Dew'|'SP'|'PV'
           sensor:[bin_section_id, sensor_type_id], inlet/outlet: [sensor_type_id], maxtemp: []
Percent   {subsection} {short_name}, Inlet {short_name}, Outlet {short_name}; short_name = 'RH'
           sensor:[bin_section_id, sensor_type_id], inlet/outlet: [sensor_type_id]
RPM       {subsection} {short_name}; short_name = 'FAN RPM'|'VFD RPM'
            sensor:[bin_section_id, sensor_type_id]
Amps      {subsection} {short_name}; short_name = 'VFD Out'
            sensor:[bin_section_id, sensor_type_id]
MPH       {subsection} {short_name}; short_name = 'Wind'
            sensor:[bin_section_id, sensor_type_id]
Misc      {subsection} {short_name}; short_name = 'jfactor'
            sensor:[top_bin_section_id, sensor_type_id]
"""


def dummy_graph_data(bin_id, query, sample_period, begin_datetime, end_datetime):
    filename = "csv_" + str(time.time()) + "_" + str(random.random()) + ".csv.gz"
    f = gzip.open("./gen_data/" + filename, 'wb')
    f.write('{"data": [')

    ts = begin_datetime
    tdelta = timedelta(minutes=sample_period)
    first = True
    while ts < end_datetime:
        if first:
            line = ""
            first = False
        else:
            line = ","
        line += "[\"%s\"" % ts.isoformat
        ts = ts + tdelta
        for i in range(len(query)):
            line += ", [%f, %f, %f]" % (i - i / (i + 1), i, i + i / (i + 2))
        line += "]"
        f.write(line)
    f.write(']}')
    f.close()

    # response.headers['Content-disposition'] = 'attachment; filename=data.csv.gz'
    response.content_type = 'application/json'
    return static_file(filename, root='./gen_data')


@route('/resources/data/graph/data', method=["GET"])
@authorized('User')
def data_graph_data():
    """
query format
 [ [TYPE_STR, [OPTS]], ...]
Type:
TYPE_STR: "sensor" - Single sensor readings
  OPTS: [bin_section_id, read_type_id]
TYPE_STR: "inlet" - Inlet data
  OPTS: [read_type_id]
TYPE_STR: "outlet" - Outlet data
  OPTS: [read_type_id]
TYPE_STR: "maxtemp"
  OPTS: []
"""
    bin_id = util.getRequiredIntParam('bin_id')
    begin_datetime = util.getDateFromParam(request.params.get('begin_datetime', None))
    end_datetime = util.getDateFromParam(request.params.get('end_datetime', None))
    sample_period = util.getRequiredIntParam('sample_period')
    query_param = json.loads(request.params.get('query'))

    return util.responseJSON(graph_data_struct(bin_id, query_param, sample_period, begin_datetime, end_datetime))


"""
query format
 [ [TYPE_STR, [OPTS]], ...]
Type:
TYPE_STR: "sensor" - Single sensor readings
  OPTS: [bin_section_id, read_type_id]
TYPE_STR: "inlet" - Inlet data
  OPTS: [read_type_id]
TYPE_STR: "outlet" - Outlet data
  OPTS: [read_type_id]
TYPE_STR: "maxtemp"
  OPTS: []

@return [[datetime, [maxq1, avgq1, minq1], [maxq2, avgq2, minq2], ...], ...]
"""


def graph_data_struct(bin_id, query, sample_period, begin_datetime, end_datetime):
    q_where = 'r.datetime >= %s AND r.datetime <= %s '
    q_where_args = [begin_datetime, end_datetime]
    if sample_period <= 0:
        sample_period = 5
    q_from = 'reading_subsample r'
    q_where += 'AND r.sample_period = %s '
    q_where_args.append(sample_period)
    j_from = 'reading_data_subsample'
    j_id = 'reading_subsample_id'

    joins = {}

    utlabel = gen_joinlabel(TOP_BIN_SECTION, TEMP_READ_TYPE_ID)
    ltlabel = gen_joinlabel(BOTTOM_BIN_SECTION, TEMP_READ_TYPE_ID)
    #uhlabel = gen_joinlabel(TOP_BIN_SECTION, HUM_READ_TYPE_ID)
    #lhlabel = gen_joinlabel(BOTTOM_BIN_SECTION, HUM_READ_TYPE_ID)

    q_select = "SELECT r.datetime "
    for d in query:
        if d[0] == "sensor":
            bin_section_id = d[1][0]
            read_type_id = d[1][1]
            label = gen_joinlabel(bin_section_id, read_type_id)
            q_select += ",  ARRAY[%s.min, %s.avg_value, %s.max] " % (label, label, label)
            append_join(joins, j_from, j_id, bin_id, bin_section_id, read_type_id)
        elif d[0] == "inlet" or d[0] == "outlet":
            read_type_id = d[1][0]
            top_label = gen_joinlabel(TOP_BIN_SECTION, read_type_id)
            bottom_label = gen_joinlabel(BOTTOM_BIN_SECTION, read_type_id)
            q_select += ", ARRAY[%s(%s.avg_value, %s.avg_value, %s.min, %s.min) " % \
                        (d[0], utlabel, ltlabel, top_label, bottom_label) + \
                        ", %s(%s.avg_value, %s.avg_value, %s.avg_value, %s.avg_value) " % \
                        (d[0], utlabel, ltlabel, top_label, bottom_label) + \
                        ", %s(%s.avg_value, %s.avg_value, %s.max, %s.max)] " % \
                        (d[0], utlabel, ltlabel, top_label, bottom_label)

            append_join(joins, j_from, j_id, bin_id, TOP_BIN_SECTION, read_type_id)
            append_join(joins, j_from, j_id, bin_id, BOTTOM_BIN_SECTION, read_type_id)

            append_join(joins, j_from, j_id, bin_id, TOP_BIN_SECTION, TEMP_READ_TYPE_ID)
            append_join(joins, j_from, j_id, bin_id, BOTTOM_BIN_SECTION, TEMP_READ_TYPE_ID)
        #Maxtemp is handled below
    sql_query = "%s FROM %s %s WHERE %s ORDER by r.datetime" % (q_select, q_from, ''.join(joins.values()), q_where)
    logging.debug("graph_data query = " + sql_query)
    logging.debug("graph_data q_WHERE_ARGS = " + str(q_where_args))
    #print query

    data = []
    conn = util.getConn()
    cur = conn.cursor()
    cur.execute(sql_query, q_where_args)
    for row in cur:
        data.append(list(row))

    # Insert maxtemps if exist
    try:
        max_temp_idx = zip(*query)[0].index('maxtemp')
        if len(data) > 0:
            times = zip(*data)[0]
            max_temps = map(lambda t: [None, t, None], EMC.computeMaxTempsMulti(times, bin_id))
            for idx in range(len(data)):
                data[idx].insert(max_temp_idx + 1, max_temps[idx])
        else:
            times = generate_max_temp_times(begin_datetime, end_datetime, sample_period, conn=conn)
            max_temps = map(lambda t: [None, t, None], EMC.computeMaxTempsMulti(times, bin_id))
            data = []
            for idx in range(len(times)):
                data.append([times[idx], max_temps[idx]])
    except ValueError:
        #No maxtemp
        pass

    #TODO: Insert in maxtemp
    return data


def generate_max_temp_times(begin_datetime, end_datetime, sample_period, conn=None):
    if not conn:
        conn = util.getConn()
    #TODO: Make a python function that does similar.
    if sample_period <= 0:
        sample_period = 1
    cur = conn.cursor()
    cur.execute("SELECT compute_sample_date(%s, %s)", (begin_datetime, sample_period))
    start = cur.fetchone()[0]
    times = []
    last = start
    while last < end_datetime:
        times.append(last)
        last = last + timedelta(minutes=sample_period)
    return times


# Local Variables:
# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
