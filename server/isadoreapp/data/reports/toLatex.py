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

from isadoreapp import app
import flask
from flask import request, abort
from isadoreapp.authentication import authorized
import isadoreapp.util as util
import logging
import subprocess
import tempfile
from isadoreapp.data.reports import binEfficiency as binEff
from isadoreapp.data.reports import fillReport
from isadoreapp.data.reports import fillReportTabulated
from isadoreapp.data.reports import hybridReport
import pytz

# TODO: make IO location more flexible
# LATEX_IO_DIR = "/home/dane/EA/isadore_web/server/src/data/reports/genData"
LATEX_IO_DIR = "./gen_data"
binSecID_upper = 13
binSecID_lower = 14


@app.route('/resources/data/report/latex_download_bin_efficiency', methods=["GET"])
@authorized('User')
def latex_download_bin_efficiency():
    # if not year:
    year = request.values.get('year')
    if not year:
        abort(400, 'Year is required.')
    try:
        year = int(year)
    except ValueError:
        abort(400, 'Bad year argument.')
    tmp_filename = latex_create_bin_efficiency(year)
    return flask.send_from_directory('./gen_data', tmp_filename, as_attachment=True,
                                     attachment_filename='bin_efficiency' + str(year) + '.pdf')


def latex_create_bin_efficiency(year, tmp_file_name=None):
    # 
    # grab data
    # 
    # bin numbers
    bin_numbers = util.getListOfBinNumbers()
    bin_numbers.sort()
    # create image and get list of lists fills (one list per bin, each list sorted by fill date
    bin_eff_img_fn, all_fills_by_bin = binEff.draw_allbin_activity_plot(bin_numbers, year)
    # 
    # compute table info
    # 
    table_info = []
    for bN, aF in zip(bin_numbers, all_fills_by_bin):
        full_pct, full_sec, empty_sec, total_sec = binEff.compute_bin_full_pct(aF)
        table_info += [{"binNum": bN, "fullPct": full_pct, "fullHrs": full_sec / 60. / 60.,
                        "emptyHrs": empty_sec / 60. / 60., "totalHrs": total_sec / 60. / 60.}]
    # 
    # open temporary Latex file
    # 
    if not tmp_file_name:
        tmp_file_name = tempfile.mktemp(prefix="BinEff", dir=".")
    fh = open("./gen_data/" + tmp_file_name + ".tex", 'w')
    # 
    # write latex file
    # 
    fh.write(start_report_string("Dryer Efficiency Report"))
    # use minipage to hold table/image together
    fh.write("\\begin{minipage}{\\textwidth} \n \\begin{minipage}[b]{0.35\\textwidth}\n")
    # start with table
    fh.write("\\dryerEffTblStart\n\n")
    for ti in table_info:
        fh.write("\\hline\n")
        row_string = "\\dryerEffTblRow{{ {} }} {{ {:.1f} }} {{ {:.1f} }} {{ {:.1f} }} {{ {:.2f} }}\n".format(
            ti["binNum"], ti["fullHrs"], ti["emptyHrs"], ti["totalHrs"], ti["fullPct"] * 100)
        fh.write(row_string)
    fh.write("\\dryerEffTblEnd \n\n")
    # 
    # close out table minipage and add image
    # 
    fh.write(
        "\\end{minipage} \n \\hfill \n \\begin{minipage}[t]{0.63\\textwidth} \n\
         \\includegraphics[height=0.93\\textheight,width=\\textwidth]{" + bin_eff_img_fn +
        "} \n \\end{minipage} \\end{minipage}")
    # end report
    fh.write(end_report_string())
    # close file
    fh.close()
    # 
    # latex the file
    # 
    latex_file(LATEX_IO_DIR, tmp_file_name)
    # return the file name base
    return tmp_file_name


