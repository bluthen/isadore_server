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

/** Functions that get data from the server api. */

(function () {

    "use strict";
    window.IsadoreData = {
        _lastReadingsTimeout: null,
        selfAccount: null,
        selfAlarms: [],
        bins: [],
        binSections: [],
        binSectionsIdMap: {},
        privileges: [],
        privilegesIdMap: {},
        privilegesNameMap: {},
        alarmTypes: [],
        alarmTypesIdMap: {},
        alarmContactTypes: [],
        alarmContactTypesIdMap: {},
        deviceTypes: [],
        deviceTypesIdMap: {},
        sensorTypes: [],
        sensorTypesIdMap: {},
        readTypes: [],
        readTypesIdMap: {},
        general: {},
        currentAlarmEvents: [],
        lastReadings: [],
        lastReadingsTime: "NA",
        lastReadingsDatetime: null,

        /**
         * inits data object and starts fetching data.
         *
         * @param readCallback
         *            Called when new reading data has been fetched.
         */
        init: function () {
            var self = window.IsadoreData;
            //TODO: Ajax errors
            async.parallel([
                function (callback) {
                    $.ajax({
                        url: '../resources/data/fill_types',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            callback(null, {'fillTypes': d.fill_types});
                        }
                    });
                },
                function (callback) {
                    $.ajax({
                        url: '../resources/conf/bins-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            callback(null, {'bins': d.bins.sort(self._binCompare)});
                        }
                    });
                },
                function (callback) {
                    $.ajax({
                        url: '../resources/conf/bin_sections-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            callback(null, {
                                'binSections': d.bin_sections,
                                'binSectionsIdMap': _.indexBy(d.bin_sections, 'id')
                            });
                        }
                    });
                }, function (callback) {
                    $.ajax({
                        url: '../resources/privileges-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            var privileges = _.sortBy(d.privileges, 'id');
                            var privilegesIdMap = _.indexBy(privileges, 'id');
                            var privilegesNameMap = _.indexBy(privileges, 'name');
                            callback(null, {
                                'privileges': privileges,
                                'privilegesIdMap': privilegesIdMap,
                                'privilegesNameMap': privilegesNameMap
                            });
                        }
                    });
                }, function (callback) {
                    $.ajax({
                        url: '../resources/alarms/alarm_types-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            callback(null, {
                                'alarmTypes': d.alarm_types,
                                'alarmTypesIdMap': _.indexBy(d.alarm_types, 'id')
                            });
                        }
                    });
                }, function (callback) {
                    $.ajax({
                        url: '../resources/alarms/alarm_contact_types-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            callback(null, {
                                'alarmContactTypes': d.alarm_contact_types,
                                'alarmContactTypesIdMap': _.indexBy(d.alarm_contact_types, 'id')
                            });
                        }
                    });
                }, function (callback) {
                    $.ajax({
                        url: '../resources/conf/devices-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            callback(null, {'devices': d.devices});
                        }
                    });
                }, function (callback) {
                    $.ajax({
                        url: '../resources/conf/read_types-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            callback(null, {'readTypes': d.read_types, 'readTypesIdMap': _.indexBy(d.read_types, 'id')});
                        }
                    });
                }, function (callback) {
                    $.ajax({
                        url: '../resources/conf/sensor_types-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            callback(null, {
                                'sensorTypes': d.sensor_types,
                                'sensorTypesIdMap': _.indexBy(d.sensor_types, 'id')
                            });
                        }
                    });
                }, function (callback) {
                    $.ajax({
                        url: '../resources/conf/device_types-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (d) {
                            self._getSensorTypesForEachDevice({deviceTypes: d.device_types}, function(err, results) {
                                results.deviceTypesIdMap = _.indexBy(results.deviceTypes, 'id');
                                callback(err, results);
                            });
                        }
                    });
                }, function (callback) {
                    $.ajax({
                        url: '../resources/accounts/self-fast',
                        type: 'GET',
                        dataType: 'json',
                        success: function (acc) {
                            var selfAccount = acc;
                            if (selfAccount.configs) {
                                try {
                                    selfAccount.configs = JSON.parse(selfAccount.configs);
                                } catch (e) {
                                    if (console && console.error) {
                                        console.error('Failed to parse account configs');
                                    }
                                }
                            }
                            selfAccount.hasPrivilege = function (privStr) {
                                var checkPriv = self.privilegesNameMap[privStr];
                                return this.privilege_id >= checkPriv.id;
                            };
                            callback(null, {selfAccount: selfAccount});
                        }
                    });
                }

            ], function (err, results) {
                var i;
                for (i = 0; i < results.length; i++) {
                    _.extend(self, results[i])
                }
                self._updateReadingData();
            });
        },
        /**
         * Gets the best guess as to the current fill for a bin.
         *
         * @param binId
         *            the bin to check for fill.
         * @param callbacks
         *            A callback after it is complete, given fill as a
         *            parameter, if null then no fill was found.
         */
        getBinCurrentFill: function (binId, callbacks) {
            var self = window.IsadoreData;
            self.getDataAll({
                url: '../resources/data/fills',
                callbacks: function (fillArray) {
                    if (fillArray.length > 0) {
                        self._getBinCurrentFill2(fillArray, callbacks);
                    } else {
                        $.ajax({
                            url: '../resources/data/fills-fast',
                            type: 'GET',
                            dataType: 'json',
                            success: function (dataXlink) {
                                self._getBinCurrentFill2(dataXlink.fills, callbacks);
                            },
                            data: {
                                'bin_id': binId
                            }
                        });
                    }
                },
                parameters: {'bin_id': binId, 'during_datetime': 'now'}
            });
        },
        /** Callback for getBinCurrentFill. */
        _getBinCurrentFill2: function (fillArray, callbacks) {
            var fill, ii;
            // Get last fill.
            fill = null;
            for (ii = 0; ii < fillArray.length; ++ii) {
                if (!fill || newDate(fill.air_begin_datetime) < newDate(fillArray[ii].air_begin_datetime)) {
                    fill = fillArray[ii];
                }
            }
            if (callbacks instanceof Function) {
                callbacks(fill);
            } else if (callbacks instanceof Array) {
                for (ii = 0; ii < callbacks.length; ++ii) {
                    callbacks[ii](fill);
                }
            }
        },
        /**
         * Gets and sets sensor types that can belong to the device.
         */
        _getSensorTypesForEachDevice: function (result, callback) {
            var self = window.IsadoreData;
            var ii, sensorTypeFunc;
            var deviceTypesSensorTypesCount = 0;
            sensorTypeFunc = function (filledArray, device_type) {
                device_type.sensor_types = filledArray;
                deviceTypesSensorTypesCount++;
                if (deviceTypesSensorTypesCount == result.deviceTypes.length) {
                    callback(null, result)
                }
            };
            for (ii = 0; ii < result.deviceTypes.length; ii++) {
                self.getDataAll({
                    url: '../resources/conf/sensor_types',
                    callbacks: sensorTypeFunc,
                    parameters: {'device_type_id': result.deviceTypes[ii].id},
                    extraArgs: result.deviceTypes[ii]
                });
            }
        },
        /**
         * Get readings from last reading, then update content. Add timeout to
         * update next interval or every minute if interval is past.
         */
        _updateReadingData: function () {
            var self = window.IsadoreData;
            //60 second backup timer in case of server failure.
            self._lastReadingsTimeout = setTimeout(function () {
                self._updateReadingData();
            }, 7500); //TODO: Make timeout value a config?
            $.ajax({
                url: '../resources/optimized_updates',
                type: 'GET',
                dataType: 'json',
                data: {account_id: self.selfAccount.id},
                success: function(result_data) {
                    var ret = {
                        selfAlarms: result_data.alarms,
                        general: result_data.general,
                        currentAlarmEvents: result_data.events
                    };

                    var i, sd = result_data.sensor_data;
                    for (i = 0; i < sd.length; i++) {
                        sd[i].datetime = newDate(sd[i].datetime);
                    }
                    ret.lastControlReadings = sd;

                    ret.lastReadings = result_data.readings;
                    _.each(ret.lastReadings, function(r) {
                        r.datetime = newDate(r.datetime);
                    });
                    ret.lastReadingsDatetime = _.max(ret.lastReadings, function(r) {
                        return r.datetime;
                    }).datetime;
                    ret.lastReadingsTime = HTMLHelper.dateToReadableO2(ret.lastReadingsDatetime, true);

                    self._readingsUpdated(ret);
                }
            });
        },
        /** Set sensors for each device. */
        _setSensorsForDevice: function (filledArray, callback) {
            var devices, devicesCount, ii, sensorSucFunc;
            var self = window.IsadoreData;
            devices = filledArray;
            if (!devices || devices.length == 0) {
                callback(devices);
                return;
            }
            devices = filledArray;
            devicesCount = 0;
            sensorSucFunc = function (filledArray, device) {
                device.sensors = filledArray;
                devicesCount++;
                if (devicesCount == devices.length) {
                    callback(devices);
                }
            };
            for (ii = 0; ii < devices.length; ++ii) {
                self.getDataAll({
                    url: '../resources/conf/sensors',
                    callbacks: sensorSucFunc,
                    parameters: {'device_id': devices[ii].id},
                    extraArgs: devices[ii]
                });
            }
        },
        /** Call back with devices with sensors set in it. */
        getDevices: function (bin_id, callback) {
            var self = window.IsadoreData;
            self.getDataAll({
                url: '../resources/conf/devices',
                callbacks: self._setSensorsForDevice,
                parameters: {'bin_id': bin_id, 'year': new Date().getFullYear()},
                extraArgs: callback
            });
        },
        /**
         * Get bin object by binId.
         * @param binId the id of the bin you want.
         */
        getBin: function (binId) {
            var self = window.IsadoreData;
            return _.findWhere(self.bins, {'id': _.parseInt(binId)});
        },
        /**
         * Goes through the xlink returned and gets fills up an array with the data
         * by following those links.
         *
         * @param args
         *            key/value pairs of the following.
         *
         * @key url (Required) The url to get a list of urls (required).
         * @key callbacks (Required) function or array of functions, that get called
         *      when everything is loaded. With filledArray of data as
         *      firstArgument.
         * @key parameters (Optional) Any parameters to give with this initial url
         *      only (Optional), null if not used.
         * @key extraArgs (Optional) Argument to pass as second argument in callback
         *      if needed.
         * @key error (Optional) Callback if there is ever a get error.
         */
        getDataAll: function (args) {
            var self=window.IsadoreData;
            $.ajax({
                url: args.url,
                type: 'GET',
                dataType: 'json',
                success: function (data) {
                    self._getDataEach(args, data);
                },
                data: args.parameters,
                error: args.error
            });
        },
        _getDataEach: function(args, xlinkdata) {
            var i, tasks = [];
            var genFetchFunc = function(xlink) {
                return function(callback) {
                    $.ajax({
                        url: ".." + xlink,
                        type: 'GET',
                        dataType: 'json',
                        success: function(data) {
                            callback(null, data);
                        },
                        error: function(er) {
                            callback(er, null);
                        }
                    });
                }
            };

            for (i = 0; i < xlinkdata.xlink.length; i++) {
                tasks.push(genFetchFunc(xlinkdata.xlink[i]));
            }

            async.parallel(tasks, function(errs, results) {
                var er;
                //If non null results
                er = _.find(errs);
                if (er) {
                    args.error(er);
                } else {
                    if(_.isFunction(args.callbacks)) {
                        args.callbacks(results, args.extraArgs);
                    } else if (_.isArray(args.callbacks)) {
                        _.each(args.callbacks, function(cb) {
                            cb(results, args.extraArgs);
                        });
                    }
                }
            });
        },
        _readingsUpdated: function (temp) {
            var lrd;
            var self = window.IsadoreData;
            self.general = temp.general;
            try {
                self.general.configs = JSON.parse(self.general.configs);
                if (!self.general.configs) {
                    self.general.configs = {};
                }
                if (window.client_version === undefined) {
                    if (self.general.configs.hasOwnProperty('client_version')) {
                        window.client_version = self.general.configs.client_version;
                    } else {
                        window.client_version = -1;
                    }
                }
                if (self.selfAccount.configs && self.selfAccount.configs.hasOwnProperty('sensor_view')) {
                    if (self.general.configs.hasOwnProperty('sensor_view')) {
                        self.general.configs.sensor_view = _.assign(self.general.configs.sensor_view, self.selfAccount.configs.sensor_view);
                    } else {
                        self.general.configs.sensor_view = self.selfAccount.configs.sensor_view;
                    }
                }

            } catch (e) {
                console.error('Unable to parse general_config.configs');
            }
            document.title = 'Isadore - ' + self.general.customer_name;
            $('.info_header > .dryer_name').text('Dryer: ' + self.general.customer_name);
            self.currentAlarmEvents = temp.currentAlarmEvents;
            self.selfAlarms = temp.selfAlarms;
            if (temp.lastReadings.length > 0) {
                self.lastReadingsTime = temp.lastReadingsTime;
                self.lastReadingsDatetime = temp.lastReadingsDatetime;

                self.lastReadings = temp.lastReadings;

                lrd = newDate(self.lastReadingsTime);

                // Overwrite control values in lastReading
                _.each(temp.lastControlReadings, function(cr) {
                    var reading = _.find(self.lastReadings, {bin_id: cr.bin_id, bin_section_id: cr.bin_section_id,
                        read_type_id: cr.read_type_id});
                    if (reading) {
                        reading.value = null;
                        reading.current_count = 1;
                        if ((lrd - cr.datetime) < 10 * 60 * 1000) {
                            reading.value = cr.value;
                            reading.control_overwrite = true;
                        }
                    }
                });

            }

            clearTimeout(self._lastReadingsTimeout);
            self._lastReadingsTimeout = setTimeout(function () {
                self._updateReadingData();
            }, 7500); //TODO: Use config?

            self._readingsUpdated2();


        },
        _readingsUpdated2: function() {
            var self = this, reading, bin_id, bin, ii;
            //Reset readings on all bins
            for (ii = 0; ii < self.bins.length; ++ii) {
                self.bins[ii].readings = [];
            }

            // Associate them with the bins.
            for (ii = 0; ii < self.lastReadings.length; ++ii) {
                reading = self.lastReadings[ii];
                bin_id = self.lastReadings[ii].bin_id;
                bin = self.getBin(bin_id);
                bin.readings.push(reading);
            }

            // CALL callbacks
            setTimeout(function() {
                $(self).triggerHandler('ReadingsUpdated');
            }, 0);
        },
        /** Comparator to sort bin by position, y then x. */
        _binCompare: function (a, b) {
            if (a.y < b.y) {
                return -1;
            }
            if (a.y > b.y) {
                return 1;
            }
            if (a.x < b.x) {
                return -1;
            }
            return 1;
        }
    };
}());
