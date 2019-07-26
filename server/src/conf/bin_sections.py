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
''' conf/bin_sections '''

from bottle import route #@UnresolvedImport
from bottle import abort
from authentication import authorized
import util
from cache import confCache

@route('/resources/conf/bin_sections', method=["GET"])
@authorized('User')
@confCache()
def bin_sections():
	ids = util.getIdsFromTable('bin_section')
	return {'xlink': ['/resources/conf/bin_sections/' + str(id) for id in ids]}

@route('/resources/conf/bin_sections/:id#[0-9]+#', method=["GET"])
@authorized('User')
@confCache()
def bin_sections_get(id):
	row = util.getRowFromTableById("bin_section", int(id))
	if(not row):
		abort(404, "Bin Section not found.")
	return row


@route('/resources/conf/bin_sections-fast', method=["GET"])
@authorized('User')
@confCache()
def bin_sections_fast():
	rows = util.getRowsFromTable('bin_section')
	return {'bin_sections': rows}


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
