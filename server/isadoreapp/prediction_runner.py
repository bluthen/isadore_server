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

import mc_prediction
import util
from alarm_watcher import Daemon

READ_TYPES = {'temp': 10, 'rh': 11, 'mcp': 200}
MCP_SUBSECTION = 13

INSERT_ONLY_AFTER_ROLL = True


def get_airon_fills():
    fill_ids = util.getIdsFromTable("fill", extraWhere='''fill_type_id = 1 AND ( ((air_begin_datetime < NOW() AND
                air_end_datetime IS NULL) OR (air_begin_datetime < NOW() AND air_end_datetime > NOW())) )''')
    return fill_ids


def get_inlet_outlet_rh_temp(bin_id, begin_datetime, end_datetime):
    data = graph_data.graph_data_struct(bin_id, [['inlet', [READ_TYPES['temp']]], ['outlet', [READ_TYPES['temp']]],
                                                 ['inlet', [READ_TYPES['rh']]], ['outlet', [READ_TYPES['rh']]]], 15,
                                        begin_datetime, end_datetime)
    return data


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


def repair_and_format_data(data):
    """
    :param data: Data from get_inlet_outlet_rh_temp
    :return: Data reformatted with gaps interpolated. All arrays in return are same length.
    :rtype: {'datetime': 1d array of datetimes, 'inlet_temp': 1d array floats,
        'outlet_temp': 1d array floats, 'inlet_rh': 1d array floats, 'outlet_rh': 1d array floats}
    """
    # Finds missing time gaps and interpolates them.
    dataz = zip(*data)
    newdata = {'datetime': list(dataz[0]), 'inlet_temp': list(zip(*dataz[1])[1]),
               'outlet_temp': list(zip(*dataz[2])[1]), 'inlet_rh': list(zip(*dataz[3])[1]),
               'outlet_rh': list(zip(*dataz[4])[1])}
    del dataz
    td15 = datetime.timedelta(minutes=15)

    # set first best_previous, cut new data till our first where all exist.
    found = False
    for i in xrange(len(newdata['datetime'])):
        if newdata['inlet_temp'][i] and newdata['outlet_temp'][i] and newdata['inlet_rh'][i] and \
                newdata['outlet_rh'][i]:
            newdata['datetime'] = newdata['datetime'][i:]
            newdata['inlet_temp'] = newdata['inlet_temp'][i:]
            newdata['outlet_temp'] = newdata['outlet_temp'][i:]
            newdata['inlet_rh'] = newdata['inlet_rh'][i:]
            newdata['outlet_rh'] = newdata['outlet_rh'][i:]
            found = True
            break

    if not found or len(newdata['datetime']) == 0:
        # We have no good data at all
        logging.error('No good data.')
        return None

    best_previous = {'datetime': newdata['datetime'][0], 'inlet_temp': newdata['inlet_temp'][0],
                     'outlet_temp': newdata['outlet_temp'][0],
                     'inlet_rh': newdata['inlet_rh'][0], 'outlet_rh': newdata['outlet_rh'][0]}

    i = 1
    # We might add to newdata so check everytime
    while i < len(newdata['datetime']):
        previous_dt = best_previous['datetime']
        if ((previous_dt + td15) - newdata['datetime'][i]).total_seconds() > 60.0:
            # We are missing a subsample interpolate all and insert into newdata
            interpolated = True
            for key in ['inlet_temp', 'outlet_temp', 'inlet_rh', 'outlet_rh']:
                interpolated = interpolate(best_previous, newdata, key, i, False)
                if not interpolated:
                    break
            if not interpolated:
                newdata['datetime'] = newdata['datetime'][0:i]
                newdata['inlet_temp'] = newdata['inlet_temp'][0:i]
                newdata['outlet_temp'] = newdata['outlet_temp'][0:i]
                newdata['inlet_rh'] = newdata['inlet_rh'][0:i]
                newdata['outlet_rh'] = newdata['outlet_rh'][0:i]
                break
            newdata['datetime'].insert(i, previous_dt + td15)
        interpolated = True
        for key in ['inlet_temp', 'outlet_temp', 'inlet_rh', 'outlet_rh']:
            # If we need can add check for bad values here.
            if not newdata[key][i]:
                interpolated = interpolate(best_previous, newdata, key, i, True)
                if not interpolated:
                    break
        if not interpolated:
            newdata['datetime'] = newdata['datetime'][0:i]
            newdata['inlet_temp'] = newdata['inlet_temp'][0:i]
            newdata['outlet_temp'] = newdata['outlet_temp'][0:i]
            newdata['inlet_rh'] = newdata['inlet_rh'][0:i]
            newdata['outlet_rh'] = newdata['outlet_rh'][0:i]
            break
        # Set our new best previous
        best_previous = {'datetime': newdata['datetime'][i], 'inlet_temp': newdata['inlet_temp'][i],
                         'outlet_temp': newdata['outlet_temp'][i],
                         'inlet_rh': newdata['inlet_rh'][i], 'outlet_rh': newdata['outlet_rh'][i]}
        i += 1

    return newdata