@app.route('/resources/data/report/latex_download_fill_report_full', methods=["GET"])
@authorized('User')
def latex_download_fill_report_full():
    report_year = request.values.get('year')
    if not report_year:
        abort(400, 'Year is required.')
    try:
        report_year = int(report_year)
    except ValueError:
        abort(400, 'Bad year argument.')
    try:
        display_tz = pytz.timezone(request.values.get("display_tz"))
        display_tz_str = request.values.get("display_tz")
    except:
        abort(400, 'invalid display_tz')

    tmp_file_name = None
    tmp_file_name = latex_create_fill_report_full(report_year, tmp_file_name)
    return flask.send_from_directory('./gen_data', tmp_file_name + ".pdf", as_attachment=True,
                                     attachment_filename='fill_report_full' + str(report_year) + '.pdf')


def latex_create_fill_report_full(report_year, file_name_base=None, display_tz_str=None):
    # 
    # create random file name, open for writing, and print file preamble stuff
    # 
    if not file_name_base:
        file_name_base = tempfile.mktemp(prefix="fillRpt_full_", dir=".")
    file_path = "./gen_data/" + file_name_base + ".tex"
    fh = open(file_path, 'w')
    fh.write("\\documentclass{IsadoreReportFillFull}\n\\rptTitle{Fill report (full)}\n\\begin{document}\n\n")
    # 
    # get all fills (will filter by year later)
    # 
    conn = util.getConn()
    # TODO: sort by fill number (in SQL?)
    # TODO: have DB only return fills from proper year to save CPU?
    db_fills = util.getRowsFromTable("fill", conn=conn)
    for db_fi, db_f in enumerate(db_fills):
        print(db_fi, "/", len(db_fills))
        fill_year = db_f["air_begin_datetime"].year if db_f["air_begin_datetime"] is not None else db_f[
            "filled_datetime"].year
        if fill_year == report_year:
            # 
            # create fill plot image 
            # 
            start_dt = util.getStartAirDT(db_f)
            end_dt = util.getStopAirDT(db_f)
            fill_graph_path = None
            try:
                fill_graph_path = fillReport.create_fill_graph(start_dt, end_dt, db_f["bin_id"],
                                                               binSecID_upper, binSecID_lower)
            except:
                # TODO: log error
                print("plot of fill data not created!")
            # 
            # print the fill rpt page for the given fill if
            # the fill is from the correct year
            # 
            fillReport.print_fill_page(db_f, fh, fill_graph_path)
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
    latex_file(LATEX_IO_DIR, file_name_base)
    # 
    # return PDF
    # 
    return file_name_base


@app.route('/resources/data/report/latex_download_fill_report_tab', methods=["GET"])
@authorized('User')
def latex_download_fill_report_tab():
    # 
    # get desired year from parameters
    # 
    report_year = request.values.get('year')
    if not report_year:
        abort(400, 'Year is required.')
    try:
        report_year = int(report_year)
    except ValueError:
        abort(400, 'Bad year argument.')
    try:
        display_tz = pytz.timezone(request.values.get("display_tz"))
        display_tz_str = request.values.get("display_tz")
    except:
        abort(400, 'invalid display_tz')

    tmp_file_name = latex_create_fill_report_tab(report_year)
    return flask.send_from_directory('./gen_data', tmp_file_name + ".pdf", as_attachment=True,
                                     attachment_filename='fill_report_tab' + str(report_year) + '.pdf')


def latex_create_fill_report_tab(report_year, file_name_base=None):
    # 
    # create random file name, open for writing, and print file preamble stuff
    # 
    if not file_name_base:
        file_name_base = tempfile.mktemp(prefix="fillRpt_tab_", dir=".")
    file_path = "./gen_data/" + file_name_base + ".tex"
    fh = open(file_path, 'w')
    fh.write("\\documentclass{IsadoreReportFillTab}\n\\rptTitle{Fill report (tabulated)}\n\\begin{document}\n\n")
    # 
    # get all fills (will filter by year later)
    # 
    conn = util.getConn()
    # TODO: have DB only return fills from proper year to save CPU?
    tmp_db_fills = util.getRowsFromTable("fill", conn=conn)
    # 
    # sort by fill number
    # 
    db_fills = [tdbf for tdbf in tmp_db_fills]
    db_fills.sort(key=lambda x: x["fill_number"])
    # 
    # start table env and print table rows
    # 
    fh.write("\\begin{fillTable}\n")
    for dbFi, dbF in enumerate(db_fills):
        # if correct year, add corresponding row to table
        fill_year = dbF["air_begin_datetime"].year if dbF["air_begin_datetime"] is not None else dbF[
            "filled_datetime"].year
        if fill_year == report_year:
            fillReportTabulated.print_row(dbF, fh)
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
    latex_file(LATEX_IO_DIR, file_name_base)
    # 
    # return PDF
    # 


