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

# conf/devices*

from isadoreapp import app
from flask import request, abort, Response, jsonify
from isadoreapp.authentication import authorized
import datetime
import isadoreapp.util as util
from isadoreapp.cache import confCache


@app.route('/resources/conf/devices', methods=["GET"])
@authorized('User')
@confCache()
def devices():
    bin_id = request.values.get('bin_id')
    bin_section_id = request.values.get('bin_section_id')
    year = request.values.get('year')
    
    # TODO: What if we want all devices regardless of year, we have no method to get a
    # TODO: list of valid years.
    if not year:
        abort(400, 'Bad parameters')
    
    extra_where = "year = %s "
    extra_args = (year,)
    if bin_id:
        try:
            bin_id = int(bin_id)
            extra_where += " AND bin_id = %s "
            extra_args += (bin_id,)
        except ValueError:
            abort(400, 'Invalid bin_id')
    if bin_section_id:
        try:
            bin_section_id = int(bin_section_id)
            extra_where += " AND bin_section_id = %s "
            extra_args += (bin_section_id,)
        except ValueError:
            abort(400, 'Invalid bin_section_id')
            
    ids = util.getIdsFromTable('device', extra_where, extra_args)
    return jsonify({'xlink': ['/resources/conf/devices/' + str(device_id) for device_id in ids]})


@app.route('/resources/conf/devices-fast', methods=["GET"])
@authorized('User')
@confCache()
def devices_fast():
    bin_id = request.values.get('bin_id')
    bin_section_id = request.values.get('bin_section_id')
    year = request.values.get('year')

    if not year:
        year = datetime.datetime.now().year
    
    extra_where = "year = %s "
    extra_args = (year,)
    if bin_id:
        try:
            bin_id = int(bin_id)
            extra_where += " AND bin_id = %s "
            extra_args += (bin_id,)
        except ValueError:
            abort(400, 'Invalid bin_id')
    if bin_section_id:
        try:
            bin_section_id = int(bin_section_id)
            extra_where += " AND bin_section_id = %s "
            extra_args += (bin_section_id,)
        except ValueError:
            abort(400, 'Invalid bin_section_id')
            
    conn = util.getConn()
    devicesl = util.getRowsFromTable('device', extraWhere=extra_where, extraArgs=extra_args, conn=conn)
    for device in devicesl:
        sensors = util.getRowsFromTable('sensor', extraWhere='device_id = %s ', extraArgs=(device['id'],), conn=conn)
        device['sensors'] = sensors

    return jsonify({'devices': devicesl})


@app.route('/resources/conf/devices', methods=["POST"])
@authorized('Config User')
def devices_new():
    parameters = {}
    try:
        parameters["device_type_id"] = int(request.values.get("device_type_id", None))
        parameters["name"] = request.values.get("name", None)
        parameters["info"] = request.values.get("info", None)
        parameters["address"] = int(request.values.get("address", None))
        parameters["port"] = int(request.values.get("port", None))
        parameters["enabled_p"] = request.values.get("enabled_p", None).lower() == 'true'
        parameters["bin_id"] = int(request.values.get("bin_id", None))
        parameters["bin_section_id"] = int(request.values.get("bin_section_id", None))
        parameters["mid_name"] = request.values.get("mid_name", None)
        parameters["year"] = int(request.values.get("year", None))
    except ValueError:
        abort(400, 'Bad parameters')
        
    device_id = util.insertRow("device", parameters)
    
    return jsonify({'xlink': ['/resources/conf/devices/' + str(device_id)]})


@app.route('/resources/conf/devices/<int:device_id>', methods=["GET"])
@authorized('User')
@confCache()
def devices_get(device_id):
    row = util.getRowFromTableById("device", int(device_id))
    if not row:
        abort(404, "Device not found.")
    return jsonify(row)


@app.route('/resources/conf/devices/<int:device_id>', methods=["PUT"])
@authorized('Config User')
def devices_update(device_id):
    row = util.getRowFromTableById("device", int(device_id))
    if not row:
        abort(404, "Device not found.")
    parameters = {}
    try:
        parameters["device_type_id"] = int(request.values.get("device_type_id", None))
        parameters["name"] = request.values.get("name", None)
        parameters["info"] = request.values.get("info", None)
        parameters["address"] = int(request.values.get("address", None))
        parameters["port"] = int(request.values.get("port", None))
        parameters["enabled_p"] = request.values.get("enabled_p", None).lower() == 'true'
        parameters["bin_id"] = int(request.values.get("bin_id", None))
        parameters["bin_section_id"] = int(request.values.get("bin_section_id", None))
        parameters["year"] = int(request.values.get("year", None))
        parameters["mid_name"] = request.values.get("mid_name", None)
    except ValueError:
        abort(400, 'Bad parameters')

    util.updateRowById("device", int(device_id), parameters)
    return Response(response="Device updated.", status=204)


@app.route('/resources/conf/devices/<int:device_id>', methods=["DELETE"])
@authorized('Config User')
def devices_delete(device_id):
    row = util.getRowFromTableById("device", int(device_id))
    if not row:
        abort(404, "Device not found.")
    util.deleteRowFromTableById("device", int(device_id))
    return Response(response="Device deleted.", status=204)


@app.route('/resources/conf/devices_clone', methods=["POST"])
@authorized('Config User')
def devices_clone():
    # TODO: Clone sensor mirrors even though not part of device anymore?
    from_year = request.values.get('from_year')
    to_year = request.values.get('to_year')
    if not from_year or not to_year:
        abort(400, 'Missing parameters')
    try:
        from_year = int(from_year)
        to_year = int(to_year)
    except ValueError:
        abort(400, 'Bad parameters')
    
    conn = util.getConn()
    cursor = conn.cursor()
    devicesl = util.getRowsFromTable("device", extraWhere='year=%s', extraArgs=(from_year,), conn=conn)
    if len(devicesl) == 0:
        abort(400, 'Bad parameters')
    
    cursor.execute('DELETE FROM device WHERE year=%s', (to_year,))
    for device in devicesl:
        nd = device.copy()
        del(nd['id'])
        nd['year'] = to_year
        nd['id'] = util.insertRow('device', nd, cursor)
        # Sensors
        sensors = util.getRowsFromTable('sensor', extraWhere='device_id=%s', extraArgs=(device['id'],), conn=conn)
        for sensor in sensors:
            ns = sensor.copy()
            del(ns['id'])
            ns['device_id'] = nd['id']
            ns['id'] = util.insertRow('sensor', ns, cursor)
    conn.commit()
    cursor.close()
    conn.close()
    return Response(response='devices configuration cloned.', status=204)
