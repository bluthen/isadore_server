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
from bottle import route #@UnresolvedImport
from bottle import request, abort, HTTPResponse
import psycopg2.extras as dbapi2extras
from authentication import authorized, midauthorized, alarmsauthorized
import datetime
import util
import threading
import json
import logging

sensor_data_insert_lock = threading.RLock()


# For monitoring # error codes
# Don't require authorization for xymon
@route('/resources/data/sensor/latesterrorcodecount', method=["GET"])
def sensor_last_error_code_count():
    sql = "SELECT count(error_code) FROM sensor_data WHERE error_code IS NOT NULL and datetime > now() - interval '10 minutes'"
    conn = util.getConn()
    cur = conn.cursor()
    cur.execute(sql)
    row = cur.fetchone()
    count = 0
    error_info = []
    if row:
        count = row[0]
        sql = """SELECT distinct ON (bin_name, bin_section_name, sensor_type_name, port, address) bin.name as bin_name,
            bin_section.name as bin_section_name,
            device.name as device_name,
            sensor_type.name as sensor_type_name,
            device.port,
            device.address
            FROM bin, bin_section, sensor, device, sensor_type, sensor_data
            WHERE sensor_data.error_code IS NOT NULL and sensor_data.datetime > now() - interval '10 minutes' and
            sensor.id = sensor_data.sensor_id and
            device.id=sensor.device_id and
            sensor_type.id=sensor.sensor_type_id and
            bin.id=device.bin_id and bin_section.id=device.bin_section_id"""
        cur.execute(sql)
        for row in cur:
            error_info.append({"bin_name": row[0],
                               "bin_section_name": row[1],
                               "device_name": row[2],
                               "sensor_type_name": row[3],
                               "port": row[4],
                               "address": row[5]})
    return util.responseJSON({"error_code_count": count, "info": error_info})


