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

# conf/sensor_types

from isadoreapp import app
from flask import abort, request, jsonify
from isadoreapp.authentication import authorized
import isadoreapp.util as util
from isadoreapp.cache import confCache


@app.route('/resources/conf/sensor_types', methods=["GET"])
@authorized('User')
@confCache()
def sensor_types():
    device_type_id = request.values.get('device_type_id', None)
    extra_where = ""
    extra_args = ()
    if device_type_id:
        try:
            device_type_id = int(device_type_id)
            extra_where = "device_type_id=%s"
            extra_args = (device_type_id,)
        except (ValueError, TypeError):
            abort(400, 'Invalid device_type_id')
        rows = util.getRowsFromTable("device_type_to_sensor_type", extraWhere=extra_where, extraArgs=extra_args)
        return jsonify({'xlink': ['/resources/conf/sensor_types/' + str(row["sensor_type_id"]) for row in rows]})
    else:
        ids = util.getIdsFromTable("sensor_type")
        return jsonify({'xlink': ['/resources/conf/sensor_types/' + str(sensor_type_id) for sensor_type_id in ids]})


@app.route('/resources/conf/sensor_types/<int:sensor_type_id>', methods=["GET"])
@authorized('User')
@confCache()
def sensor_types_get(sensor_type_id):
    row = util.getRowFromTableById("sensor_type", int(sensor_type_id))
    if not row:
        abort(404, "Sensor Type not found.")
    return jsonify(row)


@app.route('/resources/conf/sensor_types-fast', methods=["GET"])
@authorized('User')
@confCache()
def fast_sensor_types():
    rows = util.getRowsFromTable('sensor_type')
    return jsonify({'sensor_types': rows})


@app.route('/resources/conf/read_types-fast', methods=["GET"])
@authorized('User')
@confCache()
def fast_read_types():
    rows = util.getRowsFromTable('read_type')
    return jsonify({'read_types': rows})
