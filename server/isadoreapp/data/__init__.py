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
import flask
from flask import request, abort
from isadoreapp.authentication import authorized
import isadoreapp.util as util
import time
import random
import zipfile
import datetime
import os
import logging

DEFAULT_SAMPLE_PERIOD = 5


# noinspection PyListCreation,PyUnusedLocal
@app.route('/resources/data/csv_download', methods=["GET"])
@authorized('User')
def cvs_download():
    begin_datetime = util.getDateFromParam(request.values.get('begin_datetime'))
    end_datetime = util.getDateFromParam(request.values.get('end_datetime'))
    bin_ids = request.values.get("bin_ids")
    bin_section_ids = request.values.get("bin_section_ids")
    read_type_ids = request.values.get("read_type_ids")

    if not begin_datetime or not end_datetime:
        abort(400, "Begin and end datetime's required.")

    if not bin_ids:
        abort(400, "bin_ids is required.")

    if not bin_section_ids:
        abort(400, "bin_section_ids is required.")

    if not read_type_ids:
        abort(400, "read_type_ids is required.")

    bin_ids = bin_ids.split(",")
    bin_section_ids = bin_section_ids.split(",")
    read_type_ids = read_type_ids.split(",")

    sql = ["SELECT '\"'||to_char(timezone('UTC', r.datetime), 'MM/DD/YYYY HH24:MI:SS')||' UTC\",\"'||b.name||\
        '\",\"'||bs.name||'\",\"'||rt.name||'\",'||rd.avg_value "]
    sql.append("FROM reading_data_subsample rd, reading_subsample r, bin b, bin_section bs, read_type rt WHERE \
r.datetime >= %s AND r.datetime <= %s AND rd.reading_subsample_id = r.id AND r.sample_period = %s AND (")
    # noinspection PyUnusedLocal
    for bin_id in bin_ids:
        sql.append("rd.bin_id = %s")
        sql.append(" OR ")
    sql.pop()
    sql.append(") AND (")
    for bin_section_id in bin_section_ids:
        sql.append("rd.bin_section_id = %s")
        sql.append(" OR ")
    sql.pop()
    sql.append(") AND (")
    for read_type_id in read_type_ids:
        sql.append("rd.read_type_id = %s")
        sql.append(" OR ")
    sql.pop()
    sql.append(") ")
    sql.append("AND b.id = rd.bin_id \
AND bs.id = rd.bin_section_id \
AND rt.id = rd.read_type_id ORDER BY b.name, bs.name, rt.name, r.datetime")

    tstamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "csv_" + str(time.time()) + "_" + str(random.random()) + ".zip"
    filename2 = "csv_" + tstamp + str(random.random()) + ".csv"

    conn = util.getConn()
    cur = conn.cursor(filename)
    parameters = [begin_datetime, end_datetime, 5]
    parameters.extend(bin_ids)
    parameters.extend(bin_section_ids)
    parameters.extend(read_type_ids)
    logging.debug("".join(sql))
    cur.execute("".join(sql), tuple(parameters))

    with open("./gen_data/" + filename2, 'w') as f:
        f.write('"datetime","bin","bin section","sensor","value"')
        f.write("\n")
        for row in cur:
            if row[0] is not None:
                f.write(row[0])
                f.write("\n")

    with zipfile.ZipFile("./gen_data/" + filename, 'w') as myzip:
        myzip.write("./gen_data/" + filename2, 'csv_' + tstamp + ".csv")
    os.remove("./gen_data/" + filename2)

    f.close()
    return flask.send_from_directory('./gen_data', filename, attachment_filename='csvdata' + tstamp + '.zip')
