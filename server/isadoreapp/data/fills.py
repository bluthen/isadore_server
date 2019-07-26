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

import time
import sys
from datetime import datetime
from datetime import timedelta
import json
import urllib.parse
import logging
import csv
from io import StringIO
import re
from functools import cmp_to_key

from isadoreapp import app
import flask
from flask import request, abort, Response, jsonify
import psycopg2.extras as dbapi2extras
import pytz

from isadoreapp.authentication import authorized, alarmsauthorized
import isadoreapp.util as util
from isadoreapp.subscription import handler as subscription_handler
from isadoreapp.cache import noCache

TOP_BIN_SECTION = 13
BOTTOM_BIN_SECTION = 14
READ_TYPE_WETBULB = 131
READ_TYPE_MC = 300


@app.route('/resources/data/fill_config', methods=["GET"])
@authorized('User')
def fill_config_list():
    year = request.values.get("year", None)
    try:
        year = int(year)
    except ValueError:
        abort(400, 'Invalid year')
    conn = util.getConn()
    row = util.getRowsFromTable('fill_config', extraWhere="year=%s", extraArgs=(year,), checkEnabled=False, conn=conn)
    if row:
        return jsonify(row[0])
    else:
        row = util.getRowsFromTable('fill_config', extraWhere="year=%s", extraArgs=(0,), checkEnabled=False, conn=conn)
        if row:
            return jsonify(row[0])
        else:
            return jsonify({})


@app.route('/resources/data/fills', methods=["GET"])
@authorized('User')
def fill_list():
    # TODO: !!!test parameters for goodness!!!
    # print(request.values.get("begin_datetime"))
    bin_id = request.values.get("bin_id")
    field_code = request.values.get("field_code")
    truck = request.values.get("truck")
    hybrid_code = request.values.get("hybrid_code")
    storage_bin = request.values.get("storage_bin_number")
    storage_code = request.values.get("storage_bin_code")
    begin_span1 = util.getDateFromParam(request.values.get("begin_span1"))
    begin_span2 = util.getDateFromParam(request.values.get("begin_span2"))
    end_span1 = util.getDateFromParam(request.values.get("end_span1"))
    end_span2 = util.getDateFromParam(request.values.get("end_span2"))
    begin_datetime = util.getDateFromParam(request.values.get("begin_datetime"))
    end_datetime = util.getDateFromParam(request.values.get("end_datetime"))
    during_datetime = util.getDateFromParam(request.values.get("during_datetime"))

    # TODO: fieldcode, truck, hybrid_code, should be likes
    # build extraWhere portion of SQL query
    extra_where = "true AND "
    extra_args = ()
    if bin_id:
        extra_where += "bin_id = %s AND "
        extra_args += (bin_id,)
    if field_code:
        extra_where += "field_code = %s AND "
        extra_args += (field_code,)
    if truck:
        extra_where += "truck = %s AND "
        extra_args += (truck,)
    if hybrid_code:
        extra_where += "hybrid_code = %s AND "
        extra_args += (hybrid_code,)
    if storage_bin:
        extra_where += "storage_bin_number = %s AND "
        extra_args += (storage_bin,)
    if storage_code:
        extra_where += "storage_bin_code = %s AND "
        extra_args += (storage_code,)
    if begin_span1 and begin_span2:
        extra_where += "( (air_begin_datetime >= %s AND air_begin_datetime <= %s) OR \
        (filled_datetime >= %s AND filled_datetime <= %s) ) AND "
        extra_args += (begin_span1, begin_span2, begin_span1, begin_span2)
    if end_span1 and end_span2:
        extra_where += "(( air_end_datetime >= %s AND air_end_datetime <= %s ) OR \
        (emptied_datetime >= %s AND emptied_datetime <= %s) )  AND "
        extra_args += (end_span1, end_span2, end_span1, end_span2)
    if during_datetime:
        extra_where += "( ((air_begin_datetime < %s AND air_end_datetime IS NULL) OR \
        (air_begin_datetime < %s AND air_end_datetime > %s)) OR ((filled_datetime < %s AND \
        emptied_datetime IS NULL) OR (filled_datetime < %s AND emptied_datetime > %s)) ) AND "
        extra_args += (
            during_datetime, during_datetime, during_datetime, during_datetime, during_datetime, during_datetime)
    if begin_datetime:
        # extraWhere += "begin_datetime >= to_timestamp(%s,'YYYY-MM-DD HH24:MI:SS') AND "
        extra_where += "air_begin_datetime >= %s AND "
        extra_args += (begin_datetime,)
    if end_datetime:
        extra_where += "air_end_datetime <= %s AND "
        extra_args += (end_datetime,)
    # remove the extra AND at the end of the query
    extra_where = extra_where[0:len(extra_where) - 4 - 1]

    try:
        ids = util.getIdsFromTable("fill",
                                   extraWhere=extra_where,
                                   extraArgs=extra_args)
    except:
        logging.error(sys.exc_info()[0])
        return abort(400, "Query failed.  Probably due to poorly formed arguments.")

    # Just give empty list instead.
    # if not ids:
    #     abort(404, "No matching fills found")

    return jsonify({'xlink': ['/resources/data/fills/' + str(fill_id) for fill_id in ids]})


