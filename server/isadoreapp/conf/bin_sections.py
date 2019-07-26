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

# conf/bin_sections

from isadoreapp import app
from flask import abort, jsonify
from isadoreapp.authentication import authorized
import isadoreapp.util as util
from isadoreapp.cache import confCache


@app.route('/resources/conf/bin_sections', methods=["GET"])
@authorized('User')
@confCache()
def bin_sections():
    ids = util.getIdsFromTable('bin_section')
    return jsonify({'xlink': ['/resources/conf/bin_sections/' + str(bin_section_id) for bin_section_id in ids]})


@app.route('/resources/conf/bin_sections/<int:bin_section_id>', methods=["GET"])
@authorized('User')
@confCache()
def bin_sections_get(bin_section_id):
    row = util.getRowFromTableById("bin_section", int(bin_section_id))
    if not row:
        abort(404, "Bin Section not found.")
    return jsonify(row)


@app.route('/resources/conf/bin_sections-fast', methods=["GET"])
@authorized('User')
@confCache()
def bin_sections_fast():
    rows = util.getRowsFromTable('bin_section')
    return jsonify({'bin_sections': rows})
