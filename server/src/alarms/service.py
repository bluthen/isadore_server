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
from bottle import route, request, abort, HTTPResponse
from authentication import alarmsauth, alarmsauthorized
import json
import util


@route('/resources/alarms/service/alarms', method=["GET"])
@alarmsauth()
def service_alarms():
    row = util.getRowFromTableById('general_config', 1)
    configs = json.loads(row["configs"])
    return configs["alarms"]


@route('/resources/alarms/service/user_settings', method=["GET"])
@alarmsauthorized('User')
def service_alarms_user_settings():
    if "user" in request:
        user_id = request.user.id
        rows = util.getRowsFromTable('account', extraWhere="id = %s", extraArgs=(user_id,))
    else:
        rows = util.getRowsFromTable('account')
    ret = []
    for user in rows:
        u = {}
        user_configs = None
        if user["configs"]:
            user_configs = json.loads(user["configs"])
        alarm_settings = {"all_disabled": True}
        if user_configs:
            if "alarm_settings" in user_configs:
                alarm_settings = user_configs["alarm_settings"]
        u["user_info"] = {"email": user["email"], "name": user["name"], "phone": user["phone"]}
        u["alarm_settings"] = alarm_settings
        ret.append(u)
    return ret


@route('/resources/alarms/service/history', method=["GET"])
@alarmsauth()
def service_alarms_history_get():
    try:
        keys = json.loads(request.params.get('keys', None))
    except:
        abort(400, 'Bad arguments')
    where = ""
    first = True
    whereargs = []
    for key in keys:
        if not first:
            where += " OR "
        where += " key = %s "
        whereargs.append(key)
    rows = util.getRowsFromTable("alarm_history", extraWhere=where, extraArgs=whereargs)
    ret = {}
    for row in rows:
        ret[row["key"]] = json.dumps(rows["info"])
    return ret


@route('/resources/alarms/service/history', method=["POST"])
@alarmsauth()
def service_alarms_history_put():
    key = request.params.get('key', None)
    info = request.params.get('info', None)
    if not key or not info:
        abort(400, 'Bad arguments')
    try:
        json.loads(info)
    except:
        abort(400, 'Bad arguments')
    conn = util.getConn()
    cur = conn.cursor()
    cur.execute("SELECT id from alarm_history")
    r = cur.fetchone()
    if r:
        cur.execute("UPDATE alarm_history SET info = %s", (info,))
    else:
        cur.execute("INSERT INTO alarm_history (key, info) VALUES (%s, %s)", (key, info))
    conn.commit()
    cur.close()
    conn.close()

    return HTTPResponse(output="Alarms History updated", status=204)