@app.route('/resources/data/fill_number', methods=["GET"])
@authorized('User')
def fill_number_to_id():
    fill_number = request.values.get("fill_number")
    begin_date = request.values.get("begin_datetime")
    end_date = request.values.get("end_datetime")

    extra_where = "fill_number = %s AND air_begin_datetime >= %s AND air_end_datetime <= %s"
    extra_args = (fill_number, begin_date, end_date)

    ids = util.getIdsFromTable("fill",
                               extraWhere=extra_where,
                               extraArgs=extra_args)

    return jsonify({'xlink': ['/resources/data/fills/' + str(ids.fetchone()[0])]})


@app.route('/resources/data/fill_types', methods=["GET"])
@authorized('User')
def fill_types_get():
    # TODO: Cache
    types = util.getRowsFromTable('fill_type')
    return jsonify({'fill_types': types})


@app.route('/resources/data/fills', methods=["POST"])
@authorized('Fill User')
def fill_new():
    # TODO: Check that fillNumber is not already taken for the year.
    # XXX: I have a feeling that this needs to be rewritten
    # get parameter values

    fill_number = request.values.get("fill_number", None)
    start_datetime = util.getDateFromParam(request.values.get("air_begin_datetime"))
    fill_datetime = util.getDateFromParam(request.values.get("start_datetime"))
    bin_id = request.values.get("bin_id", None)
    from_subscription_id = request.values.get("from_subscription_id", None)

    conn = util.getConn()
    cur = conn.cursor()

    # check if bin_id exists
    if not util.getRowFromTableById("bin", bin_id, conn=conn):
        conn.close()
        abort(400, "Bin id does not exist.")

    if (not fill_datetime and not start_datetime) or not fill_number:
        conn.close()
        abort(400, '(air_begin_datetime and start_datetime) and fill_number are required.')

    # create new DB entry
    fill_id = util.insertRow("fill",
                             {"fill_number": fill_number,
                              "air_begin_datetime": start_datetime,
                              "filled_datetime": fill_datetime,
                              "bin_id": bin_id}, cursor=cur)

    if fill_datetime:
        year = fill_datetime.year
    else:
        year = start_datetime.year

    subscription_handler.add_event(
        {"key": 'fill', "year": year, "ids": [fill_id], "type": "add", "when": util.getDateFromParam("now")}, conn, cur,
        from_subscription_id)

    conn.commit()
    conn.close()
    # return the newly created fill's id url
    return jsonify({"xlink": ["/resources/data/fills/" + str(fill_id)]})


def get_fill_by_id(fill_id, conn=None):
    close_conn = False
    if not conn:
        conn = util.getConn()
        close_conn = True

    row = util.getRowFromTableById('fill',
                                   int(fill_id), conn=conn)
    if row:
        cur = conn.cursor()
        cur.execute("SELECT mc, datetime FROM fill_during_mc WHERE fill_id = %s ORDER BY datetime", (fill_id,))
        during_mc = cur.fetchall()
        row['during_mc'] = during_mc
        cur.close()

        sheller_windows = util.getRowsFromTable('fill_sheller_window',
                                                extraWhere=" fill_id = %s ",
                                                extraArgs=(fill_id,),
                                                orderStatement=" ORDER BY begin_datetime ",
                                                conn=conn)
        row['sheller_windows'] = sheller_windows
    if close_conn:
        conn.close()

    return row


@app.route('/resources/data/fills/<int:fill_id>', methods=["GET"])
@authorized('User')
def fill_get(fill_id):
    row = get_fill_by_id(fill_id)
    if row:
        return jsonify(row)
    else:
        abort(404, "Fill not found.")


@app.route('/resources/data/fills-fast', methods=["GET"])
@alarmsauthorized('User')
def fill_list_fast():
    begin_span1 = util.getDateFromParam(request.values.get("begin_span1"))
    begin_span2 = util.getDateFromParam(request.values.get("begin_span2"))
    bin_id = request.values.get("bin_id", None)

    extra_where = ""
    extra_args = tuple()

    if bin_id:
        try:
            bin_id = int(bin_id)
        except ValueError:
            abort(400, 'Invalid bin_id')
        if extra_where:
            extra_where += " AND "
        extra_where += " bin_id = %s "
        extra_args += (bin_id,)

    if begin_span1 and begin_span2:
        if extra_where:
            extra_where += " AND "
        extra_where += "((air_begin_datetime >= %s AND air_begin_datetime <= %s) OR \
        (filled_datetime >= %s AND filled_datetime <= %s) ) "
        extra_args += (begin_span1, begin_span2, begin_span1, begin_span2)

    conn = util.getConn()
    rows = util.getRowsFromTable('fill', extraWhere=extra_where, extraArgs=extra_args,
                                 orderStatement=" ORDER by coalesce(filled_datetime, air_begin_datetime) ", conn=conn)
    cur = conn.cursor()
    for row in rows:
        cur.execute("SELECT mc, datetime FROM fill_during_mc WHERE fill_id = %s ORDER BY datetime", (row["id"],))
        during_mc = cur.fetchall()
        row['during_mc'] = during_mc
        sheller_windows = util.getRowsFromTable('fill_sheller_window',
                                                extraWhere=" fill_id = %s ",
                                                extraArgs=(row['id'],),
                                                orderStatement=" ORDER BY begin_datetime ",
                                                conn=conn)
        row['sheller_windows'] = sheller_windows
    cur.close()
    conn.close()

    return jsonify({'fills': rows})


