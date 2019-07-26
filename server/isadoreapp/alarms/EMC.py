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

import isadoreapp.util as util
import operator
import datetime
import logging
import numpy
from functools import reduce


def compute_max_temps_single(time, bin_id, conn=None):
    if not conn:
        conn = util.getConn()
    extra_where = ' bin_id = %s AND ' + \
                  '((air_begin_datetime <= %s AND air_end_datetime > %s) OR ' + \
                  '(air_begin_datetime <= %s AND air_end_datetime IS NULL)) '
    order_statement = ' ORDER BY air_begin_datetime DESC LIMIT 1'
    fills = util.getRowsFromTable("fill", extraWhere=extra_where, extraArgs=(bin_id, time, time, time),
                                  orderStatement=order_statement, conn=conn)
    if len(fills) == 0:
        return None
    fill = fills[0]
    (start_mc, lut_id) = get_fill_start_mc_lut_id(fill['id'], fill=fill, conn=conn)
    if start_mc is None and fill["pre_mc"]:
        start_mc = sum(fill["pre_mc"]) / len(fill["pre_mc"])
    if start_mc is None or lut_id is None:
        return None

    return compute_max_temps_db(fill['air_begin_datetime'], time, lut_id, start_mc, [time])[0]


# @param times array of times to calc max temp for, sorted asc
# @param binID the bin to calc maxtemps for
# @param conn database connection
def compute_max_temps_multi(times, bin_id, conn=None):
    if not conn:
        conn = util.getConn()
    start_datetime = times[0]
    end_datetime = times[len(times) - 1]
    extra_where = ' bin_id = %s AND ' + \
                  '((air_begin_datetime >= %s AND air_begin_datetime < %s) OR ' + \
                  '(air_begin_datetime <= %s AND air_end_datetime > %s) OR ' + \
                  '(air_begin_datetime < %s AND air_end_datetime IS NULL))'

    extra_args = (bin_id,
                  start_datetime, end_datetime,
                  start_datetime, start_datetime,
                  end_datetime)

    order_statement = ' ORDER BY air_begin_datetime '
    fills = util.getRowsFromTable("fill", extraWhere=extra_where, extraArgs=extra_args, orderStatement=order_statement,
                                  conn=conn)
    result = numpy.array([None] * len(times))
    start_times_idx = 0
    ntimes = numpy.array(times)
    for fill in fills:
        (start_mc, lut_id) = get_fill_start_mc_lut_id(fill['id'], fill=fill, conn=conn)
        if start_mc is None and fill["pre_mc"]:
            start_mc = sum(fill["pre_mc"]) / len(fill["pre_mc"])
        if start_mc is None or lut_id is None:
            continue

        filter_logic, s, lidx = filter_fill_times(fill, ntimes[start_times_idx:])
        ftimes = ntimes[start_times_idx:][filter_logic]
        if len(ftimes) > 0:
            result[start_times_idx + s:start_times_idx + lidx + 1] = compute_max_temps_db(fill['air_begin_datetime'],
                                                                                          ftimes[-1],
                                                                                          lut_id, start_mc, ftimes)
            start_times_idx = start_times_idx + lidx + 1
            if start_times_idx >= len(ntimes):
                break
    return result.tolist()


# @param startIdx index to start in times
# @param fill The fill object we are getting times for
# @param times array of times sorted asc
def filter_fill_times(fill, times):
    if not fill['air_end_datetime']:
        logic = times >= fill['air_begin_datetime']
    else:
        logic = numpy.logical_and(times >= fill['air_begin_datetime'], times < fill['air_end_datetime'])
    idxs = numpy.flatnonzero(logic)
    return logic, min(idxs), max(idxs)


def compute_max_temps_db(start_datetime, end_datetime, lut_id, start_mc, times, conn=None):
    if not conn:
        conn = util.getConn()
    cur = conn.cursor()
    cur.execute("SELECT begin_datetime, end_datetime FROM air_deduct WHERE " +
                "((begin_datetime >= %s AND begin_datetime <= %s) OR " +
                " (begin_datetime <= %s AND end_datetime IS NULL) OR " +
                "(begin_datetime <= %s AND end_datetime >= %s)) ",
                (start_datetime, end_datetime, start_datetime, start_datetime, start_datetime))
    deducts = cur.fetchall()

    cur.execute('SELECT hours_per_mc FROM mc_maxtemp_lut where id = %s', (lut_id,))
    row = cur.fetchone()
    if not row:
        return [None] * len(times)
    hours_per_mc = row[0]

    cur.execute('SELECT mc, maxtemp FROM mc_maxtemp_lut_value WHERE mc_maxtemp_lut_id = %s ORDER BY mc DESC', (lut_id,))
    lut = cur.fetchall()

    return compute_max_temps(start_mc, start_datetime, deducts, times, lut, hours_per_mc)


