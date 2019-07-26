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

import numpy as np
from isadoreapp.data.reports import fillReportTabulated


def print_hybrid_table(hybrid_code, fill_rows, fh):
    pre_mcs = []
    post_mcs = []
    mc_rmvds = []
    up_airs = []
    down_airs = []
    total_airs = []
    hrs_per_pts = []
    shelled_bus = []
    tbl_rows = [fr for fr in fill_rows if fr["hybrid_code"] == hybrid_code]
    tbl_rows.sort(key=lambda x: x["fill_number"])
    # start new table
    fh.write("\\begin{hybridTable}{" + hybrid_code + "}\n")
    # for each row in table
    for tr in tbl_rows:
        # print to file and save computed values
        (pre_mc_mean, post_mc_mean,
         mc_removed, up_air_hrs,
         down_air_hrs, total_air_hrs,
         hrs_per_pt) = fillReportTabulated.print_row(tr, fh,
                                                     cmd1="\\hybridTableRowOne",
                                                     cmd2="\\hybridTableRowTwo")
        fh.write("\\hybridTableNextRow\n\n")
        pre_mcs += [pre_mc_mean]
        post_mcs += [post_mc_mean]
        mc_rmvds += [mc_removed]
        up_airs += [up_air_hrs]
        down_airs += [down_air_hrs]
        total_airs += [total_air_hrs]
        hrs_per_pts += [hrs_per_pt]
        shelled_bus += [tr["bushels"]] if tr["bushels"] else []
    # compute stats for hybrid
    pre_mc_avg = np.mean(pre_mcs)
    post_mc_avg = np.mean(post_mcs)
    mc_rmvd_avg = np.mean(mc_rmvds)
    up_air_avg = np.mean(up_airs)
    down_air_avg = np.mean(down_airs)
    total_air_avg = np.mean(total_airs)
    hrs_per_pt_avg = np.mean(hrs_per_pts)
    up_air_pct_avg = np.mean(np.array(up_airs) / np.array(total_airs))
    down_air_pct_avg = np.mean(np.array(down_airs) / np.array(total_airs))
    up_air_tot = np.sum(up_airs)
    down_air_tot = np.sum(down_airs)
    total_air_tot = np.sum(total_airs)
    # treat shelled Bu differently b/c can be empty
    if shelled_bus:
        shelled_bu_avg = np.mean(shelled_bus)
        shelled_bu_tot = np.sum(shelled_bus)
        shelled_bu_avg_str = "{:.1f}".format(shelled_bu_avg)
        shelled_bu_tot_str = "{:.1f}".format(shelled_bu_tot)
    else:
        shelled_bu_avg_str = "N/A"
        shelled_bu_tot_str = "N/A"
    # print hybrid stats rows
    fh.write("\\hybridTableAvgRowOne{" +
             "{:.1f}".format(post_mc_avg) + "}{" +
             "{:.1f}".format(pre_mc_avg) + "}{" +
             "{:.1f}".format(mc_rmvd_avg) + "}{" +
             "{:.1f}".format(up_air_avg) + "}{" +
             "{:.1f}".format(100 * up_air_pct_avg) + "}{" +
             "{:.1f}".format(down_air_avg) + "}{" +
             "{:.1f}".format(100 * down_air_pct_avg) + "}{" +
             "{:.1f}".format(total_air_avg) + "}{" +
             "{:.2f}".format(hrs_per_pt_avg) + "}\n" +
             "\\hybridTableAvgRowTwo{" + shelled_bu_avg_str + "}\n")
    fh.write("\\hybridTableNextRow\n")
    fh.write("\\hybridTableTotalRow{" +
             "{:.1f}".format(up_air_tot) + "}{" +
             "{:.1f}".format(down_air_tot) + "}{" +
             "{:.1f}".format(total_air_tot) + "}{" +
             shelled_bu_tot_str + "}\n")
    fh.write("\\hybridTableNextRow\n")
    # end table
    fh.write("\\end{hybridTable}\n\n")
    fh.flush()
