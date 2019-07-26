//   Copyright 2010-2019 Dan Elliott, Russell Valentine
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.

function HistoricalDataHandler() {
    var self = this;
    var manageFills = [];
    var airDeductions = [];
    var fill = null;
    var fillSub = null;
    var deduction = null;
    var naFillMin = 99999;
    var naFillMax = -99999;
    var fillMin = naFillMin;
    var fillMax = naFillMax;
    var _fillsTableInited = false;
    var deleteDialog = null;
    var init = function () {
        makeReportsPDF($('#historical_fills_report_pdf'));
        $($('#content_historical_data h2')[0]).hide();
        $('#historical_fills_report_pdf').hide();
        $('#new_fill').click(newFillClick);
        $('#historical_fills_report_view').click(viewFillReport);
        $('#historical_fills_report_type_wrapper input').click(fillReportTypeClick);
        $('#historical_fills_report_type_fill').prop('checked', true);
        $('#historical_fills_report_form_full').prop('checked', true);

        $('#new_deduction').click(newDeductionClick);
        $('#historical_bin').change(historicalBinChange);
        $('#historical_data_results').click(downloadCSV);
        $('#historical_fills_report_fills1').numeric({decimal: false, negative: false});
        $('#historical_fills_report_fills2').numeric({decimal: false, negative: false});
        $('#historical_year').numeric({decimal: false, negative: false});
        $('#historical_year').val((new Date()).getFullYear());
        lastYear_ = $('#historical_year').val();
        $('#historical_year').change(function () {
            year = parseInt($('#historical_year').val(), 10);
            if (isNaN(year)) {
                $('#historical_year').val(lastYear_);
            } else {
                lastYear_ = year;
                updateManageTable();
                updateDeductTable();
            }
        });
        deleteDialog = new IsadoreDialog('#delete_lightbox', {width: 400});
    };

    var makeReportsPDF = function($div) {
        var button, select, reports, i, report;
        $div.html('<div class="label"><label for="historical_fills_report_pdf_choice">Report</label></div>\
        <div><select id="historical_fills_report_pdf_choice"></select></div>\
        <div class="label">\
        <button id="historical_fills_report_view_pdf" type="button" value="View">View</button>\
        </div>');
        $button = $('button', $div);
        $select = $('select', $div);
        reports = [['Bin Efficiency', '../resources/data/report/latex_download_bin_efficiency'], ['Hybrid Tabulated', '../resources/data/report/latex_download_fill_report_tab'], ['Fill', '../resources/data/report/latex_download_fill_report_full'], ['Fill Tabulated', '../resources/data/report/latex_download_fill_report_tab']];
        for(i = 0; i < reports.length; i++) {
            report = reports[i];
            $select.append('<option value="'+report[1]+'">'+report[0]+'</option>');
        }
        $button.click(function() {
            var year = $('#historical_year').val();
            var reportUrl = $select.val();
            window.open(reportUrl+'?'+HTMLHelper.makeParameters({year: year, display_tz: jstz.determine().name(), ts: new Date().getTime()}))
        });
    };

    var downloadCSV = function () {
        var start = $('#historical_start').datetimepicker('getDate');
        var end = $('#historical_end').datetimepicker('getDate');
        var bin = $('#historical_bin').val();
        var section = $('#historical_bin_section').val();
        var sensor = $('#historical_sensor_type').val();
        var raw = $('#historical_raw').is(':checked');

        var errors = [];
        if (!start || isNaN(start.getTime()) || !end || isNaN(end.getTime())) {
            errors.push("Start and end time required.");
        }

        if (!bin || bin.length == 0) {
            errors.push("At least one bin must be selected.");
        }

        if (!section || section.length == 0) {
            errors.push("At least one section must be selected.");
        }

        if (!sensor || sensor.length == 0) {
            errors.push("At least one sensor must be selected.");
        }

        var errorsDiv = $('#content_historical_data_filters div.errors');
        errorsDiv.empty();
        if (errors.length > 0) {
            errorsDiv.append(HTMLHelper.makeList(errors));
            errorsDiv.show();
            fixHeights();
            return;
        }
        errorsDiv.hide();
        fixHeights();

        var parameters = {};
        parameters.begin_datetime = HTMLHelper.dateToParamString(start);
        parameters.end_datetime = HTMLHelper.dateToParamString(end);
        parameters.bin_ids = bin.join(",");
        parameters.bin_section_ids = section.join(",")
        parameters.read_type_ids = sensor.join(",")
        parameters.raw = raw;
        parameters.ts = new Date().getTime();

        window.open('../resources/data/csv_download?' + HTMLHelper.makeParameters(parameters) + "/csvdata.zip", 'dl');
    };

    var historicalBinChange = function () {
        var binId = $('#historical_bin').val();
        var bin = IsadoreData.getBin(binId);

    };

    var fillReportTypeClick = function () {
        if ($('#historical_fills_report_type_fill').is(':checked')) {
            $('#historical_fills_report_form_full').show();
            $('#historical_fills_report_form_wrapper label[for="historical_fills_report_form_full"]').show();
            $('#historical_fills_report_form_csv').show();
            $('#historical_fills_report_form_wrapper label[for="historical_fills_report_form_csv"]').show();
            $('#historical_fills_report_form_full').prop('checked', true);
        } else if ($('#historical_fills_report_type_hybrid').is(':checked')) {
            $('#historical_fills_report_form_full').hide();
            $('#historical_fills_report_form_wrapper label[for="historical_fills_report_form_full"]').hide();
            $('#historical_fills_report_form_csv').hide();
            $('#historical_fills_report_form_wrapper label[for="historical_fills_report_form_csv"]').hide();
            $('#historical_fills_report_form_tab').prop("checked", true);
        }
    };

    var viewFillReport = function () {
        var year = $('#historical_year').val();
        var begin_fill_number = $('#historical_fills_report_fills1').val();
        var end_fill_number = $('#historical_fills_report_fills2').val();
        var type = null;
        var form = null;
        if ($('#historical_fills_report_type_fill').is(':checked')) {
            type = "fill";
        } else {
            type = "hybrid";
        }
        if ($('#historical_fills_report_form_full').is(':checked')) {
            form = 'full';
        } else if ($('#historical_fills_report_form_tab').is(':checked')) {
            form = 'tab';
        } else {
            form = 'csv';
        }
        //TODO: Check for valid input.
        window.open('../resources/data/report/fill_report?year=' + year + "&begin_fill_number=" + begin_fill_number + "&end_fill_number=" + end_fill_number + "&type=" + type + "&form=" + form + '&display_tz=' + encodeURIComponent(jstz.determine().name()), 'fillreport' + year + "_" + begin_fill_number + "_" + end_fill_number + "_" + type + "_" + form);
    };

    var deleteFillCanceled = function () {
        deleteDialog.close();
    };

    var deleteFillDone = function () {
        $('#delete_lightbox_delete_spinner').hide();
        $('#delete_lightbox_delete').show();
        $('#delete_lightbox_cancel').show();
        window.pageHandlers.historical.refresh();
        deleteFillCanceled();
    };

    var deleteFillConfirmClick = function () {
        $('#delete_lightbox_delete').hide();
        $('#delete_lightbox_cancel').hide();
        $('#delete_lightbox_delete_spinner').show();
        $.ajax({
            url: '../resources/data/fills/' + fill.id,
            type: 'DELETE',
            dataType: 'text',
            success: function() {
                DataManager.dataPub({key: 'fill', 'type': 'delete', 'year': lastYear_, ids: [fill.id]});
                deleteFillDone();
            }
        });
    };

    var deleteFillClick = function (event) {
        $('#delete_lightbox_delete_spinner').hide();
        $('#delete_lightbox_delete').show();
        $('#delete_lightbox_cancel').show();
        var fid = parseInt(_.parseInt($(event.currentTarget).closest('tr').attr('data-fill_id')), 10);
        fill = _.findWhere(manageFills, {'id': fid});
        $('#delete_lightbox h1:first').html('Delete Fill');
        $('#delete_lightbox_entry_info').html('Fill #' + fill.fill_number + '.');
        $('#delete_lightbox_delete').unbind('click');
        $('#delete_lightbox_delete').click(deleteFillConfirmClick);
        $('#delete_lightbox_cancel').unbind('click');
        $('#delete_lightbox_cancel').click(deleteFillCanceled);
        deleteDialog.open();
    };

    var editFillClick = function (event) {
        var fid = parseInt($(event.currentTarget).closest('tr').attr('data-fill_id'), 10);
        fill = _.findWhere(manageFills, {'id': fid});
        lightboxHandlers.editFillLightbox.open({year: lastYear_, fill_id: fill.id});
    };

    var updateManageTable2 = function (d) {
        var ii, fill, fillsTable, fillRow;
        manageFills = d.fills;
        fillsTable = [];
        fillMin = naFillMin;
        fillMax = naFillMax;
        for (ii = 0; ii < manageFills.length; ++ii) {
            fill = manageFills[ii];
            fillRow = [ 'NA', 'NA', 'NA', 'NA', 'NA', HTMLHelper.actionButtons,
                'NA' ];
            fillRow[0] = fill.fill_number;
            if (fill.fill_number < fillMin) {
                fillMin = fill.fill_number;
            }
            if (fill.fill_number > fillMax) {
                fillMax = fill.fill_number;
            }
            fillRow[1] = IsadoreData.getBin(fill.bin_id).name.split(' ')[1];
            fillRow[2] = fill.rotation_number;
            if (fill.hybrid_code) {
                fillRow[3] = fill.hybrid_code;
            }
            if (fill.field_code) {
                fillRow[4] = fill.field_code;
            }
            fillRow[6] = fill.id;
            fillsTable.push(fillRow);
        }
        if (_fillsTableInited) {
            $('#historical_fills_manage_table').dataTable().fnReloadAAData(fillsTable);
            $('#historical_fills_manage_table_spinner').hide();
            $('#historical_fills_manage_table').show();
        } else {
            $('#historical_fills_manage_table_spinner').hide();
            $('#historical_fills_manage_table').show();
            $('#historical_fills_manage_table').dataTable({
                "bDestroy": true,
                "bPaginate": true,
                "bFilter": true,
                "aaData": fillsTable,
                "aoColumns": [
                    {'sTitle': 'Fill #'},
                    {'sTitle': 'Bin'},
                    {'sTitle': 'Rotation'},
                    {'sTitle': 'Hybrid Code'},
                    {'sTitle': 'Field Code'},
                    {'sTitle': 'Actions', 'bSortable': false},
                    {'sTitle': 'data-fill_id', 'bVisible': false}
                ],
                'fnRowCallback': function (nRow, aData, ididx, ididxf) {
                    nRow.setAttribute('data-fill_id', aData[6]);
                    $('td:eq(5)', nRow).addClass('action');
                    $('td:not(:last-child)', nRow).unbind('click').click(
                        function (event) {
                            editFillClick(event);
                        }
                    );
                    $('span.action[data-action_type="edit"]', nRow).hide().unbind('click').click(
                        function (event) {
                            editFillClick(event).hide();
                        }
                    );
                    $('span.action[data-action_type="delete"]', nRow).unbind('click').click(
                        function (event) {
                            deleteFillClick(event);
                        }
                    );
                    return nRow;
                }
            });
            //$('#historical_fills_manage_table span.action[data-action_type="edit"]').click(editFillClick);
            //$('#historical_fills_manage_table span.action[data-action_type="delete"]').click(deleteFillClick);
            $('select[name="historical_fills_manage_table_length"]').change(function () {
                setTimeout(fixHeights, 500);
            });
            _fillsTableInited = true;

        }
        if (fillMin == naFillMin) {
            fillMin = "";
        }
        if (fillMax == naFillMax) {
            fillMax = "";
        }
        $('#historical_fills_report_fills1').val(fillMin);
        $('#historical_fills_report_fills2').val(fillMax);
        fixHeights();
        fixHeights();
        setTimeout(fixHeights, 500);
    };

    var newFillClick = function () {
        lightboxHandlers.editFillLightbox.open({year: lastYear_});
    };

    var updateManageTable = function () {
        var year;
        $('#historical_fills_manage_table').hide();
        $('#historical_fills_manage_table_spinner').show();
        year = $('#historical_year').val();
        if (isNaN(parseInt(year, 10))
            || year.length != 4) {
            return;
        }
        manageFills = [];
        DataManager.getFills({year: year, callback: updateManageTable2});
        if (fillSub) {
            DataManager.dataUnSub(fillSub);
            fillSub = null;
        }
        fillSub = DataManager.dataSub({
            key: "fill",
            type: ['edit', 'add', 'delete'],
            year: parseInt(year, 10),
            callback: function() {
                DataManager.getFills({year: year, callback: updateManageTable2});
            }
        })
    };


    var updateDeductTable2 = function (d) {
        var ii, deductionsTable, deduction, beginDate, endDate;
        airDeductions = d.air_deductions;
        deductionsTable = [];
        for (ii = 0; ii < airDeductions.length; ++ii) {
            deduction = airDeductions[ii];
            deductionRow = [ 'NA', 'NA', 'NA', HTMLHelper.actionButtons, 'NA' ];
            beginDate = newDate(deduction.begin_datetime);
            deductionRow[0] = HTMLHelper.dateToReadableO2(beginDate);
            if (deduction.end_datetime) {
                endDate = newDate(deduction.end_datetime);
                deductionRow[1] = HTMLHelper.dateToReadableO2(endDate);
                deductionRow[2] = parseInt((endDate.getTime() - beginDate.getTime()) / (1000 * 60), 10) + ' m';
            }
            deductionRow[4] = deduction.id;
            deductionsTable.push(deductionRow);
        }
        $('#historical_fills_deduct_table_spinner').hide();
        $('#historical_fills_deduct_table').show();
        $('#historical_fills_deduct_table').dataTable({
            "bDestroy": true,
            "bPaginate": false,
            "bFilter": false,
            "aaData": deductionsTable,
            "aoColumns": [
                {'sTitle': 'Start'},
                {'sTitle': 'End'},
                {'sTitle': 'Time span'},
                {'sTitle': 'Actions', 'bSortable': false},
                {'sTitle': 'data-deduction_id', 'bVisible': false}
            ],
            'fnRowCallback': function (nRow, aData, ididx, ididxf) {
                nRow.setAttribute('data-deduction_id', aData[4]);
                $('td:eq(3)', nRow).addClass('action');
                return nRow;
            }
        });
        $('#historical_fills_deduct_table span.action[data-action_type="edit"]').click(editDeductionClick);
        $('#historical_fills_deduct_table span.action[data-action_type="delete"]').click(deleteDeductionClick);
        fixHeights();
        setTimeout(fixHeights, 500);
    };


    var updateDeductTable = function () {
        var year, startYear, endYear;
        $('#historical_fills_deduct_table').hide();
        $('#historical_fills_deduct_table_spinner').show();
        year = $('#historical_year').val();
        if (isNaN(parseInt(year, 10))
            || year.length != 4) {
            return;
        }
        startYear = new Date(year, 0, 1, 0, 0, 0, 0);
        endYear = new Date(year, 11, 31, 23, 59, 59, 999);
        $.ajax({
            url: '../resources/data/air_deductions-fast',
            type: 'GET',
            dataType: 'json',
            success: updateDeductTable2,
            data: {
                'begin_span1': HTMLHelper.dateToParamString(startYear),
                'begin_span2': HTMLHelper.dateToParamString(endYear)
            },
            error: function () {
                updateDeductTable2([]);
            }
        });
    };

    var newDeductionClick = function () {
        lightboxHandlers.deductionLightbox.open(null);
    };

    var editDeductionClick = function (event) {
        var did = parseInt($(event.currentTarget).closest('tr').attr('data-deduction_id'), 10);
        deduction = _.findWhere(airDeductions, {'id': did});
        lightboxHandlers.deductionLightbox.open(deduction);
    };


    var deleteDeductionCanceled = function () {
        deleteDialog.close();
    };

    var deleteDeductionDone = function () {
        $('#delete_lightbox_delete_spinner').hide();
        $('#delete_lightbox_delete').show();
        $('#delete_lightbox_cancel').show();
        window.pageHandlers.historical.refresh();
        deleteDeductionCanceled();
    };

    var deleteDeductionConfirmClick = function () {
        $('#delete_lightbox_delete').hide();
        $('#delete_lightbox_cancel').hide();
        $('#delete_lightbox_delete_spinner').show();
        $.ajax({
            url: '../resources/data/air_deductions/' + deduction.id,
            type: 'DELETE',
            dataType: 'text',
            success: deleteDeductionDone
        });
    };

    var deleteDeductionClick = function (event) {
        var did;
        $('#delete_lightbox_delete_spinner').hide();
        $('#delete_lightbox_delete').show();
        $('#delete_lightbox_cancel').show();
        did = parseInt($(event.currentTarget).closest('tr').attr('data-deduction_id'), 10);
        deduction = _.findWhere(airDeductions, {'id': did});
        $('#delete_lightbox h1:first').html('Delete Air Deduction');
        $('#delete_lightbox_entry_info').html('Delete Air Deduction');
        $('#delete_lightbox_delete').unbind('click');
        $('#delete_lightbox_delete').click(deleteDeductionConfirmClick);
        $('#delete_lightbox_cancel').unbind('click');
        $('#delete_lightbox_cancel').click(deleteDeductionCanceled);
        deleteDialog.open();
    };

    this.refresh = function () {
        var binSelect, binSectionSelect, sTypes, ii, jj;
        var found, sensor, sensorTypeSelect;
        if (!$('#content_historical_data').is(':visible')) {
            return;
        }
        checkClientVersion();
        $('#historical_year').change();
        $('#menu_historical_data').removeClass('unselected');
        $('#menu_historical_data').addClass('selected');
        $('#content_historical_data_filters div.errors').hide();

        if (!IsadoreData.general.emchrs_per_point) {
            $('#historical_fills_deduct_wrapper').hide();
        } else {
            $('#historical_fills_deduct_wrapper').show();
        }

        binSelect = HTMLHelper.makeSelect(IsadoreData.bins, 'name', 'id');
        binSelect.attr("id", "historical_bin");
        binSelect.attr("multiple", "multiple");
        binSelect.attr("size", "6");
        $('#historical_bin').replaceWith(binSelect);

        binSectionSelect = HTMLHelper.makeSelect(IsadoreData.binSections, 'name', 'id');
        binSectionSelect.attr("id", "historical_bin_section");
        binSectionSelect.attr("multiple", "multiple");
        binSectionSelect.attr("size", "6");
        $('#historical_bin_section').replaceWith(binSectionSelect);

        sTypes = [];
        for (ii = 0; ii < IsadoreData.readTypes.length; ii++) {
            found = false;
            for (jj = 0; jj < sTypes.length; jj++) {
                if (sTypes[jj].name == IsadoreData.readTypes[ii].name) {
                    sTypes[jj].id = sTypes[jj].id + ";" + IsadoreData.readTypes[ii].id;
                    found = true;
                }
            }
            if (!found) {
                sensor = {};
                sensor.name = IsadoreData.readTypes[ii].name;
                sensor.id = IsadoreData.readTypes[ii].id;
                sTypes.push(sensor);
            }
        }
        sTypes.sort(function (a, b) {
            if (a.name > b.name) {
                return 1;
            } else if (a.name == b.name) {
                return 0;
            } else {
                return -1;
            }
        });
        sensorTypeSelect = HTMLHelper.makeSelect(sTypes, 'name', 'id');
        sensorTypeSelect.attr("id", "historical_sensor_type");
        sensorTypeSelect.attr("multiple", "multiple");
        sensorTypeSelect.attr("size", "6");
        $('#historical_sensor_type').replaceWith(sensorTypeSelect);
        //Compress sensors


        fixHeights();
    };
    init();
}