@app.route('/resources/data/fills/<int:fill_id>', methods=["PUT"])
@authorized('Fill User')
def fill_update(fill_id):
    try:
        fid = int(fill_id)
    except ValueError:
        return abort(404, "Fill not found")
    # TODO: Check that fillNumber is not already taken for the year.
    # get parameter values
    fill_number = request.values.get("fill_number", None)
    fill_type_id = request.values.get("fill_type_id", None)

    air_begin_datetime = util.getDateFromParam(request.values.get("air_begin_datetime"))
    emptied_datetime = request.values.get('emptied_datetime')
    if emptied_datetime == 'empty':
        emptied_datetime = "empty"
    else:
        emptied_datetime = util.getDateFromParam(emptied_datetime)

    if request.values.get('filled_datetime') == "empty":
        filled_datetime = "empty"
    else:
        filled_datetime = util.getDateFromParam(request.values.get("filled_datetime"))

    if request.values.get("air_end_datetime") == "empty":
        air_end_datetime = "empty"
    else:
        air_end_datetime = util.getDateFromParam(request.values.get("air_end_datetime"))

    rotation_number = request.values.get("rotation_number", None)
    bin_id = request.values.get("bin_id", None)
    hybrid_code = request.values.get("hybrid_code", None)
    field_code = request.values.get("field_code", None)
    truck = request.values.get("truck", None)
    lot_number = request.values.get("lot_number", None)
    storage_bin_number = request.values.get("storage_bin_number", None)
    storage_bin_code = request.values.get("storage_bin_code", None)
    pre_mc_data = request.values.get("pre_mc", None)
    post_mc_data = request.values.get("post_mc", None)
    during_mc_data = request.values.get("during_mc", None)
    during_mc_date_data = request.values.get("during_mc_date", None)
    roll_datetime = request.values.get('roll_datetime', None)
    bushels = request.values.get("bushels", None)
    depth = request.values.get("depth", None)
    extras = request.values.get("extras", None)
    roll_time_array = list()
    pre_mc_array = list()
    post_mc_array = list()
    during_mc_array = list()
    during_mc_dates_array = list()
    from_subscription_id = request.values.get("from_subscription_id", None)

    # parse arrays
    if pre_mc_data and pre_mc_data != "empty":
        pre_mc_array = [float(i) for i in pre_mc_data.split(",")]
    if post_mc_data and post_mc_data != "empty":
        post_mc_array = [float(i) for i in post_mc_data.split(",")]
    if during_mc_data and during_mc_data != "empty":
        during_mc_array = [float(i) for i in during_mc_data.split(",")]
    if during_mc_date_data and during_mc_date_data != "empty":
        during_mc_dates_array = [util.getDateFromParam(d) for d in during_mc_date_data.split(',')]
    if roll_datetime and roll_datetime != "empty":
        roll_time_array = [util.getDateFromParam(d) for d in roll_datetime.split(',')]

    if len(during_mc_array) != len(during_mc_dates_array):
        abort(400, "During MC values/dates mismatch.")

    update_dict = {}
    if fill_number:
        update_dict['fill_number'] = fill_number
    if fill_type_id:
        update_dict['fill_type_id'] = fill_type_id
    if air_begin_datetime:
        update_dict['air_begin_datetime'] = air_begin_datetime
    if filled_datetime:
        update_dict['filled_datetime'] = filled_datetime
    if emptied_datetime:
        update_dict['emptied_datetime'] = emptied_datetime
    if air_end_datetime:
        update_dict['air_end_datetime'] = air_end_datetime
    if roll_time_array:
        update_dict['roll_datetime'] = roll_time_array
    if rotation_number:
        update_dict['rotation_number'] = rotation_number
    if bin_id:
        update_dict['bin_id'] = bin_id
    if hybrid_code:
        update_dict['hybrid_code'] = hybrid_code.strip()
    if field_code:
        update_dict['field_code'] = field_code.strip()
    if truck:
        update_dict['truck'] = truck.strip()
    if lot_number:
        update_dict['lot_number'] = lot_number
    if storage_bin_number:
        update_dict['storage_bin_number'] = storage_bin_number
    if storage_bin_code:
        update_dict['storage_bin_code'] = storage_bin_code
    if pre_mc_array:
        update_dict['pre_mc'] = pre_mc_array
    if post_mc_array:
        update_dict['post_mc'] = post_mc_array
    if bushels:
        update_dict['bushels'] = bushels
    if depth:
        update_dict['depth'] = depth
    if extras:
        update_dict['extras'] = extras

    if extras == "empty":
        update_dict['extras'] = None
    elif extras is not None:
        try:
            json.loads(extras)
        except json.decoder.JSONDecodeError:
            abort(400, "Invalid extras parameter")

    if pre_mc_data == "empty":
        update_dict['pre_mc'] = None
    if post_mc_data == "empty":
        update_dict['post_mc'] = None
    if roll_datetime == "empty":
        update_dict['roll_datetime'] = None

    for key in update_dict.keys():
        if update_dict[key] == 'empty':
            update_dict[key] = None

    conn = util.getConn()
    cur = conn.cursor()
    oldrow = util.getRowFromTableById("fill", fid, conn=conn)

    if update_dict:
        # create new DB entry
        util.updateRowById("fill", fid,
                           update_dict, cursor=cur)

    if during_mc_data == "empty":
        cur.execute('DELETE FROM fill_during_mc WHERE fill_id = %s', (fid,))
    elif during_mc_array:
        cur.execute('DELETE FROM fill_during_mc WHERE fill_id = %s', (fid,))
        for duringMC in zip(during_mc_array, during_mc_dates_array):
            cur.execute("INSERT INTO fill_during_mc (fill_id, mc, datetime) VALUES (%s, %s, %s)",
                        (fill_id, duringMC[0], duringMC[1]))
    elif not update_dict:
        abort(400, 'No parameters given.')

    sheller_windows = request.values.get("sheller_windows", None)
    if sheller_windows:
        sheller_windows = json.loads(sheller_windows)
        cur.execute('DELETE from fill_sheller_window where fill_id = %s', (fid,))
        for sheller_window in sheller_windows:
            if sheller_window['begin_datetime']:
                util.getDateFromParam(sheller_window['begin_datetime'])
            if sheller_window['end_datetime']:
                util.getDateFromParam(sheller_window['end_datetime'])
            cur.execute(
                'INSERT INTO fill_sheller_window (fill_id, bin_id, bin_section_id, begin_datetime, end_datetime) ' +
                'VALUES (%s, %s, %s, %s, %s)', (fid, sheller_window['bin_id'], sheller_window['bin_section_id'],
                                                sheller_window['begin_datetime'], sheller_window['end_datetime']))

    row = util.getRowFromTableById("fill", fid, conn=conn)

    if row["air_begin_datetime"]:
        year = row["air_begin_datetime"].year
    else:
        year = row["filled_datetime"].year

    if oldrow["air_begin_datetime"]:
        oldyear = oldrow["air_begin_datetime"].year
    else:
        oldyear = oldrow["filled_datetime"].year

    if oldyear != year:
        subscription_handler.add_event(
            {"key": 'fill', "year": oldyear, "ids": [fid], "type": "delete", "when": util.getDateFromParam("now")},
            conn, cur, from_subscription_id)
        subscription_handler.add_event(
            {"key": 'fill', "year": year, "ids": [fid], "type": "add", "when": util.getDateFromParam("now")}, conn, cur,
            from_subscription_id)

    subscription_handler.add_event(
        {"key": 'fill', "year": year, "ids": [fid], "type": "edit", "when": util.getDateFromParam("now")}, conn, cur,
        from_subscription_id)

    conn.commit()
    cur.close()
    conn.close()
    return Response(response="Fill updated", status=204)


