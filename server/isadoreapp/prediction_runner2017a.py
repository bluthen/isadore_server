#!/usr/bin/python2
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


import sys
import logging
import datetime
import math
import croniter
import time
from data import graph_data
import numpy
import json
import re

import mc_prediction2017a
import util
from alarm_watcher import Daemon

READ_TYPES = {'temp': 10, 'rh': 11, 'mcp': 200, 'dmcp': 201, 'abshum': 4, 'gpressure': 7}
MCP_SUBSECTION = 13
BIN_SECTION_IDS = {'top': 13, 'bottom': 14}

INSERT_ONLY_AFTER_ROLL = False

general = None
json_config = None
prediction_config = None


def setup():
    global general, json_config, prediction_config
    general = util.getRowFromTableById('general_config', 1)
    json_config = json.loads(general["configs"])
    prediction_config = json_config["prediction_runner2017a"]
    prediction_config['pressure_map'] = json_config['pressure_map']

    for pm in prediction_config['pressure_map']:
        pm['name_match'] = re.compile(pm['name_match'])


# Format for json
# {
#  "M_H": [4,4,2],
#  "model_file": "model_file.pyTorch",
#  "pressure_map":
#     [
#         {
#             "name_match": "regex_str",
#             "top":
#                    {
#                        "bin_id": int,
#                        "bin_section": int
#                    },
#             "bottom":
#                    {
#                        "bin_id": int,
#                        "bin_section": int
#                    }
#         },
#         ...
#     ]
# }


def get_airon_fills():
    fill_ids = util.getIdsFromTable("fill", extraWhere='''fill_type_id = 1 AND ( ((air_begin_datetime < NOW() AND
                air_end_datetime IS NULL) OR (air_begin_datetime < NOW() AND air_end_datetime > NOW())) )''')
    return fill_ids


def get_fills_for_year(year):
    fill_ids = util.getIdsFromTable("fill", extraWhere='''fill_type_id = 1 AND 
        extract(YEAR FROM air_begin_datetime) = %s''', extraArgs=(year,))
    return fill_ids


def get_inlet_outlet_abshum_gpressure(bin, begin_datetime, end_datetime):
    ptop_data = None
    pbottom_data = None
    data = graph_data.graph_data_struct(bin['id'],
                                        [
                                            ['sensor', [BIN_SECTION_IDS['top'], READ_TYPES['abshum']]],
                                            ['sensor', [BIN_SECTION_IDS['bottom'], READ_TYPES['abshum']]],
                                            ['sensor', [BIN_SECTION_IDS['top'], READ_TYPES['temp']]],
                                            ['sensor', [BIN_SECTION_IDS['bottom'], READ_TYPES['temp']]]
                                        ],
                                        15, begin_datetime, end_datetime)
    for pm in prediction_config['pressure_map']:
        if pm['name_match'].match(bin['name']):
            ptop_data = graph_data.graph_data_struct(pm['top']['bin_id'],
                                                     [
                                                         ['sensor',
                                                          [pm['top']['bin_section'], READ_TYPES['gpressure']]]
                                                     ],
                                                     15, begin_datetime, end_datetime)
            pbottom_data = graph_data.graph_data_struct(pm['bottom']['bin_id'],
                                                        [
                                                            ['sensor',
                                                             [pm['bottom']['bin_section'], READ_TYPES['gpressure']]]
                                                        ],
                                                        15, begin_datetime, end_datetime)
            break
    # logging.debug("XXXXX bin_data_len: %d" % (len(data),))
    # logging.debug("XXXXX ptop_len: %d" % (len(ptop_data),))
    # logging.debug("XXXXX pbot_len: %d" % (len(pbottom_data),))

    return {'bin_data': data, 'pressure': {'top': ptop_data, 'bottom': pbottom_data}}


