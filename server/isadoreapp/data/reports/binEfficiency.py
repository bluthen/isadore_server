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
import sys
import datetime
import tempfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from isadoreapp.data.plot import graphLock


# get all fills for a given bin for a given year
def allFills_forBin_forYear(year, bin_id):
    conn = util.getConn()
    db_fills = util.getRowsFromTable("fill", extraWhere="bin_id=%s",
                                     extraArgs=(bin_id,), conn=conn)
    # create a list of dicts, one for each fill
    the_fills = []
    for dbf in db_fills:
        if (dbf["filled_datetime"] and dbf["filled_datetime"].year == year) or (
                    dbf["air_begin_datetime"] and dbf["air_begin_datetime"].year == year):
            the_fills += [{"fill_num": dbf["fill_number"],
                           "fill_dt": dbf["filled_datetime"],
                           "empty_dt": dbf["emptied_datetime"],
                           "air_begin_dt": dbf["air_begin_datetime"],
                           "air_end_dt": dbf["air_end_datetime"]}]
    # if no filled/emptied dt, use the air start dt
    for fill in the_fills:
        if not fill["fill_dt"]:
            fill["fill_dt"] = fill["air_begin_dt"]
        if not fill["empty_dt"]:
            fill["empty_dt"] = fill["air_end_dt"]
    # sort list of fill dicts by fill date/time
    the_fills.sort(key=lambda f: f["fill_dt"])
    # done
    return the_fills


def compute_bin_empty_td(start_dt, end_dt, fill_list):
    """
    assumes fillList is sorted
    """
    empty_td = datetime.timedelta()
    # TODO: do i need to worry about negative td?
    empty_td += fill_list[0]["fill_dt"] - start_dt
    for i in range(len(fill_list) - 1):
        empty_td += fill_list[i + 1]["fill_dt"] - fill_list[i]["empty_dt"]
    empty_td += end_dt - fill_list[-1]["empty_dt"]
    # done
    return empty_td


def compute_bin_full_pct(fill_list):
    """
    Computes percentage of time bin was full.
    fillList: list of all fills for the bin/year, sorted by fill date/time
    Assumes fillList is sorted
    """
    start_dt = fill_list[0]["fill_dt"]
    end_dt = fill_list[-1]["empty_dt"]
    empty_sec = compute_bin_empty_td(start_dt, end_dt, fill_list).total_seconds()
    total_sec = (end_dt - start_dt).total_seconds()
    full_sec = total_sec - empty_sec
    return float(full_sec) / float(total_sec), full_sec, empty_sec, total_sec


def draw_bin_activity_plot(start_dt, end_dt, bin_fills, ax, ypos=0, height=1):
    """
    assumes binFills is sorted
    """
    total_secs = 0
    start_empty_td = datetime.timedelta()
    if bin_fills[0]["fill_dt"] > start_dt:
        start_empty_td = bin_fills[0]["fill_dt"] - start_dt
    # if start_empty_td.total_seconds() > 0:
    #     start_empty_rect = patches.Rectangle((0,ypos),
    #                                          width=start_empty_td.total_seconds(),height=height,
    #                                          color="red")
    #     ax.add_patch(start_empty_rect)
    total_secs += start_empty_td.total_seconds()
    for i in range(len(bin_fills)):
        fill_duration = bin_fills[i]["empty_dt"] - bin_fills[i]["fill_dt"]
        fill_rect = patches.Rectangle((total_secs, ypos),
                                      width=fill_duration.total_seconds(), height=height,
                                      color="gray")
        ax.add_patch(fill_rect)
        # ax.annotate(str(binFills[i]["fill_num"]),xytext=(total_secs,ypos-0.5),textcoords="data")
        total_secs += fill_duration.total_seconds()
        if i < len(bin_fills) - 1:
            empty_to_next_fill_duration = bin_fills[i + 1]["fill_dt"] - bin_fills[i]["empty_dt"]
            fill_rect = patches.Rectangle((total_secs, ypos),
                                          width=empty_to_next_fill_duration.total_seconds(), height=height,
                                          color="red")
            ax.add_patch(fill_rect)
            total_secs += empty_to_next_fill_duration.total_seconds()
    if end_dt > bin_fills[-1]["empty_dt"]:
        end_empty_td = end_dt - bin_fills[-1]["empty_dt"]
        # if end_empty_td.total_seconds() > 0:
        #     end_empty_rect = patches.Rectangle((total_secs,ypos),
        #                                        width=end_empty_td.total_seconds(),height=height,
        #                                        color="red")
        #     ax.add_patch(end_empty_rect)
        total_secs += end_empty_td.total_seconds()
    # return the length of the bar in seconds
    return total_secs


