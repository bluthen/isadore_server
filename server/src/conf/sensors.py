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
''' conf/sensors* '''


from bottle import route  #@UnresolvedImport
from bottle import request, abort, HTTPResponse
import psycopg2.extras as dbapi2extras
from authentication import authorized
import util
import string
from cache import confCache

@route("/resources/conf/sensors", method=["GET"])
@authorized("User")
@confCache()
def sensors():
    device_id = request.params.get("device_id", None)
    if not device_id:
        abort(400, "Bad parameter.")
    ids = util.getIdsFromTable("sensor", extraWhere="device_id = %s ", extraArgs=(device_id,))
    return {"xlink": ["/resources/conf/sensors/" + str(id) for id in ids]}


@route("/resources/conf/sensors", method=["POST"])
@authorized("Config User")
def sensors_new():
    parameters = {}
    #TODO: Should non-super users set conver_py? They might break it, but deleting sensor could be just as bad.
    try:
        parameters["device_id"] = int(request.params.get("device_id", None))
        parameters["extra_info"] = request.params.get("extra_info", None)
        if string.strip(parameters["extra_info"]) == '':
            parameters["extra_info"]="null"
        parameters["sensor_type_id"] = int(request.params.get("sensor_type_id", None))
        parameters["convert_py"] = request.params.get("convert_py", None)
        parameters["bias"] = float(request.params.get("bias", None))
        parameters["enabled_p"] = request.params.get("enabled_p", None).lower() == "true"
    except:
        abort(400, "Bad parameters")
        
    #try:
    #    util.safeEval(parameters["convert_py"], 1.0)
    #except:
    #    abort(400, "Bad parameter: Invalid convert py string.")

    id = util.insertRow("sensor", parameters)
    
    return {"xlink": ["/resources/conf/sensors/" + str(id)]}


@route("/resources/conf/sensors-fast", method=["GET"])
@authorized("User")
@confCache()
def sensors_get_fast():
    device_id = request.params.get("device_id", None)
    if not device_id:
        abort(400, "Bad parameter.")
    try:
        device_id = int(device_id)
    except:
        abort(400, "Bad parameter.")
    rows = util.getRowsFromTable("sensor", extraWhere="device_id = %s", extraArgs=(device_id,))
    return {"sensors": rows}


@route("/resources/conf/sensors-fast", method=["DELETE"])
@authorized("Config User")
def sensors_delete_fast():
    device_id = request.params.get("device_id", None)
    if not device_id:
        abort(400, "Bad parameter.")
    try:
        device_id = int(device_id)
    except:
        abort(400, "Bad parameter.")
    conn = util.getConn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sensor WHERE device_id = %s", (device_id,))
    conn.commit()
    cur.close()
    conn.close()
    return HTTPResponse(output="sensors deleted", status=204)


@route("/resources/conf/sensors/:id#[0-9]+#", method=["GET"])
@authorized("User")
@confCache()
def sensors_get(id):
    row = util.getRowFromTableById("sensor", int(id))
    if not row:
        abort(404, "Sensor not found.")
    row["bias"] = float(row["bias"])
    return row


@route("/resources/conf/sensors/:id#[0-9]+#", method=["PUT"])
@authorized("Config User")
def sensors_update(id):
    row = util.getRowFromTableById("sensor", int(id))
    if not row:
        abort(404, "Sensor not found.")
    parameters = {}
    try:
        parameters["device_id"] = int(request.params.get("device_id", None))
        parameters["sensor_type_id"] = int(request.params.get("sensor_type_id", None))
        parameters["convert_py"] = request.params.get("convert_py", None)
        parameters["extra_info"] = request.params.get("extra_info", None)
        if string.strip(parameters["extra_info"]) == '':
            parameters["extra_info"]="null"
        parameters["bias"] = float(request.params.get("bias", None))
        parameters["enabled_p"] = request.params.get("enabled_p", None).lower() == "true"
    except:
        abort(400, "Bad parameters")

    util.updateRowById("sensor", int(id), parameters)
    return HTTPResponse(output="Sensor updated.", status=204)


@route("/resources/conf/sensors/:id#[0-9]+#", method=["DELETE"])
@authorized("Config User")
def sensors_delete(id):
    row = util.getRowFromTableById("sensor", int(id))
    if not row:
        abort(404, "Sensor not found.")
    util.deleteRowFromTableById("sensor", int(id))
    return HTTPResponse(output="Sensor deleted", status=204)


@route("/resources/conf/sensor_mirrors", method=["POST"])
@authorized("Config User")
def sensor_mirrors_new():
    parameters = {}
    try:
        parameters["sensor_id"] = int(request.params.get("sensor_id", None))
        parameters["bin_id"] = int(request.params.get("bin_id", None))
        parameters["bin_section_id"] = int(request.params.get("bin_section_id", None))
    except:
        abort(400, "Bad parameters")
    id = util.insertRow("sensor_mirror", parameters)
    return {"xlink": ["/resources/conf/sensor_mirrors/"+str(id)]}


@route("/resources/conf/sensor_mirrors/:id#[0-9]+#", method=["GET"])
@authorized("User")
@confCache()
def sensor_mirrors_get(id):
    row = util.getRowFromTableById("sensor_mirror", id)
    if not row:
        abort(404, "Sensor Mirror not found.")
    return row


@route("/resources/conf/sensor_mirrors/:id#[0-9]+#", method=["DELETE"])
@authorized("Config User")
def sensor_mirrors_delete(id):
    row = util.getRowFromTableById("sensor_mirror", int(id))
    if not row:
        abort(404, "Sensor mirror not found.")
    util.deleteRowFromTableById("sensor_mirror", int(id))
    return HTTPResponse(output="Sensor mirror deleted", status=204)


@route("/resources/conf/sensor_mirrors-fast", method=["GET"])
@authorized("User")
@confCache()
def sensor_mirrors_get_fast():
    bin_id, bin_section_id, year = (None, None, None)
    try:
        bin_id = request.params.get("bin_id", None)
        bin_section_id = request.params.get("bin_section_id", None)
        year = request.params.get("year", None)
        if bin_id:
            bin_id = int(bin_id)
        if bin_section_id:
            bin_section_id = int(bin_section_id)
        if year:
            year = int(year)
    except:
        abort(400, "Bad parameter")

    sqlargs = []
    sql = """SELECT sm.id, sm.bin_id, sm.bin_section_id, d.id as device_id, sm.sensor_id FROM
    sensor_mirror sm, sensor s, device d WHERE s.id = sm.sensor_id AND d.id = s.device_id"""

    if year:
        sql += " AND d.year = %s "
        sqlargs.append(year)
    if bin_id:
        sql += " AND sm.bin_id = %s "
        sqlargs.append(bin_id)
    if bin_section_id:
        sql += " AND sm.bin_section_id = %s "
        sqlargs.append(bin_section_id)
    conn = util.getConn()
    cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
    cur.execute(sql, sqlargs)

    results = []
    for row in cur:
        resultRow = {}
        for key in row.keys():
            resultRow[key] = row[key]
        results.append(resultRow)
    cur.close()
    conn.close()

    return {"sensor_mirrors": results}


# Local Variables:
# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
