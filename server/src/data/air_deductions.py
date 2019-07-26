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
from bottle import request, abort, HTTPResponse
from authentication import authorized
import util


@route('/resources/data/air_deductions', method=["GET"])
@authorized('User')
def air_deductions():
	beginDate = util.getDateFromParam(request.params.get("begin_span1"))
	endDate = util.getDateFromParam(request.params.get("end_span2"))

	if(not beginDate):
		ids = util.getIdsFromTable("air_deduct")
	else:
		ids=util.getIdsFromTable("air_deduct", extraWhere=" ( begin_datetime >= %s AND begin_datetime <= %s ) ", extraArgs=(beginDate, endDate))
	return {'xlink': ['/resources/data/air_deductions/'+str(id) for id in ids]}


@route('/resources/data/air_deductions-fast', method=["GET"])
@authorized('User')
def air_deductions_fast():
	beginDate = util.getDateFromParam(request.params.get("begin_span1"))
	endDate = util.getDateFromParam(request.params.get("begin_span2"))

	if(not beginDate or not endDate):
		rows = util.getRowsFromTable("air_deduct", orderStatement=" ORDER BY begin_datetime ")
	else:
		rows = util.getRowsFromTable("air_deduct", extraWhere=" ( begin_datetime >= %s AND begin_datetime <= %s ) ", extraArgs=(beginDate, endDate), orderStatement=" ORDER BY begin_datetime ")
	return util.responseJSON({'air_deductions': rows})

@route('/resources/data/air_deductions', method=["POST"])
@authorized('Fill User')
def air_deductions_post():
#	rows = util.getRowsFromTable("air_deduct", extraWhere=" end_datetime IS NULL ")
#	if(rows):
#		abort(400, 'There exists an already open air deduction close that one first.')
	beginDate = util.getDateFromParam(request.params.get("begin_datetime"))
	if(not beginDate):
		abort(400, 'begin_datetime is required.')
	parameters={'begin_datetime': beginDate}
	
	endDate = util.getDateFromParam(request.params.get("end_datetime"))
	if(endDate):
		if(beginDate > endDate):
			abort(400, 'Begin date is after end date.')
		parameters["end_datetime"]=endDate
	id=util.insertRow("air_deduct", parameters)
	return {'xlink' : ['/resources/data/air_deductions/'+str(id)]}

@route('/resources/data/air_deductions/:id#[0-9]+#', method=["GET"])
@authorized('User')
def air_deductions_get(id):
	row = util.getRowFromTableById("air_deductions", id)
	if(row):
		return util.responseJSON(row)
	else:
		abort(404, 'Air deduction not found.')

@route('/resources/data/air_deductions/:id#[0-9]+#', method=["PUT"])
@authorized('Fill User')
def air_deductions_put(id):
	air_deduct = util.getRowFromTableById("air_deduct", id)
	if not air_deduct:
		abort(404, 'Air deduct not found')
	
	beginDate = util.getDateFromParam(request.params.get("begin_datetime"))
	endDate = util.getDateFromParam(request.params.get("end_datetime"))
	parameters={}
	if(beginDate):
		parameters['begin_datetime']=beginDate
	if(endDate):
		parameters['end_datetime']=endDate
	if(request.params.get("end_datetime") == 'empty'):
		parameters['end_datetime']=None
	if(not parameters):
		abort(400, 'Arguments missing.')

		
	util.updateRowById("air_deduct", id, parameters)
	return HTTPResponse(output="Air Deduction Updated", status=202)

@route('/resources/data/air_deductions/:id#[0-9]+#', method=["DELETE"])
@authorized('Fill User')
def air_deductions_del(id):
	air_deduct = util.getRowFromTableById("air_deduct", id)
	if not air_deduct:
		abort(404, 'Air deduct not found')
	util.deleteRowFromTableById("air_deduct", id)
	return HTTPResponse(output="Air Deduction Deleted", status=202)


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