@app.route('/resources/data/fills/<int:fill_id>', methods=["DELETE"])
@authorized('Fill User')
def fill_delete(fill_id):
    # get fill info
    try:
        fid = int(fill_id)
    except ValueError:
        return abort(404, "Fill not found.")
    from_subscription_id = request.values.get("from_subscription_id", None)
    conn = util.getConn()
    cur = conn.cursor()
    row = util.getRowFromTableById('fill', fid, conn=conn)

    # return error if row not found
    if not row:
        abort(404, "Fill not found.")

    # delete alarm
    util.deleteRowFromTableById("fill", fill_id, cursor=cur)

    if row["air_begin_datetime"]:
        year = row["air_begin_datetime"].year
    else:
        year = row["filled_datetime"].year

    subscription_handler.add_event(
        {"key": 'fill', "year": year, "ids": [fid], "type": "delete", "when": util.getDateFromParam("now")}, conn, cur,
        from_subscription_id)

    conn.commit()
    conn.close()

    return Response(response="Fill deleted.", status=204)


def get_avg_wetbulb(conn, bin_id, start_datetime, end_datetime, bin_number, config):
    if not start_datetime or not end_datetime:
        return None

    if 'reports' in config and 'avg_wetbulb_replace' in config['reports'] and config['reports']['avg_wetbulb_replace']:
        for replacement in config['reports']['avg_wetbulb_replace']:
            m = re.match(replacement['number_match'], bin_number)
            if m:
                value = None
                cur = None
                try:
                    cur = conn.cursor()
                    cur.execute("""SELECT avg(rds.avg_value) FROM reading_data_subsample rds, reading_subsample rs WHERE
                                rds.reading_subsample_id = rs.id and rds.bin_id = %s and rds.bin_section_id = %s and
                                rds.read_type_id = %s and rs.sample_period = 5 and rs.datetime > %s and
                                rs.datetime < %s""",
                                (replacement['bin_id'], replacement['bin_section_id'], READ_TYPE_WETBULB,
                                 start_datetime, end_datetime))
                    row = cur.fetchone()
                    if row:
                        value = row[0]
                finally:
                    cur.close()
                return value

    value = None
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT avg(rds.avg_value) FROM reading_data_subsample rds, reading_subsample rs WHERE " +
                    "rds.reading_subsample_id = rs.id and rds.bin_id = %s and rds.read_type_id = %s and " +
                    "rs.sample_period = 5 and rs.datetime > %s and rs.datetime < %s",
                    (bin_id, READ_TYPE_WETBULB, start_datetime, end_datetime))
        row = cur.fetchone()
        if row:
            value = row[0]
    finally:
        cur.close()
    return value


