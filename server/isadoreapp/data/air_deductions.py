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


@app.route('/resources/data/air_deductions', methods=["GET"])
@authorized('User')
def air_deductions():
    begin_date = util.getDateFromParam(request.values.get("begin_span1"))
    end_date = util.getDateFromParam(request.values.get("end_span2"))

    if not begin_date:
        ids = util.getIdsFromTable("air_deduct")
    else:
        ids = util.getIdsFromTable("air_deduct", extraWhere=" ( begin_datetime >= %s AND begin_datetime <= %s ) ",
                                   extraArgs=(begin_date, end_date))
    return jsonify({'xlink': ['/resources/data/air_deductions/' + str(air_deduction_id) for air_deduction_id in ids]})


@app.route('/resources/data/air_deductions-fast', methods=["GET"])
@authorized('User')
def air_deductions_fast():
    begin_date = util.getDateFromParam(request.values.get("begin_span1"))
    end_date = util.getDateFromParam(request.values.get("begin_span2"))

    if not begin_date or not end_date:
        rows = util.getRowsFromTable("air_deduct", orderStatement=" ORDER BY begin_datetime ")
    else:
        rows = util.getRowsFromTable("air_deduct", extraWhere=" ( begin_datetime >= %s AND begin_datetime <= %s ) ",
                                     extraArgs=(begin_date, end_date), orderStatement=" ORDER BY begin_datetime ")
    return jsonify({'air_deductions': rows})


@app.route('/resources/data/air_deductions', methods=["POST"])
@authorized('Fill User')
def air_deductions_post():
    # rows = util.getRowsFromTable("air_deduct", extraWhere=" end_datetime IS NULL ")
    # if(rows):
    #     abort(400, 'There exists an already open air deduction close that one first.')
    begin_date = util.getDateFromParam(request.values.get("begin_datetime"))
    if not begin_date:
        abort(400, 'begin_datetime is required.')
    parameters = {'begin_datetime': begin_date}

    end_date = util.getDateFromParam(request.values.get("end_datetime"))
    if end_date:
        if begin_date > end_date:
            abort(400, 'Begin date is after end date.')
        parameters["end_datetime"] = end_date
    air_deduct_id = util.insertRow("air_deduct", parameters)
    return jsonify({'xlink': ['/resources/data/air_deductions/' + str(air_deduct_id)]})


@app.route('/resources/data/air_deductions/<int:air_deductions_id>', methods=["GET"])
@authorized('User')
def air_deductions_get(air_deductions_id):
    row = util.getRowFromTableById("air_deductions", air_deductions_id)
    if row:
        return jsonify(row)
    else:
        abort(404, 'Air deduction not found.')


@app.route('/resources/data/air_deductions/<int:air_deductions_id>', methods=["PUT"])
@authorized('Fill User')
def air_deductions_put(air_deductions_id):
    air_deduct = util.getRowFromTableById("air_deduct", air_deductions_id)
    if not air_deduct:
        abort(404, 'Air deduct not found')

    begin_date = util.getDateFromParam(request.values.get("begin_datetime"))
    end_date = util.getDateFromParam(request.values.get("end_datetime"))
    parameters = {}
    if begin_date:
        parameters['begin_datetime'] = begin_date
    if end_date:
        parameters['end_datetime'] = end_date
    if request.values.get("end_datetime") == 'empty':
        parameters['end_datetime'] = None
    if not parameters:
        abort(400, 'Arguments missing.')

    util.updateRowById("air_deduct", air_deductions_id, parameters)
    return Response(response="Air Deduction Updated", status=202)


@app.route('/resources/data/air_deductions/<int:air_deductions_id>', methods=["DELETE"])
@authorized('Fill User')
def air_deductions_del(air_deductions_id):
    air_deduct = util.getRowFromTableById("air_deduct", air_deductions_id)
    if not air_deduct:
        abort(404, 'Air deduct not found')
    util.deleteRowFromTableById("air_deduct", air_deductions_id)
    return Response(response="Air Deduction Deleted", status=202)
