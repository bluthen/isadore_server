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

# TODO: Log to the config_log table
import flask
from flask import Flask, request, Response, redirect
from flask.json import JSONEncoder

import logging
import time
import isadoreapp.util as util
from functools import wraps

# logging.basicConfig(filename='./flask.log', level=logging.DEBUG, format='%(asctime)s %(message)s')


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)


app = Flask(__name__, static_url_path='/s', static_folder='../s', template_folder='./views')
app.secret_key = util.Single().getSessionSecretKey()
app.json_encoder = CustomJSONEncoder
timeLogger = logging.getLogger('timeLogger')
timeLogger.propagate = False
# logging.getLogger('iso8601').setLevel(logging.ERROR)


def main():
    print("Running: ", util.Single().getRunningPort())
    app.run(host='127.0.0.1', port=util.Single().getRunningPort(), debug=True, use_reloader=False, threaded=True)


def stopwatch():
    def stopwatched_wrapped(f):
        @wraps(f)
        def wrapper31(*args, **kawrgs):
            start = time.time()
            body = f(*args, **kawrgs)
            end = time.time()
            timeLogger.info(''.join(["Exec Time: ", "%.2fs - " % (end - start), request.method, " ", request.urlparts[2]]))
            return body

        return wrapper31


# install(stopwatch)


@app.route('/')
def root():
    return redirect('/s/main.html')


@app.route('/gen_reports/<filename>')
def serve_gen_reports(filename):
    return flask.send_from_directory('./gen_reports', filename)


@app.errorhandler(400)
def error_bad_request(error):
    logging.info("Bad Request:" + error.output + ", " + request.url)
    return Response(error.output, mimetype='text/plain')


@app.errorhandler(500)
def error_server_error(error):
    logging.error("HTTPError 500: " + str(request.url) + " " + str(error.traceback))
    return Response(error.output, mimetype='text/plain')


@app.route('/exceptionTest')
def exception_test():
    return 1 / 0


# Import these so routes in flask get registered sees them.
import isadoreapp.accounts
import isadoreapp.privileges

import isadoreapp.conf.bin_sections
import isadoreapp.conf.bins
import isadoreapp.conf.device_types
import isadoreapp.conf.devices
import isadoreapp.conf.general
import isadoreapp.conf.sensor_types
import isadoreapp.conf.sensors
import isadoreapp.conf.version
import isadoreapp.conf.subsamples

import isadoreapp.alarms
import isadoreapp.alarms.alarm_types
import isadoreapp.alarms.alarm_contact_types
import isadoreapp.alarms.events

import isadoreapp.data
import isadoreapp.data.readings
import isadoreapp.data.fills
import isadoreapp.data.graph
import isadoreapp.data.graph_data
import isadoreapp.data.air_deductions

import isadoreapp.data.reports.toLatex

import isadoreapp.contact

import isadoreapp.controls

import isadoreapp.MID_WWW

import isadoreapp.login

import isadoreapp.luts
import isadoreapp.luts.mc_maxtemp

import isadoreapp.subscription

import isadoreapp.data.bin_heatmap

import isadoreapp.optimizations

if __name__ == '__main__':
    main()
