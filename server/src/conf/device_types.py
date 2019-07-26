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
'''
conf/device_types
'''


from bottle import route #@UnresolvedImport
from bottle import abort
from authentication import authorized
import util
from cache import confCache

@route('/resources/conf/device_types', method=["GET"])
@authorized('User')
@confCache()
def device_types():
	ids = util.getIdsFromTable('device_type')
	return {'xlink': ['/resources/conf/device_types/' + str(id) for id in ids]}

@route('/resources/conf/device_types/:id#[0-9]+#', method=["GET"])
@authorized('User')
@confCache()
def device_types_get(id):
	row = util.getRowFromTableById("device_type", int(id))
	if(not row):
		abort(404, "Device Type not found.")
	return row


@route('/resources/conf/device_types-fast', method=["GET"])
@authorized('User')
@confCache()
def device_types_fast():
	rows = util.getRowsFromTable("device_type")
	return {'device_types': rows}


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
