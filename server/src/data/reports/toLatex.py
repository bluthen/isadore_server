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
from authentication import authorized
import util
import subprocess
import string
import tempfile
import binEfficiency as binEff
import fillReport
import fillReportTabulated
import hybridReport
import pytz
import logging

# TODO: make IO location more flexible
#LATEX_IO_DIR = "/home/dane/EA/isadore_web/server/src/data/reports/genData"
LATEX_IO_DIR = "./gen_data"
binSecID_upper = 13
binSecID_lower = 14


@route('/resources/data/report/latex_download_bin_efficiency', method=["GET"])
@authorized('User')
def latex_download_bin_efficiency():
    #if not year:
    year = request.params.get('year')
    if not year:
        abort(400, 'Year is required.')
    try:
        year = int(year)
    except ValueError:
        abort(400, 'Bad year argument.')
    tmpFilename = latex_create_bin_efficiency(year)
    response.headers['Content-disposition'] = 'attachment; filename=bin_efficiency'+str(year)+'.pdf'
    return static_file(tmpFilename+".pdf", root="./gen_data")

def latex_create_bin_efficiency(year,tmpFileName=None):
    # 
    # grab data
    # 
    # bin numbers
    binNumbers = util.getListOfBinNumbers()
    binNumbers.sort()
    # create image and get list of lists fills (one list per bin, each list sorted by fill date
    binEffImgFN,allFillsByBin = binEff.draw_allbin_activity_plot(binNumbers,year)
    # 
    # compute table info
    # 
    tableInfo = []
    for bN,aF in zip(binNumbers,allFillsByBin):
        fullPct,fullSec,emptySec,totalSec = binEff.compute_bin_full_pct(aF)
        tableInfo += [{"binNum":bN,"fullPct":fullPct,"fullHrs":fullSec/60./60.,
                       "emptyHrs":emptySec/60./60.,"totalHrs":totalSec/60./60.}]
    # 
    # open temporary Latex file
    # 
    if not tmpFileName:
        tmpFileName = tempfile.mktemp(prefix="BinEff",dir=".")
    fh = open("./gen_data/"+tmpFileName+".tex", 'w')
    # 
    # write latex file
    # 
    fh.write(startReportString("Dryer Efficiency Report"))
    # use minipage to hold table/image together
    fh.write("\\begin{minipage}{\\textwidth} \n \\begin{minipage}[b]{0.35\\textwidth}\n")
    # start with table
    fh.write("\\dryerEffTblStart\n\n")
    for ti in tableInfo:
        fh.write("\\hline\n")
        rowString = "\\dryerEffTblRow{{ {} }} {{ {:.1f} }} {{ {:.1f} }} {{ {:.1f} }} {{ {:.2f} }}\n".format(ti["binNum"],ti["fullHrs"],ti["emptyHrs"],ti["totalHrs"],ti["fullPct"]*100)
        fh.write(rowString)
    fh.write("\\dryerEffTblEnd \n\n")
    # 
    # close out table minipage and add image
    # 
    fh.write("\\end{minipage} \n \\hfill \n \\begin{minipage}[t]{0.63\\textwidth} \n \\includegraphics[height=0.93\\textheight,width=\\textwidth]{"+binEffImgFN+"} \n \\end{minipage} \\end{minipage}")
    # end report
    fh.write(endReportString())
    # close file
    fh.close()
    # 
    # latex the file
    # 
    LatexFile(LATEX_IO_DIR, tmpFileName)
    # return the file name base
    return tmpFileName

@route('/resources/data/report/latex_download_fill_report_full', method=["GET"])
@authorized('User')
def latex_download_fill_report_full():
    reportYear = request.params.get('year')
    if not reportYear:
        abort(400, 'Year is required.')
    try:
        reportYear = int(reportYear)
    except ValueError:
        abort(400, 'Bad year argument.')
    try:
        displayTZ = pytz.timezone(request.params.get("display_tz"))
        displayTZStr = request.params.get("display_tz")
    except:
        abort(400, 'invalid display_tz')

    tmpFileName = None
    tmpFileName = latex_create_fill_report_full(reportYear, tmpFileName)
    response.headers['Content-disposition'] = 'attachment; filename=fill_report_full'+str(reportYear)+'.pdf'
    return static_file(tmpFileName+".pdf", root="./gen_data")


