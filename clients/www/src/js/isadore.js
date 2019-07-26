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

function logoutFinish() {
    console.log('logoutFinish');
    window.location.replace("./login.html");
}

function logout() {
    $.ajax({
        url: "../resources/login/logout",
        type: 'PUT',
        complete: logoutFinish
    });
}

function showContentLoader() {
    var $content_loading = $('#content_loading');
    $content_loading.show();
    var $img = $('#content_loading img');
    var imgHeight = $img.height();
    var imgWidth = $('#content_loading_img').width();
    var divWidth = $content_loading.parent().parent().width();
    var divHeight = $content_loading.parent().parent().height();
    $img.css('margin-top', (divHeight - imgHeight) / 2).css('margin-left', (divWidth - imgWidth) / 2);
}

function hideContentLoader() {
    $('#content_loading').hide();
}


function updateOutdoorConditions() {
    var i, outdoorBin, name;
    outdoorBin = _.findWhere(IsadoreData.bins, {'name': 'Outdoor'});
    if (outdoorBin.readings) {
        for (i = 0; i < outdoorBin.readings.length; ++i) {
            name = IsadoreData.readTypesIdMap[outdoorBin.readings[i].read_type_id].name;
            if (name.indexOf('Temp') >= 0) {
                if (outdoorBin.readings[i].value) {
                    $('#outdoor_temp').html(
                        outdoorBin.readings[i].value.toFixed(1) + '&deg;F');
                } else {
                    $('#outdoor_temp').html('NA');
                }
            } else if (name.indexOf('Relative Humidity') >= 0) {
                if (outdoorBin.readings[i].value) {
                    $('#outdoor_humidity').html(
                        outdoorBin.readings[i].value.toFixed(1) + '%');
                } else {
                    $('#outdoor_humidity').html('NA');
                }
            } else if (name.indexOf('Barometric Pressure') >= 0) {
                if (outdoorBin.readings[i].value) {
                    $('#outdoor_pressure').html(outdoorBin.readings[i].value.toFixed(2)+'kPa');
                } else {
                    $('#outdoor_pressure').html('NA');
                }
            } else if (name.indexOf('Wet Bulb') >= 0) {
                if (outdoorBin.readings[i].value) {
                    $('#outdoor_wetbulb').html(outdoorBin.readings[i].value.toFixed(1) + '&deg;F');
                } else {
                    $('#outdoor_wetbulb').html('NA');
                }
            }
        }

    }
    $('#outdoor_wrapper').attr('data-bin_id', outdoorBin.id);
}

function updateSystemStatus() {
    if (IsadoreData.currentAlarmEvents.length > 0) {
        $('#alerts_none').hide();
        $('#alerts_yes').show();
    } else {
        $('#alerts_none').show();
        $('#alerts_yes').hide();
    }
    window.pageHandlers.help.refresh();
}

/** Hide the things they can't do with their privilege. */
function hideUnprivileged() {
    //TODO: Move setting name somewhere else
    if (!window.yas) {
        window.yas = new YourAccountSettings($('#hidden_wrapper'));
    }
    if (!window.gss) {
        window.gss = new GaugeSensorStatus($('#hidden_wrapper'));
    }
    if (!IsadoreData.selfAccount.hasPrivilege('Super User')) {
        $('.priv_super').hide();
    }
    if (!IsadoreData.selfAccount.hasPrivilege('Power User')) {
        $('.priv_power').hide();
    }
    if (!IsadoreData.selfAccount.hasPrivilege('Config User')) {
        $('.priv_config').hide();
    }
    if (!IsadoreData.selfAccount.hasPrivilege('Fill User')) {
        $('.priv_fill').hide();
    }

}

function lastReadingUpdated() {
    // Update outdoor conditions
    updateOutdoorConditions();
    updateSystemStatus();

    if (!initialHashChange) {
        initialHashChange = true;
        $(window).triggerHandler('hashchange');
        hideUnprivileged();
    } else {
        pageHandlers.current.refresh();
    }

    // Close no connection dialog
    var ed = $('#error_dialog[data-xhrstatus="0"]');
    if (ed) {
        ed.dialog('close');
    }

}

function cbResize() {
    position = $(window).scrollTop();
    $.colorbox.resize();
    $(window).scrollTop(position);
}

function fixHeights() {
    // Seems to be a chrome bug when doing reload, it uses
    // css height instead of adjust height.
    var height = $('#content').height();
    $('#main').height(height);
    $('#navigation').height(height);
    setTimeout(function () {
        var height = $('#content').height();
        $('#main').height(height);
        $('#navigation').height(height);
    }, 1000);
}