@app.route('/resources/data/report/fill_report', methods=["GET"])
@authorized('User')
@noCache()
def fill_report():
    year = request.values.get("year", None)
    begin_fill_number = request.values.get("begin_fill_number", None)
    end_fill_number = request.values.get("end_fill_number", None)
    report_type = request.values.get('type')
    report_form = request.values.get('form')

    if report_type == "hybrid" and report_form != "tab":
        abort(400, "Hybrid does not have full report.")

    if not year:
        abort(400, "Missing year parameter.")
    if not begin_fill_number:
        abort(400, "Missing begin_fill_number")
    if not end_fill_number:
        abort(400, "Missing end_fill_number")

    try:
        year = int(year)
    except ValueError:
        abort(400, "Invalid year parameter")

    try:
        begin_fill_number = int(begin_fill_number)
    except ValueError:
        abort(400, "Invalid begin_fill_number parameter")

    try:
        end_fill_number = int(end_fill_number)
    except ValueError:
        abort(400, "Invalid end_fill_number parameter")

    if begin_fill_number > end_fill_number:
        abort(400, "begin fill number is greater than end fill number")

    try:
        display_tz = pytz.timezone(request.values.get("display_tz"))
        display_tz_str = request.values.get("display_tz")
    except:
        return abort(400, 'invalid display_tz')

    fname = 'fill_report_%s_%s_%s-%s' % (report_type, year, begin_fill_number, end_fill_number)

    extra_where = "fill_number >= %s AND fill_number <= %s AND (air_begin_datetime >= %s AND air_begin_datetime <= %s) "
    year_start_datetime = datetime(year, 1, 1, 0, 0, 0, 0)  # y, mon, d, h, min, s, mic s
    year_end_datetime = datetime(year, 12, 31, 23, 59, 59, 999999)
    extra_args = (begin_fill_number, end_fill_number, year_start_datetime, year_end_datetime)
    order = " ORDER BY fill_number "
    conn = util.getConn()
    rows = util.getRowsFromTable("fill", extraWhere=extra_where, extraArgs=extra_args, orderStatement=order, conn=conn)
    general = util.getRowFromTableById("general_config", 1)
    general["configs"] = json.loads(general["configs"])

    report_title = general["customer_name"]
    fills = []
    for row in rows:
        cur = conn.cursor()
        cur.execute("SELECT mc, datetime FROM fill_during_mc WHERE fill_id = %s ORDER by datetime", (row['id'],))
        during_mc = cur.fetchall()
        during_mc = [(mc[0], util.datetimeToReadable(mc[1], display_tz)) for mc in during_mc]
        cur.close()

        bin_id = row['bin_id']
        bin_number = None
        if bin_id:
            bin_number = util.getRowFromTableById('bin', row['bin_id'], conn=conn)['name'].split(' ')[1]

        # Average Wetbulb
        avg_wetbulb = None
        if 'reports' in general['configs'] and 'avg_wetbulb' in general['configs']['reports'] and \
                general['configs']['reports']['avg_wetbulb']:
            avg_wetbulb = get_avg_wetbulb(conn, row["bin_id"], row["air_begin_datetime"], row["air_end_datetime"],
                                          bin_number, general['configs'])

        if avg_wetbulb is None:
            avg_wetbulb = ''

        post_mc = row["post_mc"]
        pre_mc = row["pre_mc"]
        post_avg = 0.0
        has_pre = False
        pre_avg = 0.0
        if pre_mc:
            for p in pre_mc:
                has_pre = True
                pre_avg = pre_avg + p
            pre_avg = pre_avg / float(len(pre_mc))
        has_post = False
        if post_mc:
            for p in post_mc:
                has_post = True
                post_avg = post_avg + p
            post_avg /= float(len(post_mc))

        sheller_sensor_mc = get_fill_sheller_sensor_mc(row['id'])
        post_stddev = ''
        post_oe = ''
        if not has_post and sheller_sensor_mc['avg']:
            has_post = True
            post_mc = sheller_sensor_mc['avg']
            post_avg = sheller_sensor_mc['avg']
            post_stddev = sheller_sensor_mc['stddev']
            post_oe = 'OE' if sheller_sensor_mc['open_ended'] else ''

        mc_removed = None
        if has_post and has_pre:
            mc_removed = pre_avg - post_avg

        if not has_post:
            post_avg = None
        if not has_pre:
            pre_avg = None

        air_begin_datetime = row["air_begin_datetime"]
        air_end_datetime = row["air_end_datetime"]

        hrs_per_point = None
        if has_post and has_pre and air_begin_datetime and air_end_datetime:
            hrs = util.timedeltaToHours(air_end_datetime - air_begin_datetime)
            if post_avg > 0.1 and pre_avg > 0.1 and pre_avg - post_avg > 0.0:
                hrs_per_point = hrs / (pre_avg - post_avg)
            else:
                hrs_per_point = None

        roll_time = row['roll_datetime']
        orig_roll_time = roll_time
        if not roll_time:
            if air_end_datetime:
                roll_time = [air_end_datetime]
            else:
                roll_time = [util.getDateFromParam('now')]

        # TODO: Support multi roll
        # TODO: Support air detection
        up_time = None
        if roll_time and len(roll_time) > 0 and air_begin_datetime:
            up_time = roll_time[0] - air_begin_datetime
            up_time = (util.timedeltaToHours(up_time))

        down_time = None
        if roll_time and len(roll_time) > 0 and air_end_datetime:
            down_time = air_end_datetime - roll_time[0]
            down_time = (util.timedeltaToHours(down_time))

        total_time = None
        if air_begin_datetime and air_end_datetime:
            total_time = air_end_datetime - air_begin_datetime
            total_time = (util.timedeltaToHours(total_time))

        up_percent = None
        down_percent = None
        if up_time is not None and down_time is not None and total_time is not None and total_time > 0:
            up_percent = (100.0 * float(up_time) / total_time)
            down_percent = (100.0 * float(down_time) / total_time)

        # if(air_begin_datetime):
        #     air_begin_datetime = util.datetimeToReadable(air_begin_datetime, displayTZ)
        #
        # if(air_end_datetime):
        #     air_end_datetime = util.datetimeToReadable(air_end_datetime, displayTZ)

        filled_datetime = row['filled_datetime']
        emptied_datetime = row['emptied_datetime']

        # if(filled_datetime):
        #     filled_datetime = util.datetimeToReadable(filled_datetime, displayTZ)
        # if(emptied_datetime):
        #     emptied_datetime = util.datetimeToReadable(emptied_datetime, displayTZ)

        roll_time = orig_roll_time
        if roll_time:
            roll_time = roll_time[0]
        else:
            roll_time = None

        for key in ["hybrid_code", "field_code", "truck"]:
            if row[key]:
                row[key] = row[key].split("\n")
        fill = {"fill_number": row["fill_number"],
                "id": row["id"],
                "fill_type_id": row["fill_type_id"],
                "year": year,
                "bin_id": bin_id,
                "bin_number": bin_number,
                "rotation": row["rotation_number"],
                "hybrid": row["hybrid_code"],
                "field_name": row["field_code"],
                "truck": row["truck"],
                "depth": row["depth"],
                "filled_datetime": filled_datetime,
                "emptied_datetime": emptied_datetime,
                "air_begin_time": air_begin_datetime,
                "roll_time": roll_time,
                "air_end_time": air_end_datetime,
                "up_time": up_time,
                "up_percent": up_percent,
                "down_time": down_time,
                "down_percent": down_percent,
                "air_total": total_time,
                "pre_mc": pre_mc,  # Array
                "pre_avg": pre_avg,
                "during_mc": during_mc,  # [(value, date), ..]
                "post_mc": post_mc,  # array
                "post_avg": post_avg,
                "post_stddev": post_stddev,
                "post_oe": post_oe,
                "mc_removed": mc_removed,
                "bushels": row["bushels"],
                "hrs_per_point": hrs_per_point,
                "lot_number": row["lot_number"],
                "storage_code": row["storage_bin_code"],
                "storage_number": row["storage_bin_number"],
                "avg_wetbulb": avg_wetbulb
                }
        # for key in fill.keys():
        #     if(not fill[key]):
        #         if(formS == 'csv'):
        #             fill[key]=''
        #         else:
        #             fill[key] = '&#xA0;'
        fills.append(fill)

    now_str = util.datetimeToReadable(util.getDateFromParam("now"), display_tz)

    total_keys = ["depth", "up_time", "up_percent", "down_time", "down_percent", "air_total", "pre_avg", "post_avg",
                  "hrs_per_point", "mc_removed", "bushels", "avg_wetbulb"]
    if report_type == 'fill' and report_form == 'full':
        fills_to_string(fills, report_form, display_tz, nbsp_none=True)
        # for key in fill.keys():
        #    if not fill[key]:
        #        fill[key] = '&#xA0;'
        return flask.render_template('fill_report.html', report_title=report_title, fills=fills, general=general,
                                     ts=int(time.time() * 1000),
                                     display_tz=urllib.parse.quote(display_tz_str, ''))
    elif report_type == 'fill' and report_form == 'tab':
        totals, avgs = get_total_avgs(total_keys, fills)
        fills_to_string([totals], report_form, display_tz)
        fills_to_string([avgs], report_form, display_tz)
        fills_to_string(fills, report_form, display_tz)
        return flask.render_template('fill_tab.html', report_title="Yearly Report", fills=fills, general=general,
                                     timestamp=now_str,
                                     totals=totals,
                                     avgs=avgs)
    elif report_type == 'fill' and report_form == 'csv':
        extra_column_map = {}
        if 'reports' in general['configs'] and 'csv_reversal_snapshot' in general['configs']['reports']:
            addons = []
            if 'csv_reversal_snapshot_addons' in general['configs']['reports']:
                addons = general['configs']['reports']['csv_reversal_snapshot_addons']
            extra_column_map = add_reversal_snapshot(conn, general['configs']['reports']['csv_reversal_snapshot'],
                                                     fills, addons)
        fills_to_string(fills, report_form, display_tz)
        return csv_fill(fills, general, fname, extra_column_map)
    elif report_type == 'hybrid' and report_form == 'tab':
        totals, avgs = get_total_avgs(total_keys, fills)
        fills_to_string([totals], report_form, display_tz)
        fills_to_string([avgs], report_form, display_tz)
        groups = group_to_hybrid(fills)
        group_totals = []
        group_avgs = []
        for group in groups:
            g_total, g_avg = get_total_avgs(total_keys, group)
            fills_to_string([g_total], report_form, display_tz)
            fills_to_string([g_avg], report_form, display_tz)
            group_totals.append(g_total)
            group_avgs.append(g_avg)
            fills_to_string(group, report_form, display_tz)
        return flask.render_template('fill_hybrid_tab.html', report_title="Yearly Hybrid Report", groups=groups,
                                     general=general,
                                     groupTotals=group_totals, groupAvgs=group_avgs, totals=totals, avgs=avgs,
                                     timestamp=now_str)