def draw_allbin_activity_plot(bin_numbers, year):
    # convert bin_numbers to bin_ids
    bin_ids = [util.convertBinNumToID(bN) for bN in bin_numbers]
    # grab all bin fills for each bin
    all_fills_by_bin = [allFills_forBin_forYear(year, bin_id) for bin_id in bin_ids]
    # determine earliest fill dt
    tmp_sorted_fills = [af[0]["fill_dt"] for af in all_fills_by_bin]
    tmp_sorted_fills.sort()
    earliest_fill_dt = tmp_sorted_fills[0]
    # determine latest empty dt
    tmp_sorted_fills = [af[-1]["empty_dt"] for af in all_fills_by_bin]
    tmp_sorted_fills.sort(reverse=True)
    latest_empty_dt = tmp_sorted_fills[0]
    # create fig and axis
    graphLock.acquire()
    try:
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        # draw each bin's activity bar
        bar_lengths = []
        for bi, (bN, aFBB) in enumerate(zip(bin_numbers, all_fills_by_bin)):
            bar_lengths += [draw_bin_activity_plot(earliest_fill_dt, latest_empty_dt, aFBB, ax, ypos=bi, height=0.8)]
        # set image size
        bar_lengths.sort()
        ax.set_xlim((0, bar_lengths[-1]))
        ax.set_ylim((-0.5, len(bin_numbers) + 0.5))
        # setup y-axis ticks and labels
        yticks = np.arange(0.5, len(bin_numbers), 1)
        ytick_labels = ["Bin " + str(i) for i in bin_numbers]
        ax.set_yticks(yticks)
        ax.set_yticklabels(ytick_labels)
        # setup x-axis ticks and labels
        xticks = []
        xticks_labels = []
        # add beginning of harvest as a tick label
        xticks += [0]
        # xticks_labels += [earliestFill_dt.strftime("%m/%d,%H:%M")]
        xticks_labels += [earliest_fill_dt.strftime("%m/%d")]
        # add end of harvest as tick label
        xticks += [bar_lengths[-1]]
        # xticks_labels += [latestEmpty_dt.strftime("%m/%d,%H:%M")]
        xticks_labels += [latest_empty_dt.strftime("%m/%d")]
        # figure out end of first day
        second_day_start_dt = datetime.datetime(year=earliest_fill_dt.year,
                                                month=earliest_fill_dt.month,
                                                day=earliest_fill_dt.day,
                                                tzinfo=earliest_fill_dt.tzinfo)
        second_day_start_dt += datetime.timedelta(days=1)
        first_day_secs = (second_day_start_dt - earliest_fill_dt).total_seconds()
        tick = first_day_secs
        day_counter = 2
        while tick < (latest_empty_dt - earliest_fill_dt).total_seconds():
            xticks += [tick]
            xticks_labels += [str(day_counter)]
            day_counter += 1
            ax.axvline(x=tick, alpha=0.2)
            tick += 24 * 60. * 60.  # in seconds
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticks_labels, rotation="vertical")
        fig.subplots_adjust(bottom=0.13)
        ax.set_xlabel("days")
        # create random temporary file name
        # TODO: use config to determine location of temporary files
        img_file_name = tempfile.mktemp(suffix=".eps", prefix="BinEff", dir=".")
        img_file_path = "./gen_data/" + img_file_name
        # save to file and return filename
        fig.savefig(img_file_path)
        return img_file_name, all_fills_by_bin
    finally:
        graphLock.release()


#
# running as a script
# 

configFileLoc = "/home/dane/isadoredev1-dane-home/EA/isadore_business/reports/MC_predict/"
configFilePrefix = "settings_"
configFileExt = ".cfg"

if __name__ == "__main__":
    customerName = sys.argv[1]
    util.Single().configLoc = configFileLoc + configFilePrefix + customerName + configFileExt
    # read some basic info
    util.Single().loadSettings()
    print(util.Single().dbname)
    print(util.Single().dbuser)
    print(util.Single().dbhost)
    # get sorted list of bin numbers
    binNumbers = util.getListOfBinNumbers()
    binNumbers.sort()
    # create report