def next_not_none(ourlist, start_idx):
    for i in xrange(start_idx, len(ourlist)):
        # If we need can add check for bad values here.
        if ourlist[i] is not None:
            return i
    return -1


def interpolate(best_previous, newdata, key, i, replace):
    """

    :param best_previous:
    :param newdata:
    :param key:
    :param i:
    :param replace:
    :return: True if successfully interpolated, false then there is no end data to interpolate against.
    """
    td15 = datetime.timedelta(minutes=15)
    p = 0
    if replace:
        p = 1
    idx = next_not_none(newdata[key], i + p)
    if idx < 0:
        # No more good data we are all done
        return False
    # Interpolation
    m = (newdata[key][idx] - best_previous[key]) / \
        ((newdata['datetime'][idx] - best_previous['datetime']).total_seconds())
    v = m * td15.total_seconds() + best_previous[key]
    if replace:
        newdata[key][i] = v
    else:
        newdata[key].insert(i, v)

    return True


def restructure_data(data):
    dataz = zip(*(data['bin_data']))
    newdata = {'datetime': list(dataz[0]),
               'top_abshum': list(zip(*dataz[1])[1]),
               'bottom_abshum': list(zip(*dataz[2])[1]),
               'top_temp': list(zip(*dataz[3])[1]),
               'bottom_temp': list(zip(*dataz[4])[1])
               }
    del dataz

    dataz = zip(*(data['pressure']['top']))
    newdata['top_gpressure'] = list(zip(*dataz[1])[1])
    del dataz

    dataz = zip(*(data['pressure']['bottom']))
    newdata['bottom_gpressure'] = list(zip(*dataz[1])[1])
    del dataz

    return newdata


def cut_to_alldata(newdata):
    '''
    Cuts the data to a point where at least all the needed data exists at the same time.
    :param newdata:
    :return:
    '''
    keys = newdata.keys()
    keys.remove('datetime')
    akeys=['datetime']
    akeys.extend(keys)
    # set first best_previous, cut new data till our first where all exist.
    found = False
    for i in xrange(len(newdata['datetime'])):
        if all(list(map(lambda x: newdata[x][i], keys))):
            for key in akeys:
                newdata[key] = newdata[key][i:]
            found = True
            break

    if not found or len(newdata['datetime']) == 0:
        # We have no good data at all
        raise Exception('No good data.')


def repair_data(newdata):
    """
    :param data: Data from get_inlet_outlet_gpressure_temp
    :return: Data reformatted with gaps interpolated. All arrays in return are same length.
    :rtype: {'datetime': 1d array of datetimes, 'inlet_abshum': 1d array floats,
        'outlet_abshum': 1d array floats, 'inlet_gpressure': 1d array floats, 'outlet_gpressure': 1d array floats}
    """
    # Finds missing time gaps and interpolates them.

    keys = newdata.keys()
    keys.remove('datetime')
    akeys=['datetime']
    akeys.extend(keys)
    td15 = datetime.timedelta(minutes=15)

    cut_to_alldata(newdata)

    # We know at least the first index is good from our previous cut.
    best_previous = {}
    for key in akeys:
        best_previous[key] = newdata[key][0]

    i = 1
    # We might add to newdata so check everytime
    while i < len(newdata['datetime']):
        previous_dt = best_previous['datetime']
        e_dt = (previous_dt + td15) - newdata['datetime'][i]
        if e_dt.total_seconds() < -60.0:
            # We are missing a subsample interpolate all and insert into newdata
            interpolated = True
            for key in keys:
                interpolated = interpolate(best_previous, newdata, key, i, False)
                if not interpolated:
                    break
            if not interpolated:
                for key in akeys:
                    newdata[key] = newdata[key][0:i]
                break
            newdata['datetime'].insert(i, previous_dt + td15)
        interpolated = True
        for key in keys:
            # If we need can add check for bad values here.
            if not newdata[key][i]:
                interpolated = interpolate(best_previous, newdata, key, i, True)
                if not interpolated:
                    break
        if not interpolated:
            for key in akeys:
                newdata[key] = newdata[key][0:i]
            break
        # Set our new best previous
        for key in akeys:
            best_previous[key] = newdata[key][i]
        i += 1


