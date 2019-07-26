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
''' conf/general'''

from bottle import route  # @UnresolvedImport
from bottle import request, abort, HTTPResponse, response
from authentication import authorized
from cache import confCache
import util


@route('/resources/conf/general', method=["GET"])
@authorized('User')
@confCache()
def general():
    # TODO: Allow MID
    row = util.getRowFromTableById('general_config', 1)
    del row['id']
    del row['mid_pass']
    return row


@route('/resources/conf/general', method=["PUT"])
@authorized('Super User')
def general_update():
    parameters = {}
    try:
        parameters['configs'] = request.params.get('configs', None)
        if not parameters['configs']:
            abort(400, 'Bad arguments')
    except:
        abort(400, 'Bad arguments')


    util.updateRowById('general_config', 1, parameters)

    return HTTPResponse(output="General Config updated.", status=204)  # Local Variables:

# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
