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

# conf/bins

from isadoreapp import app
from flask import abort, jsonify
from isadoreapp.authentication import authorized
import isadoreapp.util as util
from isadoreapp.cache import confCache


@app.route('/resources/conf/bins', methods=["GET"])
@authorized('User')
@confCache()
def bins():
    ids = util.getIdsFromTable('bin')
    return jsonify({'xlink': ['/resources/conf/bins/' + str(bin_id) for bin_id in ids]})


@app.route('/resources/conf/bins/<int:bin_id>', methods=["GET"])
@authorized('User')
@confCache()
def bins_get(bin_id):
    row = util.getRowFromTableById("bin", int(bin_id))
    if not row:
        abort(404, "Bin not found.")
    return jsonify(row)


@app.route('/resources/conf/bins-fast', methods=["GET"])
@authorized('User')
@confCache()
def fast_bins():
    rows = util.getRowsFromTable("bin", orderStatement=" ORDER BY y, x")
    return jsonify({'bins': rows})