def diff_data(newdata):
    keys = newdata.keys()
    keys.remove('datetime')
    akeys=['datetime']
    akeys.extend(keys)

    # Now lets make the data we really want
    for key in akeys:
        newdata[key] = numpy.array(newdata[key])
    upair = numpy.array(newdata['top_temp']) < numpy.array(newdata['bottom_temp'])
    newdata['diff_abshum'] = (newdata['top_abshum'] - newdata['bottom_abshum']) * upair
    newdata['diff_abshum'] += (newdata['bottom_abshum'] - newdata['top_abshum']) * numpy.logical_not(upair)
    newdata['diff_gpressure'] = newdata['bottom_gpressure'] * upair
    newdata['diff_gpressure'] += (newdata['top_gpressure'] - newdata['bottom_gpressure']) * numpy.logical_not(upair)
    # Delete original data
    for key in keys:
        del newdata[key]

    return newdata


def none_data_around_rolls(roll_datetimes, data):
    td1h = datetime.timedelta(hours=1)
    for rolldt in roll_datetimes:

        for i in xrange(len(data['datetime']) - 1, -1, -1):
            if data['datetime'][i] >= (rolldt - td1h) and data['datetime'][i] <= (rolldt + td1h):
                for key in data.keys():
                    if key == 'datetime':
                        continue
                    data[key][i] = None
    return data


def upsert_reading_data_subsamples(fill, data, mcs, dmcs):
    conn = util.getConn()
    cur = conn.cursor()
    # TODO: Is this too slow?
    try:
        dt15 = datetime.timedelta(minutes=15)
        sql = '''DELETE FROM reading_data_subsample rds WHERE
        rds.bin_id = %s AND rds.read_type_id = %s AND rds.reading_subsample_id IN
        (SELECT id from reading_subsample rs where rs.datetime >= %s AND rs.datetime <= %s)'''
        cur.execute(sql, (fill['bin_id'], READ_TYPES['mcp'], data['datetime'][0] - dt15, data['datetime'][-1] + dt15))
        cur.execute(sql, (fill['bin_id'], READ_TYPES['dmcp'], data['datetime'][0] - dt15, data['datetime'][-1] + dt15))
        dt5 = datetime.timedelta(minutes=5)
        for i in xrange(len(data['datetime'])):
            sql = '''SELECT update_reading_data_subsample(%s, %s, %s, %s, %s);'''
            cur.execute(sql, (data['datetime'][i], fill['bin_id'], MCP_SUBSECTION, READ_TYPES['mcp'], mcs[i]))
            cur.execute(sql, (data['datetime'][i], fill['bin_id'], MCP_SUBSECTION, READ_TYPES['dmcp'], dmcs[i]))
            if i != len(data['datetime']) - 1:
                cur.execute(sql, (data['datetime'][i] - dt5, fill['bin_id'], MCP_SUBSECTION, READ_TYPES['mcp'], mcs[i]))
                cur.execute(sql, (data['datetime'][i] + dt5, fill['bin_id'], MCP_SUBSECTION, READ_TYPES['mcp'], mcs[i]))
                cur.execute(sql, (data['datetime'][i] - dt5, fill['bin_id'], MCP_SUBSECTION, READ_TYPES['dmcp'],
                                  dmcs[i]))
                cur.execute(sql, (data['datetime'][i] + dt5, fill['bin_id'], MCP_SUBSECTION, READ_TYPES['dmcp'],
                                  dmcs[i]))

        conn.commit()
        cur.close()
        conn.close()
        cur = None
        conn = None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.rollback()
            conn.close()


