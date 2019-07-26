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

import data.graph_data as gd
from data.plot import graphLock


sensorTypeID_T = 10

def printFillPage(fill,fh,fillPlotPath):
    # 
    # print fill info section
    # 
    # determine fill's year
    fillYear = fill["air_begin_datetime"].year if fill["air_begin_datetime"] != None else fill["filled_datetime"].year
    # determine actual bin number
    binNum = util.convertBinIDtoNum(fill["bin_id"])
    fh.write("\\begin{FillInfoSec}\n")
    # left column
    fh.write("\\FillInfoSecColL{"+
             str(fillYear)+"}{"+
             str(fill["fill_number"])+"}{"+
             str(fill["rotation_number"])+"}{"+
             str(binNum)+"}\n")
    fh.flush()
    # center column
    hybrid = "N/A" if fill["hybrid_code"]==None else util.escapeSpecialLatexChars(fill["hybrid_code"])
    field = "N/A" if fill["field_code"]==None else util.escapeSpecialLatexChars(fill["field_code"])
    truck = "N/A" if fill["truck"]==None else fill["truck"]
    depth = "N/A" if fill["depth"]==None else str(fill["depth"])
    fh.write("\\FillInfoSecColC{"+hybrid +"}{"+field+"}{"+truck+"}{"+depth+"}\n")
    fh.flush()
    # right column
    storage = "N/A" if fill["storage_bin_code"]==None else str(fill["storage_bin_code"])
    shelledBu = "N/A" if fill["bushels"]==None else "{:.2f}".format(fill["bushels"])
    hrsPerPt = "N/A"
    if fill["pre_mc"] and fill["post_mc"]:
        ptsLost = np.mean(fill["pre_mc"]) - np.mean(fill["post_mc"])
        airHrs = util.computeAirHrs(fill)
        hrsPerPt = "{:.2f}".format(airHrs/ptsLost)
    fh.write("\\FillInfoSecColR{"+storage+"}{"+shelledBu+"}{"+hrsPerPt+"}\n")
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
    fill_dt = "N/A" if fill["filled_datetime"]==None else fill["filled_datetime"].strftime("%H:%M %m/%d")
    empty_dt = "N/A" if fill["emptied_datetime"]==None else fill["emptied_datetime"].strftime("%H:%M %m/%d")
    fh.write("\\fillTimes{"+fill_dt+"}{"+empty_dt+"}\n")
    fh.flush()
    # center column
    # TODO: make compatible with multiple roll times
    startAir_dt = "N/A" if fill["air_begin_datetime"]==None else fill["air_begin_datetime"].strftime("%H:%M %m/%d")
    stopAir_dt = "N/A" if fill["air_end_datetime"]==None else fill["air_end_datetime"].strftime("%H:%M %m/%d")
    rollAir_dt = "N/A" if (fill["roll_datetime"]==None or len(fill["roll_datetime"]) == 0) else fill["roll_datetime"][0].strftime("%H:%M %m/%d") # don't think i need the 2nd part of IF test
    fh.write("\\airTimes{"+startAir_dt+"}{"+rollAir_dt+"}{"+stopAir_dt+"}\n")
    fh.flush()
    # right column:
    # compute up air hrs
    try:
        upAirHrs = util.computeAirHrs(fill)
        if upAirHrs:
            upAirHrs_txt = "{:.2f}".format(upAirHrs)
        else:
            upAirHrs = 0
            upAirHrs_txt = "N/A"
    except util.UtilComputationError:
        # TODO: log error
        upAirHrs = 0
        upAirHrs_txt = "N/A"
    # compute down air hrs
    try:
        downAirHrs = util.computeDownAirHrs(fill)
        if downAirHrs:
            downAirHrs_txt = "{:.2f}".format(downAirHrs)
        else:
            downAirHrs = 0
            downAirHrs = "N/A"
    except Exception as e:
        # TODO: log error
        downAirHrs = 0
        downAirHrs_txt = "N/A"
    # compute total air hrs and percentages
    totalAirHrs = upAirHrs + downAirHrs
    if totalAirHrs == 0:
        totalAirHrs_txt = "N/A"
        upAirPct_txt = "N/A"
        downAirPct_txt = "N/A"
    else:
        totalAirHrs_txt = "{:.2f}".format(totalAirHrs)
        upAirPct_txt = "{:.2f}".format(upAirHrs/totalAirHrs*100)
        downAirPct_txt = "{:.2f}".format(downAirHrs/totalAirHrs*100)
    fh.write("\\airStats{"+
             upAirHrs_txt+"}{"+
             downAirHrs_txt+"}{"+
             totalAirHrs_txt+"}{"+
             upAirPct_txt+"\\%}{"+
             downAirPct_txt+"\\%}\n")
    fh.flush()
    # end Section
    fh.write("\\end{AirTimesSec}\n\n")
    fh.flush()
    # 
    # print MC sample section
    # 
    # compute pre and post MC means
    preMCmean = "N/A" if (not fill["pre_mc"]) else "{:.2f}".format(np.mean(fill["pre_mc"]))
    postMCmean = "N/A" if (not fill["post_mc"]) else "{:.2f}".format(np.mean(fill["post_mc"]))
    # start Section
    fh.write("\\begin{MoistureSamplesSec}{"+preMCmean+"}{"+postMCmean+"}\n")
    # left column
    fh.write("\\begin{MoistureSampleSecColPre}\n")
    if fill["pre_mc"]:
        for pMC in fill["pre_mc"]:
            fh.write("\\PreColLine{"+"{:.2f}".format(pMC)+"}\n")
    fh.write("\\end{MoistureSampleSecColPre}\n")
    fh.flush()
    # center column (during drying MC samples)
    duringMCs = util.getRowsFromTable("fill_during_mc",
                                      extraWhere="fill_id=%s",extraArgs=(fill["id"],))
    fh.write("\\begin{MoistureSampleSecColDuring}\n")
    for dMC in duringMCs:
        fh.write("\\DuringColLine{"+dMC["datetime"].strftime("%H:%M %m/%d")+"}{"+"{:.2f}".format(dMC["mc"])+"}\n")
    fh.write("\\end{MoistureSampleSecColDuring}\n")
    fh.flush()
    # right column (post-drying MC)
    fh.write("\\begin{MoistureSampleSecColPost}\n")
    if fill["post_mc"]:
        for pMC in fill["post_mc"]:
            fh.write("\\PostColLine{"+"{:.2f}".format(pMC)+"}\n")
    fh.write("\\end{MoistureSampleSecColPost}\n")
    fh.write("\\end{MoistureSamplesSec}\n\n")
    fh.flush()
    # 
    # place image
    # 
    if fillPlotPath:            # None signifies plot not created
        fh.write("\\insertFillPlot{"+fillPlotPath+"}")
    fh.flush()


