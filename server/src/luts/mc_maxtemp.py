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

@route('/resources/luts/mc_maxtemp_default', method=["PUT"])
@authorized('Config User')
def mc_maxtemp_default():
	try:
		lutId = request.params.get('mc_maxtemp_lut_id')
		if not lutId:
			abort(400, 'Bad arguments')
		lutId = int(lutId)
	except ValueError:
		abort(400, 'Bad arguments')
	
	conn = util.getConn()
	row = util.getRowFromTableById("mc_maxtemp_lut", lutId, conn=conn)
	if not row:
		abort(400, 'Bad arguments')
	curr = conn.cursor()
	curr.execute("UPDATE general_config SET default_mc_maxtemp_lut_id=%s", (lutId,))
	conn.commit()
	curr.close()
	conn.close()
	return HTTPResponse(output='Default Set', status=204)


@route('/resources/luts/mc_maxtemp-fast', method=["GET"])
@authorized('User')
def luts_mc_maxtemp_fast():
	conn = util.getConn()
	luts=util.getRowsFromTable("mc_maxtemp_lut", conn=conn)
	for lut in luts:
		values = util.getRowsFromTable("mc_maxtemp_lut_value", extraWhere="mc_maxtemp_lut_id=%s", extraArgs=(lut['id'],), orderStatement=" ORDER BY mc ", conn=conn)
		lut["values"]=values
	return util.responseJSON({'luts': luts})

# TODO: nonfast get

@route('/resources/luts/mc_maxtemp/:id#[0-9]+#', method=["GET"])
@authorized('User')
def luts_mc_maxtemp_getsingle(id):
	conn = util.getConn()
	lut = util.getRowFromTableById("mc_maxtemp_lut", id, conn=conn)
	values = util.getRowsFromTable("mc_maxtemp_lut_value", extraWhere="mc_maxtemp_lut_id=%s", extraArgs=(lut['id'],), orderStatement=" ORDER BY mc ", conn=conn)
	lut["values"]=values
	return util.responseJSON(lut)


@route('/resources/luts/mc_maxtemp', method=["POST"])
@authorized('Config User')
def luts_mc_maxtemp_post():
	name, hours_per_mc, mcs, maxtemps = luts_mc_maxtemp_args()
	conn = util.getConn()
	cur = conn.cursor()
	newId = util.insertRow("mc_maxtemp_lut", {'name': name, 'hours_per_mc': hours_per_mc}, cur)
	for idx in xrange(0, len(mcs)):
		util.insertRow("mc_maxtemp_lut_value", {'mc': mcs[idx], 'maxtemp': maxtemps[idx], 'mc_maxtemp_lut_id': newId}, cur)
	
	general = util.getRowFromTableById("general_config", 1, conn=conn)
	if not general["default_mc_maxtemp_lut_id"]:
		cur.execute('UPDATE general_config SET default_mc_maxtemp_lut_id=%s', (newId,))
	
	conn.commit()
	cur.close()
	conn.close()
	return {'xlink': ['/resources/luts/mc_maxtemp/'+str(newId)]}
	
	
	
def luts_mc_maxtemp_args():
	name = request.params.get('name', None)
	hours_per_mc = request.params.get('hours_per_mc', None)
	mcs = request.params.get('mcs', None)
	maxtemps = request.params.get('maxtemps', None)
	
	if not mcs:
		mcs = []
	else:
		mcs = mcs.split(',')
	if not maxtemps:
		maxtemps = []
	else:
		maxtemps = maxtemps.split(',')

	if name == None or hours_per_mc == None:
		abort(400, 'Missing parameters')

	try:
		hours_per_mc = float(hours_per_mc)
	except ValueError:
		abort(400, 'Invalid hours_per_mc')
		
	if len(mcs) != len(maxtemps):
		abort(400, 'mcs and maxtemps do not match.')
	
	try:
		for idx in xrange(0, len(mcs)):
			mcs[idx]=float(mcs[idx])
			maxtemps[idx]=float(maxtemps[idx])
	except ValueError:
		abort(400, 'Invalid mcs or maxtemps')
	
	return (name, hours_per_mc, mcs, maxtemps)


@route('/resources/luts/mc_maxtemp/:id#[0-9]+#', method=['PUT'])
@authorized('Config User')
def luts_mc_maxtemp_put(id):
	name, hours_per_mc, mcs, maxtemps = luts_mc_maxtemp_args()
	row = util.getRowFromTableById('mc_maxtemp_lut', id)
	if not row:
		abort(404, 'LUT not found.')
		
	conn = util.getConn()
	cur = conn.cursor()
	util.updateRowById("mc_maxtemp_lut", id, {'name': name, 'hours_per_mc': hours_per_mc}, cur)
	cur.execute('DELETE FROM mc_maxtemp_lut_value WHERE mc_maxtemp_lut_id=%s', (id,))
	for idx in xrange(0, len(mcs)):
		util.insertRow("mc_maxtemp_lut_value", {'mc': mcs[idx], 'maxtemp': maxtemps[idx], 'mc_maxtemp_lut_id': id}, cur)
	conn.commit()
	cur.close()
	conn.close()
	return HTTPResponse(output='LUT Updated', status=204)

@route('/resources/luts/mc_maxtemp/:id#[0-9]+#', method=['DELETE'])
@authorized('Config User')
def luts_mc_maxtemp_delete(id):
	conn = util.getConn()
	row = util.getRowFromTableById('mc_maxtemp_lut', id, conn=conn)
	if not row:
		abort(404, 'LUT not found.')

	cur = conn.cursor()
	
	util.deleteRowFromTableById("mc_maxtemp_lut", id, cursor=cur)

	general = util.getRowFromTableById("general_config", 1, conn=conn)
	if not general["default_mc_maxtemp_lut_id"]:
		cur.execute('UPDATE general_config SET default_mc_maxtemp_lut_id=(SELECT id FROM mc_maxtemp_lut ORDER BY id LIMIT 1)')
	conn.commit()
	cur.close()
	conn.close()
	return HTTPResponse(output='LUT Deleted', status=204)
	

