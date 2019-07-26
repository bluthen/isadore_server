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

# from authentication import authorized
import isadoreapp.util as util
import tempfile
import numpy as np
import matplotlib.pyplot as plt

import isadoreapp.data.graph_data as gd
from isadoreapp.data.plot import graphLock

sensorTypeID_T = 10


def print_fill_page(fill, fh, fill_plot_path):
    # 
    # print fill info section
    # 
    # determine fill's year
    if fill["air_begin_datetime"] is not None:
        fill_year = fill["air_begin_datetime"].year
    else:
        fill["filled_datetime"].year
    # determine actual bin number
    bin_num = util.convertBinIDtoNum(fill["bin_id"])
    fh.write("\\begin{FillInfoSec}\n")
    # left column
    fh.write("\\FillInfoSecColL{" +
             str(fill_year) + "}{" +
             str(fill["fill_number"]) + "}{" +
             str(fill["rotation_number"]) + "}{" +
             str(bin_num) + "}\n")
    fh.flush()
    # center column
    hybrid = "N/A" if fill["hybrid_code"] is None else util.escapeSpecialLatexChars(fill["hybrid_code"])
    field = "N/A" if fill["field_code"] is None else util.escapeSpecialLatexChars(fill["field_code"])
    truck = "N/A" if fill["truck"] is None else fill["truck"]
    depth = "N/A" if fill["depth"] is None else str(fill["depth"])
    fh.write("\\FillInfoSecColC{" + hybrid + "}{" + field + "}{" + truck + "}{" + depth + "}\n")
    fh.flush()
    # right column
    storage = "N/A" if fill["storage_bin_code"] is None else str(fill["storage_bin_code"])
    shelled_bu = "N/A" if fill["bushels"] is None else "{:.2f}".format(fill["bushels"])
    hrs_per_pt = "N/A"
    if fill["pre_mc"] and fill["post_mc"]:
        pts_lost = np.mean(fill["pre_mc"]) - np.mean(fill["post_mc"])
        air_hrs = util.computeAirHrs(fill)
        hrs_per_pt = "{:.2f}".format(air_hrs / pts_lost)
    fh.write("\\FillInfoSecColR{" + storage + "}{" + shelled_bu + "}{" + hrs_per_pt + "}\n")
    fh.flush()
    # end of Section
    fh.write("\end{FillInfoSec}\n\n")
    fh.flush()
    # 
    # print air times section
    # 
    # start section
    fh.write("\\begin{AirTimesSec}\n")
    # left column
    fill_dt = "N/A" if fill["filled_datetime"] is None else fill["filled_datetime"].strftime("%H:%M %m/%d")
    empty_dt = "N/A" if fill["emptied_datetime"] is None else fill["emptied_datetime"].strftime("%H:%M %m/%d")
    fh.write("\\fillTimes{" + fill_dt + "}{" + empty_dt + "}\n")
    fh.flush()
    # center column
    # TODO: make compatible with multiple roll times
    start_air_dt = "N/A" if fill["air_begin_datetime"] is None else fill["air_begin_datetime"].strftime("%H:%M %m/%d")
    stop_air_dt = "N/A" if fill["air_end_datetime"] is None else fill["air_end_datetime"].strftime("%H:%M %m/%d")
    roll_air_dt = "N/A" if (fill["roll_datetime"] is None or len(fill["roll_datetime"]) == 0) else \
        fill["roll_datetime"][0].strftime("%H:%M %m/%d")  # don't think i need the 2nd part of IF test
    fh.write("\\airTimes{" + start_air_dt + "}{" + roll_air_dt + "}{" + stop_air_dt + "}\n")
    fh.flush()
    # right column:
    # compute up air hrs
    try:
        up_air_hrs = util.computeAirHrs(fill)
        if up_air_hrs:
            up_air_hrs_txt = "{:.2f}".format(up_air_hrs)
        else:
            up_air_hrs = 0
            up_air_hrs_txt = "N/A"
    except util.UtilComputationError:
        # TODO: log error
        up_air_hrs = 0
        up_air_hrs_txt = "N/A"
    # compute down air hrs
    try:
        down_air_hrs = util.computeDownAirHrs(fill)
        if down_air_hrs:
            down_air_hrs_txt = "{:.2f}".format(down_air_hrs)
        else:
            down_air_hrs_txt = "N/A"
    except:
        # TODO: log error
        down_air_hrs = 0
        down_air_hrs_txt = "N/A"
    # compute total air hrs and percentages
    total_air_hrs = up_air_hrs + down_air_hrs
    if total_air_hrs == 0:
        total_air_hrs_txt = "N/A"
        up_air_pct_txt = "N/A"
        down_air_pct_txt = "N/A"
    else:
        total_air_hrs_txt = "{:.2f}".format(total_air_hrs)
        up_air_pct_txt = "{:.2f}".format(up_air_hrs / total_air_hrs * 100)
        down_air_pct_txt = "{:.2f}".format(down_air_hrs / total_air_hrs * 100)
    fh.write("\\airStats{" +
             up_air_hrs_txt + "}{" +
             down_air_hrs_txt + "}{" +
             total_air_hrs_txt + "}{" +
             up_air_pct_txt + "\\%}{" +
             down_air_pct_txt + "\\%}\n")
    fh.flush()
    # end Section
    fh.write("\\end{AirTimesSec}\n\n")
    fh.flush()
    # 
    # print MC sample section
    # 
    # compute pre and post MC means
    pre_mc_mean = "N/A" if (not fill["pre_mc"]) else "{:.2f}".format(np.mean(fill["pre_mc"]))
    post_mc_mean = "N/A" if (not fill["post_mc"]) else "{:.2f}".format(np.mean(fill["post_mc"]))
    # start Section
    fh.write("\\begin{MoistureSamplesSec}{" + pre_mc_mean + "}{" + post_mc_mean + "}\n")
    # left column
    fh.write("\\begin{MoistureSampleSecColPre}\n")
    if fill["pre_mc"]:
        for pMC in fill["pre_mc"]:
            fh.write("\\PreColLine{" + "{:.2f}".format(pMC) + "}\n")
    fh.write("\\end{MoistureSampleSecColPre}\n")
    fh.flush()
    # center column (during drying MC samples)
    during_mcs = util.getRowsFromTable("fill_during_mc",
                                       extraWhere="fill_id=%s", extraArgs=(fill["id"],))
    fh.write("\\begin{MoistureSampleSecColDuring}\n")
    for dMC in during_mcs:
        fh.write(
            "\\DuringColLine{" + dMC["datetime"].strftime("%H:%M %m/%d") + "}{" + "{:.2f}".format(dMC["mc"]) + "}\n")
    fh.write("\\end{MoistureSampleSecColDuring}\n")
    fh.flush()
    # right column (post-drying MC)
    fh.write("\\begin{MoistureSampleSecColPost}\n")
    if fill["post_mc"]:
        for pMC in fill["post_mc"]:
            fh.write("\\PostColLine{" + "{:.2f}".format(pMC) + "}\n")
    fh.write("\\end{MoistureSampleSecColPost}\n")
    fh.write("\\end{MoistureSamplesSec}\n\n")
    fh.flush()
    # 
    # place image
    # 
    if fill_plot_path:  # None signifies plot not created
        fh.write("\\insertFillPlot{" + fill_plot_path + "}")
    fh.flush()