# @param fillId
# @return (startMC, mc_maxtemp_lut_id)
def get_fill_start_mc_lut_id(fill_id, fill=None, conn=None):
    if not conn:
        conn = util.getConn()
    cur = conn.cursor()
    if not fill:
        fill = util.getRowFromTableById('fill', fill_id, conn=conn)
    # Get start mc from transfer
    cur.execute(
        'SELECT avg(w.average_mc) FROM (SELECT DISTINCT ON (t.id) t.average_mc FROM \
        transfer t, transfer_field_fill tff \
        WHERE t.id = tff.transfer_id AND tff.to_id = %s ORDER BY t.id) as w', (fill['id'],))
    row = cur.fetchone()
    if not row:
        return None, None

    start_mc = row[0]

    lut_id = fill['mc_maxtemp_lut_id']
    if not lut_id:
        cur.execute('SELECT default_mc_maxtemp_lut_id FROM general_config LIMIT 1')
        row = cur.fetchone()
        lut_id = row[0]
    if not lut_id:
        return None, None
    return start_mc, lut_id


def compute_emc(start_mc, hrs_per_pt, air_time):
    # convert to dry time in seconds then compute EMC
    return start_mc - util.timedeltaToHours(air_time) / hrs_per_pt


def compute_air_time(start_time, end_time, deduct_times):
    # returns air time in seconds taking deduct times into account
    return end_time - start_time - reduce(operator.add, deduct_times)


def get_air_times(fill_id):
    fill_info = util.getRowFromTableById("fill", fill_id, checkEnabled=True)
    if fill_info["air_end_datetime"]:
        return fill_info["air_begin_datetime"], fill_info["air_end_datetime"]
    else:
        return fill_info["air_begin_datetime"], datetime.datetime.now()


# TODO: add settings to DB to control max and min temps/EMCs
def compute_max_temps(start_mc, start_time, deductions, times, lut, hrs_per_pt):
    # compute total air time using applicable deduct times
    ded = list(deductions)
    logging.debug("alarms.EMC.computeMaxTemps: startMC=" + str(start_mc) +
                  ", startTime=" + str(start_time) + ", len(deductions)=" + str(len(deductions)) +
                  ", len(times)=" + str(len(times)) + ", hrsPerPt=" + str(hrs_per_pt))
    sorted(ded, key=operator.itemgetter(1))
    return [compute_max_temp(lut, emc, hrs_per_pt)
            for emc in [compute_emc(start_mc,
                                    hrs_per_pt,
                                    compute_time(start_time, t, ded))
                        for t in times]]


def compute_max_temp(lut, emc, hrs_per_pt):
    mylist = [tr[1] for tr in lut if emc < tr[0]]
    if not mylist:
        return lut[1][1]
    else:
        return mylist[-1]


def compute_time(air_start_time, air_end_time, deductions):
    time = datetime.timedelta(0)
    last_time = air_start_time
    if not deductions:
        return air_end_time - air_start_time
    for dst, det in deductions:
        if dst <= last_time:
            if det is None or det >= air_end_time:
                # logging.debug("alarms.EMC.computeTime :"+str(time))
                return time
            elif det < last_time:
                continue
            else:
                last_time = det
        elif dst > last_time:
            if dst >= air_end_time:
                break
            elif dst < air_end_time:
                time = time + (dst - last_time)
                if det is not None and det < air_end_time:
                    last_time = det
                else:
                    return time
    time = time + (air_end_time - last_time)
    return time


def compute_deduct_time(air_start_time, air_end_time, deduct_start_time, deduct_end_time):
    deduct_time = deduct_end_time - deduct_start_time
    if air_start_time > deduct_start_time:
        deduct_time = deduct_time - (air_start_time - deduct_start_time)
    if air_end_time < deduct_end_time:
        deduct_time = deduct_time - (deduct_end_time - air_end_time)
    return deduct_time
