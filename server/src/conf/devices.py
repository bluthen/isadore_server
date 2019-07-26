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
''' conf/devices* '''

from bottle import route  #@UnresolvedImport
from bottle import request, abort, HTTPResponse
from authentication import authorized
import datetime
import util
from cache import confCache

@route('/resources/conf/devices', method=["GET"])
@authorized('User')
@confCache()
def devices():
    bin_id = request.params.get('bin_id')
    bin_section_id = request.params.get('bin_section_id')
    year = request.params.get('year')
    
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
    return {'xlink': ['/resources/conf/devices/' + str(id) for id in ids]}


@route('/resources/conf/devices-fast', method=["GET"])
@authorized('User')
@confCache()
def devices_fast():
    bin_id = request.params.get('bin_id')
    bin_section_id = request.params.get('bin_section_id')
    year = request.params.get('year')

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

    return {'devices': devicesl}


@route('/resources/conf/devices', method=["POST"])
@authorized('Config User')
def devices_new():
    parameters = {}
    try:
        parameters["device_type_id"] = int(request.params.get("device_type_id", None))
        parameters["name"] = request.params.get("name", None)
        parameters["info"] = request.params.get("info", None)
        parameters["address"] = int(request.params.get("address", None))
        parameters["port"] = int(request.params.get("port", None))
        parameters["enabled_p"] = request.params.get("enabled_p", None).lower() == 'true'
        parameters["bin_id"] = int(request.params.get("bin_id", None))
        parameters["bin_section_id"] = int(request.params.get("bin_section_id", None))
        parameters["mid_name"] = request.params.get("mid_name", None)
        parameters["year"] = int(request.params.get("year", None))
    except:
        abort(400, 'Bad parameters')
        
    id = util.insertRow("device", parameters)
    
    return {'xlink': ['/resources/conf/devices/' + str(id)]}


@route('/resources/conf/devices/:id#[0-9]+#', method=["GET"])
@authorized('User')
@confCache()
def devices_get(id):
    row = util.getRowFromTableById("device", int(id))
    if not row:
        abort(404, "Device not found.")
    return row


@route('/resources/conf/devices/:id#[0-9]+#', method=["PUT"])
@authorized('Config User')
def devices_update(id):
    row = util.getRowFromTableById("device", int(id))
    if not row:
        abort(404, "Device not found.")
    parameters = {}
    try:
        parameters["device_type_id"] = int(request.params.get("device_type_id", None))
        parameters["name"] = request.params.get("name", None)
        parameters["info"] = request.params.get("info", None)
        parameters["address"] = int(request.params.get("address", None))
        parameters["port"] = int(request.params.get("port", None))
        parameters["enabled_p"] = request.params.get("enabled_p", None).lower() == 'true'
        parameters["bin_id"] = int(request.params.get("bin_id", None))
        parameters["bin_section_id"] = int(request.params.get("bin_section_id", None))
        parameters["year"] = int(request.params.get("year", None))
        parameters["mid_name"] = request.params.get("mid_name", None)
    except:
        abort(400, 'Bad parameters')

    util.updateRowById("device", int(id), parameters)
    return HTTPResponse(output="Device updated.", status=204)


@route('/resources/conf/devices/:id#[0-9]+#', method=["DELETE"])
@authorized('Config User')
def devices_delete(id):
    row = util.getRowFromTableById("device", int(id))
    if not row:
        abort(404, "Device not found.")
    util.deleteRowFromTableById("device", int(id))
    return HTTPResponse(output="Device deleted.", status=204)


@route('/resources/conf/devices_clone', method=["POST"])
@authorized('Config User')
def devices_clone():
    # TODO: Clone sensor mirrors even though not part of device anymore?
    from_year = request.params.get('from_year')
    to_year = request.params.get('to_year')
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
    return HTTPResponse(output='devices configuration cloned.', status=204)


# Local Variables:
# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
