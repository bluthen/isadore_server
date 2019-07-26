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

from isadoreapp import app
from flask import request, abort, Response, jsonify
from isadoreapp.authentication import authorized
import isadoreapp.util as util


@app.route('/resources/luts/mc_maxtemp_default', methods=["PUT"])
@authorized('Config User')
def mc_maxtemp_default():
    try:
        lut_id = request.values.get('mc_maxtemp_lut_id')
        if not lut_id:
            return abort(400, 'Bad arguments')
        lut_id = int(lut_id)
    except ValueError:
        return abort(400, 'Bad arguments')

    conn = util.getConn()
    row = util.getRowFromTableById("mc_maxtemp_lut", lut_id, conn=conn)
    if not row:
        return abort(400, 'Bad arguments')
    curr = conn.cursor()
    curr.execute("UPDATE general_config SET default_mc_maxtemp_lut_id=%s", (lut_id,))
    conn.commit()
    curr.close()
    conn.close()
    return Response(response='Default Set', status=204)


@app.route('/resources/luts/mc_maxtemp-fast', methods=["GET"])
@authorized('User')
def luts_mc_maxtemp_fast():
    conn = util.getConn()
    luts = util.getRowsFromTable("mc_maxtemp_lut", conn=conn)
    for lut in luts:
        values = util.getRowsFromTable("mc_maxtemp_lut_value", extraWhere="mc_maxtemp_lut_id=%s",
                                       extraArgs=(lut['id'],), orderStatement=" ORDER BY mc ", conn=conn)
        lut["values"] = values
    return jsonify({'luts': luts})


# TODO: nonfast get

@app.route('/resources/luts/mc_maxtemp/<int:mc_maxtemp_lut_id>', methods=["GET"])
@authorized('User')
def luts_mc_maxtemp_getsingle(mc_maxtemp_lut_id):
    conn = util.getConn()
    lut = util.getRowFromTableById("mc_maxtemp_lut", mc_maxtemp_lut_id, conn=conn)
    values = util.getRowsFromTable("mc_maxtemp_lut_value", extraWhere="mc_maxtemp_lut_id=%s", extraArgs=(lut['id'],),
                                   orderStatement=" ORDER BY mc ", conn=conn)
    lut["values"] = values
    return jsonify(lut)


@app.route('/resources/luts/mc_maxtemp', methods=["POST"])
@authorized('Config User')
def luts_mc_maxtemp_post():
    name, hours_per_mc, mcs, maxtemps = luts_mc_maxtemp_args()
    conn = util.getConn()
    cur = conn.cursor()
    new_id = util.insertRow("mc_maxtemp_lut", {'name': name, 'hours_per_mc': hours_per_mc}, cur)
    for idx in range(0, len(mcs)):
        util.insertRow("mc_maxtemp_lut_value", {'mc': mcs[idx], 'maxtemp': maxtemps[idx], 'mc_maxtemp_lut_id': new_id},
                       cur)

    general = util.getRowFromTableById("general_config", 1, conn=conn)
    if not general["default_mc_maxtemp_lut_id"]:
        cur.execute('UPDATE general_config SET default_mc_maxtemp_lut_id=%s', (new_id,))

    conn.commit()
    cur.close()
    conn.close()
    return {'xlink': ['/resources/luts/mc_maxtemp/' + str(new_id)]}


def luts_mc_maxtemp_args():
    name = request.values.get('name', None)
    hours_per_mc = request.values.get('hours_per_mc', None)
    mcs = request.values.get('mcs', None)
    maxtemps = request.values.get('maxtemps', None)

    if not mcs:
        mcs = []
    else:
        mcs = mcs.split(',')
    if not maxtemps:
        maxtemps = []
    else:
        maxtemps = maxtemps.split(',')

    if name is None or hours_per_mc is None:
        abort(400, 'Missing parameters')

    try:
        hours_per_mc = float(hours_per_mc)
    except ValueError:
        abort(400, 'Invalid hours_per_mc')

    if len(mcs) != len(maxtemps):
        abort(400, 'mcs and maxtemps do not match.')

    try:
        for idx in range(0, len(mcs)):
            mcs[idx] = float(mcs[idx])
            maxtemps[idx] = float(maxtemps[idx])
    except ValueError:
        abort(400, 'Invalid mcs or maxtemps')

    return name, hours_per_mc, mcs, maxtemps


@app.route('/resources/luts/mc_maxtemp/<int:mc_maxtemp_lut_id>', methods=['PUT'])
@authorized('Config User')
def luts_mc_maxtemp_put(mc_maxtemp_lut_id):
    name, hours_per_mc, mcs, maxtemps = luts_mc_maxtemp_args()
    row = util.getRowFromTableById('mc_maxtemp_lut', mc_maxtemp_lut_id)
    if not row:
        abort(404, 'LUT not found.')

    conn = util.getConn()
    cur = conn.cursor()
    util.updateRowById("mc_maxtemp_lut", mc_maxtemp_lut_id, {'name': name, 'hours_per_mc': hours_per_mc}, cur)
    cur.execute('DELETE FROM mc_maxtemp_lut_value WHERE mc_maxtemp_lut_id=%s', (mc_maxtemp_lut_id,))
    for idx in range(0, len(mcs)):
        util.insertRow("mc_maxtemp_lut_value",
                       {'mc': mcs[idx], 'maxtemp': maxtemps[idx], 'mc_maxtemp_lut_id': mc_maxtemp_lut_id}, cur)
    conn.commit()
    cur.close()
    conn.close()
    return Response(response='LUT Updated', status=204)


@app.route('/resources/luts/mc_maxtemp/<int:mc_maxtemp_lut_id>', methods=['DELETE'])
@authorized('Config User')
def luts_mc_maxtemp_delete(mc_maxtemp_lut_id):
    conn = util.getConn()
    row = util.getRowFromTableById('mc_maxtemp_lut', mc_maxtemp_lut_id, conn=conn)
    if not row:
        abort(404, 'LUT not found.')

    cur = conn.cursor()

    util.deleteRowFromTableById("mc_maxtemp_lut", mc_maxtemp_lut_id, cursor=cur)

    general = util.getRowFromTableById("general_config", 1, conn=conn)
    if not general["default_mc_maxtemp_lut_id"]:
        cur.execute(
            'UPDATE general_config SET default_mc_maxtemp_lut_id=(SELECT id FROM mc_maxtemp_lut ORDER BY id LIMIT 1)')
    conn.commit()
    cur.close()
    conn.close()
    return Response(response='LUT Deleted', status=204)
