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
import isadoreapp.util as util
from isadoreapp.data.reports import toLatex
import isadoreapp.uptime as uptime

config_file_loc = "/home/dane/isadoredev1-dane-home/EA/isadore_business/reports/MC_predict/"
config_file_prefix = "settings_"
config_file_ext = ".cfg"

if __name__ == "__main__":
    customer_name = sys.argv[1]
    report_year = int(sys.argv[2])
    report_type = sys.argv[3]
    tmp_file_name = customer_name + "_" + report_type + "_" + str(report_year)
    print(tmp_file_name)
    util.Single().configLoc = config_file_loc + config_file_prefix + customer_name + config_file_ext
    util.Single().loadSettings()
    print(util.Single().dbname)
    print(util.Single().dbuser)
    print(util.Single().dbhost)

    if report_type == "BinEff":
        toLatex.latex_create_bin_efficiency(report_year,
                                            tmp_file_name=tmp_file_name)
    elif report_type == "FillFull":
        toLatex.latex_create_fill_report_full(report_year,
                                              file_name_base=tmp_file_name)
    elif report_type == "FillTab":
        toLatex.latex_create_fill_report_tab(report_year,
                                             file_name_base=tmp_file_name)
    elif report_type == "HybridTab":
        toLatex.latex_create_fill_report_hybrid(report_year,
                                                file_name_base=tmp_file_name)
    elif report_type == "Uptime":
        uptime_res = uptime.compute(report_year)
        table_stuff = [(bn, dt.total_seconds() / 60. / 60., tt.total_seconds() / 60. / 60.,
                        dt.total_seconds() / tt.total_seconds()) for bn, tt, dt in
                       zip(uptime_res[0], uptime_res[1], uptime_res[2])]
        for tS in table_stuff:
            print(tS[0], tS[1], tS[2], tS[3] * 100)
    else:
        print("not a valid report type, yo!")
