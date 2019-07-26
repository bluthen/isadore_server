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
import util
import toLatex
import uptime

configFileLoc = "/home/dane/isadoredev1-dane-home/EA/isadore_business/reports/MC_predict/"
configFilePrefix = "settings_"
configFileExt = ".cfg"

if __name__ == "__main__":
    customerName = sys.argv[1]
    reportYear = int(sys.argv[2])
    reportType = sys.argv[3]
    tmpFileName=customerName+"_"+reportType+"_"+str(reportYear)
    print tmpFileName
    util.Single().configLoc = configFileLoc + configFilePrefix + customerName + configFileExt
    util.Single().loadSettings()
    print util.Single().dbname
    print util.Single().dbuser
    print util.Single().dbhost

    if reportType == "BinEff":
        toLatex.latex_create_bin_efficiency(reportYear,
                                            tmpFileName=tmpFileName)
    elif reportType == "FillFull":
        toLatex.latex_create_fill_report_full(reportYear,
                                              fileNameBase=tmpFileName)
    elif reportType == "FillTab":
        toLatex.latex_create_fill_report_tab(reportYear,
                                             fileNameBase=tmpFileName)
    elif reportType == "HybridTab":
        toLatex.latex_create_fill_report_hybrid(reportYear,
                                                fileNameBase=tmpFileName)
    elif reportType == "Uptime":
        uptimeRes = uptime.compute(reportYear)
        tableStuff = [(bn,dt.total_seconds()/60./60.,tt.total_seconds()/60./60.,dt.total_seconds()/tt.total_seconds()) for bn,tt,dt in zip(uptimeRes[0],uptimeRes[1],uptimeRes[2])]
        for tS in tableStuff:
            print tS[0],tS[1],tS[2],tS[3]*100
    else:
        print "not a valid report type, yo!"
