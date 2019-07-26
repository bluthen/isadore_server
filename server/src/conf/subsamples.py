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
''' conf/subsamples* '''

from bottle import route #@UnresolvedImport
from bottle import request, abort, HTTPResponse
from authentication import authorized
import util


@route('/resources/conf/subsamples', method=["GET"])
@authorized('User')
def subsamples():
	result = []
	conn = util.getConn()
	cur = conn.cursor()
	cur.execute("SELECT subsample FROM default_subsample ORDER BY subsample")
	for row in cur:
		result.append(row[0])
	conn.close()
	return {'subsamples': result}

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