@app.route('/resources/data/report/latex_download_fill_report_hybrid', methods=["GET"])
@authorized('User')
def latex_download_fill_report_hybrid():
    # 
    # get desired year from parameters
    # 
    report_year = request.values.get('year')
    if not report_year:
        abort(400, 'Year is required.')
    try:
        report_year = int(report_year)
    except ValueError:
        abort(400, 'Bad year argument.')
    try:
        display_tz = pytz.timezone(request.values.get("display_tz"))
        display_tz_str = request.values.get("display_tz")
    except:
        abort(400, 'invalid display_tz')

    tmp_file_name = latex_create_fill_report_hybrid(report_year)
    if tmp_file_name:
        return flask.send_from_directory('./gen_data', tmp_file_name + ".pdf", as_attachment=True,
                                         attachment_filename='fill_report_hybrid' + str(report_year) + '.pdf')
    else:
        pass  # Russ?


def latex_create_fill_report_hybrid(report_year, file_name_base=None):
    # 
    # create random file name, open for writing, and print file preamble stuff
    # 
    if not file_name_base:
        file_name_base = tempfile.mktemp(prefix="fillRpt_hyb_", dir=".")
    file_path = "./gen_data/" + file_name_base + ".tex"
    fh = open(file_path, 'w')
    fh.write("\\documentclass{IsadoreReportHybridTab}\n\\rptTitle{Fill report (hybrid)}\n\\begin{document}\n\n")
    # 
    # get all fills (will filter by year later)
    # 
    conn = util.getConn()
    # TODO: have DB only return fills from proper year to save CPU?
    tmp_db_fills = util.getRowsFromTable("fill", conn=conn)
    # 
    # get list of hybrids
    # 
    hybrid_set = list(
        set([tdbf["hybrid_code"] for tdbf in tmp_db_fills if util.getStartAirDT(tdbf).year == report_year]))
    hybrid_list = [hs for hs in hybrid_set if hs]
    # 
    # create one table for each hybrid found
    # 
    # grab fills for the current year
    if hybrid_list:
        db_fills = [tdbf for tdbf in tmp_db_fills if util.getStartAirDT(tdbf).year == report_year]
        for hyb in hybrid_set:
            hybridReport.print_hybrid_table(hyb, db_fills, fh)
        # 
        # end file
        # 
        fh.write("\n\n\\end{document}")
        # 
        # latex
        # 
        latex_file(LATEX_IO_DIR, file_name_base)
        # 
        # return PDF
        # 
        return LATEX_IO_DIR + "/" + file_name_base + ".pdf"
    return None