def none_data_around_rolls(roll_datetimes, data):
    td1h = datetime.timedelta(hours=1)
    for rolldt in roll_datetimes:
        for i in xrange(len(data)-1, -1, -1):
            if (rolldt-td1h) <= data[i][0] <= (rolldt + td1h):
                for j in [1, 2, 3, 4]:
                    data[i][j] = [None, None, None]
    return data


def upsert_reading_data_subsamples(fill, data, mcs):
    conn = util.getConn()
    cur = conn.cursor()
    # TODO: Is this too slow?
    try:
        sql = '''DELETE FROM reading_data_subsample rds WHERE
        rds.bin_id = %s AND rds.read_type_id = %s AND rds.reading_subsample_id IN
        (SELECT id from reading_subsample rs where rs.datetime >= %s AND rs.datetime <= %s)'''
        cur.execute(sql, (fill['bin_id'], READ_TYPES['mcp'], data['datetime'][0], data['datetime'][-1]))
        dt5 = datetime.timedelta(minutes=5)
        for i in xrange(len(data['datetime'])):
            sql = '''SELECT update_reading_data_subsample(%s, %s, %s, %s, %s);'''
            cur.execute(sql, (data['datetime'][i], fill['bin_id'], MCP_SUBSECTION, READ_TYPES['mcp'], mcs[i]))
            if i != len(data['datetime'])-1:
                cur.execute(sql, (data['datetime'][i]-dt5, fill['bin_id'], MCP_SUBSECTION, READ_TYPES['mcp'], mcs[i]))
                cur.execute(sql, (data['datetime'][i]+dt5, fill['bin_id'], MCP_SUBSECTION, READ_TYPES['mcp'], mcs[i]))

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


def update_last_mc_predictions(bin_id, mc):
    conn = util.getConn()
    cur = conn.cursor()
    sql = '''DELETE FROM last_mc_prediction WHERE bin_id = %s'''
    cur.execute(sql, (bin_id,))
    sql = '''INSERT INTO last_mc_prediction (bin_id, value) VALUES (%s, %s)'''
    cur.execute(sql, (bin_id, mc))
    conn.commit()
    cur.close()
    conn.close()


def initial_mc(fill):
    avg_mc = 0.0
    for v in fill['pre_mc']:
        avg_mc += v
    avg_mc = avg_mc/len(fill['pre_mc'])
    return avg_mc


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
    # Get the correct start and end dates
    endtime = util.getDateFromParam('now')
    if fill['air_end_datetime']:
        endtime = fill['air_end_datetime']
    if not fill['air_begin_datetime']:
        logging.error('fill_id=%d has no air_begin_datetime.' % (fill_id,))
        return
    # Fetch inlet/outlet temp/rh data for each airon fill
    data = get_inlet_outlet_rh_temp(fill['bin_id'], fill['air_begin_datetime'], endtime)
    # Set values around roll to None, then repair_and_format_data will interpolate them
    if fill['roll_datetime']:
        data = none_data_around_rolls(fill['roll_datetime'], data)
    # Repair data and format data
    data = repair_and_format_data(data)
    if not data:
        return
    imc = initial_mc(fill)
    mcs = mc_prediction.calculate_ESN_inTRH_regWithAssumption(data['inlet_temp'], data['outlet_temp'], data['inlet_rh'],
                                            data['outlet_rh'], imc)
    # upsert reading_data_subsamples
    upsert_reading_data_subsamples(fill, data, mcs)
    # Store last value in special table table
    # TODO: This should be in calling function, so you can calculate for older fill if want.
    update_last_mc_predictions(fill['bin_id'], mcs[-1])


def prediction_calculation_for_airon_fills():
    logging.debug('prediction_calculation_for_airon_fills() started.')
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

        # Get last data from last_mc_prediction table
        cur.execute("SELECT value FROM last_mc_prediction WHERE bin_id = %s", (fill['bin_id'],))
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
        logging.basicConfig(filename='./prediction_runner.log', level=logging.DEBUG,
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
                else:
                    reading_data_filler(now)

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
                time.sleep(5*60)


if __name__ == "__main__":
    daemon = PredictionRunner('prediction_runner.pid')
    if len(sys.argv) == 2:
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
