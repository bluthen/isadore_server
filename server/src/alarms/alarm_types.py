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
from bottle import request, abort
from authentication import authorized
import util

@route('/resources/alarms/alarm_types', method=["GET"])
@authorized('User')
def alarm_types_list():
	format = request.params.get("format", "json")
	ids = util.getIdsFromTable("alarm_type")
	return {'xlink': ['/resources/alarms/alarm_types/' + str(id) for id in ids]}

@route('/resources/alarms/alarm_types/:id#[0-9]+#', method=["GET"])
@authorized('User')
def alarm_types_get(id):
	format = request.params.get("format", "json")
	row = util.getRowFromTableById("alarm_type", int(id))

	if(row):
		return row
	else:
		abort(404, "Alarm type not found")


@route('/resources/alarms/alarm_types-fast', method=["GET"])
@authorized('User')
def fast_alarm_types_list():
	rows = util.getRowsFromTable("alarm_type")
	return {'alarm_types': rows}

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
