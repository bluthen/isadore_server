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

from isadoreapp import app
from flask import request, abort, Response, jsonify
from isadoreapp.authentication import authorized
import uuid
import json
import isadoreapp.util as util


@app.route('/resources/subscription', methods=["POST"])
@authorized('User')
def subscription_new():
    subscriber_id = str(uuid.uuid4())
    conn = util.getConn()
    cur = conn.cursor()
    util.insertRow('subscription',
                   {"subscriber_id": subscriber_id, "last_datetime": util.getDateFromParam('now')}, cursor=cur)
    # cur.execute("DELETE FROM subscription WHERE last_datetime < now() - interval '2 hours'")
    conn.commit()
    conn.close()
    return jsonify({"subscriber_id": subscriber_id})


@app.route('/resources/subscription/<uuid:subscriber_id>', methods=["PUT"])
@authorized('User')
def subscription_event_update(subscriber_id):
    subscribed = request.values.get("subscribed", None)
    if not subscribed:
        abort(400, 'subscribed parameter missing')
    try:
        json.loads(subscribed)
    except json.decoder.JSONDecodeError:
        abort(400, 'subscribed invalid json')
    conn = util.getConn()
    cur = conn.cursor()
    row = util.getRowsFromTable("subscription", extraWhere="subscriber_id=%s", extraArgs=(subscriber_id,), conn=conn)
    util.updateRowById('subscription', row[0]["id"],
                       {"last_datetime": util.getDateFromParam("now"), "subscribed": subscribed}, cur)
    conn.commit()
    conn.close()
    return Response(response="Subscription updated", status=204)


@app.route('/resources/subscription/<uuid:subscriber_id>', methods=["DELETE"])
@authorized('User')
def subscription_delete(subscriber_id):
    conn = util.getConn()
    cur = conn.cursor()
    cur.execute("DELETE FROM subscriber WHERE subscriber_id = %s", (subscriber_id,))
    conn.commit()
    conn.close()
    return Response(response="Subscription deleted.", status=204)


@app.route('/resources/subscription_event/<uuid:subscriber_id>', methods=["DELETE"])
@authorized('User')
def subscription_event_delete(subscriber_id):
    conn = util.getConn()
    cur = conn.cursor()
    row = util.getRowsFromTable("subscription", extraWhere="subscriber_id=%s", extraArgs=(subscriber_id,), conn=conn)
    if not row:
        conn.close()
        abort(404, 'Subscriber not found')

    util.updateRowById("subscription", row[0]["id"], {"last_datetime": util.getDateFromParam("now")}, cursor=cur)

    rows = util.getRowsFromTable('subscription_event', extraWhere="subscriber_id=%s", extraArgs=(subscriber_id,),
                                 conn=conn)
    if rows:
        cur.execute("DELETE FROM subscription_event where subscriber_id = %s", (subscriber_id,))
    conn.commit()
    conn.close()
    return jsonify({"events": rows})
