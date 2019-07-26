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

import psycopg2.extras as dbapi2extras
from isadoreapp import app
from flask import abort, request, jsonify
from isadoreapp.authentication import midauthorized
from functools import reduce
import isadoreapp.util as util
import datetime
import json

SENSOR_UNIT_ID = 10
TACH_UNIT_ID = 13

BURNER_DEVICE_IDS = (11, 12, 16, 17, 18, 19)
VFD_DEVICE_IDS = (14, 15)  # TODO: remove 14
AB_P700_DEVICE_ID = 14

TEMP_ID = 10
HUM_ID = 11
ANEMOMETER_ID = 12
PRESSURE_ID = 14
PV_ID = 20
SP_ID = 21
TACH_ID = 40
TC_A_ID = 41
TC_B_ID = 42
MULTI_PT_T_ID = 15
VFD_RPM_ID = 50
VFD_AMPS_ID = 51
VFD_TACH_FB_ID = 52
DMMC_ID = 300
RTM2000_ID = 400  # SENSOR_TYPE_ID

MAX_NUM_BINS = 400

CURRENT_YEAR = datetime.datetime.now().year


@app.route('/resources/MID', methods=["GET"])
@midauthorized()
def mid_config():
    mid_name = request.values.get("mid_name", None)

    # fill in stuff from general_config table
    row = util.getRowFromTableById("general_config", 1, columns="interval,mid_pass,enabled_p")
    cfg = {
        "queryInterval": row["interval"],
        "midPass": row["mid_pass"],
        "enabled_p": row["enabled_p"],
        "commandInfo": [],
        "RC": []
    }

    # add devices to config
    cfg["commandInfo"] += buildAllTempRHJSON(mid_name)
    cfg["commandInfo"] += buildAllPressureJSON(mid_name)
    cfg["commandInfo"] += buildAllTCJSON(mid_name)
    cfg["commandInfo"] += buildAllAnemometerJSON(mid_name)
    cfg["commandInfo"] += buildAllDMMCJSON(mid_name)
    cfg["commandInfo"] += buildAllRTM2000JSON(mid_name)
    cfg["commandInfo"] += buildAllTachJSON(mid_name)
    cfg["commandInfo"] += buildAllMultPtJSON(mid_name)

    cfg["burnerControls"] = buildAllBurnerControlsJSON(mid_name)
    cfg["AB_VFD_special"] = buildAllAB_VFD_specialJSON(mid_name)

    cfg["RC"] += addRemoteControlsToConfig(mid_name)

    # TODO: was here to create backup display. remove?
    # add bin and bin section metadata to config
    # addBinNamesToConfig(cfg)
    # addBinSectionNamesToConfig(cfg)

    # note that the configs have been successfully deployed
    # util.updateRowById("general_config",1,{"deployed_p":True})

    # return this goofy data structure
    return jsonify(cfg)


def getSensorAndDeviceInfo(conn, year, sensor_type_id, mid_name=None, device_id=None):
    sql = """SELECT s.id as sensor_id, s.convert_py, s.bias,
    d.mid_name, d.port, d.address, d.bin_id, d.bin_section_id, s.extra_info, d.id as device_id, d.name as device_name
    FROM sensor s, device d
    WHERE d.port >= 0 AND d.year = %s AND s.device_id = d.id AND s.enabled_p AND s.sensor_type_id = %s """
    sql_params = [year, sensor_type_id]
    if mid_name:
        sql += " AND d.mid_name = %s"
        sql_params.append(mid_name)
    if device_id:
        sql += " AND d.id = %s"
        sql_params.append(device_id)
    cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
    cur.execute(sql, sql_params)
    results = []
    for row in cur:
        result_row = {}
        for key in row.keys():
            result_row[key] = row[key]
        results.append(result_row)
    cur.close()
    return results