def latex_create_fill_report_full(reportYear,fileNameBase=None, displayTZStr=None):
    # 
    # create random file name, open for writing, and print file preamble stuff
    # 
    if not fileNameBase:
        fileNameBase = tempfile.mktemp(prefix="fillRpt_full_",dir=".")
    filePath = "./gen_data/"+fileNameBase+".tex"
    fh = open(filePath, 'w')
    fh.write("\\documentclass{IsadoreReportFillFull}\n\\rptTitle{Fill report (full)}\n\\begin{document}\n\n")
    # 
    # get all fills (will filter by year later)
    # 
    conn = util.getConn()
    # TODO: sort by fill number (in SQL?)
    # TODO: have DB only return fills from proper year to save CPU?
    dbFills = util.getRowsFromTable("fill",conn=conn)
    for dbFi,dbF in enumerate(dbFills):
        print dbFi,"/",len(dbFills)
        fillYear = dbF["air_begin_datetime"].year if dbF["air_begin_datetime"] != None else dbF["filled_datetime"].year
        if fillYear == reportYear:
            # 
            # create fill plot image 
            # 
            startDT = util.getStartAirDT(dbF)
            endDT = util.getStopAirDT(dbF)
            fillGraphPath = None
            try:
                fillGraphPath = fillReport.createFillGraph(startDT,endDT,dbF["bin_id"],
                                                           binSecID_upper, binSecID_lower)
            except:
                # TODO: log error
                print "plot of fill data not created!"
            # 
            # print the fill rpt page for the given fill if
            # the fill is from the correct year
            # 
            fillReport.printFillPage(dbF,fh,fillGraphPath)
            fh.write("\n\\newpage\n\n")
            fh.write("%%% next fill %%%\n\n")
    conn.close()
    # 
    # end writing to file
    # 
    fh.write("\n\n\\end{document}")
    fh.close()
    # 
    # latex
    # 
    LatexFile(LATEX_IO_DIR, fileNameBase)
    # 
    # return PDF
    # 
    return fileNameBase

@route('/resources/data/report/latex_download_fill_report_tab', method=["GET"])
@authorized('User')
def latex_download_fill_report_tab():
    # 
    # get desired year from parameters
    # 
    reportYear = request.params.get('year')
    if not reportYear:
        abort(400, 'Year is required.')
    try:
        reportYear = int(reportYear)
    except ValueError:
        abort(400, 'Bad year argument.')
    try:
        displayTZ = pytz.timezone(request.params.get("display_tz"))
        displayTZStr = request.params.get("display_tz")
    except:
        abort(400, 'invalid display_tz')

    tmpFileName = latex_create_fill_report_tab(reportYear)
    response.headers['Content-disposition'] = 'attachment; filename=fill_report_tab'+str(reportYear)+'.pdf'
    return static_file(tmpFileName+".pdf", root="./gen_data")


def latex_create_fill_report_tab(reportYear,fileNameBase=None):
    # 
    # create random file name, open for writing, and print file preamble stuff
    # 
    if not fileNameBase:
        fileNameBase = tempfile.mktemp(prefix="fillRpt_tab_",dir=".")
    filePath = "./gen_data/"+fileNameBase+".tex"
    fh = open(filePath, 'w')
    fh.write("\\documentclass{IsadoreReportFillTab}\n\\rptTitle{Fill report (tabulated)}\n\\begin{document}\n\n")
    # 
    # get all fills (will filter by year later)
    # 
    conn = util.getConn()
    # TODO: have DB only return fills from proper year to save CPU?
    tmpDBFills = util.getRowsFromTable("fill",conn=conn)
    # 
    # sort by fill number
    # 
    dbFills = [tdbf for tdbf in tmpDBFills]
    dbFills.sort(key=lambda x: x["fill_number"])
    # 
    # start table env and print table rows
    # 
    fh.write("\\begin{fillTable}\n")
    for dbFi,dbF in enumerate(dbFills):
        # if correct year, add corresponding row to table
        fillYear = dbF["air_begin_datetime"].year if dbF["air_begin_datetime"] != None else dbF["filled_datetime"].year
        if fillYear == reportYear:
            fillReportTabulated.printRow(dbF,fh)
            fh.write("\\fillTableNextRow\n")
    conn.close()
    # 
    # end env and file
    # 
    fh.write("\\end{fillTable}\n\n\\end{document}")
    fh.close()
    # 
    # latex
    # 
    LatexFile(LATEX_IO_DIR, fileNameBase)
    # 
    # return PDF
    # 