def update_last_mc_predictions(bin_id, mc, dt, dmc):
    conn = util.getConn()
    cur = conn.cursor()
    sql = '''DELETE FROM reading_data_latest WHERE bin_id = %s and bin_section_id = %s and read_type_id = %s'''
    cur.execute(sql, (bin_id, MCP_SUBSECTION, READ_TYPES['mcp']))
    cur.execute(sql, (bin_id, MCP_SUBSECTION, READ_TYPES['dmcp']))
    sql = '''INSERT INTO reading_data_latest (datetime, bin_id, bin_section_id, read_type_id, value) VALUES 
        (%s, %s, %s, %s, %s)'''
    cur.execute(sql, (dt, bin_id, MCP_SUBSECTION, READ_TYPES['mcp'], mc))
    cur.execute(sql, (dt, bin_id, MCP_SUBSECTION, READ_TYPES['dmcp'], dmc))

    conn.commit()
    cur.close()
    conn.close()


def initial_mc(fill):
    avg_mc = 0.0
    for v in fill['pre_mc']:
        avg_mc += v
    avg_mc = avg_mc / len(fill['pre_mc'])
    return avg_mc


def make_diff(a, b):
    return (numpy.array(b) - numpy.array(a)).tolist()


def d_mcs(mcs):
    a = numpy.diff(numpy.array(mcs))
    return (4.0*numpy.insert(a, 0, a[0])).tolist()


def prediction_calculation_for_fill(fill_id):
    logging.debug('Doing mc predictions for fill_id=%d' % (fill_id,))
    # Get the fill
    fill = util.getRowFromTableById("fill", fill_id)
    if INSERT_ONLY_AFTER_ROLL and not fill['roll_datetime']:
        logging.debug('Skipping fill_id=%d no roll.' % (fill_id,))
        return
    if not fill['pre_mc']:
        logging.debug('Skipping fill_id=%d no pre_mc' % (fill_id,))
        return
    if not fill['depth']:
        logging.debug('Skipping fill_id=%d no depth' % (fill_id,))
        return
    bin = util.getRowFromTableById('bin', fill['bin_id'])
    # Get the correct start and end dates
    endtime = util.getDateFromParam('now')
    if fill['air_end_datetime']:
        endtime = fill['air_end_datetime']
    if not fill['air_begin_datetime']:
        logging.error('fill_id=%d has no air_begin_datetime.' % (fill_id,))
        return
    # Fetch inlet/outlet temp/rh data for each airon fill
    data = get_inlet_outlet_abshum_gpressure(bin, fill['air_begin_datetime'], endtime)
    data = restructure_data(data)
    # Set values around roll to None, then repair_and_format_data will interpolate them
    if fill['roll_datetime']:
        data = none_data_around_rolls(fill['roll_datetime'], data)
    # Repair data and format data
    data = repair_data(data)
    if not data:
        return
    diff_data(data)
    imc = initial_mc(fill)
    # logging.debug(data)
    for key in data:
        logging.debug("key: %s - %d" % (key, len(data[key]),))
    # logging.debug(fill['depth'])
    # logging.debug(imc)
    mcs = mc_prediction2017a.MC_predict_beta2017(prediction_config["model_file"], prediction_config["M_H"],
                                                 data['diff_gpressure'], data['diff_abshum'],
                                                 fill['depth'], imc)
    mcs = list(map(lambda x: x[0], mcs))
    dmcs = d_mcs(mcs)
    # logging.debug(mcs)
    # upsert reading_data_subsamples
    upsert_reading_data_subsamples(fill, data, mcs, dmcs)
    # Store last value in special table table
    # TODO: This should be in calling function, so you can calculate for older fill if want.
    if fill_id in get_airon_fills():
        update_last_mc_predictions(fill['bin_id'], mcs[-1], data['datetime'][-1], dmcs[-1])


