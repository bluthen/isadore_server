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
import util
import datetime
import logging
import numpy as np


def printRow(fill,fh,cmd1="\\fillTableRowOne",cmd2="\\fillTableRowTwo"):
    # determine actual bin number
    binNum = util.convertBinIDtoNum(fill["bin_id"])
    # compute up air hrs
    try:
        upAirHrs = util.computeAirHrs(fill)
        upAirHrs_txt = "{:.1f}".format(upAirHrs)
    except util.UtilComputationError:
        # TODO: log error
        upAirHrs = 0
        upAirHrs_txt = "N/A"
    # compute down air hrs
    try:
        downAirHrs = util.computeDownAirHrs(fill)
        downAirHrs_txt = "{:.2f}".format(downAirHrs)
    except util.UtilComputationError:
        # TODO: log error
        downAirHrs = 0
        downAirHrs_txt = "N/A"
    # compute total air hrs and percentages
    totalAirHrs = upAirHrs + downAirHrs
    totalAirHrs_txt = "{:.1f}".format(totalAirHrs)
    upAirPct_txt = "{:.1f}".format(upAirHrs/totalAirHrs*100)
    downAirPct_txt = "{:.1f}".format(downAirHrs/totalAirHrs*100)
    # compute pre and post MC means
    preMCmean = None if (not fill["pre_mc"]) else np.mean(fill["pre_mc"])
    postMCmean = None if (not fill["post_mc"]) else np.mean(fill["post_mc"])
    preMCmean_txt = "N/A" if (not preMCmean) else "{:.1f}".format(preMCmean)
    postMCmean_txt = "N/A" if (not postMCmean) else "{:.1f}".format(postMCmean)
    # compute MC removed
    MCremoved = None if ((not preMCmean) or (not postMCmean)) else preMCmean - postMCmean
    MCremoved_txt = "N/A" if (not MCremoved) else "{:.1f}".format(MCremoved)
    # compute hrs per pt
    hrsPerPt_txt = "N/A"
    hrsPerPt = None
    airHrs = util.computeAirHrs(fill) # returns None if cannot be computed
    if preMCmean and postMCmean and airHrs:
        ptsLost = preMCmean - postMCmean
        hrsPerPt = airHrs/ptsLost
        hrsPerPt_txt = "{:.1f}".format(hrsPerPt)
    shelledBu = "N/A" if fill["bushels"]==None else "{:.2f}".format(fill["bushels"])

    fh.write(cmd1+"{"+
             str(fill["fill_number"])+"}{"+
             str(binNum)+"}{"+
             util.escapeSpecialLatexChars(fill["field_code"])+"}{"+
             postMCmean_txt+"}{"+
             preMCmean_txt+"}{"+
             MCremoved_txt+"}{"+
             upAirHrs_txt+"}{"+
             upAirPct_txt+"}{"+
             downAirHrs_txt+"}\n"+
             cmd2+"{"+
             downAirPct_txt+"}{"+
             totalAirHrs_txt+"}{"+
             hrsPerPt_txt+"}{"+
             str(fill["bushels"])+"}\n")
    fh.flush()
    # return computed values
    return (preMCmean,postMCmean,MCremoved,upAirHrs,downAirHrs,totalAirHrs,hrsPerPt)

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
    
