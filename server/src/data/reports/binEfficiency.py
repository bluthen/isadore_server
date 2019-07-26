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
from bottle import route #@UnresolvedImport
from bottle import request, abort, static_file, response
# from authentication import authorized
import util
import datetime
import logging
import tempfile
import numpy as np
import matplotlib.pyplot as plt                                                                    
import matplotlib.patches as patches
from data.plot import graphLock

# get all fills for a given bin for a given year
def allFills_forBin_forYear(year,bin_id):
    conn = util.getConn()
    dbFills = util.getRowsFromTable("fill",extraWhere="bin_id=%s",
                                     extraArgs=(bin_id,), conn=conn)
    # create a list of dicts, one for each fill
    theFills = []
    for dbf in dbFills:
        if (dbf["filled_datetime"] and dbf["filled_datetime"].year == year) or (dbf["air_begin_datetime"] and dbf["air_begin_datetime"].year == year):
            theFills += [{"fill_num":dbf["fill_number"],
                          "fill_dt":dbf["filled_datetime"],
                          "empty_dt":dbf["emptied_datetime"],
                          "air_begin_dt":dbf["air_begin_datetime"],
                          "air_end_dt":dbf["air_end_datetime"]}]
    # if no filled/emptied dt, use the air start dt
    for fill in theFills:
        if not fill["fill_dt"]:
            fill["fill_dt"] = fill["air_begin_dt"]
        if not fill["empty_dt"]:
            fill["empty_dt"] = fill["air_end_dt"]
    # sort list of fill dicts by fill date/time
    theFills.sort(key=lambda f: f["fill_dt"])
    # done
    return theFills

def compute_bin_empty_td(start_dt, end_dt, fillList):
    """
    assumes fillList is sorted
    """
    empty_td = datetime.timedelta()
    # TODO: do i need to worry about negative td?
    empty_td += fillList[0]["fill_dt"]-start_dt
    for i in range(len(fillList)-1):
        empty_td += fillList[i+1]["fill_dt"] - fillList[i]["empty_dt"]
    empty_td += end_dt - fillList[-1]["empty_dt"]
    # done
    return empty_td

def compute_bin_full_pct(fillList):
    """
    Computes percentage of time bin was full.
    fillList: list of all fills for the bin/year, sorted by fill date/time
    Assumes fillList is sorted
    """
    start_dt = fillList[0]["fill_dt"]
    end_dt = fillList[-1]["empty_dt"]
    empty_sec = compute_bin_empty_td(start_dt,end_dt,fillList).total_seconds()
    total_sec = (end_dt - start_dt).total_seconds()
    full_sec = total_sec - empty_sec
    return float(full_sec) / float(total_sec), full_sec, empty_sec, total_sec

def draw_bin_activity_plot(start_dt,end_dt,binFills,ax,ypos=0,height=1):
    """
    assumes binFills is sorted
    """
    total_secs = 0
    start_empty_td = datetime.timedelta()
    if binFills[0]["fill_dt"] > start_dt:
        start_empty_td = binFills[0]["fill_dt"] - start_dt
    # if start_empty_td.total_seconds() > 0:
    #     start_empty_rect = patches.Rectangle((0,ypos),
    #                                          width=start_empty_td.total_seconds(),height=height,
    #                                          color="red")
    #     ax.add_patch(start_empty_rect)
    total_secs += start_empty_td.total_seconds()
    for i in range(len(binFills)):
        fill_duration = binFills[i]["empty_dt"] - binFills[i]["fill_dt"]
        fill_rect = patches.Rectangle((total_secs,ypos),
                                      width=fill_duration.total_seconds(),height=height,
                                      color="gray")
        ax.add_patch(fill_rect)
        # ax.annotate(str(binFills[i]["fill_num"]),xytext=(total_secs,ypos-0.5),textcoords="data")
        total_secs += fill_duration.total_seconds()
        if i < len(binFills)-1:
            empty_to_next_fill_duration = binFills[i+1]["fill_dt"] - binFills[i]["empty_dt"]
            fill_rect = patches.Rectangle((total_secs,ypos),
                                          width=empty_to_next_fill_duration.total_seconds(),height=height,
                                          color="red")
            ax.add_patch(fill_rect)
            total_secs += empty_to_next_fill_duration.total_seconds()
    end_empty_td = datetime.timedelta()
    if end_dt > binFills[-1]["empty_dt"]:
        end_empty_td = end_dt - binFills[-1]["empty_dt"]
    # if end_empty_td.total_seconds() > 0:
    #     end_empty_rect = patches.Rectangle((total_secs,ypos),
    #                                        width=end_empty_td.total_seconds(),height=height,
    #                                        color="red")
    #     ax.add_patch(end_empty_rect)
        total_secs += end_empty_td.total_seconds()
    # return the length of the bar in seconds
    return total_secs
    
