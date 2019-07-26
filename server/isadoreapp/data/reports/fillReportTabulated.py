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

import isadoreapp.util as util
import numpy as np


def print_row(fill, fh, cmd1="\\fillTableRowOne", cmd2="\\fillTableRowTwo"):
    # determine actual bin number
    bin_num = util.convertBinIDtoNum(fill["bin_id"])
    # compute up air hrs
    try:
        up_air_hrs = util.computeAirHrs(fill)
        up_air_hrs_txt = "{:.1f}".format(up_air_hrs)
    except util.UtilComputationError:
        # TODO: log error
        up_air_hrs = 0
        up_air_hrs_txt = "N/A"
    # compute down air hrs
    try:
        down_air_hrs = util.computeDownAirHrs(fill)
        down_air_hrs_txt = "{:.2f}".format(down_air_hrs)
    except util.UtilComputationError:
        # TODO: log error
        down_air_hrs = 0
        down_air_hrs_txt = "N/A"
    # compute total air hrs and percentages
    total_air_hrs = up_air_hrs + down_air_hrs
    total_air_hrs_txt = "{:.1f}".format(total_air_hrs)
    up_air_pct_txt = "{:.1f}".format(up_air_hrs / total_air_hrs * 100)
    down_air_pct_txt = "{:.1f}".format(down_air_hrs / total_air_hrs * 100)
    # compute pre and post MC means
    pre_mc_mean = None if (not fill["pre_mc"]) else np.mean(fill["pre_mc"])
    post_mc_mean = None if (not fill["post_mc"]) else np.mean(fill["post_mc"])
    pre_mc_mean_txt = "N/A" if (not pre_mc_mean) else "{:.1f}".format(pre_mc_mean)
    post_mc_mean_txt = "N/A" if (not post_mc_mean) else "{:.1f}".format(post_mc_mean)
    # compute MC removed
    mc_removed = None if (not pre_mc_mean or not post_mc_mean) else pre_mc_mean - post_mc_mean
    mc_removed_txt = "N/A" if (not mc_removed) else "{:.1f}".format(mc_removed)
    # compute hrs per pt
    hrs_per_pt_txt = "N/A"
    hrs_per_pt = None
    air_hrs = util.computeAirHrs(fill)  # returns None if cannot be computed
    if pre_mc_mean and post_mc_mean and air_hrs:
        pts_lost = pre_mc_mean - post_mc_mean
        hrs_per_pt = air_hrs / pts_lost
        hrs_per_pt_txt = "{:.1f}".format(hrs_per_pt)
    shelled_bu = "N/A" if fill["bushels"] is None else "{:.2f}".format(fill["bushels"])

    fh.write(cmd1 + "{" +
             str(fill["fill_number"]) + "}{" +
             str(bin_num) + "}{" +
             util.escapeSpecialLatexChars(fill["field_code"]) + "}{" +
             post_mc_mean_txt + "}{" +
             pre_mc_mean_txt + "}{" +
             mc_removed_txt + "}{" +
             up_air_hrs_txt + "}{" +
             up_air_pct_txt + "}{" +
             down_air_hrs_txt + "}\n" +
             cmd2 + "{" +
             down_air_pct_txt + "}{" +
             total_air_hrs_txt + "}{" +
             hrs_per_pt_txt + "}{" +
             str(fill["bushels"]) + "}\n")
    fh.flush()
    # return computed values
    return pre_mc_mean, post_mc_mean, mc_removed, up_air_hrs, down_air_hrs, total_air_hrs, hrs_per_pt


#
# running as a script
# 

configFileLoc = "/home/dane/isadoredev1-dane-home/EA/isadore_business/reports/MC_predict/"
configFilePrefix = "settings_"
configFileExt = ".cfg"

if __name__ == "__main__":
    import sys

    customerName = sys.argv[1]
    util.Single().configLoc = configFileLoc + configFilePrefix + customerName + configFileExt
    # read some basic info
    util.Single().loadSettings()
    print(util.Single().dbname)
    print(util.Single().dbuser)
    print(util.Single().dbhost)