def add_reversal_snapshot(conn, snapshot_minutes, fills, addons):
    column_map = {}
    for fill in fills:
        if fill['roll_time']:
            snapshot_time = fill['roll_time'] - timedelta(minutes=snapshot_minutes)
            sql = """SELECT rs.datetime, bs.name as bin_section_name, rds.avg_value, rt.short_name, rt.units
            FROM reading_data_subsample rds, reading_subsample rs, read_type rt, bin_section bs
            WHERE rds.bin_id = %s AND (rds.bin_section_id = %s OR rds.bin_section_id = %s) AND
            rds.reading_subsample_id = rs.id AND rt.id = rds.read_type_id AND rs.datetime = compute_sample_date(%s, 10)
            AND bs.id = rds.bin_section_id AND sample_period=10"""
            cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
            cur.execute(sql, (fill['bin_id'], TOP_BIN_SECTION, BOTTOM_BIN_SECTION, snapshot_time))
            rows = cur.fetchall()
            if len(rows) > 0:
                fill['reversal_snapshot_datetime'] = rows[0]['datetime']
                column_map['reversal_snapshot_datetime'] = 'Reversal Snapshot Datetime'
                for row in rows:
                    if row['short_name'] in ['MCP', 'jfactor']:
                        continue
                    key = 'reversal_snapshot_' + row['short_name'] + '_' + row['bin_section_name']
                    fill[key] = row['avg_value']
                    column_map[key] = 'Reversal Snapshot ' + row['bin_section_name'] + \
                                      ' ' + row['short_name'] + '(' + row['units'].replace(';', '') + ')'
            cur.close()

            for addon in addons:
                m = re.match(addon['number_match'], fill['bin_number'])
                if m:
                    sql = """SELECT rs.datetime, bs.name as bin_section_name, rds.avg_value, rt.short_name, rt.units
                            FROM reading_data_subsample rds, reading_subsample rs, read_type rt, bin_section bs
                            WHERE rds.bin_id = %s AND rds.bin_section_id = %s AND rds.read_type_id = %s AND
                            rds.reading_subsample_id = rs.id AND rt.id = rds.read_type_id AND 
                            rs.datetime = compute_sample_date(%s, 10) AND bs.id = rds.bin_section_id AND 
                            sample_period=10"""
                    cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
                    cur.execute(sql, (addon['bin_id'], addon['bin_section_id'], addon['read_type_id'], snapshot_time))
                    rows = cur.fetchall()
                    if len(rows) > 0:
                        row = rows[0]
                        fill['reversal_snapshot_datetime'] = rows[0]['datetime']
                        column_map['reversal_snapshot_datetime'] = 'Reversal Snapshot Datetime'
                        key = addon['column_key']
                        fill[key] = row['avg_value']
                        column_map[key] = addon['column_label']
                    cur.close()

    return column_map


