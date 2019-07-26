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
from bottle import response, request, abort, HTTPResponse
from authentication import authorized, unauthorized
import util

@route('/resources/alarms/alarm_contact_types',method=["GET"])
@authorized('User')
def alarm_contact_types_list():
	format = request.params.get("format","json")
	ids = util.getIdsFromTable("alarm_contact_type")
	return {'xlink': ['/resources/alarms/alarm_contact_types/' + str(id) for id in ids]}

@route('/resources/alarms/alarm_contact_types/:id#[0-9]+#',method=["GET"])
@authorized('User')
def alarm_contact_types_get(id):
	format = request.params.get("format","json")
	row = util.getRowFromTableById("alarm_contact_type",int(id))

	if(row):
		return row
	else:
		abort(404, "Alarm contact type not found")
		
@route('/resources/alarms/alarm_contact_types-fast',method=["GET"])
@authorized('User')
def alarm_contact_types_list_fast():
	rows = util.getRowsFromTable("alarm_contact_type")
	return {'alarm_contact_types': rows}


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
