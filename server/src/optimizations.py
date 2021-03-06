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

from bottle import route
from bottle import request, abort
from authentication import authorized
import util
from data import readings
import alarms
import controls
from alarms import events
import json
from cache import noCache



@route('/resources/optimized_updates', method=["GET"])
@authorized('User')
@noCache()
def optimized_updates():
    account_id = request.user.id
    conn = util.getConn()
    readings_jsonstr = readings.r_readings_data_latest(conn=conn)
    alarms_fast = alarms.r_alarms_fast(account_id=account_id, conn=conn)
    controls_last_readings = controls.r_controls_last_readings(conn=conn)
    current_events_fast = events.r_alarm_current_events_fast(conn=conn)
    general = util.getRowFromTableById('general_config', 1)
    del general['id']
    del general['mid_pass']
    ret = {
        "general": general,
        "sensor_data": json.loads(controls_last_readings)["sensor_data"],
        "alarms": json.loads(alarms_fast)["alarms"],
        "readings": json.loads(readings_jsonstr)["results"],
        "events": json.loads(current_events_fast)["events"]
    }
    conn.close()

    return util.responseJSON(ret)

