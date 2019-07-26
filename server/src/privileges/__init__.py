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
from bottle import abort, request
from authentication import authorized
import util


@route('/resources/privileges', method=["GET"])
@authorized('User')
def privileges_list():
	format = request.params.get("format", "json")
	ids = util.getIdsFromTable("privilege")
	return {'xlink': ['/resources/privileges/' + str(id) for id in ids]}


@route('/resources/privileges/:id#[0-9]+#', method=["GET"])
@authorized('User')
def privileges_get(id):
	row = util.getRowFromTableById('privilege', int(id))
	#print row
	if(row):
		return row
	else:
		abort(404, "Privilege not found.")


@route('/resources/privileges-fast', method=["GET"])
@authorized('User')
def fast_privileges_list():
	rows  = util.getRowsFromTable("privilege")
	return {'privileges': rows}


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
