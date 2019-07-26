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
from bottle import response, request, abort, HTTPResponse
import psycopg2.extras as dbapi2extras
from authentication import authorized, unauthorized
import util
import operator
import datetime
import logging
import numpy


# TODO: add settings to control hrs/pt
#@route('/resources/alarmsWTF', method=["GET"])
#@authorized('User')
#def getEMC():
#	fillID = request.params.get("fill_id")
#	if fillID:
#		try:
#			# get fill info
#			# fillInfo = util.getRowFromTableById("fill",fillID,checkEnabled=True)
#			(airStartTime,airEndTime) = getAirTimes(fillID)
#			if not airStartTime:
#				abort(400, "Missing air begin time")
#				# get air_deducts that started during this fill
#				airDeducts = util.getRowsFromTable("air_deduct",
#												   extraWhere="begin_datetime >= %s AND begin_datetime <= %s OR end_datetime >= %s AND end_datetime <= %s",
#												   extraArgs=(airStartTime,
#															  airEndTime,
#															  airStartTime,
#															  airEndTime))
#				# compute the actual lengths of time to deduct from the air time
#				airDeductLens = [computeDeductTime(airStartTime,
#												   airEndTime,
#												   i["begin_datetime"],
#												   i["end_datetime"]) for i in airDeducts]
#				# do the EMC computation
#				return util.responseJSON(computeEMC(reduce(operator.add,fillInfo["pre_mc"])/len(fillInfo["pre_mc"]),
#													util.getRowFromTableById("general_config", 1)["air_deducts"],
#													computeAirTime(airStartTime,
#																   airEndtime,
#																   airDeductLens)
#													)
#										 )
#		except:
#			abort(400,"EMC calculation failed")
#		else:
#			abort(400, "Bad fill_id parameter.")

def computeMaxTempsSingle(time, binId, conn=None):
	if not conn:
		conn = util.getConn()
	extraWhere = ' bin_id = %s AND '+\
			'((air_begin_datetime <= %s AND air_end_datetime > %s) OR '+\
			'(air_begin_datetime <= %s AND air_end_datetime IS NULL)) '
	orderStatement = ' ORDER BY air_begin_datetime DESC LIMIT 1'
	fills = util.getRowsFromTable("fill", extraWhere=extraWhere, extraArgs=(binId, time, time, time), orderStatement=orderStatement, conn=conn)
	if len(fills) == 0:
		return None
	fill = fills[0]
	(startMC, lutId) = getFillStartMCLUTId(fill['id'], fill=fill, conn=conn)
	if startMC == None and fill["pre_mc"]:
		startMC=sum(fill["pre_mc"])/len(fill["pre_mc"])
	if startMC == None or lutId == None:
		return None

	return computeMaxTempsDB(fill['air_begin_datetime'], time, lutId, startMC, [time])[0]

# @param times array of times to calc max temp for, sorted asc
# @param binID the bin to calc maxtemps for
# @param conn database connection
def computeMaxTempsMulti(times, binId, conn=None):
	if not conn:
		conn = util.getConn()
	startDatetime = times[0]
	endDatetime = times[len(times)-1]
	extraWhere = ' bin_id = %s AND '+\
			'((air_begin_datetime >= %s AND air_begin_datetime < %s) OR '+\
			'(air_begin_datetime <= %s AND air_end_datetime > %s) OR '+ \
			'(air_begin_datetime < %s AND air_end_datetime IS NULL))'

	extraArgs = (binId, 
				startDatetime, endDatetime,
				startDatetime, startDatetime,
				endDatetime)
			
	orderStatement = ' ORDER BY air_begin_datetime '
	fills = util.getRowsFromTable("fill", extraWhere=extraWhere, extraArgs=extraArgs, orderStatement=orderStatement, conn=conn)
	result = numpy.array([None]*len(times))
	startTimesIdx = 0
	ntimes=numpy.array(times)
	for fill in fills:
		(startMC, lutId) = getFillStartMCLUTId(fill['id'], fill=fill, conn=conn)
		if startMC == None and fill["pre_mc"]:
			startMC=sum(fill["pre_mc"])/len(fill["pre_mc"])
		if startMC == None or lutId == None:
			continue
		
		filterLogic, s, l = filterFillTimes(fill, ntimes[startTimesIdx:])
		ftimes = ntimes[startTimesIdx:][filterLogic]
		if len(ftimes) > 0:
			result[startTimesIdx+s:startTimesIdx+l+1]=computeMaxTempsDB(fill['air_begin_datetime'], ftimes[-1], lutId, startMC, ftimes)
			startTimesIdx = startTimesIdx+l+1
			if startTimesIdx >= len(ntimes):
				break
	return result.tolist()

# @param startIdx index to start in times
# @param fill The fill object we are getting times for
# @param times array of times sorted asc
def filterFillTimes(fill, times):
	if not fill['air_end_datetime']:
		logic= times >= fill['air_begin_datetime']
	else:
		logic = numpy.logical_and(times >= fill['air_begin_datetime'], times < fill['air_end_datetime'])
	idxs = numpy.flatnonzero(logic)
	return (logic, min(idxs), max(idxs))