def latex_file(io_dir, latex_file_name):
    # 
    # Latex run 1
    # 
    p = subprocess.Popen(("/usr/bin/latex", "-interaction=nonstopmode", "-output-directory=" + io_dir,
                          io_dir + "/" + latex_file_name + ".tex"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("latex failed: ", output[1])
    # 
    # Latex run 2
    # 
    p = subprocess.Popen(("/usr/bin/latex", "-interaction=nonstopmode", "-output-directory=" + io_dir,
                          io_dir + "/" + latex_file_name + ".tex"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("latex failed: ", output[1])
    # 
    # Latex run 3
    # 
    p = subprocess.Popen(("/usr/bin/latex", "-interaction=nonstopmode", "-output-directory=" + io_dir,
                          io_dir + "/" + latex_file_name + ".tex"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("latex failed: ", output[1])
    # 
    # dvips
    # 
    p = subprocess.Popen(
        ("/usr/bin/dvips", "-P", "pdf", "-t", "landscape", "-o", io_dir + "/" + latex_file_name + ".ps",
         io_dir + "/" + latex_file_name + ".dvi"), shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("dvips failed: ", output[1])
    # 
    # ps2pdf
    # 
    p = subprocess.Popen(
        ("/usr/bin/ps2pdf", io_dir + "/" + latex_file_name + ".ps", io_dir + "/" + latex_file_name + ".pdf"),
        shell=False, stdout=None, stderr=subprocess.PIPE)
    output = p.communicate()
    if p.returncode != 0:
        logging.error("ps2pdf failed: ", output[1])
    # 
    # return
    # 
    return io_dir + "/" + latex_file_name + ".pdf"


def print_fill_info(fill_info):
    print(fill_info)
    fill_info["depth1"] = fill_info["depth1"] if fill_info["depth1"] else 0
    fill_info["depth2"] = fill_info["depth2"] if fill_info["depth2"] else 0
    if fill_info['field']:
        field = fill_info['field'][0]
    else:
        field = "None"
    if fill_info['hybrid']:
        hybrid = fill_info['hybrid'][0]
    else:
        hybrid = "None"
    return_str = "\\dryerMgmtFillLineOneA{{ {} }} {{ {} }} {{ {} }} {{ {} }} {{ {:.1f}\\% }} {{ {:.1f} }} {{ {:n} }} {{ {:.1f} }} {{ {} }}\n".format(
        # return_str = "\\dryerMgmtFillLineOneA{{ {} }} {{ {} }} {{ {} }} {{ {} }} {{ {}\\% }} {{ {:.2f} }} {{ {} }} {{ {} }} {{ {} }}\n".format(
        fill_info["fillNum"],
        fill_info["binNum"],
        field,
        escape_special_latex_chars(hybrid),
        fill_info["loadMC"],
        (float(fill_info["depth1"]) + float(fill_info["depth2"])) / 2.0,
        int(fill_info["SRBu"]),
        fill_info["upHrs"],
        fill_info["airStart"].replace(tzinfo=None).strftime("%m-%d %H:%M") if fill_info["airStart"] else "NA")

    return_str += "\dryerMgmtFillLineOneB {{ {!s} }} {{ {:.1f}\\% }} {{ {:.2f} }}\n".format(
        fill_info["shellDate"],
        fill_info["shellMC"] if fill_info["shellMC"] else 0,
        fill_info["dryRate"])

    return_str += "\dryerMgmtFillLineTwo {{ {:.2f} }} {{ {!s} }}\n".format(
        float(fill_info["downHrs"]),
        fill_info["airRev"][0].replace(tzinfo=None).strftime("%m-%d %H:%M") if fill_info["airRev"] else "NA")
    return_str += "\dryerMgmtFillLineThree {{ {:.2f} }} {{ {!s} }}".format(
        float(fill_info["totHrs"]),
        fill_info["airStop"].replace(tzinfo=None).strftime("%m-%d %H:%M") if fill_info["airStop"] else "NA")
    return return_str


def print_date_line(date, load_mc, bin_depth, sr_bu, air_hours, shell_mc, dry_rate):
    return "\\dryerMgmtStart{{ {!s} }} {{ {:.1f}\\% }} {{ {:.1f} }} {{ {:n} }} {{ {:.2f} }} {{ {:.1f} }} {{ {:.2f} }}\n".format(
        date, load_mc if load_mc else 0, bin_depth, int(sr_bu) if sr_bu else 0, air_hours, shell_mc if shell_mc else 0,
        dry_rate if dry_rate else 0)
    # return "\\dryerMgmtStart{{ {!s} }} {{ {:.1f}\\% }} {{ {:.1f} }} {{ {:.2f} }} {{ {:.2f} }} {{ {:.1f} }} {{ {:.2f} }}\n".format(date,0,0,0,0,0,0)


def start_report_string(doc_title):
    # return "\\documentclass{IsadoreReport}\n\\begin{document}\n\n\\title{"+docTitle+"}\n\\date{\\today}\n\\maketitle\n\n"
    return "\\documentclass{IsadoreReport}\n\\rptTitle{" + doc_title + "}\n\\begin{document}\n\n{\\Huge " + doc_title + "} \\newline \\today\n\n"


def end_report_string():
    return "\end{document}"


def escape_special_latex_chars(old_str):
    return old_str.replace("_", "\\_").replace("&", "\\&")
