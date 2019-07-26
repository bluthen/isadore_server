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

# conf/device_types

from isadoreapp import app
from flask import abort, jsonify
from isadoreapp.authentication import authorized
import isadoreapp.util as util
from isadoreapp.cache import confCache


@app.route('/resources/conf/device_types', methods=["GET"])
@authorized('User')
@confCache()
def device_types():
    ids = util.getIdsFromTable('device_type')
    return jsonify({'xlink': ['/resources/conf/device_types/' + str(device_type_id) for device_type_id in ids]})


@app.route('/resources/conf/device_types/<int:device_type_id>', methods=["GET"])
@authorized('User')
@confCache()
def device_types_get(device_type_id):
    row = util.getRowFromTableById("device_type", int(device_type_id))
    if not row:
        abort(404, "Device Type not found.")
    return jsonify(row)


@app.route('/resources/conf/device_types-fast', methods=["GET"])
@authorized('User')
@confCache()
def device_types_fast():
    rows = util.getRowsFromTable("device_type")
    return jsonify({'device_types': rows})