def getSensorAndDeviceInfo2(conn, year, sensor_type_id, sensor_type_id2, mid_name=None, device_id=None):
    a = getSensorAndDeviceInfo(conn, year, sensor_type_id, mid_name, device_id)
    b = getSensorAndDeviceInfo(conn, year, sensor_type_id2, mid_name, device_id)
    for i in range(len(a) - 1, -1, -1):
        av = a[i]
        av['sensor_id2'] = None
        av['convert_py2'] = None
        av['bias2'] = None
        for j in range(len(b) - 1, -1, -1):
            bv = b[j]
            if av["device_id"] == bv["device_id"]:
                av['sensor_id2'] = bv['sensor_id']
                av['convert_py2'] = bv['convert_py']
                av['bias2'] = bv['bias']
                del b[j]
    for bv in b:
        bv.update({
            'sensor_id2': bv['sensor_id'],
            'convert_py2': bv['convert_py'],
            'bias2': bv['bias'],
            'sensor_id': None,
            'convert_py': None,
            'bias': None,
        })
        a.append(bv)
    return a


def buildAllDMMCJSON(mid_name):
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo(conn, CURRENT_YEAR, DMMC_ID, mid_name)
    for tr in rows:
        ret_val += [{"type": "dm_mc", "device_type": "dm",
                     "sensor_id": tr["sensor_id"],
                     "addy": tr["address"], "port": tr["port"],
                     "convert": tr["convert_py"], "bias": tr["bias"],
                     "sensor_extra_info": tr["extra_info"],
                     "mid_name": tr["mid_name"],
                     "bin_id": tr["bin_id"], "bin_sec_id": tr["bin_section_id"]}]
    return ret_val


def buildAllRTM2000JSON(mid_name):
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo(conn, CURRENT_YEAR, RTM2000_ID, mid_name)
    for tr in rows:
        ret_val += [{"type": "rtm2000", "device_type": "rtm2000",
                     "sensor_id": tr["sensor_id"],
                     "addy": tr["address"], "port": tr["port"],
                     "convert": tr["convert_py"], "bias": tr["bias"],
                     "sensor_extra_info": tr["extra_info"],
                     "mid_name": tr["mid_name"], "device_name": tr["device_name"],
                     "bin_id": tr["bin_id"], "bin_sec_id": tr["bin_section_id"]}]
    return ret_val


def buildAllTempRHJSON(mid_name):
    # NOTE: assumes there is only one enabled RH sensor per device
    # TODO: log an error if multiple rh rows are returned
    # TODO: exception handling!
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo2(conn, CURRENT_YEAR, TEMP_ID, HUM_ID, mid_name)
    for tr in rows:
        ret_val += [{"type": "temp_rh", "device_type": "sensor unit",
                     "temp_id": tr["sensor_id"], "rh_id": tr['sensor_id2'],
                     "addy": tr["address"], "port": tr["port"],
                     "temp_convert": tr["convert_py"], "rh_convert": tr["convert_py2"],
                     "temp_bias": tr["bias"], "rh_bias": tr["bias2"],
                     "sensor_extra_info": tr["extra_info"],
                     "mid_name": tr["mid_name"],
                     "bin_id": tr["bin_id"], "bin_sec_id": tr["bin_section_id"]}]
    return ret_val


# TODO: get rid of this
def buildAllAnemometerJSON(mid_name):
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo(conn, CURRENT_YEAR, ANEMOMETER_ID, mid_name)
    for tr in rows:
        ret_val += [{"type": "wind", "device_type": "sensor unit",
                     "sensor_id": tr["sensor_id"],
                     "addy": tr["address"], "port": tr["port"],
                     "convert": tr["convert_py"], "bias": tr["bias"],
                     "sensor_extra_info": tr["extra_info"],
                     "mid_name": tr["mid_name"],
                     "bin_id": tr["bin_id"], "bin_sec_id": tr["bin_section_id"]}]
    return ret_val


def buildAllPressureJSON(mid_name):
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo(conn, CURRENT_YEAR, PRESSURE_ID, mid_name)
    for tr in rows:
        ret_val += [{"type": "pressure", "device_type": "sensor unit",
                     "sensor_id": tr["sensor_id"],
                     "addy": tr["address"], "port": tr["port"],
                     "convert": tr["convert_py"], "bias": tr["bias"],
                     "sensor_extra_info": tr["extra_info"],
                     "mid_name": tr["mid_name"],
                     "bin_id": tr["bin_id"], "bin_sec_id": tr["bin_section_id"]}]
    return ret_val


