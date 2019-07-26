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
#TODO: Log to the config_log table


from bottle import route, error, install #@UnresolvedImport
from bottle import static_file, response, request
import logging
import time
import re

from cache import noCache

#Import these so bottle sees them.
import accounts #@UnusedImport
import privileges #@UnusedImport

import conf.bin_sections #@UnusedImport
import conf.bins #@UnusedImport
import conf.device_types #@UnusedImport
import conf.devices #@UnusedImport
import conf.general #@UnusedImport
import conf.sensor_types #@UnusedImport
import conf.sensors #@UnusedImport
import conf.version #@UnusedImport
import conf.subsamples #@UnusedImport

import alarms #@UnusedImport
import alarms.alarm_types #@UnusedImport
import alarms.alarm_contact_types #@UnusedImport
import alarms.events #@UnusedImport

import data #@UnusedImport
import data.readings #@UnusedImport
import data.fills #@UnusedImport
import data.graph #@UnusedImport
import data.graph_data #@UnusedImport
import data.air_deductions #@UnusedImport

import data.reports.toLatex

import contact #@UnusedImport

import controls #@UnusedImport

import MID_WWW #@UnusedImport

import login #@UnusedImport

import luts #@UnusedImport
import luts.mc_maxtemp #@UnusedImport

import subscription

import data.bin_heatmap

import optimizations
import psycopg2
import psycopg2.extras
psycopg2.extras.register_default_json(loads=lambda x: x)


timeLogger = logging.getLogger('timeLogger')

timeLogger.propagate = False

logging.getLogger('iso8601').setLevel(logging.ERROR)

def stopwatch(callback):
	def wrapper(*args, **kawrgs):
		start = time.time()
		body = callback(*args, **kawrgs)
		end = time.time()
		timeLogger.info(''.join(["Exec Time: ", "%.2fs - " % (end - start), request.method, " ", request.urlparts[2]]) )
		return body
	return wrapper

install(stopwatch)

@route('/s/:filename#.*?\\.html#')
@noCache()
def serve_static_html(filename):
	#logging.debug("No cache static: %s" % filename)
	return static_file(filename, root='./s')

@route('/s/:filename#.*?__[a-zA-Z0-9]{32}.*#')
def serve_static_fingerprint(filename):
	m=re.search('(.*?)__[a-zA-Z0-9]{32}(.*)', filename)
	filename = m.group(1)+m.group(2)
	#logging.debug("fingerprint static: %s" % filename)
	return static_file(filename, root='./s')

@route('/s/:filename#.*#')
def serve_static(filename):
	return static_file(filename, root='./s')

@route('/gen_reports/:filename#.*#')
def serve_gen_reports(filename):
	return static_file(filename, root='./gen_reports', download=filename)


@error(400)
def errorBadRequest(error):
	response.content_type="text/plain"
	logging.info("Bad Request:"+ error.output+", "+request.url)
	return error.output


@error(500)
def errorServerError(error):
	response.content_type="text/plain"
	logging.error("HTTPError 500: "+str(request.url)+" "+str(error.traceback))
	return error.output

@route('/exceptionTest')
def exceptionTest():
	1/0
	


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