@route('/resources/data/report/latex_download_fill_report_hybrid', method=["GET"])
@authorized('User')
def latex_download_fill_report_hybrid():
    # 
    # get desired year from parameters
    # 
    reportYear = request.params.get('year')
    if not reportYear:
        abort(400, 'Year is required.')
    try:
        reportYear = int(reportYear)
    except ValueError:
        abort(400, 'Bad year argument.')
    try:
        displayTZ = pytz.timezone(request.params.get("display_tz"))
        displayTZStr = request.params.get("display_tz")
    except:
        abort(400, 'invalid display_tz')

    tmpFileName = latex_create_fill_report_hybrid(reportYear)
    if tmpFileName:
        response.headers['Content-disposition'] = 'attachment; filename=fill_report_hybrid'+str(reportYear)+'.pdf'
        return static_file(tmpFileName+".pdf", root="./gen_data")
    else:
        pass                    # Russ?


def latex_create_fill_report_hybrid(reportYear,fileNameBase=None):
    # 
    # create random file name, open for writing, and print file preamble stuff
    # 
    if not fileNameBase:
        fileNameBase = tempfile.mktemp(prefix="fillRpt_hyb_",dir=".")
    filePath = "./gen_data/"+fileNameBase+".tex"
    fh = open(filePath, 'w')
    fh.write("\\documentclass{IsadoreReportHybridTab}\n\\rptTitle{Fill report (hybrid)}\n\\begin{document}\n\n")
    # 
    # get all fills (will filter by year later)
    # 
    conn = util.getConn()
    # TODO: have DB only return fills from proper year to save CPU?
    tmpDBFills = util.getRowsFromTable("fill",conn=conn)
    # 
    # get list of hybrids
    # 
    hybridSet = list(set([tdbf["hybrid_code"] for tdbf in tmpDBFills if util.getStartAirDT(tdbf).year == reportYear]))
    hybridList = [hs for hs in hybridSet if hs]
    # 
    # create one table for each hybrid found
    # 
    # grab fills for the current year
    if hybridList:
        dbFills = [tdbf for tdbf in tmpDBFills if util.getStartAirDT(tdbf).year == reportYear]
        for hyb in hybridSet:
            hybridReport.printHybridTable(hyb, dbFills, fh)
        # 
        # end file
        # 
        fh.write("\n\n\\end{document}")
        # 
        # latex
        # 
        LatexFile(LATEX_IO_DIR, fileNameBase)
        # 
        # return PDF
        # 
        return LATEX_IO_DIR+"/"+fileNameBase+".pdf"
    return None
        

