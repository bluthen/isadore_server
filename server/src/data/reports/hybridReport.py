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
import tempfile
import numpy as np
import fillReportTabulated

def printHybridTable(hybridCode,fillRows,fh):
    preMCs=[];postMCs=[];MCrmvds=[];upAirs=[];downAirs=[];totalAirs=[];hrsPerPts=[];
    shelledBus=[]
    tblRows = [fr for fr in fillRows if fr["hybrid_code"]==hybridCode]
    tblRows.sort(key=lambda x: x["fill_number"])
    # start new table
    fh.write("\\begin{hybridTable}{"+hybridCode+"}\n")
    # for each row in table
    for tr in tblRows:
        # print to file and save computed values
        (preMCmean,postMCmean,
         MCremoved,upAirHrs,
         downAirHrs,totalAirHrs,
         hrsPerPt) = fillReportTabulated.printRow(tr,fh,
                                                  cmd1="\\hybridTableRowOne",
                                                  cmd2="\\hybridTableRowTwo")
        fh.write("\\hybridTableNextRow\n\n")
        preMCs+=[preMCmean];postMCs+=[postMCmean];MCrmvds+=[MCremoved];
        upAirs+=[upAirHrs];downAirs+=[downAirHrs];totalAirs+=[totalAirHrs];
        hrsPerPts+=[hrsPerPt];
        shelledBus += [tr["bushels"]] if tr["bushels"] else []
    # compute stats for hybrid
    preMC_avg=np.mean(preMCs);postMC_avg=np.mean(postMCs);MCrmvd_avg=np.mean(MCrmvds);
    upAir_avg=np.mean(upAirs);downAir_avg=np.mean(downAirs);totalAir_avg=np.mean(totalAirs);
    hrsPerPt_avg=np.mean(hrsPerPts); 
    upAirPct_avg = np.mean(np.array(upAirs)/np.array(totalAirs))
    downAirPct_avg = np.mean(np.array(downAirs)/np.array(totalAirs))
    upAir_tot=np.sum(upAirs);downAir_tot=np.sum(downAirs);totalAir_tot=np.sum(totalAirs);
    # treat shelled Bu differently b/c can be empty
    if shelledBus:
        shelledBu_avg=np.mean(shelledBus)
        shelledBu_tot=np.sum(shelledBus)
        shelledBu_avg_str = "{:.1f}".format(shelledBu_avg)
        shelledBu_tot_str = "{:.1f}".format(shelledBu_tot)
    else:
        shelledBu_avg=None
        shelledBu_tot=None
        shelledBu_avg_str = "N/A"
        shelledBu_tot_str = "N/A"
    # print hybrid stats rows
    fh.write("\\hybridTableAvgRowOne{"+
             "{:.1f}".format(postMC_avg)+"}{"+
             "{:.1f}".format(preMC_avg)+"}{"+
             "{:.1f}".format(MCrmvd_avg)+"}{"+
             "{:.1f}".format(upAir_avg)+"}{"+
             "{:.1f}".format(100*upAirPct_avg)+"}{"+
             "{:.1f}".format(downAir_avg)+"}{"+
             "{:.1f}".format(100*downAirPct_avg)+"}{"+
             "{:.1f}".format(totalAir_avg)+"}{"+
             "{:.2f}".format(hrsPerPt_avg)+"}\n"+
             "\\hybridTableAvgRowTwo{"+shelledBu_avg_str+"}\n")
    fh.write("\\hybridTableNextRow\n")
    fh.write("\\hybridTableTotalRow{"+
             "{:.1f}".format(upAir_tot)+"}{"+
             "{:.1f}".format(downAir_tot)+"}{"+
             "{:.1f}".format(totalAir_tot)+"}{"+
             shelledBu_tot_str+"}\n")
    fh.write("\\hybridTableNextRow\n")
    # end table
    fh.write("\\end{hybridTable}\n\n")
    fh.flush()