def create_fill_graph(start_dt, end_dt, bin_id, top_sec_id, bot_sec_id):
    tmp_conn = util.getConn()
    # 
    # grab readings that occured during fill
    # 
    reading_rows = util.getRowsFromTable("reading",
                                         extraWhere="datetime>=%s AND datetime <= %s",
                                         extraArgs=(start_dt, end_dt),
                                         conn=tmp_conn)
    # 
    # use optimized method to get data
    # 
    gds = gd.graph_data_struct(bin_id,
                               [["sensor", [top_sec_id, sensorTypeID_T]],
                                ["sensor", [bot_sec_id, sensorTypeID_T]]],
                               15,
                               start_dt, end_dt)

    # 
    # plot upper and lower T
    # 
    # massage into x and y
    x_vals = [xv[0] for xv in gds]
    upper_ts = [tv[1][1] for tv in gds]
    lower_ts = [tv[2][1] for tv in gds]
    # do the plot
    graphLock.acquire()
    try:
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(x_vals, upper_ts, "-r")
        ax.plot(x_vals, lower_ts, "--r")
        #
        # save fig to file and return path
        #
        tmp_file_name = tempfile.mktemp(prefix="FillRptPlot_", dir="./") + ".eps"
        fig.savefig("./gen_data/" + tmp_file_name)
        fig.clf()
        return tmp_file_name
    finally:
        graphLock.release()


#
# running as a script
# 

config_file_loc = "/home/dane/isadoredev1-dane-home/EA/isadore_business/reports/MC_predict/"
config_file_prefix = "settings_"
config_file_ext = ".cfg"

if __name__ == "__main__":
    import sys

    customer_name = sys.argv[1]
    util.Single().configLoc = config_file_loc + config_file_prefix + customer_name + config_file_ext
    # read some basic info
    util.Single().loadSettings()
    print(util.Single().dbname)
    print(util.Single().dbuser)
    print(util.Single().dbhost)