/** If client version mismatch reload. */
function checkClientVersion() {
    try {
        if (IsadoreData.general.configs.hasOwnProperty('client_version') && window.client_version !== IsadoreData.general.configs.client_version) {
            location.reload(true);
        }
    } catch (e) {
        if (console) {
            console.error(e);
        }
    }
}

$(document).ready(function () {
    var modWarning = '<p>If you were changing settings, or saving data, that may have not gone through.</p>';
    $('#content').width($('#main_center').width() - $('#navigation').width() + 'px');

    var shifterEnabled = true;
    var $nav_shifter = $('#navigation > .shifter');
    var $content_shifter = $('#content > .shifter');

    if (shifterEnabled) {
        $nav_shifter.click(function () {
            $('#navigation').hide();
            $content_shifter.show();
            $(window).resize();
        });
        $content_shifter.click(function () {
            $('#navigation').show();
            $content_shifter.hide();
            $(window).resize();
        });
    } else {
        $nav_shifter.hide();
        $content_shifter.hide();
    }
    $(window).resize(function () {
        var $content = $('#content');
        if ($('#navigation').is(':visible')) {
            $content.removeClass('full_round').width($('#main_center').width() - $('#navigation').width() + 'px');
            if (shifterEnabled) {
                $('#content').css('left', $('#navigation').width() + 'px');
            }
        } else {
            $content.addClass('full_round').width($('#main_center').width());
            $content.css('left', '0px');
            //$('#content').position({my: 'center', at: 'center', of: '#main'})
        }
    });
    $('.info_header > .timezone').text('Time Zone: ' + jstz.determine().name());
    // Catch 401s
    $.ajaxPrefilter(function(options, originalOptions, jqXHR) {
        jqXHR.originalRequestOptions = originalOptions;
    });
    $.ajaxSetup({
        error: function (xhr, status, err) {
            var ed = $('#error_dialog');
            if (xhr.status == 401) {
                logout();
                return;
            }
            ed.attr('data-xhrstatus', xhr.status);
            if (xhr.status == 0) {
                ed.html("Error: Unable to access the server, check internet connection." + modWarning).dialog({
                    zIndex: 99999,
                    modal: true,
                    buttons: {
                        Ok: function () {
                            $(this).dialog('close');
                        }
                    }
                });
            } else {
                if(console && console.error) {
                    console.error(xhr);
                    console.error(status);
                    console.error(err);
                    console.error(xhr.originalRequestOptions.url);
                }
                ed.html("Error: " + xhr.status + ", " + status + modWarning).dialog({
                    zIndex: 99999,
                    modal: true,
                    buttons: {
                        Ok: function () {
                            $(this).dialog('close');
                        }
                    }
                });
            }
        }
    });
    // Hide all pages.
    var $contentDivs = $('#content_wrapper > div');
    var $menus = $('#menu > a');
    $contentDivs.hide();
    showContentLoader();

    window.initialHashChange = false;

    IsadoreData.init();
    $(IsadoreData).on("ReadingsUpdated", function () {
        lastReadingUpdated();
    });


    window.lightboxHandlers = {
        binLightbox: new BinLightbox(),
        editFillLightbox: new EditFillLightbox(),
        accountLightbox: new AccountLightbox(),
        alarmLightbox: new AlarmLightbox(),
        deductionLightbox: new DeductionLightbox()
    };

    window.pageHandlers = {
        current: new CurrentDataHandler(),
        historical: new HistoricalDataHandler(),
        settings: new SettingsHandler(),
        help: new HelpHandler()
    };

    // Anchor bindings so back, forward, and menu works.
    $(window).bind('hashchange', function () {
        var hash = window.location.hash || '#current_data';
        checkClientVersion();
        $menus.removeClass('selected');
        $menus.addClass('unselected');
        $contentDivs.hide();
        if (hash == '#historical_data') {
            $('#content_historical_data').show();
            pageHandlers.historical.refresh();
        } else if (hash == '#settings') {
            $('#content_settings').show();
            pageHandlers.settings.refresh();
        } else if (hash == '#help') {
            $('#content_help').show();
            pageHandlers.help.refresh();
        } else if (hash == "#logout") {
            logout();
        } else {
            $('#content_current_data').show();
            pageHandlers.current.refresh();
        }
        fixHeights();
    });

    // Outdoor conditions click.
    $('#outdoor_wrapper').click(lightboxHandlers.binLightbox.binClick);
    $('#alerts').click(function () {
        console.info("clicked");
        window.location = $('#menu_help').attr('href');
    });

    // Date time pickers
    calendarRegister($('.calendar'));
    calendarImageRegister($('img[src="imgs/icon_calendar.gif"]'));
});
