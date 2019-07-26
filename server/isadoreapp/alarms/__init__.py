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

# TODO: prevent all users from messing with alarms for EA users
# TODO: users should not be allowed to modify an alarm so that it now belongs to another user

import psycopg2.extras as dbapi2extras
from isadoreapp import app
from flask import request, abort, Response, jsonify
from isadoreapp.authentication import authorized, unauthorized
import isadoreapp.util as util


@app.route('/resources/alarms', methods=["GET"])
@authorized('User')
def alarms_list():
    account_id = request.values.get("account_id")

    if account_id:
        try:
            account_id = int(account_id)
        except ValueError:
            abort(400, "Bad account_id parameter")

    conn = util.getConn()
    cur = conn.cursor()

    if not request.user.is_power_user():
        account_id = request.user.id

    sql = "SELECT alarm.id FROM alarm, account WHERE account.id = alarm.account_id AND account.privilege_id <= %s "
    args = [request.user.privilege_id]
    if account_id:
        sql += " AND alarm.account_id = %s"
        args.append(account_id)

    cur.execute(sql, tuple(args))
    xlink = ['/resources/alarms/' + str(row[0]) for row in cur]
    cur.close()
    conn.close()
    return jsonify({'xlink': xlink})


@app.route('/resources/alarms-fast', methods=["GET"])
@authorized('User')
def alarms_fast(account_id=None, conn=None):
    return jsonify(r_alarms_fast(account_id, conn))


def r_alarms_fast(account_id, conn):
    conn_given = False
    if not account_id:
        account_id = request.values.get("account_id")

    if account_id:
        try:
            account_id = int(account_id)
        except ValueError:
            abort(400, "Bad account_id parameter")

    if not request.user.is_power_user():
        account_id = request.user.id

    if conn:
        conn_given = True
    else:
        conn = util.getConn()
    cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)  # DictCursor doesn't give real dictionaries

    sql = "SELECT alarm.* FROM alarm, account WHERE account.id = alarm.account_id AND account.privilege_id <= %s "
    args = [request.user.privilege_id]
    if account_id:
        sql += " AND alarm.account_id = %s"
        args.append(account_id)

    cur.execute(sql, tuple(args))
    results = []
    for row in cur:
        result_row = {}
        for key in row.keys():
            result_row[key] = row[key]
        results.append(result_row)
    cur.close()

    if not conn_given:
        conn.close()

    return {'alarms': results}


@app.route('/resources/alarms', methods=["POST"])
@authorized('User')
def alarms_new():
    # get parameter values
    alarm_type_id = request.values.get("alarm_type_id")
    account_id = request.values.get("account_id")
    greater_than_p = request.values.get("greater_than_p", '').lower() == 'true'
    alarm_contact_type_ids = request.values.get('alarm_contact_type_ids', None)
    value = request.values.get("value")

    # check parameter values
    if not util.getRowFromTableById('alarm_type', alarm_type_id):
        abort(400, 'Invalid alarm_type_id')
    if not util.getRowFromTableById("account", account_id, checkEnabled=True):
        abort(400, "Invalid account_id")

    alarm_type = util.getRowFromTableById('alarm_type', alarm_type_id)

    if not alarm_type:
        abort(400, 'Invalid alarm type.')

    # can only create alarms for self or be super-user
    if not request.user.is_power_user() and not request.user.id == int(account_id):
        # print("User " + str(request.user.id) + " cannot create account for " + account_id)
        unauthorized()

    contact_type_ids = []
    if alarm_contact_type_ids:
        try:
            contact_type_ids = [int(c) for c in alarm_contact_type_ids.split(',')]
        except ValueError:
            abort(400, 'invalid alarm_contact_type_ids parameter.')

    column_data = {"alarm_type_id": alarm_type_id,
                   "account_id": account_id}

    if alarm_type['threshold_p']:
        column_data["greater_than_p"] = greater_than_p
        try:
            column_data["value"] = float(value)
        except ValueError:
            abort(400, 'Invalid value.')

    # create new alarm
    # TODO: alarm and alarm_contact should be in single transaction.
    alarm_id = util.insertRow("alarm", column_data)

    for alarm_contact_type_id in contact_type_ids:
        util.insertRow('alarm_contact', {'alarm_id': alarm_id, 'alarm_contact_type_id': alarm_contact_type_id})

    # return the newly created alarm's id url
    return jsonify({'xlink': ['/resources/alarms/' + str(alarm_id)]})