def buildAllTachJSON(mid_name):
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo(conn, CURRENT_YEAR, TACH_ID, mid_name)
    for tr in rows:
        ret_val += [{"type": "tach", "device_type": "sensor unit",
                     "sensor_id": tr["sensor_id"],
                     "addy": tr["address"], "port": tr["port"],
                     "convert": tr["convert_py"], "bias": tr["bias"],
                     "sensor_extra_info": tr["extra_info"],
                     "mid_name": tr["mid_name"],
                     "bin_id": tr["bin_id"], "bin_sec_id": tr["bin_section_id"]}]
    return ret_val


def buildAllMultPtJSON(mid_name):
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo(conn, CURRENT_YEAR, MULTI_PT_T_ID, mid_name)
    for tr in rows:
        ret_val += [{"type": "MP_T", "device_type": "sensor unit",
                     "sensor_id": tr["sensor_id"],
                     "addy": tr["address"], "port": tr["port"],
                     "convert": tr["convert_py"], "bias": tr["bias"],
                     "sensor_extra_info": tr["extra_info"],
                     "mid_name": tr["mid_name"],
                     "bin_id": tr["bin_id"], "bin_sec_id": tr["bin_section_id"]}]
    return ret_val


def buildAllTCJSON(mid_name):
    # NOTE: assumes only one A and/or B sensor per device
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo2(conn, CURRENT_YEAR, TC_A_ID, TC_B_ID, mid_name)
    for tr in rows:
        ret_val.append({"type": "TC", "device_type": "sensor unit",
                        "A_id": tr['sensor_id'], "B_id": tr['sensor_id2'],
                        "addy": tr["address"], "port": tr["port"],
                        "mid_name": tr["mid_name"],
                        "A_convert": tr['convert_py'],
                        "B_convert": tr['convert_py2'],
                        "A_bias": tr['bias'], "B_bias": tr['bias2'],
                        "bin_id": tr["bin_id"], "bin_sec_id": tr["bin_section_id"]})
    return ret_val


def addRemoteControlsToConfig(mid_name):
    # TODO: need to add anything about year column in device table?
    ret_val = []
    # get latest control settings for each sensor in table
    conn = util.getConn()
    if mid_name:
        sql = """SELECT c.sensor_id, d.id as device_id, d.mid_name, d.device_type_id, s.sensor_type_id, d.address, 
        c.id as ctrl_id, c.value, c.fetched_datetime from control c, sensor s, device d WHERE 
        c.fetched_datetime is NULL and c.sensor_id = s.id and s.device_id = d.id and d.year = %s and d.mid_name = %s"""
        cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
        cur.execute(sql, (CURRENT_YEAR, mid_name))
    else:
        sql = """SELECT c.sensor_id, d.id as device_id, d.mid_name, d.device_type_id, s.sensor_type_id, d.address, 
        c.id as ctrl_id, c.value, c.fetched_datetime from control c, sensor s, device d WHERE 
        c.fetched_datetime is NULL and c.sensor_id = s.id and s.device_id = d.id and 
        d.year = %s and d.mid_name IS NULL"""
        cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
        cur.execute(sql, (CURRENT_YEAR,))

    for ncv in cur:
        # get sensor info
        ret_val += [{"sensor_id": ncv["sensor_id"],
                     "device_id": ncv["device_id"],
                     "mid_name": mid_name,
                     "device_type_id": ncv["device_type_id"],
                     "sensor_type_id": ncv["sensor_type_id"],
                     "address": ncv["address"],
                     "ctrl_id": ncv["ctrl_id"],
                     "value": ncv["value"]}]
        # note that cmd has been sent
        # TODO: throw error if this fails
        util.updateRowById("control", ncv["ctrl_id"], {"fetched_datetime": datetime.datetime.now()})
    conn.close()
    return ret_val


