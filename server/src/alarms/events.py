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
import psycopg2.extras as dbapi2extras
from bottle import route  # @UnresolvedImport
from bottle import request, abort
from authentication import authorized
import util
from datetime import datetime
from cache import noCache


@route('/resources/alarms/events', method=["GET"])
@authorized('User')
def alarm_events_list():
    # TODO: include ability to query based upon alarm or alarm type?

    # parse times
    start_time = datetime.strptime(request.params.get("begin"),
                                   "%d%m%y%H%M%S")
    end_time = datetime.strptime(request.params.get("end"),
                                 "%d%m%y%H%M%S")

    # TODO: I'm sure this is shitty code.
    ids = util.getIdsFromTable("alarm_event",
                               extraWhere="(begin_datetime BETWEEN timestamp %s AND timestamp %s) OR (end_datetime BETWEEN timestamp %s AND timestamp %s)",
                               extraArgs=(start_time, end_time, start_time, end_time))
    return {'xlink': ['/resources/alarms/events/' + str(event_id) for event_id in ids]}


@route('/resources/alarms/events/:alarm_event_id#[0-9]+#', method=["GET"])
@authorized('User')
def alarm_events_get(alarm_event_id):
    row = util.getRowFromTableById("alarm_event", int(alarm_event_id))

    if row:
        return util.responseJSON(row)
    else:
        abort(404, "Alarm event not found")


# TODO: write API method to insert new alarm event?

@route('/resources/alarms/currentEvents', method=["GET"])
@authorized('User')
@noCache()
def alarm_current_events():
    conn = util.getConn()
    extra_where = " (begin_datetime < %s AND end_datetime IS NULL) "
    now = util.getDateFromParam("now")
    global_rows = util.getIdsFromTable("alarm_global_event", extraWhere=extra_where, extraArgs=(now,), conn=conn)
    # TODO: Add user events
    sql = "SELECT alarm_event.id from alarm_event, alarm WHERE alarm_id = alarm.id AND alarm.account_id = %s AND (alarm_event.begin_datetime < %s AND alarm_event.end_datetime IS NULL) "
    cur = conn.cursor()
    cur.execute(sql, (request.user.id, now))
    xlink = ['/resources/alarms/globalEvents/' + str(global_id) for global_id in global_rows]
    xlink.extend(['/resources/alarms/events/' + str(row[0]) for row in cur])
    cur.close()
    conn.close()
    return {'xlink': xlink}


@route('/resources/alarms/currentEvents-fast', method=["GET"])
@authorized('User')
@noCache()
def alarm_current_events_fast(conn=None):
    return r_alarm_current_events_fast(conn)


def r_alarm_current_events_fast(conn=None):
    conn_given = False
    if conn:
        conn_given = True
    else:
        conn = util.getConn()
    extra_where = " (begin_datetime < %s AND end_datetime IS NULL) "
    now = util.getDateFromParam("now")
    global_events = util.getRowsFromTable("alarm_global_event", extraWhere=extra_where, extraArgs=(now,), conn=conn)
    # TODO: Add user events
    sql = "SELECT alarm_event.* from alarm_event, alarm WHERE alarm_id = alarm.id AND alarm.account_id = %s AND (alarm_event.begin_datetime < %s AND alarm_event.end_datetime IS NULL) "
    cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
    cur.execute(sql, (request.user.id, now))

    results = []
    for row in cur:
        result_row = {}
        for key in row.keys():
            result_row[key] = row[key]
        results.append(result_row)

    global_events.extend(results)
    cur.close()
    if not conn_given:
        conn.close()
    return util.responseJSON({'events': global_events})


@route('/resources/alarms/pastEvents', method=["GET"])
@authorized('User')
@noCache()
def alarm_past_events():
    after_dt = util.getDateFromParam(request.params.get("after_datetime"))
    if not after_dt:
        abort(400, 'No after_datetime argument.')
    conn = util.getConn()
    extra_where = " (begin_datetime > %s AND end_datetime IS NOT NULL) "
    global_rows = util.getIdsFromTable("alarm_global_event", extraWhere=extra_where, extraArgs=(after_dt,), conn=conn)
    sql = "SELECT alarm_event.id FROM alarm_event, alarm WHERE alarm_id = alarm.id AND alarm.account_id = %s AND (alarm_event.begin_datetime < %s AND alarm_event.end_datetime IS NOT NULL) "
    cur = conn.cursor()
    cur.execute(sql, (request.user.id, after_dt))
    xlink = ['/resources/alarms/globalEvents/' + str(global_id) for global_id in global_rows]
    xlink.extend(['/resources/alarms/events/' + str(row[0]) for row in cur])
    cur.close()
    conn.close()
    return {'xlink': xlink}


@route('/resources/alarms/pastEvents-fast', method=["GET"])
@authorized('User')
@noCache()
def alarm_past_events_fast():
    after_dt = util.getDateFromParam(request.params.get("after_datetime"))
    if not after_dt:
        abort(400, 'No after_datetime argument.')
    conn = util.getConn()
    extra_where = " (begin_datetime > %s AND end_datetime IS NOT NULL) "
    global_events = util.getRowsFromTable("alarm_global_event", extraWhere=extra_where, extraArgs=(after_dt,), conn=conn)
    sql = "SELECT alarm_event.id FROM alarm_event, alarm WHERE alarm_id = alarm.id AND alarm.account_id = %s AND (alarm_event.begin_datetime < %s AND alarm_event.end_datetime IS NOT NULL) "
    cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
    cur.execute(sql, (request.user.id, after_dt))

    results = []
    for row in cur:
        result_rows = {}
        for key in row.keys():
            result_rows[key] = row[key]
        results.append(result_rows)

    global_events.extend(results)
    cur.close()
    conn.close()
    return util.responseJSON({'events': global_events})


@route('/resources/alarms/globalEvents/:global_id#[0-9]+#', method=["GET"])
@authorized('User')
def alarm_global_events_get(global_id):
    row = util.getRowFromTableById("alarm_global_event", global_id)

    if row:
        return util.responseJSON(row)
    else:
        abort(404, "Global Alarm Event not found.")

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