@app.route('/resources/alarms/<int:alarm_id>', methods=["GET"])
@authorized('User')
def alarms_get(alarm_id):
    # TODO: Check that alarm belongs to you, or are power user.
    row = util.getRowFromTableById('alarm',
                                   int(alarm_id))
    if not row:
        abort(404, "Alarm not found.")
    else:
        # contact types
        rows = util.getRowsFromTable('alarm_contact', columns='alarm_contact_type_id', extraWhere='alarm_id=%s ',
                                     extraArgs=(alarm_id,))
        alarm_contact_type_ids = []
        for arow in rows:
            alarm_contact_type_ids.append(arow['alarm_contact_type_id'])
        row['alarm_contact_type_ids'] = alarm_contact_type_ids
        return jsonify(row)


@app.route('/resources/alarms/<int:alarm_id>', methods=["PUT"])
@authorized('User')
def alarms_update(alarm_id):
    # get alarm info
    alarm = util.getRowFromTableById('alarm', int(alarm_id))
    # return error if row not found
    if not alarm:
        abort(404, "Alarm not found.")

    if request.user.id == int(alarm["account_id"]) or request.user.is_power_user():

        # get parameter values
        alarm_type_id = request.values.get("alarm_type_id")
        account_id = request.values.get("account_id")
        greater_than_p = request.values.get("greater_than_p", '').lower() == 'true'
        alarm_contact_type_ids = request.values.get('alarm_contact_type_ids', None)
        value = request.values.get("value")

        # check parameter values
        if not util.getRowFromTableById('alarm_type', alarm_type_id):
            abort(400, 'Invalid alarm_type_id')
        if not util.getRowFromTableById("account", account_id, checkEnabled=True):
            abort(400, "Invalid account_id")

        alarm_type = util.getRowFromTableById('alarm_type', alarm_type_id)

        if not alarm_type:
            abort(400, 'Invalid alarm type.')

        # can only create alarms for self or be super-user
        if not request.user.is_power_user() and not request.user.id == int(account_id):
            # print("User " + str(request.user.id) + " cannot change alarm to " + account_id)
            unauthorized()

        contact_type_ids = []
        if alarm_contact_type_ids:
            try:
                contact_type_ids = [int(c) for c in alarm_contact_type_ids.split(',')]
            except ValueError:
                abort(400, 'invalid alarm_contact_type_ids parameter.')

        column_data = {"alarm_type_id": alarm_type_id,
                       "account_id": account_id}

        if alarm_type['threshold_p']:
            column_data["greater_than_p"] = greater_than_p
            try:
                column_data["value"] = float(value)
            except ValueError:
                abort(400, 'Invalid value.')
        else:
            column_data['greater_than_p'] = None
            column_data['value'] = None

        # TODO: alarm and alarm_contact should be in single transaction.
        util.updateRowById('alarm', alarm['id'], column_data)

        conn = util.getConn()
        cur = conn.cursor()
        cur.execute('DELETE from alarm_contact WHERE alarm_id = %s', (alarm['id'],))
        conn.commit()
        cur.close()
        conn.close()
        for alarm_contact_type_id in contact_type_ids:
            util.insertRow('alarm_contact', {'alarm_id': alarm['id'], 'alarm_contact_type_id': alarm_contact_type_id})

    else:
        unauthorized()

    return Response(response="Alarm updated.", status=202)


@app.route('/resources/alarms/<int:alarm_id>', methods=["DELETE"])
@authorized('User')
def alarms_delete(alarm_id):
    # get alarm info
    row = util.getRowFromTableById('alarm',
                                   int(alarm_id),
                                   columns="account_id")

    # is row there?
    if not row:
        abort(404, "Alarm " + str(alarm_id) + " not found")

    if request.user.id == int(row["account_id"]) or request.user.is_power_user():
        # get alarm info
        row = util.getRowFromTableById('alarm', int(alarm_id))

        # return error if row not found
        if not row:
            abort(404, "Alarm not found.")

        # delete alarm
        util.deleteRowFromTableById("alarm", alarm_id)

    # TODO: manually delete all alarm contacts associated with this alarm? No delete cascade will take care of it.
    else:
        unauthorized()

    return Response(response="Alarm deleted.", status=204)