def buildAllBurnerControlsJSON(mid_name):
    ret_val = []
    conn = util.getConn()
    # query DB
    extra_where = reduce(lambda x, y: x + " OR device_type_id=%s",
                         BURNER_DEVICE_IDS[1:],
                         "device_type_id=%s") + " AND year=%s AND port >= 0"
    if mid_name:
        extra_where += " AND mid_name = %s "

    extra_args = BURNER_DEVICE_IDS + (CURRENT_YEAR,)

    if mid_name:
        extra_args += (mid_name,)
    rows = util.getRowsFromTable("device",
                                 columns="id,address,port,bin_id,bin_section_id,device_type_id,mid_name",
                                 extraWhere=extra_where,
                                 extraArgs=extra_args,
                                 checkEnabled=True)
    for tr in rows:
        extra_where = "device_id=%s AND sensor_type_id=%s"
        sensor = util.getRowsFromTable("sensor", extraWhere=extra_where, extraArgs=(tr["id"], PV_ID), checkEnabled=True,
                                       conn=conn)  # PV sensors for device
        if sensor:
            ret_val += [{"type": PV_ID, "device_type": tr["device_type_id"], "sensor_id": sensor[0]["id"],
                         "addy": tr["address"], "mid_name": tr["mid_name"], "bin_id": tr["bin_id"],
                         "bin_sec_id": tr["bin_section_id"]}]
        sensor = util.getRowsFromTable("sensor", extraWhere=extra_where, extraArgs=(tr["id"], SP_ID), checkEnabled=True,
                                       conn=conn)  # SP sensors for device
        if sensor:
            ret_val += [{"type": SP_ID, "device_type": tr["device_type_id"], "sensor_id": sensor[0]["id"],
                         "addy": tr["address"], "mid_name": tr["mid_name"], "bin_id": tr["bin_id"],
                         "bin_sec_id": tr["bin_section_id"]}]
    conn.close()
    return ret_val


def buildAllAB_VFD_specialJSON(mid_name):
    ret_val = []
    conn = util.getConn()
    rows = getSensorAndDeviceInfo2(conn, CURRENT_YEAR, VFD_RPM_ID, VFD_TACH_FB_ID, mid_name)
    for tr in rows:
        ret_val += [{"type": "P700", "device_type": "P700", "sensor_id": (tr['sensor_id'], tr['sensor_id2']),
                     "name": tr["device_name"], "mid_name": tr["mid_name"], "bin_id": tr["bin_id"],
                     "bin_sec_id": tr["bin_section_id"]}]
    return ret_val


def addBinNamesToConfig(cfg):
    conn = util.getConn()
    rows = util.getRowsFromTable("bin", columns="id,name", conn=conn)
    for r in rows:
        # add to config
        cfg["binNames"][r["id"]] = r["name"]
        conn.close()


def addBinSectionNamesToConfig(cfg):
    conn = util.getConn()
    rows = util.getRowsFromTable("bin_section", columns="id,name", conn=conn)
    for r in rows:
        # add to config
        cfg["binSectionNames"][r["id"]] = r["name"]
        conn.close()


@app.route('/resources/MIDalt', methods=["GET"])
@midauthorized()
def mid_config_alt():
    mid_name = request.values.get("mid_name", None)
    year = request.values.get("year", None)
    if not year:
        year = datetime.datetime.now().year
    else:
        try:
            year = int(year)
        except ValueError:
            abort(400, 'Bad Arguments')

    row = util.getRowFromTableById("general_config", 1, columns="interval,mid_pass,enabled_p")
    cfg = {
        "interval": row["interval"],
        "sensors": []
    }

    sql = """SELECT d.mid_name, d.id as device_id, d.device_type_id, d.port, d.address,
    s.sensor_type_id, s.convert_py, s.bias, s.extra_info
    FROM sensor s, device d
    WHERE d.port >= 0 AND d.year = %s AND s.device_id = d.id AND s.enabled_p"""
    sql_params = [year]
    if mid_name:
        sql += " AND d.mid_name = %s"
        sql_params.append(mid_name)
    conn = util.getConn()
    cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)
    cur.execute(sql, sql_params)
    for row in cur:
        cfg["sensors"]["year"] = year
        cfg["sensors"]["mid_name"] = row["mid_name"]
        cfg["sensors"]["device_id"] = row["device_id"]
        cfg["sensors"]["device_type_id"] = row["device_type_id"]
        cfg["sensors"]["port"] = row["port"]
        cfg["sensors"]["address"] = row["address"]
        cfg["sensors"]["sensor_type_id"] = row["sensor_type_id"]
        cfg["sensors"]["convert_py"] = row["convert_py"]
        cfg["sensors"]["bias"] = row["bias"]
        cfg["sensors"]["extra_info"] = row["extra_info"]

    return jsonify(cfg)