def fill_hybrid_number_sort(x, y):
    if not x["hybrid"] and not y["hybrid"]:
        return x["fill_number"] - y["fill_number"]
    elif not x["hybrid"] and y["hybrid"]:
        return -1
    elif x["hybrid"] and not y["hybrid"]:
        return 1
    else:
        xh = x["hybrid"][0].strip()
        yh = y["hybrid"][0].strip()
        if xh < yh:
            return -1
        elif xh > yh:
            return 1
        else:
            return x["fill_number"] - y["fill_number"]


def group_to_hybrid(fills):
    groups = []
    group = []
    sfills = sorted(fills, key=cmp_to_key(fill_hybrid_number_sort))
    current_hybrid = -1
    for fill in sfills:
        hybrid = fill["hybrid"]
        if hybrid:
            hybrid = hybrid[0]
        if hybrid != current_hybrid:
            group = []
            current_hybrid = hybrid
            groups.append(group)
        group.append(fill)
    return groups


def get_total_avgs(keys, fills):
    total = {}
    avgs = {}
    for key in keys:
        total[key] = 0
        key_count = 0
        for fill in fills:
            if isinstance(fill[key], float) and not isinstance(total[key], float):
                total[key] = float(total[key]) + fill[key]
                key_count = key_count + 1
            elif fill[key] is not None and fill[key] != '':
                total[key] = total[key] + fill[key]
                key_count = key_count + 1
        if key_count > 0:
            avgs[key] = float(total[key]) / float(key_count)
        else:
            avgs[key] = 0
    return total, avgs


def fills_to_string(fills, form_s, display_tz, nbsp_none=False):
    for row in fills:
        for key in row.keys():
            if isinstance(row[key], str):
                continue
            elif row[key] is None:
                # if(formS == 'full'):
                #     row[key]='&#xA0;'
                # else:
                if nbsp_none:
                    row[key] = chr(160)
                else:
                    row[key] = ''
            elif isinstance(row[key], datetime):
                row[key] = util.datetimeToReadable(row[key], display_tz)
            elif isinstance(row[key], float):
                row[key] = "%.2f" % row[key]
            elif isinstance(row[key], int):
                row[key] = str(row[key])
        for key in ["hybrid", "field_name", "truck"]:
            if key in row:
                if row[key]:
                    if form_s == "full" or form_s == "tab":
                        row[key] = "<br/>".join(row[key])
                    else:
                        row[key] = ",".join(row[key])