def prediction_calculation_for_airon_fills():
    logging.debug('prediction_calculation_for_airon_fills() started.')
    # Fetch all airon fills
    fill_ids = get_airon_fills()
    for fill_id in fill_ids:
        try:
            prediction_calculation_for_fill(fill_id)
        except:
            logging.exception("prediction_calculation for fill=%d failed." % (fill_id,))


def prediction_calculation_for_fills_in_year(year):
    logging.debug('prediction_calculation_for_fills_in_year() started.')
    # Fetch all airon fills
    fill_ids = get_airon_fills()
    for fill_id in fill_ids:
        try:
            prediction_calculation_for_fill(fill_id)
        except:
            logging.exception("prediction_calculation for fill=%d failed." % (fill_id,))


def reading_data_filler(now):
    logging.debug('reading_data_filler() started.')
    fill_ids = get_airon_fills()
    conn = util.getConn()
    cur = conn.cursor()
    for fill_id in fill_ids:
        fill = util.getRowFromTableById("fill", fill_id)
        if INSERT_ONLY_AFTER_ROLL and not fill['roll_datetime']:
            logging.debug('Skipping fill_id=%d no roll.' % (fill_id,))
            continue
        if not fill['pre_mc']:
            logging.debug('Skipping fill_id=%d no pre_mc' % (fill_id,))
            continue
        if not fill['depth']:
            logging.debug('Skipping fill_id=%d has no depth' % (fill_id,))
            continue

        # Get last data from last_mc_prediction table
        for read_type_id in [READ_TYPES['mcp'], READ_TYPES['dmcp']]:
            cur.execute("SELECT value FROM reading_data_latest WHERE bin_id = %s AND read_type_id = %s", (fill['bin_id'], read_type_id))
            row = cur.fetchone()
            if row:
                # Insert into reading_data_subsamples
                value = row[0]
                sql = '''SELECT update_reading_data_subsample(%s, %s, %s, %s, %s);'''
                cur.execute(sql, (now, fill['bin_id'], MCP_SUBSECTION, READ_TYPES['mcp'], value))
        conn.commit()
    cur.close()
    conn.close()


class PredictionRunner(Daemon):
    def run(self):
        setup()
        logging.basicConfig(filename='./prediction_runner2017a.log', level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s')
        first_run = True
        dtiter = None
        while True:
            try:
                # Two types of runs prediction_calculation, and reading_data_filler
                # prediction_calculation done at clock time: 0, 15, 30, 45
                # reading_data_filler done at 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55
                # When both times are the same, prediction_calculation is done first.

                # If first_run we run no matter what time it is.

                now = util.getDateFromParam('now')
                tdnow = now - now.replace(hour=0, minute=0, second=0, microsecond=0)
                fifteens = math.modf(((tdnow.seconds / 60.0) % 60.0) / 15.0)[0] * 15.0

                if first_run or fifteens < 2.0 or fifteens > 13.0:
                    prediction_calculation_for_airon_fills()
                # else:
                #    reading_data_filler(now)

                if first_run:
                    logging.debug('IS FIRST RUN')
                    first_run = False
                    dtiter = croniter.croniter('*/5 * * * *', now)

                # Sleep until next 5 min interval
                crondt = dtiter.get_next(datetime.datetime)
                cronchecktd = crondt - util.getDateFromParam('now')
                # TODO: Or should we just quickly update even if took longer than 5 minutes?
                while cronchecktd.total_seconds() < 0:
                    logging.warn('Next cron is in the past, process takes longer than 5 minutes')
                    crondt = dtiter.get_next(datetime.datetime)
                    cronchecktd = crondt - util.getDateFromParam('now')
                logging.debug('Sleeping %d' % (cronchecktd.total_seconds(),))
                time.sleep(cronchecktd.total_seconds())
            except:
                logging.exception("Got exception in daemon loop.")
                time.sleep(5 * 60)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        daemon = PredictionRunner('prediction_runner2017a.pid')
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