def LatexFile(IOdir,LatexFileName):
    # 
    # Latex run 1
    # 
    p=subprocess.Popen(("/usr/bin/latex","-interaction=nonstopmode","-output-directory="+IOdir, IOdir+"/"+LatexFileName+".tex"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("latex failed: "+output[1])
    # 
    # Latex run 2
    # 
    p=subprocess.Popen(("/usr/bin/latex","-interaction=nonstopmode","-output-directory="+IOdir, IOdir+"/"+LatexFileName+".tex"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("latex failed: "+output[1])
    # 
    # Latex run 3
    # 
    p=subprocess.Popen(("/usr/bin/latex","-interaction=nonstopmode","-output-directory="+IOdir, IOdir+"/"+LatexFileName+".tex"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("latex failed: "+output[1])
    # 
    # dvips
    # 
    p=subprocess.Popen(("/usr/bin/dvips","-P","pdf","-t","landscape","-o", IOdir+"/"+LatexFileName+".ps", IOdir+"/"+LatexFileName+".dvi"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("dvips failed: "+output[1])
    # 
    # ps2pdf
    # 
    p=subprocess.Popen(("/usr/bin/ps2pdf",IOdir+"/"+LatexFileName+".ps",IOdir+"/"+LatexFileName+".pdf"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("ps2pdf failed: "+output[1])
    # 
    # return
    # 
    return IOdir+"/"+LatexFileName+".pdf"


def printFillInfo(fillInfo):
    print fillInfo
    fillInfo["depth1"] = fillInfo["depth1"] if fillInfo["depth1"] else 0
    fillInfo["depth2"] = fillInfo["depth2"] if fillInfo["depth2"] else 0
    if fillInfo['field']:
        field = fillInfo['field'][0]
    else:
        field = "None"
    if fillInfo['hybrid']:
        hybrid=fillInfo['hybrid'][0]
    else:
        hybrid = "None"
    returnStr = "\\dryerMgmtFillLineOneA{{ {} }} {{ {} }} {{ {} }} {{ {} }} {{ {:.1f}\\% }} {{ {:.1f} }} {{ {:n} }} {{ {:.1f} }} {{ {} }}\n".format(
    # returnStr = "\\dryerMgmtFillLineOneA{{ {} }} {{ {} }} {{ {} }} {{ {} }} {{ {}\\% }} {{ {:.2f} }} {{ {} }} {{ {} }} {{ {} }}\n".format(
        fillInfo["fillNum"],
        fillInfo["binNum"],
        field,
        escapeSpecialLatexChars(hybrid),
        fillInfo["loadMC"],
        (float(fillInfo["depth1"])+float(fillInfo["depth2"]))/2.0,
        int(fillInfo["SRBu"]),
        fillInfo["upHrs"],
        fillInfo["airStart"].replace(tzinfo=None).strftime("%m-%d %H:%M") if fillInfo["airStart"] else "NA")

    returnStr += "\dryerMgmtFillLineOneB {{ {!s} }} {{ {:.1f}\\% }} {{ {:.2f} }}\n".format(
        fillInfo["shellDate"],
        fillInfo["shellMC"] if fillInfo["shellMC"] else 0,
        fillInfo["dryRate"])

    returnStr += "\dryerMgmtFillLineTwo {{ {:.2f} }} {{ {!s} }}\n".format(
        float(fillInfo["downHrs"]),
        fillInfo["airRev"][0].replace(tzinfo=None).strftime("%m-%d %H:%M") if fillInfo["airRev"] else "NA")
    returnStr += "\dryerMgmtFillLineThree {{ {:.2f} }} {{ {!s} }}".format(
        float(fillInfo["totHrs"]),
        fillInfo["airStop"].replace(tzinfo=None).strftime("%m-%d %H:%M") if fillInfo["airStop"] else "NA")
    return returnStr


def printDateLine(date,loadMC,binDepth,SRBu,airHours,shellMC,dryRate):
    return "\\dryerMgmtStart{{ {!s} }} {{ {:.1f}\\% }} {{ {:.1f} }} {{ {:n} }} {{ {:.2f} }} {{ {:.1f} }} {{ {:.2f} }}\n".format(date,loadMC if loadMC else 0,binDepth,int(SRBu) if SRBu else 0,airHours,shellMC if shellMC else 0,dryRate if dryRate else 0)
    # return "\\dryerMgmtStart{{ {!s} }} {{ {:.1f}\\% }} {{ {:.1f} }} {{ {:.2f} }} {{ {:.2f} }} {{ {:.1f} }} {{ {:.2f} }}\n".format(date,0,0,0,0,0,0)

def startReportString(docTitle):
    # return "\\documentclass{IsadoreReport}\n\\begin{document}\n\n\\title{"+docTitle+"}\n\\date{\\today}\n\\maketitle\n\n"
    return "\\documentclass{IsadoreReport}\n\\rptTitle{"+docTitle+"}\n\\begin{document}\n\n{\\Huge "+docTitle+"} \\newline \\today\n\n"

def endReportString():
    return "\end{document}"

def escapeSpecialLatexChars(oldStr):
    return string.replace(string.replace(oldStr,"_","\\_"),"&","\\&")
