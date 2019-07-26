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

function EditFillLightbox() {
    var self=this;
    var fill = null;
    var _year = null;
    var _dataBindingsEnabled = false;
    var arrayRemoveButton = '<button type="button" value="Remove"><img src="imgs/icon_delete_button.png" alt="delete"/></button>';
    var _dirty = false;
    var _dirtyOverride = false;
    var closeCallback = null;
    var dialog = null;
    var shellerSelectHTML = null;
    var DM_MC_SENSOR_TYPE_ID = 300;
    var _parseType = function (typeStr) {
        var type = {};
        var n, i;
        if (typeStr && typeStr.indexOf("numeric") === 0) {
            n = {decimal: '.', negative: true};
            type.type = 'numeric';
            typeStr = typeStr.split(';');
            for (i = 1; i < typeStr.length; i++) {
                if (typeStr[i].indexOf('decimal:') == 0) {
                    if (typeStr[i].split(':')[1] === 'false') {
                        n.decimal = false;
                    }
                } else if (typeStr[i].indexOf('negative:') == 0) {
                    if (typeStr[i].split(':')[1] === 'false') {
                        n.negative = false;
                    }
                }
            }
            _.assign(type, n);
        } else if (typeStr && typeStr.indexOf('datetime') === 0) {
            type.type = 'datetime'
        } else if (typeStr && typeStr.indexOf('array') === 0) {
            type.type = 'array';
            typeStr = typeStr.split(';');
            if (typeStr[1].indexOf("datetime") === 0) {
                type.subtype = 'datetime';
            }
        } else {
            type.type = 'string';
        }
        return type;
    };
    var _formTypes = function (selections) {
        selections.each(
            function (index, element) {
                var type = _parseType($(element).attr('data-type'));
                var n = {};
                if ($(element).prop('tagName') != 'select' && type.type === 'numeric') {
                    n.decimal = type.decimal;
                    n.negative = type.negative;
                    console.log('_formTypes', element, n);
                    $(element).numeric(n);
                }
            }
        );
    };
    var _dataBind = function (selections) {
        selections.change(function (e) {
            if (!_dataBindingsEnabled) {
                return;
            }
            var key = $(e.target).attr('data-key');
            var type = _parseType($(e.target).attr('data-type'));
            var val = $(e.target).val().trim();
            var tmp;
            displayErrors([]); //TODO: What if there was a list of errors, now you can't see the others.
            if (!val) {
                fill[key] = null;
            } else {
                //Do some specific checks.
                if (key === 'fill_number') {
                    if (val) {
                        tmp = parseInt(val, 10);
                        _uniqueFillNumberCheck(tmp);
                    }
                }
                if (key === 'filled_datetime' || key === 'air_begin_datetime') {
                    //TODO: Check that new value year is in same year as _year, if so display warn dialog.
                }
                if (type.type === 'numeric') {
                    if (type.decimal === false) {
                        fill[key] = parseInt(val, 10);
                    } else {
                        fill[key] = parseFloat(val);
                    }
                } else if (type.type === 'datetime') {
                    tmp = $(e.target).datetimepicker('getDate');
                    if (isNaN(tmp.getTime())) {
                        displayErrors(["Invalid date format for " + key]);
                    } else {
                        fill[key] = HTMLHelper.dateToParamString(tmp);
                    }
                } else if (type.type == 'array') {
                    if (type.subtype == 'datetime') { // fill.roll
                        tmp = $(e.target).datetimepicker('getDate');
                        if (isNaN(tmp.getTime())) {
                            displayErrors(["Invalid date format for " + key]);
                        } else {
                            fill[key] = [HTMLHelper.dateToParamString(tmp)];
                        }
                    }
                } else { //String
                    fill[key] = val;
                }
            }
            _dirty = true;
            console.log(key, val, type);
            console.log(fill[key]);
            console.log(fill);
        });
    };
    var init = function () {
        $('#editfill_lightbox_ok').click(function () {
            save(function () {
                close();
            });
        });
        $('#editfill_lightbox_apply').click(function () {
            save();
        });
        $('#editfill_lightbox_cancel').click(function () {
            close();
        });

        _formTypes($('#editfill_lightbox_nonarray [data-type^="numeric"]'));
        _dataBind($('#editfill_lightbox_nonarray [data-key]'));
        $('#editfill_lightbox_previous').click(function (e) {
            openIncFill(-1);
        });
        $('#editfill_lightbox_next').click(function (e) {
            openIncFill(1);
        });
        dialog = new IsadoreDialog($('#editfill_lightbox'),
            {
                title: 'Edit Fill',
                width: 750,
                beforeClose: function () {
                    if (isDirty()) {
                        close();
                        return false;
                    } else {
                        return true;
                    }
                },
                close: editFillClosed
            }
        );
    };

    /**
     * Sets the fill variable with fresh data, then calls callback.
     *
     * @param id
     *            The fill id to get.
     * @param year
     *            The year of the fill.
     * @param callback
     *            The callback to call after setting the fill.
     */
    var reloadFill = function (year, id, bin_id, callback) {
        var tmp;
        _year = year;
        _dirty = false;
        if (id !== null) {
            DataManager.getFills({year: year, ids: [id], callback: function (d) {
                fill = d.fills[0];
                callback();
            }});

        } else {
            //New fills are auto dirty
            _dirty = true;
            fill = {id: null};

            $('#editfill_lightbox_nonarray [data-key]').each(function (index, element) {
                var key = $(element).attr('data-key');
                fill[key]=null;
            });
            tmp=$('#editfill_lightbox_bin');
            if (bin_id) {
                console.log('Trying to set bin to bin_id=' + bin_id);
                fill.bin_id = bin_id;
                tmp.val(bin_id)
            }
            fill.bin_id = parseInt(tmp.val(), 10);
            fill.fill_type_id = 1; //Normal fill
            $('#editfill_lightbox_fill_type').val(fill.fill_type_id);
            fill.roll_datetime = null;
            fill.pre_mc = null;
            fill.post_mc = null;
            fill.during_mc = null;
            fill.sheller_windows = [];
            //Lets get next fill_number
            DataManager.getFills({year: year, callback: function (d) {
                var max_fill_number = 0;
                var i;
                for (i = 0; i < d.fills.length; i++) {
                    if (d.fills[i].fill_number > max_fill_number) {
                        max_fill_number = d.fills[i].fill_number;
                    }
                }
                fill.fill_number = max_fill_number + 1;
                callback();
            }});
        }
    };

    /**
     * Toggles showing spinner and disabling fields.
     *
     * @param processing
     *            If true show spinner.
     */
    var _spinning = function (processing) {
        if (processing) {
            //hide button
            $('#editfill_lightbox_save').hide();
            //show spinner
            $('#editfill_lightbox_save_spinner').show();
            //disable fields
            $('#editfill_lightbox_nonarray input, #editfill_lightbox_nonarray select, #editfill_lightbox_nonarray textarea').each(
                function (index, value) {
                    $(value).attr('disabled', 'true');
                }
            );
        } else {
            //hide button
            $('#editfill_lightbox_save').show();
            //show spinner
            $('#editfill_lightbox_save_spinner').hide();
            //disable fields
            $('#editfill_lightbox_nonarray input, #editfill_lightbox_nonarray select, #editfill_lightbox_nonarray textarea').each(
                function (index, value) {
                    $(value).removeAttr('disabled');
                }
            );
        }
    };

    var isDirty = function () {
        var arrays_dirty = false;
        //TODO: If they didn't click out of a text box yet, it won't get the change.
        $('#editfill_lightbox [data-arrayadd="true"]').each(function (index, element) {
            if ($(element).val().trim()) {
                arrays_dirty = true;
            }
        });
        return !_dirtyOverride && (_dirty || arrays_dirty);
    };

    var _uniqueFillNumberCheck = function (fill_number) {
        var fill_number_check = function (fills) {
            var i;
            for (i = 0; i < fills.fills.length; i++) {
                if (fills.fills[i].fill_number === fill_number) {
                    if (!fill.hasOwnProperty('id') || fill.id != fills.fills[i].id) {
                        //Display warning
                        $('#error_dialog').html("Warning: Fill number already in use.").dialog({
                            zIndex: 99999,
                            modal: true,
                            buttons: {
                                Ok: function () {
                                    $(this).dialog('close');
                                }
                            }
                        });
                        return;
                    }
                }
            }
        };

        DataManager.getFills({
            year: _year,
            callback: function (fills) {
                fill_number_check(fills);
            }
        });
    };


    var close = function (customClose) {
        var arrays_dirty = false;
        var msg;
        $('#editfill_lightbox [data-arrayadd="true"]').each(function (index, element) {
            if ($(element).val().trim()) {
                arrays_dirty = true;
            }
        });
        if (isDirty()) {
            if(arrays_dirty) {
                msg = "Warning: Did you forget to press the 'plus' buttons? There may be some unsaved changes. Click 'Ok' to continue and lose your changes.";
            } else {
                msg = "Warning: There may be some unsaved changes. Click 'Ok' to continue and lose your changes.";
            }

            $('#error_dialog').html(msg).dialog({
                zIndex: 99999,
                modal: true,
                buttons: {
                    Ok: function () {
                        $(this).dialog('close');
                        _dirtyOverride = true;
                        if(!customClose) {
                            dialog.close();
                        } else {
                            customClose();
                        }
                    },
                    Cancel: function () {
                        $(this).dialog('close');
                    }
                }
            });
        } else {
            if(!customClose) {
                dialog.close();
            } else {
                customClose();
            }
        }
    };

    var displayErrors = function (errors) {
        var errorsDiv = $('#editfill_lightbox_nonarray div.errors');
        if (errors.length == 0) {
            errorsDiv.hide();
        }
        errorsDiv.empty();
        if (errors.length > 0) {
            errorsDiv.append(HTMLHelper.makeList(errors));
            errorsDiv.show();
            cbResize();
        }
    };


    /**
     * Verify we have the minimum needed to save.
     * @returns True if no verify errors, false if okay.
     */
    var verify = function () {
        //Required ones
        var errors = [];
        if (!fill.fill_number) {
            errors.push('Fill Number is required and needs to be a number.');
        }
        if (!fill.bin_id) {
            errors.push('Bin is required and needs to be a number.');
        }
        if (!fill.fill_type_id) {
            errors.push('Fill type is required and needs to be a number.');
        }
        if (!fill.air_begin_datetime && !fill.filled_datetime) {
            errors.push('Either Air Start Date/Time or Filled Date/Time is required.');
        }
        displayErrors(errors);
        return (errors.length === 0);
    };

    var save = function (doneSavingCallBack) {
        if (!_dirty) {
            if(doneSavingCallBack) {
                doneSavingCallBack();
            }
        } else if (verify()) {
            console.log('Saving fill:' + fill.id);
            _doSave(doneSavingCallBack);
        }
    };

    var _getYear = function (yfill) {
        var year;
        if (yfill.filled_datetime && yfill.filled_datetime !== 'empty') {
            year = newDate(yfill.filled_datetime).getFullYear();
        } else if (yfill.started_datetime && yfill.started_datetime !== 'empty') {
            year = newDate(yfill.filled_datetime).getFullYear();
        } else {
            year = newDate(yfill.air_begin_datetime).getFullYear();
        }
        return year;
    };

    var _doSaveUpdate = function (saveFill, added, saveSuccessCallback) {
        var id = saveFill.id;
        delete saveFill.id;
        _spinning(true);
        $.ajax({
            url: '../resources/data/fills/' + id,
            type: 'PUT',
            dataType: 'text',
            data: saveFill,
            success: function () {
                var year;
                _spinning(false);
                //TODO: What if year changed, we need to send deletes.
                year = _getYear(saveFill);
                if (!added && _year !== year) {

                    DataManager.dataPub({key: 'fill', 'type': 'delete', 'year': _year, ids: [fill.id]});
                    DataManager.dataPub({key: 'fill', 'type': 'add', 'year': year, ids: [fill.id], data: {fills: [fill]}});
                } else {
                    DataManager.dataPub({key: 'fill', 'type': 'edit', 'year': year, ids: [fill.id], data: {fills: [fill]}});
                }
                $('#editfill_lightbox_save_status').html('Saved').show().fadeOut(3000);
                _dirty = false;
                if (saveSuccessCallback) {
                    saveSuccessCallback();
                }
            },
            error: function () {
                _spinning(false);
                $('#editfill_lightbox_save_status').html('Error').show();
            }
        });
    };

    var _doSave = function (saveSuccessCallback) {
        var saveFill = _.cloneDeep(fill);
        var data;
        saveFill.from_subscription_id = DataManager.getRestSubscriberId();
        _.forOwn(saveFill, function (value, key, obj) {
            var dmc, dmcd, i;
            if (key === 'id') {
                return;
            }
            if (!value) {
                obj[key] = 'empty';
                if(key==='during_mc') {
                    obj['during_mc_date'] = 'empty';
                }
            } else if(key==='during_mc') {
                dmc = [];
                dmcd = [];
                for (i = 0; i < obj[key].length; i++) {
                    dmc.push(obj[key][i][0]);
                    dmcd.push(obj[key][i][1]);
                }
                if (dmc.length === 0) {
                    obj['during_mc'] = 'empty';
                    obj['during_mc_date'] = 'empty';
                } else {
                    obj['during_mc'] = dmc.join(',');
                    obj['during_mc_date'] = dmcd.join(',');
                }
            } else if(key==='pre_mc' || key==='post_mc') {
                dmc = [];
                if (obj[key].length === 0) {
                    obj[key] = 'empty';
                } else {
                    obj[key] = obj[key].join(',');
                }
            } else if(key =='sheller_windows') {
                obj['sheller_windows'] = JSON.stringify(value);
            } else {
                if (_.isArray(value)) {
                    obj[key] = value.join(',');
                }
            }
        });
        if (!saveFill.id) {
            //Need to make the fill first.
            data = {bin_id: saveFill.bin_id, fill_type_id: saveFill.fill_type_id, air_begin_datetime: saveFill.air_begin_datetime, start_datetime: fill.filled_datetime, fill_number: fill.fill_number, from_subscription_id: saveFill.from_subscription_id};
            if (IsadoreData.air_begin_datetime === 'empty') {
                delete IsadoreData.air_begin_datetime;
            }
            if (IsadoreData.filled_datetime === 'empty') {
                delete IsadoreData.filled_datetime;
            }

            _spinning(true);
            $.ajax({
                url: '../resources/data/fills',
                type: 'POST',
                dataType: 'json',
                data: data,
                success: function (d) {
                    var id = d.xlink[0].split('/');
                    var year;
                    id = parseInt(id[id.length-1], 10);
                    fill.id = id;
                    year = _getYear(fill);
                    DataManager.dataPub({key: 'fill', 'type': 'add', 'year': year, ids: [fill.id], data: {fills: [fill]}});
                    saveFill.id = id;
                    _doSaveUpdate(saveFill, true, saveSuccessCallback);
                },
                error: function () {
                    _spinning(false);
                    $('#editfill_lightbox_save_status').html('Error').show();
                }
            });
        } else {
            _doSaveUpdate(saveFill, false, saveSuccessCallback);
        }
    };

    var openIncFill = function (inc) {
        var lfill, i, year, fill_number, cfill = null, minFill = null, maxFill = null;
        year = _year;
        fill_number = fill.fill_number + inc;
        DataManager.getFills({
            year: _year,
            callback: function(d) {
                //Find closest fill to fill_number
                for (i = 0; i < d.fills.length; i++) {
                    lfill = d.fills[i];
                    if (lfill.fill_number === fill_number) {
                        cfill = lfill;
                        break;
                    }
                    //If incrementing, and lfill is greater than fill_number and lfill < cfill
                    if (inc === 1 && lfill.fill_number > fill_number && (!cfill || lfill.fill_number < cfill.fill_number)) {
                        cfill = lfill;
                    } else if (inc === -1 && lfill.fill_number < fill_number && (!cfill || lfill.fill_number > cfill.fill_number)) {
                        cfill = lfill;
                    }
                    if (!minFill || lfill.fill_number < minFill.fill_number) {
                        minFill = lfill;
                    }
                    if (!maxFill || lfill.fill_number > maxFill.fill_number) {
                        maxFill = lfill;
                    }
                }
                if (!cfill) {
                    if (inc === -1) {
                        cfill = maxFill;
                    } else {
                        cfill = minFill;
                    }
                }
                if (!cfill) {
                    cfill = fill;
                }
                close(function() {
                    self.open({year: year, fill_id: cfill.id, customCloseCallback: closeCallback});
                });
            }
        });

    };

    /** Callback for when delete roll has been clicked.*/
    var delRoll = function (event) {
        var delidx;
        delidx = $(event.currentTarget).closest('li').attr('data-roll_idx');
        fill.roll_datetime.splice(delidx, 1);
        _dirty = true;
        refreshRolls();
    };

    /** Callback for when add roll has been clicked. */
    var addRoll = function (event) {
        var newDate, roll_datetime, ii;
        newDate = $('#editfill_lightbox_rolladd').datetimepicker('getDate');
        if (isNaN(newDate.getTime())) {
            var errors = $('#editfill_lightbox_rolls span.errors');
            errors.html('Invalid date.');
            errors.show();
            cbResize();
            return;
        }
        if (!fill.roll_datetime) {
            fill.roll_datetime = [];
        }
        fill.roll_datetime.push(HTMLHelper.dateToParamString(newDate));
        _dirty = true;
        refreshRolls();
    };

    /** Updates the page with current fill roll information. */
    var refreshRolls = function () {
        var errors, jj, ul, html;
        errors = $('#editfill_lightbox_rolls span.errors');
        errors.hide();
        html = [];
        if (fill.roll_datetime) {
            for (jj = 0; jj < fill.roll_datetime.length; ++jj) {
                html.push('<li data-roll_idx="' + jj
                    + '"><span class="roll_date" data-roll_value="' + fill.roll_datetime[jj] + '">');
                html.push(HTMLHelper.dateToReadableO2(newDate(
                    fill.roll_datetime[jj])));
                html.push('</span>');
                html.push(arrayRemoveButton);
                html.push('</li>');
            }
        }
        // New roll
        html.push('<li>');
        html.push('<input type="text" class="calendar" id="editfill_lightbox_rolladd" data-arrayadd="true"/>');
        html.push('<img src="imgs/icon_calendar.gif" data-date_id="editfill_lightbox_rolladd" alt="Pick date/time" />');
        html.push('<button id="editfill_lightbox_rolladd_add"type="button"><img src="imgs/icon_add.png" alt="add" /></button>');
        html.push('<span class="errors"></span></li>');

        ul = $('#editfill_lightbox_rolls ul');
        ul.html(html.join(''));
        // Calendar events
        calendarRegister($('.calendar', ul));
        calendarImageRegister($('img[src="imgs/icon_calendar.gif"]', ul));
        // Add click events for delete/add
        $('#editfill_lightbox_rolladd_add', ul).click(addRoll);
        $('#editfill_lightbox_rolls button[value="Remove"]').click(delRoll);
        cbResize();
    };

    /** Callback when delete MC has been clicked. */
    var delMC = function (event) {
        var ul, mcType, delIdx;
        ul = $(event.currentTarget).closest('ul');
        mcType = 'post_mc';
        if ($(ul).attr('id') == 'editfill_lightbox_pre_mc') {
            mcType = 'pre_mc';
        } else if ($(ul).attr('id') == 'editfill_lightbox_during_mc') {
            mcType = 'during_mc';
        }
        delIdx = $(event.currentTarget).closest('li').attr('data-' + mcType + '_idx');
        fill[mcType].splice(delIdx, 1);
        _dirty = true;
        refreshMC();
    };

    /** Callback when add mc has been clicked. */
    var addMC = function (event) {
        var ul, mcType, newMC, newMCDate, errors;
        ul = $(event.currentTarget).closest('ul');

        mcType = 'post_mc';
        if ($(ul).attr('id') == 'editfill_lightbox_pre_mc') {
            mcType = 'pre_mc';
        } else if ($(ul).attr('id') == 'editfill_lightbox_during_mc') {
            mcType = 'during_mc';
        }

        newMC = parseFloat($('#editfill_lightbox_add_value_' + mcType).val());
        if (isNaN(newMC)) {
            errors = $('span.errors', ul);
            errors.html('Invalid input (should be a number).');
            errors.show();
            cbResize();
            return;
        }
        newMCDate = null;
        if (mcType == 'during_mc') {
            newMCDate = $('#editfill_lightbox_add_value_datetime_during_mc').datetimepicker('getDate');
            if (!newMCDate || isNaN(newMCDate.getTime())) {
                errors = $('span.errors', ul);
                errors.html('Date required for during MC').show();
                return;
            }
            newMCDate = HTMLHelper.dateToParamString(newMCDate);
        }

        if (!fill[mcType]) {
            fill[mcType] = [];
        }
        if (mcType == 'during_mc') {
            fill[mcType].push([newMC, newMCDate])
        } else {
            fill[mcType].push(newMC);
        }
        _dirty = true;
        refreshMC();
    };

    var deleteSheller = function(event) {
        "use strict";
        var $li = $(event.currentTarget).closest('li');
        var id = parseInt($li.attr('data-id'), 10);
        _.remove(fill.sheller_windows, {id: id});
        _dirty = true;
        refreshSheller();
    };

    var addSheller = function() {
        "use strict";
        var $ul, ids, bin_id, bin_section_id, begin_datetime, end_datetime, sheller_window_id;
        if (!fill.sheller_windows) {
            fill.sheller_windows = [];
        }
        $ul = $('#editfill_lightbox_sheller_windows');
        sheller_window_id = _.random(10000000000, 999999999999);
        ids = $('select', $('#sheller_window_begin_datetime_add', $ul).parent()).val().split(',');
        bin_id = parseInt(ids[0], 10);
        bin_section_id = parseInt(ids[1], 10);
        begin_datetime = $('#sheller_window_begin_datetime_add', $ul).datetimepicker('getDate');
        end_datetime = $('#sheller_window_end_datetime_add', $ul).datetimepicker('getDate');
        if(!begin_datetime || isNaN(begin_datetime.getTime())) {
            begin_datetime = null;
        }
        if(!end_datetime || isNaN(end_datetime.getTime())) {
            end_datetime = null;
        }
        fill.sheller_windows.push({
            id: sheller_window_id,
            bin_id: bin_id,
            bin_section_id: bin_section_id,
            begin_datetime: begin_datetime,
            end_datetime: end_datetime});
        _dirty = true;
        refreshSheller();
    };

    var changeSheller = function(event) {
        "use strict";
        var $li = $(event.currentTarget).closest('li');
        var id = parseInt($li.attr('data-id'), 10);
        var sheller_window = _.find(fill.sheller_windows, {id: id});
        var bins = $('select', $li).val().split(',');
        var bin_id = parseInt(bins[0], 10);
        var bin_section_id = parseInt(bins[1], 10);
        var begin_datetime = $('#sheller_window_begin_datetime'+sheller_window.id, $li).datetimepicker('getDate');
        var end_datetime = $('#sheller_window_end_datetime'+sheller_window.id, $li).datetimepicker('getDate');
        if(!begin_datetime || isNaN(begin_datetime.getTime())) {
            begin_datetime = null;
        }
        if(!end_datetime || isNaN(end_datetime.getTime())) {
            end_datetime = null;
        }
        sheller_window.id = id;
        sheller_window.bin_id = bin_id;
        sheller_window.bin_section_id = bin_section_id;
        sheller_window.begin_datetime = begin_datetime;
        sheller_window.end_datetime = end_datetime;
        _dirty = true;
    };

    var refreshSheller = function() {
        "use strict";
        // See if any devices are configured for MC, if so make sheller select html
        if (!shellerSelectHTML) {
            var sheller_devices = _.filter(IsadoreData.devices, function(device) {
                return device.enabled_p && _.filter(device.sensors, function(sensor) {
                        return sensor.enabled_p && sensor.sensor_type_id === DM_MC_SENSOR_TYPE_ID;
                    }).length > 0;
            });
            if (sheller_devices.length > 0) {
                //Make the drop down html string
                var selectHTML = '<select>';
                _.each(sheller_devices, function (device) {
                    var bin = _.find(IsadoreData.bins, {id: device.bin_id});
                    var binSection = _.find(IsadoreData.binSections, {id: device.bin_section_id});
                    var name = bin.name + ':' + binSection.name;
                    selectHTML += '<option value="' + bin.id + ',' + binSection.id + '">' + name + '</option>';
                });
                shellerSelectHTML = selectHTML;
            } else {
                $('#editfill_lightbox_sheller_windows_wrapper').hide();
                return;
            }
        }

        $('#editfill_lightbox_sheller_windows_wrapper').show();
        var $ul = $('#editfill_lightbox_sheller_windows');
        $ul.empty();
        _.each(fill.sheller_windows, function(sheller_window) {
            var $li, optionValue, $beginDatetime, $endDatetime;
            var $select = $(shellerSelectHTML);
            //If the bin/bin_section currently set is not available we will add.
            optionValue = sheller_window.bin_id+','+sheller_window.bin_section_id;
            if($('option[value="'+optionValue+'"]', $select).length === 0) {
                var bin = _.find(IsadoreData.bins, {id: sheller_window.bin_id});
                var binSection = _.find(IsadoreData.binSections, {id: sheller_window.bin_section_id});
                var name = bin.name + ':' + binSection.name;
                $select.append('<option value="' + optionValue + '">' + name + '</option>');
            }
            $select.val(optionValue);
            $li = $('<li data-id="'+sheller_window.id+'"></li>');
            $li.append($select);
            var $removeButton = $(arrayRemoveButton);
            $li.append($removeButton);
            $li.append('</br>');
            $beginDatetime = $('<input type="text" class="calendar" id="sheller_window_begin_datetime'+sheller_window.id+'"/>');

            $li.append($beginDatetime);
            $li.append('<img src="imgs/icon_calendar.gif" data-date_id="sheller_window_begin_datetime'+sheller_window.id+'" alt="Pick date/time" />');
            $li.append('-');
            $endDatetime = $('<input type="text" class="calendar" id="sheller_window_end_datetime'+sheller_window.id+'"/>');
            $li.append($endDatetime);
            $li.append('<img src="imgs/icon_calendar.gif" data-date_id="sheller_window_end_datetime'+sheller_window.id+'" alt="Pick date/time" />');
            calendarRegister($('.calendar', $li));
            calendarImageRegister($('img[src="imgs/icon_calendar.gif"]', $li));
            if (sheller_window.begin_datetime) {
                $beginDatetime.datetimepicker('setDate', newDate(sheller_window.begin_datetime));
            }
            if (sheller_window.end_datetime) {
                $endDatetime.datetimepicker('setDate', newDate(sheller_window.end_datetime));
            }
            $ul.append($li);
            $select.change(changeSheller);
            $beginDatetime.change(changeSheller);
            $endDatetime.change(changeSheller);
            //TODO: When a change need to update inplace fill
            $removeButton.click(deleteSheller);
        });

        //New sheller window option
        var $li = $('<li></li>');
        var $select = $(shellerSelectHTML);
        $li.append($select);
        $li.append('</br>');
        var $beginDatetime = $('<input type="text" class="calendar" id="sheller_window_begin_datetime_add"/>');
        $li.append($beginDatetime);
        $li.append('<img src="imgs/icon_calendar.gif" data-date_id="sheller_window_begin_datetime_add" alt="Pick date/time" />');
        $li.append('-');
        var $endDatetime = $('<input type="text" class="calendar" id="sheller_window_end_datetime_add"/>');
        $li.append($endDatetime);
        $li.append('<img src="imgs/icon_calendar.gif" data-date_id="sheller_window_end_datetime_add" alt="Pick date/time" />');
        var $addButton = $('<button type="button" value="Add"><img src="imgs/icon_add.png" alt="add" /></button>');
        $li.append($addButton);
        calendarRegister($('.calendar', $li));
        calendarImageRegister($('img[src="imgs/icon_calendar.gif"]', $li));
        $ul.append($li);
        $addButton.click(addSheller);
    };

    /** Updates the page with current fill mc data. */
    var refreshMC = function () {
        var labels, ii, html, label, arr, jj, ul;
        labels = ["pre_mc", "post_mc"];
        if (IsadoreData.general.during_mc) {
            labels.push("during_mc");
        }
        for (ii = 0; ii < labels.length; ++ii) {
            html = [];
            label = labels[ii];
            arr = fill[label];
            if (arr) {
                for (jj = 0; jj < arr.length; ++jj) {
                    html.push('<li data-' + label + '_idx="' + jj
                        + '"><span class="mc_value">');
                    if (label == "during_mc") {
                        html.push(arr[jj][0].toFixed(1));
                        html.push('%');
                        html.push(" ");
                        html.push(HTMLHelper.dateToReadableO2(newDate(arr[jj][1])));
                    } else {
                        html.push(arr[jj].toFixed(1));
                        html.push('%');
                    }
                    html.push('</span>');
                    html.push(arrayRemoveButton);
                    html.push('</li>');
                }
            }
            html.push('<li>');
            html.push('<input type="text" id="editfill_lightbox_add_value_' + label + '" data-arrayadd="true"/>');
            if (label == "during_mc") {
                html.push('<br/><input type="text" class="calendar" id="editfill_lightbox_add_value_datetime_' + label + '" data-arrayadd="true"/>');
                html.push('<img src="imgs/icon_calendar.gif" data-date_id="editfill_lightbox_add_value_datetime_' + label + '" alt="Pick date/time" />');
            }
            html.push('<button type="button" data-mc_action="add"><img src="imgs/icon_add.png" alt="add" /></button>');
            html.push('<br/><span class="errors"></span></li>');
            ul = $('#editfill_lightbox_' + label);
            ul.html(html.join(''));
            $('input', ul).numeric({negative: false});
            if (label == "during_mc") {
                calendarRegister($('.calendar', ul));
                calendarImageRegister($('img[src="imgs/icon_calendar.gif"]', ul));
            }
            // Add click events for delete/add
            $('button[data-mc_action="add"]', ul).click(addMC);
            $('button[data-mc_action!="add"]', ul).click(delMC);
        }
        cbResize();
    };

    var editFillClosed = function () {
        _dirtyOverride = false;
        pageHandlers.historical.refresh();
        if (closeCallback) {
            closeCallback();
        }
    };

    /** Updates the top of the edit fill page, the non mc or roll data. */
    var refreshNonArrayForm = function () {
        var formElements;
        _spinning(false);

        // Blank all the non-required fields
        //Lets empty everything

        formElements = $('#editfill_lightbox_nonarray [data-key]');
        formElements.val('');

        formElements.each(function (index, element) {
            var key = $(element).attr('data-key');
            var type = _parseType($(element).attr('data-type'));
            if (fill.hasOwnProperty(key) && fill[key]) {
                if (type.type === 'datetime' || (type.subtype && type.subtype === 'datetime')) {
                    if (type.type === 'array') {
                        if (fill[key][0]) {
                            $(element).datetimepicker('setDate', newDate(fill[key][0]));
                        }
                    } else {
                        $(element).datetimepicker('setDate', newDate(fill[key]));
                    }
                } else {
                    $(element).val(fill[key]);
                }
            }
        });

        if (!IsadoreData.general.multiple_rolls) {
            $('#editfill_lightbox_nonarray_roll_option').show();
            $('#editfill_lightbox_array_rolls_option').hide();
        } else {
            $('#editfill_lightbox_nonarray_roll_option').hide();
            $('#editfill_lightbox_array_rolls_option').show();
        }

        if (!IsadoreData.general.multiple_rolls) {
            if (fill.roll_datetime && fill.roll_datetime.length > 0) {
                $('#editfill_lightbox_nonarray_roll').datetimepicker('setDate',
                    (newDate(fill.roll_datetime[0])));
            }
        }

        cbResize();
    };

    /** Called when fill data has been refresh to then display the box. */
    var open2 = function () {
        refreshNonArrayForm();
        refreshRolls();
        refreshMC();
        refreshSheller();

        _dataBindingsEnabled = true;
        $('#editfill_lightbox_overflow_spinner').hide();
        $('#editfill_lightbox_overflow').show();
        dialog.open();
    };


    /**
     * Call this to open the edit fill dialog.
     *
     * @param args.year
     *            The year of the fills.
     * @param args.fill_id
     *            the id of the fill to edit, or null if new fill.
     * @param args.customCloseCallback
     *            Callback to call when dialog closes.
     */
    this.open = function (args) {
        var realBins, binSelect, jj;
        args = _.assign({year: new Date().getFullYear(), fill_id: null, customCloseCallback: null, bin_id: null}, args);
        closeCallback = args.customCloseCallback;
        // TODO: Put realbins in data.
        _dataBindingsEnabled = false;
        _dirtyOverride = false;
        realBins = [];
        for (jj = 0; jj < IsadoreData.bins.length; ++jj) {
            if (IsadoreData.bins[jj].name.split(' ')[0] == 'Bin') {
                realBins.push(IsadoreData.bins[jj]);
            }
        }
        $('#editfill_lightbox_overflow').hide();
        $('#editfill_lightbox_overflow_spinner').show();
        $('#editfill_lightbox_save_status').empty();
        $('#editfill_lightbox_overflow div.errors').hide();
        binSelect = HTMLHelper.makeSelect(realBins, 'name', 'id');
        binSelect.attr('id', 'editfill_lightbox_bin');
        binSelect.attr('data-key', 'bin_id');
        binSelect.attr('data-type', 'numeric;decimal:false;negative:false');
        $('#editfill_lightbox_bin').replaceWith(binSelect);
        _formTypes($('#editfill_lightbox_bin'));
        _dataBind($('#editfill_lightbox_bin'));

        fillTypeSelect = HTMLHelper.makeSelect(IsadoreData.fillTypes, 'name', 'id');
        fillTypeSelect.attr('id', 'editfill_lightbox_fill_type');
        fillTypeSelect.attr('data-key', 'fill_type_id');
        fillTypeSelect.attr('data-type', 'numeric;decimal:false;negative:false');
        $('#editfill_lightbox_fill_type').replaceWith(fillTypeSelect);
        _formTypes($('#editfill_lightbox_fill_type'));
        _dataBind($('#editfill_lightbox_fill_type'));

        reloadFill(args.year, args.fill_id, args.bin_id, open2);
    };

    init();
}