def draw_allbin_activity_plot(binNumbers,year):
    # convert binNumbers to binIDs
    binIDs = [util.convertBinNumToID(bN) for bN in binNumbers]
    # grab all bin fills for each bin
    allFillsByBin = [allFills_forBin_forYear(year,bin_id) for bin_id in binIDs]
    # determine earliest fill dt
    tmp_sortedFills = [af[0]["fill_dt"] for af in allFillsByBin]
    tmp_sortedFills.sort()
    earliestFill_dt = tmp_sortedFills[0]
    # determine latest empty dt
    tmp_sortedFills = [af[-1]["empty_dt"] for af in allFillsByBin]
    tmp_sortedFills.sort(reverse=True)
    latestEmpty_dt = tmp_sortedFills[0]
    # create fig and axis
    graphLock.acquire()
    try:
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        # draw each bin's activity bar
        barLengths = []
        for bi,(bN,aFBB) in enumerate(zip(binNumbers,allFillsByBin)):
            barLengths += [draw_bin_activity_plot(earliestFill_dt, latestEmpty_dt, aFBB, ax, ypos=bi, height=0.8)]
        # set image size
        barLengths.sort()
        ax.set_xlim((0,barLengths[-1]))
        ax.set_ylim((-0.5,len(binNumbers)+0.5))
        # setup y-axis ticks and labels
        yticks = np.arange(0.5,len(binNumbers),1)
        ytick_labels = ["Bin "+str(i) for i in binNumbers]
        ax.set_yticks(yticks)
        ax.set_yticklabels(ytick_labels)
        # setup x-axis ticks and labels
        xticks = []
        xticks_labels = []
        # add beginning of harvest as a tick label
        xticks += [0]
        # xticks_labels += [earliestFill_dt.strftime("%m/%d,%H:%M")]
        xticks_labels += [earliestFill_dt.strftime("%m/%d")]
        # add end of harvest as tick label
        xticks += [barLengths[-1]]
        # xticks_labels += [latestEmpty_dt.strftime("%m/%d,%H:%M")]
        xticks_labels += [latestEmpty_dt.strftime("%m/%d")]
        # figure out end of first day
        secondDayStart_dt = datetime.datetime(year=earliestFill_dt.year,
                                              month=earliestFill_dt.month,
                                              day=earliestFill_dt.day,
                                              tzinfo=earliestFill_dt.tzinfo)
        secondDayStart_dt += datetime.timedelta(days=1)
        firstDaySecs = (secondDayStart_dt - earliestFill_dt).total_seconds()
        tick = firstDaySecs
        dayCounter = 2
        while tick < (latestEmpty_dt-earliestFill_dt).total_seconds():
            xticks += [tick]
            xticks_labels += [str(dayCounter)]
            dayCounter += 1
            ax.axvline(x=tick,alpha=0.2)
            tick += 24*60.*60. # in seconds
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticks_labels,rotation="vertical")
        fig.subplots_adjust(bottom=0.13)
        ax.set_xlabel("days")
        # create random temporary file name
        # TODO: use config to determine location of temporary files
        imgFileName = tempfile.mktemp(suffix=".eps",prefix="BinEff",dir=".")
        imgFilePath = "./gen_data/"+imgFileName
        # save to file and return filename
        fig.savefig(imgFilePath)
        return imgFileName,allFillsByBin
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
    print util.Single().dbname
    print util.Single().dbuser
    print util.Single().dbhost
    # get sorted list of bin numbers
    binNumbers = util.getListOfBinNumbers()
    binNumbers.sort()
    # create report
    