def csv_fill(fills, general, fname, extra_column_map):
    ret = StringIO()
    csvw = csv.writer(ret)
    header = ['Bin #', 'Fill #', 'Fill Type', 'Rotation',
              'Hybrid(s)', 'Field(s)', 'Lot #', 'Truck(s)',
              'Filled time', 'Emptied time', 'Air begin time',
              'Air roll time', 'Air end time', 'Depth', 'Harvest H2O',
              'Sheller H2O', 'Pts H2O removed', 'Up air hrs',
              'Downair hrs', 'Total air hrs', '% up hrs',
              '% down hrs', 'hrs/point', 'bushels',
              'Storage code', 'Storage number']
    wetbulb = False
    if 'reports' in general['configs'] and 'avg_wetbulb' in general['configs']['reports'] and \
            general['configs']['reports']['avg_wetbulb']:
        wetbulb = True
        header.append('Wetbulb average')

    column_maps = []
    if extra_column_map:
        for key, value in extra_column_map.iteritems():
            column_maps.append([key, value])
            header.append(value)

    csvw.writerow(header)
    # Bin #, Fill #, Field, Harvest H20, Sheller H20, Pts H20 removed, up air hrs, down air hrs, total air hrs,
    # % up hrs, hrs/point, bushels.
    for fill in fills:
        ftype = 'Normal'
        # TODO: I'm dumb, why did I make them all strings?
        if fill['fill_type_id'] == '2':
            ftype = 'Bypass'
        row = [fill["bin_number"], fill["fill_number"], ftype, fill["rotation"],
               fill['hybrid'], fill["field_name"], fill['lot_number'], fill['truck'],
               fill['filled_datetime'], fill['emptied_datetime'], fill['air_begin_time'],
               fill['roll_time'], fill['air_end_time'], fill['depth'], fill["pre_avg"],
               fill["post_avg"], fill["mc_removed"], fill["up_time"],
               fill['down_time'], fill["air_total"], fill["up_percent"],
               fill['down_percent'], fill["hrs_per_point"], fill["bushels"],
               fill['storage_code'], fill['storage_number']]

        if wetbulb:
            row.append(fill['avg_wetbulb'])

        for c in column_maps:
            key = c[0]
            if key in fill:
                row.append(fill[key])
            else:
                row.append('')
        csvw.writerow(row)
    return flask.send_file(ret, mimetype='text/csv', as_attachment=True, attachment_filename=fname + '.csv')


@app.route('/resources/data/sheller_sensor_mc', methods=['GET'])
@authorized('User')
@noCache()
def sheller_sensor_mc_get():
    fill_id = int(request.values.get('fill_id'))
    ret = get_fill_sheller_sensor_mc(fill_id)
    ret['fill_id'] = fill_id
    return jsonify(fill_id)


def get_fill_sheller_sensor_mc(fill_id, conn=None):
    close_conn = False
    if not conn:
        conn = util.getConn()
        close_conn = True

    # We don't want to use subsample here

    # Get the fill
    fill = get_fill_by_id(fill_id, conn)
    # For each sheller_window
    cur = conn.cursor()
    sql_where = ""
    first = True
    sql_whereargs = []
    open_ended = False
    for sheller_window in fill['sheller_windows']:
        if not sheller_window['begin_datetime']:
            continue
        # Combine into one query to get min,max, and stddev

        # Find MC sensor_id using fill's year, bin, and bin_section
        cur.execute("""SELECT s.id FROM sensor s, device d WHERE
             s.sensor_type_id = %s AND s.device_id = d.id AND d.bin_id = %s AND
             d.bin_section_id = %s""", (READ_TYPE_MC, sheller_window['bin_id'], sheller_window['bin_section_id']))
        row = cur.fetchone()
        if not row:
            continue
        sensor_id = row[0]

        end_datetime = sheller_window['end_datetime']
        if not end_datetime:
            open_ended = True
            end_datetime = util.getDateFromParam('now')
        if not first:
            sql_where += " OR "
        first = False
        sql_where += " (sensor_id = %s AND value > 2.0 AND datetime >= %s AND datetime <= %s) "
        sql_whereargs.extend([sensor_id, sheller_window['begin_datetime'], end_datetime])

    if len(sql_whereargs) == 0:
        return {'avg': None, 'min': None, 'max': None, 'stddev': None, 'count': None, 'open_ended': open_ended}

    sql = "SELECT avg(value), min(value), max(value), stddev(value), count(value) FROM sensor_data WHERE " + \
          sql_where + " AND error_code IS NULL"
    logging.debug(sql + ' % ' + json.dumps(sql_whereargs, default=util.customJSONHandler))

    cur.execute(sql, sql_whereargs)
    row = cur.fetchone()
    if not row:
        return {'avg': None, 'min': None, 'max': None, 'stddev': None, 'count': None, 'open_ended': open_ended}

    ret = {'avg': row[0], 'min': row[1], 'max': row[2], 'stddev': row[3], 'count': row[4], 'open_ended': open_ended}
    cur.close()
    if close_conn:
        conn.close()
    return ret
