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

# conf/sensors*


from isadoreapp import app
from flask import request, abort, Response, jsonify
import psycopg2.extras as dbapi2extras
from isadoreapp.authentication import authorized
import isadoreapp.util as util
from isadoreapp.cache import confCache


@app.route("/resources/conf/sensors", methods=["GET"])
@authorized("User")
@confCache()
def sensors():
    device_id = request.values.get("device_id", None)
    if not device_id:
        abort(400, "Bad parameter.")
    ids = util.getIdsFromTable("sensor", extraWhere="device_id = %s ", extraArgs=(device_id,))
    return jsonify({"xlink": ["/resources/conf/sensors/" + str(sensor_id) for sensor_id in ids]})


@app.route("/resources/conf/sensors", methods=["POST"])
@authorized("Config User")
def sensors_new():
    parameters = {}
    # TODO: Should non-super users set convert_py? They might break it, but deleting sensor could be just as bad.
    try:
        parameters["device_id"] = int(request.values.get("device_id", None))
        parameters["extra_info"] = request.values.get("extra_info", None)
        if parameters["extra_info"].strip() == '':
            parameters["extra_info"] = "null"
        parameters["sensor_type_id"] = int(request.values.get("sensor_type_id", None))
        parameters["convert_py"] = request.values.get("convert_py", None)
        parameters["bias"] = float(request.values.get("bias", None))
        parameters["enabled_p"] = request.values.get("enabled_p", None).lower() == "true"
    except ValueError:
        abort(400, "Bad parameters")

    # try:
    #    util.safeEval(parameters["convert_py"], 1.0)
    # except:
    #    abort(400, "Bad parameter: Invalid convert py string.")

    sensor_id = util.insertRow("sensor", parameters)

    return jsonify({"xlink": ["/resources/conf/sensors/" + str(sensor_id)]})


@app.route("/resources/conf/sensors-fast", methods=["GET"])
@authorized("User")
@confCache()
def sensors_get_fast():
    device_id = request.values.get("device_id", None)
    if not device_id:
        abort(400, "Bad parameter.")
    try:
        device_id = int(device_id)
    except ValueError:
        abort(400, "Bad parameter.")
    rows = util.getRowsFromTable("sensor", extraWhere="device_id = %s", extraArgs=(device_id,))
    return jsonify({"sensors": rows})


@app.route("/resources/conf/sensors-fast", methods=["DELETE"])
@authorized("Config User")
def sensors_delete_fast():
    device_id = request.values.get("device_id", None)
    if not device_id:
        abort(400, "Bad parameter.")
    try:
        device_id = int(device_id)
    except ValueError:
        abort(400, "Bad parameter.")
    conn = util.getConn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sensor WHERE device_id = %s", (device_id,))
    conn.commit()
    cur.close()
    conn.close()
    return Response(response="sensors deleted", status=204)


@app.route("/resources/conf/sensors/<int:sensor_id>", methods=["GET"])
@authorized("User")
@confCache()
def sensors_get(sensor_id):
    row = util.getRowFromTableById("sensor", int(sensor_id))
    if not row:
        abort(404, "Sensor not found.")
    row["bias"] = float(row["bias"])
    return jsonify(row)


@app.route("/resources/conf/sensors/<int:sensor_id>", methods=["PUT"])
@authorized("Config User")
def sensors_update(sensor_id):
    row = util.getRowFromTableById("sensor", int(sensor_id))
    if not row:
        abort(404, "Sensor not found.")
    parameters = {}
    try:
        parameters["device_id"] = int(request.values.get("device_id", None))
        parameters["sensor_type_id"] = int(request.values.get("sensor_type_id", None))
        parameters["convert_py"] = request.values.get("convert_py", None)
        parameters["extra_info"] = request.values.get("extra_info", None)
        if parameters["extra_info"].strip() == '':
            parameters["extra_info"] = "null"
        parameters["bias"] = float(request.values.get("bias", None))
        parameters["enabled_p"] = request.values.get("enabled_p", None).lower() == "true"
    except ValueError:
        abort(400, "Bad parameters")

    util.updateRowById("sensor", int(sensor_id), parameters)
    return Response(response="Sensor updated.", status=204)


@app.route("/resources/conf/sensors/<int:sensor_id>", methods=["DELETE"])
@authorized("Config User")
def sensors_delete(sensor_id):
    row = util.getRowFromTableById("sensor", int(sensor_id))
    if not row:
        abort(404, "Sensor not found.")
    util.deleteRowFromTableById("sensor", int(sensor_id))
    return Response(response="Sensor deleted", status=204)


@app.route("/resources/conf/sensor_mirrors", methods=["POST"])
@authorized("Config User")
def sensor_mirrors_new():
    parameters = {}
    try:
        parameters["sensor_id"] = int(request.values.get("sensor_id", None))
        parameters["bin_id"] = int(request.values.get("bin_id", None))
        parameters["bin_section_id"] = int(request.values.get("bin_section_id", None))
    except ValueError:
        abort(400, "Bad parameters")
    sensor_mirror_id = util.insertRow("sensor_mirror", parameters)
    return jsonify({"xlink": ["/resources/conf/sensor_mirrors/" + str(sensor_mirror_id)]})


@app.route("/resources/conf/sensor_mirrors/<int:sensor_mirror_id>", methods=["GET"])
@authorized("User")
@confCache()
def sensor_mirrors_get(sensor_mirror_id):
    row = util.getRowFromTableById("sensor_mirror", sensor_mirror_id)
    if not row:
        abort(404, "Sensor Mirror not found.")
    return jsonify(row)


@app.route("/resources/conf/sensor_mirrors/<int:sensor_mirror_id>", methods=["DELETE"])
@authorized("Config User")
def sensor_mirrors_delete(sensor_mirror_id):
    row = util.getRowFromTableById("sensor_mirror", int(sensor_mirror_id))
    if not row:
        abort(404, "Sensor mirror not found.")
    util.deleteRowFromTableById("sensor_mirror", int(sensor_mirror_id))
    return Response(response="Sensor mirror deleted", status=204)


@app.route("/resources/conf/sensor_mirrors-fast", methods=["GET"])
@authorized("User")
@confCache()
def sensor_mirrors_get_fast():
    bin_id, bin_section_id, year = (None, None, None)
    try:
        bin_id = request.values.get("bin_id", None)
        bin_section_id = request.values.get("bin_section_id", None)
        year = request.values.get("year", None)
        if bin_id:
            bin_id = int(bin_id)
        if bin_section_id:
            bin_section_id = int(bin_section_id)
        if year:
            year = int(year)
    except ValueError:
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
        result_row = {}
        for key in row.keys():
            result_row[key] = row[key]
        results.append(result_row)
    cur.close()
    conn.close()

    return jsonify({"sensor_mirrors": results})
