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

# conf/subsamples*

from flask import jsonify
from isadoreapp import app
from isadoreapp.authentication import authorized
import isadoreapp.util as util


@app.route('/resources/conf/subsamples', methods=["GET"])
@authorized('User')
def subsamples():
    result = []
    conn = util.getConn()
    cur = conn.cursor()
    cur.execute("SELECT subsample FROM default_subsample ORDER BY subsample")
    for row in cur:
        result.append(row[0])
    conn.close()
    return jsonify({'subsamples': result})