def computeMaxTempsDB(startDatetime, endDatetime, lutId, startMC, times, conn=None):
	if not conn:
		conn = util.getConn()
	cur = conn.cursor()
	cur.execute("SELECT begin_datetime, end_datetime FROM air_deduct WHERE "+
						"((begin_datetime >= %s AND begin_datetime <= %s) OR "+
						" (begin_datetime <= %s AND end_datetime IS NULL) OR "+
						"(begin_datetime <= %s AND end_datetime >= %s)) ", (startDatetime, endDatetime, startDatetime, startDatetime, startDatetime))
	deducts = cur.fetchall()
	
	cur.execute('SELECT hours_per_mc FROM mc_maxtemp_lut where id = %s', (lutId,))
	row = cur.fetchone()
	if not row:
		return [None]*len(times)
	hours_per_mc = row[0]
	
	cur.execute('SELECT mc, maxtemp FROM mc_maxtemp_lut_value WHERE mc_maxtemp_lut_id = %s ORDER BY mc DESC', (lutId,))
	lut=cur.fetchall()
	
	return computeMaxTemps(startMC, startDatetime, deducts, times, lut, hours_per_mc)

# @param fillId
# @return (startMC, mc_maxtemp_lut_id)
def getFillStartMCLUTId(fillId, fill=None, conn=None):
	if not conn:
		conn = util.getConn()
	cur = conn.cursor()
	if not fill:
		fill = util.getRowFromTableById('fill', fillId, conn=conn)
	# Get start mc from transfer
	cur.execute('SELECT avg(w.average_mc) FROM (SELECT DISTINCT ON (t.id) t.average_mc FROM transfer t, transfer_field_fill tff '+\
			'WHERE t.id = tff.transfer_id AND tff.to_id = %s ORDER BY t.id) as w', (fill['id'],))
	row = cur.fetchone()
	if not row:
		return (None, None)

	startMC = row[0]
	
	lutId = fill['mc_maxtemp_lut_id']
	if not lutId:
		cur.execute('SELECT default_mc_maxtemp_lut_id FROM general_config LIMIT 1')
		row = cur.fetchone()
		lutId = row[0]
	if not lutId:
		return (None, None)
	return (startMC, lutId)

def computeEMC(startMC,hrsPerPt,airTime):
	# convert to dry time in seconds then compute EMC
	return startMC - util.timedeltaToHours(airTime)/hrsPerPt

def computeAirTime(startTime,endTime,deductTimes):
	# returns air time in seconds taking deduct times into account
	return endTime - startTime - reduce(operator.add,deductTimes)

def getAirTimes(fillID):
	fillInfo = util.getRowFromTableById("fill",fillID,checkEnabled=True)
	if fillInfo["air_end_datetime"]:
		return (fillInfo["air_begin_datetime"],fillInfo["air_end_datetime"])
	else:
		return (fillInfo["air_begin_datetime"],datetime.datetime.now())
	
# TODO: add settings to DB to control max and min temps/EMCs
def computeMaxTemps(startMC,startTime,deductions,times,lut,hrsPerPt):
	# compute total air time using applicable deduct times
	ded = list(deductions)
	logging.debug("alarms.EMC.computeMaxTemps: startMC="+str(startMC)+
				", startTime="+str(startTime)+", len(deductions)="+str(len(deductions))+
				", len(times)="+str(len(times))+", hrsPerPt="+str(hrsPerPt))
	sorted(ded, key=operator.itemgetter(1))
	return [computeMaxTemp(lut, emc,hrsPerPt)
			for emc in [computeEMC(startMC,
								   hrsPerPt,
								   computeTime(startTime, t, ded))
						for t in times]]

def computeMaxTemp(lut, EMC,hrsPerPt):
	mylist=[tr[1] for tr in lut if EMC < tr[0]]
	if(not mylist):
		return lut[1][1]
	else:
		return mylist[-1]

def computeTime(airStartTime, airEndTime, deductions):
	time = datetime.timedelta(0)
	lastTime = airStartTime
	if not deductions:
		return airEndTime-airStartTime
	for dst, det in deductions:
		if(dst <= lastTime):
			if((det == None or det >= airEndTime)):
#				logging.debug("alarms.EMC.computeTime :"+str(time))
				return time
			elif(det < lastTime):
				continue
			else:
				lastTime = det
		elif(dst > lastTime):
			if(dst >= airEndTime):
				break
			elif(dst < airEndTime):
				time = time + (dst - lastTime)
				if(det != None and det < airEndTime):
					lastTime=det
				else:
					return time
	time = time + (airEndTime - lastTime)
	return time


def computeDeductTime(airStartTime,airEndTime,deductStartTime,deductEndTime):
	deductTime = deductEndTime - deductStartTime
	if airStartTime > deductStartTime:
		deductTime = deductTime - (airStartTime - deductStartTime)
	if airEndTime < deductEndTime:
		deductTime = deductTime - (deductEndTime - airEndTime)
	return deductTime




# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