# Don't require authorization for xymon
@route('/resources/data/readings/lasttimedelta', method=["GET"])
def readings_last_time_delta():
    sample_period = request.params.get("sample_period")
    if not sample_period:
        sample_period = 5
    conn = util.getConn()
    cur = conn.cursor()
    cur.execute('SELECT extract(epoch from (now()-datetime))/60 from reading_subsample WHERE sample_period = %s ORDER by datetime desc limit 1', (sample_period,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        abort(404, "Last reading not found. No readings in the database?")
    minutes = row[0]

    latest = r_diag_sensor_data_latest(conn)
    error_info = []
    now = util.getDateFromParam('now')
    for row in latest:
        if (now - row['datetime']).total_seconds() > 300:
            error_info.append({"bin_name": row['bin_name'],
                               "bin_section_name": row['bin_section_name'],
                               "device_name": row['device_name'],
                               "sensor_type_name": row['sensor_type_name'],
                               "port": row['port'],
                               "address": row['address'],
                               "delta": (now - row['datetime']).total_seconds()})
    return util.responseJSON({'td': minutes, "info": error_info})
    

@route('/resources/data/readings/last', method=["GET"])
@alarmsauthorized('User')
def readings_last():
    sample_period = request.params.get("sample_period")
    if not sample_period:
        sample_period = 5
    # connect to DB
    conn = util.getConn()
    cur = conn.cursor()
    # perform SQL query
    cur.execute("SELECT id, datetime from reading_subsample WHERE sample_period = %s ORDER BY datetime desc limit 2", (sample_period,))
    # check if query returned anything
    rows = []
    for row in cur:
        rows.append(row)
    if len(rows) == 0:
        cur.close()
        conn.close()
        abort(404, "Last reading not found.  No readings in the database?")
    row = rows[0]
    dt = row[1]
    grow = util.getRowFromTableById('general_config', 1)
    countdown = (dt + datetime.timedelta(seconds=grow['interval']) - datetime.datetime.now(dt.tzinfo) + datetime.timedelta(seconds=30)).total_seconds()
    countdown2 = 9999999
    if len(rows) == 2:
        countdown2 = 1.5*(rows[0][1] - rows[1][1]).total_seconds() - (datetime.datetime.now(dt.tzinfo) - rows[0][1]).total_seconds()
    if (rows[0][1] - rows[1][1]) < datetime.timedelta(seconds=3*grow['interval']):
        countdown = countdown2
    # if countdown2 < countdown:
    #    countdown = countdown2
    # return the id URL
    reading_id = row[0]
    d = row[1]
    id2 = None
    if len(rows) == 2:
        id2 = rows[1][0]
    cur.close()
    conn.close()
    xlinks = ['/resources/data/readings/%d' % (reading_id,)]
    if id2:
        xlinks.append('/resources/data/readings/%d' % (id2,))
    return util.responseJSON({'xlink': xlinks,
                              'datetime': d,
                              'countdown': countdown})


@route('/resources/data/readings/:id#[0-9]+#', method=["GET"])
@alarmsauthorized('User')
def reading_get_data(id):

    # get parameter values
    bin_id = request.params.get("bin_id")
    bin_section_id = request.params.get("bin_section_id")
    read_type_id = request.params.get("read_type_id")
    
    extra_where = " reading_subsample_id = %s"
    extra_args = (id,)
    
    if bin_id:
        try:
            extra_where += " AND bin_id = %s"
            extra_args += (bin_id,)
        except ValueError:
            abort(400, 'Invalid bin_id.')
    if bin_section_id:
        try:
            extra_where += " AND bin_section_id = %s "
            extra_args += (bin_section_id,)
        except ValueError:
            abort(400, 'Invalid bin_section_id')
    if read_type_id:
        try:
            extra_where += " AND read_type_id = %s "
            extra_args += (read_type_id,)
        except ValueError:
            abort(400, 'Invalid sensor_type_id')

    # find read data
    reading_data = util.getRowsFromTable('reading_data_subsample', columns='*',
                                         extraWhere=extra_where, extraArgs=extra_args)
    if not reading_data:
        abort(404, 'reading data not found')

    # return the newly created alarm's id url
    return {"results": reading_data}


@route('/resources/data/readings/latest', method=['GET'])
@authorized('User')
def readings_data_latest(conn=None):
    return r_readings_data_latest(conn)


def r_readings_data_latest(conn=None):

    # get parameter values
    bin_id = request.params.get("bin_id")
    bin_section_id = request.params.get("bin_section_id")
    read_type_id = request.params.get("read_type_id")

    extra_where = ""
    extra_args = ()

    if bin_id:
        try:
            extra_where += " bin_id = %s"
            extra_args += (bin_id,)
        except ValueError:
            abort(400, 'Invalid bin_id.')
    if bin_section_id:
        try:
            if extra_where:
                extra_where += " AND "
            extra_where += " bin_section_id = %s "
            extra_args += (bin_section_id,)
        except ValueError:
            abort(400, 'Invalid bin_section_id')
    if read_type_id:
        try:
            if extra_where:
                extra_where += " AND "
            extra_where += " read_type_id = %s "
            extra_args += (read_type_id,)
        except ValueError:
            abort(400, 'Invalid sensor_type_id')

    # find read data
    reading_data = util.getRowsFromTable('reading_data_latest', columns='*',
                                         extraWhere=extra_where, extraArgs=extra_args, conn=conn)
    if not reading_data:
        abort(404, 'reading data latest not found')

    # return the newly created alarm's id url
    return util.responseJSON({"results": reading_data})


@route('/resources/data/sensor_data_latest', method=["GET"])
@authorized('User')
def sensor_data_latest():
    sensor_ids = request.params.get("sensor_ids")
    try:
        sensor_ids = sensor_ids.split(',')
        sensor_ids = map(int, sensor_ids)
    except:
        abort(400, 'Invalid sensor_ids')
    extra_where = ""
    extra_args = []
    for i in sensor_ids:
        if extra_where:
            extra_where += " OR "
        extra_where += " sensor_id = %s "
        extra_args.append(i)

    rows = util.getRowsFromTable('sensor_data_latest', extraWhere=extra_where, extraArgs=extra_args)
    return util.responseJSON({"results": rows})


@route('/resources/data/diagnostics_sensor_data_latest_reset', method=["DELETE"])
@authorized('Config User')
def diag_sensor_data_latest_reset():
    conn = util.getConn()
    cur = conn.cursor()
    sql = "SELECT err_out_latest_sensor_data()"
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    return HTTPResponse(output="Sensor Data Latest Reset", status=204)


@route('/resources/data/diagnostics_sensor_data_latest', method=["GET"])
@authorized('User')
def diag_sensor_data_latest():
    return util.responseJSON({"results": r_diag_sensor_data_latest()})


def r_diag_sensor_data_latest(con=None):
    sql = """SELECT
    sdl.value, sdl.raw_data, sdl.error_code, sdl.datetime,
    st.name as sensor_type_name, rt.name as read_type_name, rt.short_name as read_type_short_name, rt.units,
    d.name as device_name, d.info as device_info, dt.name as device_type_name, d.mid_name, d.port, d.address, d.bin_id, d.bin_section_id,
    b.name as bin_name, bs.name as bin_section_name
FROM
    sensor_data_latest sdl, sensor s, device d, bin b, bin_section bs, device_type dt, sensor_type st, read_type rt
WHERE
    sdl.datetime >= date_trunc('year', now()) AND sdl.datetime < date_trunc('year', now())+'1 years'::interval AND
    s.id = sdl.sensor_id AND d.id = s.device_id AND b.id = d.bin_id AND bs.id = d.bin_section_id AND
    dt.id = d.device_type_id AND st.id = s.sensor_type_id AND rt.id = st.read_type_id"""
    close_con = False
    try:
        if not con:
            con = util.getConn()
            close_con = True
        cur = con.cursor(cursor_factory=dbapi2extras.DictCursor)
        cur.execute(sql)
        results = []
        for row in cur:
            result_row = {}
            for key in row.keys():
                result_row[key] = row[key]
            results.append(result_row)
        cur.close()
        if close_con:
            con.close()
        return results
    finally:
        if close_con:
            con.close()


@route('/resources/data/sensor', method=["POST"])
@midauthorized()
def data_new():
    global sensor_data_insert_lock
    # Parameters
    # data = [{'sensor_id': int, 'value': float, 'raw_data': float, 'datetime': str#iso8601, error_code: int}, ...]

    try:
        data = json.loads(request.params.get('data'))
    except:
        logging.exception('Bad parameters, json: %s' % (json.dumps(request.params.get('data'))))
        abort(400, 'Bad parameters.')
    # TODO: Check on any concurrent database issues with trigger, then maybe can remove thread lock.
    conn = None
    cur = None
    try:
        sensor_data_insert_lock.acquire()
        conn = util.getConn()
        cur = conn.cursor()
        idx = 0
        for record in data:
            db_args = {'sensor_id': None, 'value': None, 'raw_data': None, 'datetime': None, 'error_code': None}
            if 'sensor_id' in record:
                db_args['sensor_id'] = record['sensor_id']
            if 'value' in record:
                db_args['value'] = record['value']
            if 'raw_data' in record:
                db_args['raw_data'] = record['raw_data']
            if 'datetime' in record:
                db_args['datetime'] = util.getDateFromParam(record['datetime'])
            if 'error_code' in record:
                db_args['error_code'] = record['error_code']

            # Verify, must have sensor_id, datetime, and at least a value, raw_data, or error_code
            if not db_args['sensor_id']:
                logging.error('Bad parameter: Entry in data array missing sensor_id: idx=%d, record=%s' %
                              (idx, json.dumps(record)))
                abort(400, 'Entry in data array missing sensor_id')
            if not db_args['datetime']:
                logging.error('Bad parameter: Entry in data array missing datetime: idx=%d, record=%s' %
                              (idx, json.dumps(record)))
                abort(400, 'Entry in data array missing datetime')
            if 'value' not in db_args and 'raw_data' not in db_args and 'error_code' not in db_args:
                logging.error('Bad parameter: Entry in data array missing something to store (value, raw_data, ' +
                              'or error_code: idx=%d, record=%s' % (idx, json.dumps(record)))
                abort(400, 'Entry in data array missing something to store (value, raw_data, or error_code')

            util.insertRow('sensor_data', db_args, cur)
            idx += 1
        conn.commit()
        cur.close()
        conn.close()
        cur = None
        conn = None

        # TODO: add a little more info in response
        return HTTPResponse(output="Data added.", status=204)
    finally:
        sensor_data_insert_lock.release()
        if cur:
            cur.close()
        if conn:
            conn.rollback()
            conn.close()

# Local Variables:
# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
