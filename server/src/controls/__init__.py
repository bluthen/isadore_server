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
from bottle import request, abort, HTTPResponse
from authentication import authorized
import util
import datetime


@route('/resources/controls', method=['POST'])
@authorized('Config User')
def controls_set():
    try:
        sensor_id = int(request.params.get('sensor_id', None))
    except:
        abort(400, 'Invalid sensor_id parameter.')
    try:
        value = float(request.params.get('value', None))
    except:
        abort(400, 'Invalid value parameter.')

    sensor = util.getRowFromTableById('sensor', sensor_id, checkEnabled=True)
    if not sensor:
        abort(400, 'Wrong sensor_id')

    sensor_type = util.getRowFromTableById('sensor_type', sensor['sensor_type_id'])
    if not sensor_type['controllable']:
        abort(400, 'Sensor is not controllable')

    # TODO: Check against type
    control_id = util.insertRow('control',
                        {'sensor_id': sensor_id,
                         'sensor_type_id': sensor_type['id'],
                         'value': value})

    return {'xlink': ['/resources/consols/' + str(control_id)]}


@route('/resources/controls/last', method=['GET'])
@authorized('User')
def controls_last():
    sensor_id = request.params.get('sensor_id')
    if not sensor_id:
        abort(400, 'Missing sensor_id')
    sensor = util.getRowFromTableById("sensor", int(sensor_id), checkEnabled=True)
    if not sensor:
        abort(400, 'Invalid sensor_id')
    sensor_type = util.getRowFromTableById('sensor_type', sensor['sensor_type_id'])
    if not sensor_type['controllable']:
        abort(400, 'Sensor is not controllable')

    conn = util.getConn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM control WHERE sensor_id = %s ORDER BY posted_datetime desc limit 1", (sensor_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return {'xlink': []}
    control_id = row[0]
    cur.close()
    conn.close()
    return {'xlink': ['/resources/controls/' + str(control_id)]}


@route('/resources/controls/:control_id#[0-9]+#', method=['GET'])
@authorized('User')
def controls_get(control_id):
    row = util.getRowFromTableById('control', int(control_id))
    if row:
        return util.responseJSON(row)
    else:
        abort(404, 'Control not found.')


@route('/resources/controls/:control_id#[0-9]+#', method=['PUT'])
# @authorized('User')
def controls_fetched(control_id):
    # TODO: need to do any TZ checking with the fetched_datetime?
    # check if sensor is in DB
    if not util.getRowFromTableById("control", control_id):
        abort(404, "Not found.")
    # TODO: check to see if command already marked as fetched
    # parse parameters
    fetched_p = bool(request.params.get("fetched", False))  # did it work?
    if not fetched_p:
        util.updateRowById("control", control_id,
                           {"fetched_note": "MID reported update failure at " + util.datetimeToReadable(
                               datetime.now()) + "."})
        return HTTPResponse(output="Remote control value update failure recorded.", status=204)
    # update row to reflect new value was applied to device
    util.updateRowById("control", control_id,
                       {"fetched_note": "MID reports update success.",
                        "fetched_datetime": datetime.datetime.now()})
    return HTTPResponse(output="Remote control value update success recorded.", status=204)


@route('/resources/controls/last_readings', method=['GET'])
@authorized('User')
def controls_last_readings(conn=None):
    return r_controls_last_readings(conn)


def r_controls_last_readings(conn=None):
    year = datetime.datetime.now().year
    conn_given = False
    if conn:
        conn_given = True
    else:
        conn = util.getConn()
    cur = conn.cursor()
    cur2 = conn.cursor()
    cur.execute("SELECT device.bin_id, device.bin_section_id, device.id as device_id, sensor.id as sensor_id, \
        sensor_type.id as sensor_type_id, sensor_type.read_type_id from sensor, device, sensor_type WHERE device.id=sensor.device_id and \
        device.year=%s and sensor_type.id = sensor.sensor_type_id and sensor_type.controllable=true", (year,))
    ret = []
    for row in cur:
        bin_id = row[0]
        bin_section_id = row[1]
        device_id = row[2]
        sensor_id = row[3]
        sensor_type_id = row[4]
        read_type_id = row[5]
        cur2.execute("SELECT value, datetime FROM sensor_data_latest WHERE sensor_id = %s AND \
                error_code IS NULL ORDER BY datetime desc LIMIT 1", (sensor_id,))
        row2 = cur2.fetchone()
        value = None
        dt = None
        if row2:
            value = row2[0]
            dt = row2[1]
        ret.append({'bin_id': bin_id, 'bin_section_id': bin_section_id, "device_id": device_id,
                    "sensor_id": sensor_id, "value": value, "datetime": dt, "sensor_type_id": sensor_type_id,
                    "read_type_id": read_type_id})
    if not conn_given:
        conn.close()
    return util.responseJSON({'sensor_data': ret})


# Local Variables:
# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
