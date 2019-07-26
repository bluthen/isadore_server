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
''' conf/sensor_types '''

from bottle import route #@UnresolvedImport
from bottle import abort, request
from authentication import authorized
import util
from cache import confCache


@route('/resources/conf/sensor_types', method=["GET"])
@authorized('User')
@confCache()
def sensor_types():
    device_type_id = request.params.get('device_type_id', None)
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
        return {'xlink': ['/resources/conf/sensor_types/' + str(row["sensor_type_id"]) for row in rows]}
    else:
        ids = util.getIdsFromTable("sensor_type")
        return {'xlink': ['/resources/conf/sensor_types/' + str(id) for id in ids]}


@route('/resources/conf/sensor_types/:id#[0-9]+#', method=["GET"])
@authorized('User')
@confCache()
def sensor_types_get(id):
    row = util.getRowFromTableById("sensor_type", int(id))
    if not row:
        abort(404, "Sensor Type not found.")
    return row


@route('/resources/conf/sensor_types-fast', method=["GET"])
@authorized('User')
@confCache()
def fast_sensor_types():
    rows = util.getRowsFromTable('sensor_type')
    return {'sensor_types': rows}


@route('/resources/conf/read_types-fast', method=["GET"])
@authorized('User')
@confCache()
def fast_read_types():
    rows = util.getRowsFromTable('read_type')
    return {'read_types': rows}


# Local Variables:
# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
