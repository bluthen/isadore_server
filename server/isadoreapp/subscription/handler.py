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

import json
import isadoreapp.util as util
import logging
import sys


def add_event(event, conn=None, cur=None, from_subscription_id=None):
    logging.debug('add_event' + str(event))
    made_conn = False
    if not conn:
        made_conn = True
        conn = util.getConn()
        cur = conn.cursor()
    subs = get_subscribers(event, conn)
    for s in subs:
        if s != from_subscription_id:
            util.insertRow("subscription_event",
                           {"subscriber_id": s, "event": json.dumps(event, default=util.customJSONHandler)}, cursor=cur)
    if made_conn:
        conn.commit()
        conn.close()


def is_subscribed(event, sub):
    try:
        logging.debug('========= is_subscribed')
        logging.debug(str(event))
        logging.debug(str(sub))
        if event["key"] == sub["key"]:
            logging.debug('Key - key')
            if event["key"] == "fill" and event["year"] == sub["year"]:  # Currently only support fills
                logging.debug('Key is fill and year matches')
                if type(sub["type"]) is list:
                    if event["type"] in sub["type"]:
                        logging.debug('event is a subscriber type')
                        if event["type"] in ["add", "delete"]:
                            logging.debug('type is add or delete')
                            return True
                        elif event["type"] == "edit":
                            logging.debug('Type is edit')
                            if "ids" not in sub:
                                logging.debug('All ids')
                                return True
                            else:
                                if type(sub["ids"]) is list:
                                    if type(event["ids"]) is list:
                                        for eid in event["ids"]:
                                            if eid in sub["ids"]:
                                                logging.debug('id is in subs ids')
                                                return True
                                    else:
                                        if event["ids"] in sub["ids"]:
                                            logging.debug('id is in subs ids')
                                            return True
                                elif event["ids"] == sub["ids"]:
                                    logging.debug('id is subs id')
                                    return True
    except:
        logging.error(sys.exc_info()[0])
    return False


def get_subscribers(event, conn):
    subs = util.getRowsFromTable("subscription", conn=conn)
    subscribers = []
    for s in subs:
        try:
            if s["subscribed"]:
                se = json.loads(s["subscribed"])
                for seev in se["subscriptions"]:
                    if is_subscribed(event, seev):
                        subscribers.append(s["subscriber_id"])
        except:
            logging.exception("Error parsing subscribed.")
    return subscribers
