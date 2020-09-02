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

from isadoreapp import app
from flask import abort, jsonify
from isadoreapp.authentication import authorized
import isadoreapp.util as util


@app.route('/resources/alarms/alarm_types', methods=["GET"])
@authorized('User')
def alarm_types_list():
    ids = util.getIdsFromTable("alarm_type")
    return jsonify({'xlink': ['/resources/alarms/alarm_types/' + str(alarm_type_id) for alarm_type_id in ids]})


@app.route('/resources/alarms/alarm_types/<int:alarm_type_id>', methods=["GET"])
@authorized('User')
def alarm_types_get(alarm_type_id):
    row = util.getRowFromTableById("alarm_type", int(alarm_type_id))

    if row:
        return jsonify(row)
    else:
        abort(404, "Alarm type not found")


@app.route('/resources/alarms/alarm_types-fast', methods=["GET"])
@authorized('User')
def fast_alarm_types_list():
    rows = util.getRowsFromTable("alarm_type")
    return jsonify({'alarm_types': rows})