import psycopg2.extras as dbapi2extras
from isadoreapp import app
from flask import request, abort, jsonify
from isadoreapp.authentication import authorized
import isadoreapp.util as util
from datetime import datetime
from isadoreapp.cache import noCache


@app.route('/resources/alarms/events', methods=["GET"])
@authorized('User')
def alarm_events_list():
    # TODO: include ability to query based upon alarm or alarm type?

    # parse times
    start_time = datetime.strptime(request.values.get("begin"),
                                   "%d%m%y%H%M%S")
    end_time = datetime.strptime(request.values.get("end"),
                                 "%d%m%y%H%M%S")

    # TODO: I'm sure this is shitty code.
    ids = util.getIdsFromTable("alarm_event",
                               extraWhere="(begin_datetime BETWEEN timestamp %s AND timestamp %s) OR \
                               (end_datetime BETWEEN timestamp %s AND timestamp %s)",
                               extraArgs=(start_time, end_time, start_time, end_time))
    return jsonify({'xlink': ['/resources/alarms/events/' + str(event_id) for event_id in ids]})


@app.route('/resources/alarms/events/<int:alarm_event_id>', methods=["GET"])
@authorized('User')
def alarm_events_get(alarm_event_id):
    row = util.getRowFromTableById("alarm_event", int(alarm_event_id))

    if row:
        return jsonify(row)
    else:
        abort(404, "Alarm event not found")


# TODO: write API method to insert new alarm event?

@app.route('/resources/alarms/currentEvents', methods=["GET"])
@authorized('User')
@noCache()
def alarm_current_events():
    conn = util.getConn()
    extra_where = " (begin_datetime < %s AND end_datetime IS NULL) "
    now = util.getDateFromParam("now")
    global_rows = util.getIdsFromTable("alarm_global_event", extraWhere=extra_where, extraArgs=(now,), conn=conn)
    # TODO: Add user events
    sql = "SELECT alarm_event.id from alarm_event, alarm WHERE alarm_id = alarm.id AND alarm.account_id = %s AND \
    (alarm_event.begin_datetime < %s AND alarm_event.end_datetime IS NULL) "
    cur = conn.cursor()
    cur.execute(sql, (request.user.id, now))
    xlink = ['/resources/alarms/globalEvents/' + str(global_id) for global_id in global_rows]
    xlink.extend(['/resources/alarms/events/' + str(row[0]) for row in cur])
    cur.close()
    conn.close()
    return jsonify({'xlink': xlink})


@app.route('/resources/alarms/currentEvents-fast', methods=["GET"])
@authorized('User')
@noCache()
def alarm_current_events_fast(conn=None):
    return jsonify(r_alarm_current_events_fast(conn))


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
    sql = "SELECT alarm_event.* from alarm_event, alarm WHERE alarm_id = alarm.id AND alarm.account_id = %s AND \
    (alarm_event.begin_datetime < %s AND alarm_event.end_datetime IS NULL) "
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
    return {'events': global_events}


@app.route('/resources/alarms/pastEvents', methods=["GET"])
@authorized('User')
@noCache()
def alarm_past_events():
    after_dt = util.getDateFromParam(request.values.get("after_datetime"))
    if not after_dt:
        abort(400, 'No after_datetime argument.')
    conn = util.getConn()
    extra_where = " (begin_datetime > %s AND end_datetime IS NOT NULL) "
    global_rows = util.getIdsFromTable("alarm_global_event", extraWhere=extra_where, extraArgs=(after_dt,), conn=conn)
    sql = "SELECT alarm_event.id FROM alarm_event, alarm WHERE alarm_id = alarm.id AND alarm.account_id = %s AND \
    (alarm_event.begin_datetime < %s AND alarm_event.end_datetime IS NOT NULL) "
    cur = conn.cursor()
    cur.execute(sql, (request.user.id, after_dt))
    xlink = ['/resources/alarms/globalEvents/' + str(global_id) for global_id in global_rows]
    xlink.extend(['/resources/alarms/events/' + str(row[0]) for row in cur])
    cur.close()
    conn.close()
    return jsonify({'xlink': xlink})


@app.route('/resources/alarms/pastEvents-fast', methods=["GET"])
@authorized('User')
@noCache()
def alarm_past_events_fast():
    after_dt = util.getDateFromParam(request.values.get("after_datetime"))
    if not after_dt:
        abort(400, 'No after_datetime argument.')
    conn = util.getConn()
    extra_where = " (begin_datetime > %s AND end_datetime IS NOT NULL) "
    global_events = util.getRowsFromTable("alarm_global_event", extraWhere=extra_where, extraArgs=(after_dt,),
                                          conn=conn)
    sql = "SELECT alarm_event.id FROM alarm_event, alarm WHERE alarm_id = alarm.id AND alarm.account_id = %s AND \
    (alarm_event.begin_datetime < %s AND alarm_event.end_datetime IS NOT NULL) "
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
    return jsonify({'events': global_events})


@app.route('/resources/alarms/globalEvents/:global_id#[0-9]+#', methods=["GET"])
@authorized('User')
def alarm_global_events_get(global_id):
    row = util.getRowFromTableById("alarm_global_event", global_id)

    if row:
        return jsonify(row)
    else:
        abort(404, "Global Alarm Event not found.")

# Local Variables:
# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