def createFillGraph(startDT,endDT,binID,topSecID,botSecID):
    tmpConn = util.getConn()
    # 
    # grab readings that occured during fill
    # 
    readingRows = util.getRowsFromTable("reading",
                                        extraWhere="datetime>=%s AND datetime <= %s",
                                        extraArgs=(startDT,endDT),
                                        conn=tmpConn)
    # 
    # use optimized method to get data
    # 
    gds = gd.graph_data_struct(binID,
                               [["sensor",[topSecID,sensorTypeID_T]],
                                ["sensor",[botSecID,sensorTypeID_T]]],
                               15,
                               startDT, endDT)
    
    # 
    # plot upper and lower T
    # 
    # massage into x and y
    xVals = [xv[0] for xv in gds]
    upperTs = [tv[1][1] for tv in gds]
    lowerTs = [tv[2][1] for tv in gds]
    # do the plot
    graphLock.acquire()
    try:
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.plot(xVals,upperTs,"-r")
        ax.plot(xVals,lowerTs,"--r")
        #
        # save fig to file and return path
        #
        tmpFileName = tempfile.mktemp(prefix="FillRptPlot_",dir="./")+".eps"
        fig.savefig("./gen_data/"+tmpFileName)
        fig.clf()
        return tmpFileName
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
    
