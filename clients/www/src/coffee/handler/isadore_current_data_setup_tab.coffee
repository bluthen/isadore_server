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


class window.SetupTab
    constructor: () ->
        self=this
        self.$element = $('#bin_lightbox_tabs-setup')
        self.deviceTableView = new DeviceTableView(self)
        
    refresh: (bin) ->
        self=this
        self.devices = []
        self.bin=bin
        self.deviceTableView.refresh()

# Lists bin devices in a table
class DeviceTableView
    constructor: (setupTab) ->
        self=this
        self.setupTab = setupTab
        self.devices = []
        self.$element =$('<div>
            <div id="bin_lightbox_devices">
                <h1>Devices</h1>
                <div class="right">
                    <button id="new_device" type="button" value="New Device">
                        <img src="imgs/icon_add.png" alt="add" />New Device
                    </button>
                </div>
                <img id="bin_lightbox_devices_table_spinner"
                    class="center_margins spinner" src="imgs/ajax-loader.gif"
                    alt="Loading Spinner" />
                <table id="bin_lightbox_devices_table" class="display"
                    style="width: 90%;" rules="rows">
                </table>
                <h2>Sensor Mirrors</h2>
                <div class="right">
                    <button id="new_device_sensor_mirror" type="button" value="New Sensor Mirror">
                        <img src="imgs/icon_add.png" alt="add" />New Sensor Mirror
                    </button>
                </div>
                <img id="bin_lightbox_devices_sensor_mirrors_table_spinner"
                    class="center_margins spinner" src="imgs/ajax-loader.gif"
                    alt="Loading Spinner" />
                <table id="bin_lightbox_devices_sensor_mirrors_table" class="display"
                    style="width: 90%;" rules="rows">
                </table>
            </div>
        </div>')
        self.setupTab.$element.append(self.$element)
        self.deviceView = new DeviceView(self)
        self.sensorMirrorView = new SensorMirrorView(self)
        $('#new_device', self.$element).click(() ->
            self.hide()
            self.deviceView.show().refresh(null)
        )
        $('#new_device_sensor_mirror', self.$element).click(() ->
            self.hide()
            self.sensorMirrorView.show().refresh(null)
        )
        self.deleteDialog = new IsadoreDialog('#delete_lightbox', { width: 400, title: 'Delete Confirm' })
        
        
    _editDeviceClick: (event) ->
        self=this
        did = _.parseInt($(event.currentTarget).closest('tr').attr('data-device_id'))
        device = _.findWhere(self.devices, {'id': did})
        if device
            self.hide()
            self.deviceView.show().refresh(device)
            return
        console.error('SetupTab.editDeviceClick - Device not found to edit.')
        #TODO: emit error

    # Brings up the setup tab again, on canceled.
    _deleteDeviceCanceled: () ->
        self=this
        self.deleteDialog.close()
        lightboxHandlers.binLightbox.open(self.setupTab.bin.id, self.setupTab.bin)
    
    # Resets the delete dialog, brings up the setup tab again.
    _deleteDeviceDone: () ->
        self=this
        $('#delete_lightbox_delete_spinner').hide()
        $('#delete_lightbox_delete').show()
        $('#delete_lightbox_cancel').show()
        self._deleteDeviceCanceled()

    _deleteDeviceConfirmClick: () ->
        self=this
        $('#delete_lightbox_delete').hide()
        $('#delete_lightbox_cancel').hide()
        $('#delete_lightbox_delete_spinner').show()
        $.ajax({
            url: '../resources/conf/devices/'+self.device.id
            type: 'DELETE'
            dataType: 'text'
            success: () -> self._deleteDeviceDone()
        })

    _deleteDeviceClick: (event) ->
        self=this
        $('#delete_lightbox_delete_spinner').hide()
        $('#delete_lightbox_delete').show()
        $('#delete_lightbox_cancel').show()
        did = _.parseInt($(event.currentTarget).closest('tr').attr('data-device_id'))
        self.device = _.findWhere(self.devices, {'id': did})
        $('#delete_lightbox h1:first').html('Delete Device')
        deviceType = IsadoreData.deviceTypesIdMap[self.device.device_type_id]
        $('#delete_lightbox_entry_info').html(deviceType.name+' in '+IsadoreData.binSectionsIdMap[self.device.bin_section_id].name+' of '+IsadoreData.getBin(self.device.bin_id).name)
        $('#delete_lightbox_delete').unbind('click')
        $('#delete_lightbox_delete').click(() -> self._deleteDeviceConfirmClick())
        $('#delete_lightbox_cancel').unbind('click')
        $('#delete_lightbox_cancel').click(() -> self._deleteDeviceCanceled())
        self.deleteDialog.open()

    _deleteSensorMirrorConfirmClick: (id) ->
        self=this
        $('#delete_lightbox_delete').hide()
        $('#delete_lightbox_cancel').hide()
        $('#delete_lightbox_delete_spinner').show()
        $.ajax({
            url: '../resources/conf/sensor_mirrors/'+id
            type: 'DELETE'
            dataType: 'text'
            success: () -> self._deleteDeviceDone()
        })

    _deleteSensorMirrorClick: (event) ->
        self=this
        $('#delete_lightbox_delete_spinner').hide()
        $('#delete_lightbox_delete').show()
        $('#delete_lightbox_cancel').show()
        sid = _.parseInt($(event.currentTarget).closest('tr').attr('data-sensor_mirror_id'))
        $('#delete_lightbox h1:first').html('Delete Sensor Mirror')
        $('#delete_lightbox_entry_info').html('')
        $('#delete_lightbox_delete').unbind('click')
        $('#delete_lightbox_delete').click(() ->
            self._deleteSensorMirrorConfirmClick(sid)
        )
        $('#delete_lightbox_cancel').unbind('click')
        $('#delete_lightbox_cancel').click(() -> self._deleteDeviceCanceled())
        self.deleteDialog.open()

    spinnerDevices: (toggled) ->
        self=this
        if toggled
            $('#bin_lightbox_devices_table_spinner', self.$element).show()
            $('#bin_lightbox_devices_table', self.$element).hide()
        else
            $('#bin_lightbox_devices_table_spinner', self.$element).hide()
            $('#bin_lightbox_devices_table', self.$element).show()
        return self

    spinnerSensorMirrors: (toggled) ->
        self=this
        if toggled
            $('#bin_lightbox_devices_sensor_mirrors_table_spinner', self.$element).show()
            $('#bin_lightbox_devices_sensor_mirrors_table', self.$element).hide()
        else
            $('#bin_lightbox_devices_sensor_mirrors_table_spinner', self.$element).hide()
            $('#bin_lightbox_devices_sensor_mirrors_table', self.$element).show()
        return self

    
    show: () ->
        self=this
        $('#bin_lightbox_devices', self.$element).show()
        self.deviceView.hide()
        return self

    hide: () ->
        self=this
        $('#bin_lightbox_devices', self.$element).hide()
        return self
        
    _refreshDeviceList: () ->
        self=this
        console.info('refresh device list table')
        devicesData=[]
        for device in self.devices
            deviceType = IsadoreData.deviceTypesIdMap[device.device_type_id]
            activeSensorCount = 0
            for sensor in device.sensors
                if sensor.enabled_p
                    activeSensorCount=activeSensorCount+1
            d = [IsadoreData.binSectionsIdMap[device.bin_section_id].name,
                device.name,
                deviceType.name,
                activeSensorCount,
                device.mid_name,
                device.port,
                device.address,
                HTMLHelper.actionButtons,
                device.id]
            devicesData.push(d)
        self.spinnerDevices(false)
        $('#bin_lightbox_devices_table').dataTable({
            bDestroy: true
            bPaginate: false
            bFilter: false
            aaData: devicesData
            aoColumns: [
                { sTitle: 'Section' }
                { sTitle: 'Name' }
                { sTitle: 'Device' }
                { sTitle: '# Sensor Active' }
                { sTitle: 'MID Name'}
                { sTitle: 'Port' }
                { sTitle: 'Address' }
                { sTitle: 'Actions', bSortable: false }
                { sTitle: 'data-device_id', bVisible: false } ]
            fnRowCallback: (nRow, aData, ididx, ididxf) ->
                nRow.setAttribute('data-device_id', aData[8])
                $('td:eq(7)', nRow).addClass('action')
                return nRow
        })
        $('#bin_lightbox_devices_table span.action[data-action_type="edit"]').click((event) -> self._editDeviceClick(event))
        $('#bin_lightbox_devices_table span.action[data-action_type="delete"]').click((event) -> self._deleteDeviceClick(event))
        cbResize()
        return self

    _refreshSensorMirrorsList: (smd) ->
        self=this
        mirrorsData = []
        for mirror in self.sensorMirrors
            binSection = IsadoreData.binSectionsIdMap[mirror.bin_section_id]
            device = _.findWhere(IsadoreData.devices, {id: mirror.device_id})
            dbin = _.findWhere(IsadoreData.bins, {id: device.bin_id})
            dbinSection = IsadoreData.binSectionsIdMap[device.bin_section_id]
            sensor = _.findWhere(device.sensors, {id: mirror.sensor_id})

            mirrorsData.push([
                binSection.name,
                dbin.name,
                dbinSection.name,
                device.name+' - '+IsadoreData.sensorTypesIdMap[sensor.sensor_type_id].name
                HTMLHelper.actionButtons,
                mirror.id
            ])
        $('#bin_lightbox_devices_sensor_mirrors_table').dataTable({
            bDestroy: true
            bPaginate: false
            bFilter: false
            aaData: mirrorsData
            aoColumns: [
                { sTitle: 'Section' }
                { sTitle: 'Mirrored Bin' }
                { sTitle: 'Mirrored Bin Section' }
                { sTitle: 'Mirrored Sensor' }
                { sTitle: 'Actions', bSortable: false }
                { sTitle: 'data-sensor_mirror_id', bVisible: false }]
            fnRowCallback: (nRow, aData, ididx, ididxf) ->
                nRow.setAttribute('data-sensor_mirror_id', aData[5])
                $('td:eq(4)', nRow).addClass('action')
                return nRow
        })
        self.spinnerSensorMirrors(false)
        $('#bin_lightbox_devices_sensor_mirrors_table span.action[data-action_type="edit"]').remove()
        $('#bin_lightbox_devices_sensor_mirrors_table span.action[data-action_type="delete"]').click((event) -> self._deleteSensorMirrorClick(event))
        cbResize()

    refresh: () ->
        self=this
        self.devices = null
        self.sensorMirrors = null
        self.show().spinnerDevices(true).spinnerSensorMirrors(true)
        $.ajax({
            url: '../resources/conf/devices-fast'
            type: 'GET'
            dataType: 'json'
            data: { bin_id: self.setupTab.bin.id, year: new Date().getFullYear() }
            success: (d) ->
                self.devices=d.devices
                self._refreshDeviceList()
                $.ajax({
                    url: '../resources/conf/sensor_mirrors-fast'
                    type: 'GET'
                    dataType: 'json'
                    data: { bin_id: self.setupTab.bin.id, year: new Date().getFullYear() }
                    success: (d) ->
                        self.sensorMirrors=d.sensor_mirrors
                        self._refreshSensorMirrorsList()
                })

        })

        return self
    

# Device setup form
class DeviceView
    @MIRROR_DEVICE_ID=5
    constructor: (deviceTableView) ->
        self=this
        self.deviceTableView = deviceTableView
        self.$element = $('<div id="bin_lightbox_adddevice">
                <h1>Add/Edit Device</h1>
                <div class="errors"></div>
                <div class="float">
                    <div class="label">
                        <label for="bin_lightbox_adddevice_section">Section</label>
                    </div>
                    <div>
                        <select id="bin_lightbox_adddevice_section">
                        </select>
                    </div>
                    <div class="label">
                        <label for="bin_lightbox_adddevice_device">Device</label>
                    </div>
                    <div>
                        <select id="bin_lightbox_adddevice_device">
                        </select>
                    </div>
                    <div class="label">
                        <label for="bin_lightbox_adddevice_name">Device Name</label>
                    </div>
                    <div>
                        <input type="text" id="bin_lightbox_adddevice_name" />
                    </div>
                    <div class="label">
                        <label for="bin_lightbox_adddevice_info">Device Info</label>
                    </div>
                    <div>
                        <input type="text" id="bin_lightbox_adddevice_info" />
                    </div>

                </div>
                <div class="float" id="bin_lightbox_adddevice_port_address_side">
                    <div class="label">
                        <label for="bin_lightbox_adddevice_midname">MID Name</label>
                    </div>
                    <div>
                        <input type="text" id="bin_lightbox_adddevice_midname" />
                    </div>
                    <div class="label">
                        <label for="bin_lightbox_adddevice_port">Port</label>
                    </div>
                    <div>
                        <input type="text" id="bin_lightbox_adddevice_port" />
                    </div>
                    <div class="label">
                        <label for="bin_lightbox_adddevice_address">Address</label>
                    </div>
                    <div>
                        <input type="text" id="bin_lightbox_adddevice_address" />
                    </div>
                </div>
                <div class="clears"></div>
                <div id="bin_lightbox_add_device_sensors_div"></div>
                <div class="label">
                    <img id="bin_lightbox_adddevice_save_spinner" class="spinner"
                        src="imgs/ajax-loader.gif" alt="Loading Spinner" />
                    <button id="bin_lightbox_adddevice_save" type="button"
                        value="Save">Save</button>
                    <button id="bin_lightbox_adddevice_cancel" type="button"
                        value="Cancel">Cancel</button>
                </div>
            </div>')
        self.deviceTableView.$element.append(self.$element)
        self.sensorView = new SensorView(self, $('#bin_lightbox_add_device_sensors_div', self.$element)).hide()

        $('#bin_lightbox_adddevice_save').click(() -> self.save())
        $('#bin_lightbox_adddevice_cancel').click(() -> self.cancel())
        
        $('#bin_lightbox_adddevice_port', self.$element).numeric({ decimal: false, negative: true })
        $('#bin_lightbox_adddevice_address', self.$element).numeric({ decimal: false, negative: false })

    updateSensorView_: () ->
        self=this
        device_type_id = parseInt($('#bin_lightbox_adddevice_device').val(), 10)
        if device_type_id == DeviceView.MIRROR_DEVICE_ID # Mirror device
            self.sensorView.hide()
            # Port and Address disabled
            $('#bin_lightbox_adddevice_port_address_side').hide()
            self.sensorView.hide()
            #self.mirrorSensorView.show().refresh()
        else
            #self.mirrorSensorView.hide()
            $('#bin_lightbox_adddevice_port_address_side').show()
            #self.mirrorSensorView.hide()
            self.sensorView.show().refresh(device_type_id)
        return self
        

    save: () ->
        self=this
        # Saving Spinner
        self.spinner(true)
        # check errors
        deviceArgs = {
            device_type_id: parseInt($('#bin_lightbox_adddevice_device').val(), 10)
            address: parseInt($('#bin_lightbox_adddevice_address').val(), 10)
            port: parseInt($('#bin_lightbox_adddevice_port').val(), 10)
            mid_name: $('#bin_lightbox_adddevice_midname').val()
            name: $('#bin_lightbox_adddevice_name').val()
            info: $('#bin_lightbox_adddevice_info').val()
            enabled_p: 'true'
            bin_id: self.deviceTableView.setupTab.bin.id
            bin_section_id: parseInt($('#bin_lightbox_adddevice_section').val(), 10)
            year: new Date().getFullYear()
        }
        
        errors = []
        
        # Validate user inputs.
        if deviceArgs.device_type_id != DeviceView.MIRROR_DEVICE_ID
            if isNaN(deviceArgs.address) or deviceArgs.address <= 0 or deviceArgs.address >= 65536
                errors.push('Address is required and needs to be a number from 1 to 65535')
            
            if isNaN(deviceArgs.port)
                errors.push('Port is required and needs to be a number')
        else
            delete deviceArgs.address
            delete deviceArgs.port
        
        # If normal sensors
        if deviceArgs.device_type_id != DeviceView.MIRROR_DEVICE_ID
            errors.push.apply(errors, self.sensorView.getErrors())
        # Mirror sensors
        else
            #errors.push.apply(errors, self.mirrorSensorView.getErrors())
            pass

        errorsDiv = $('#bin_lightbox_adddevice div.errors')
        errorsDiv.empty() # Remove any preexisting errors.
        if errors.length > 0
            errorsDiv.append(HTMLHelper.makeList(errors)) # Remove any preexisting errors.
            self.spinner(false)
            errorsDiv.show()
            return
        errorsDiv.hide()

        # Save sensors.
        saveSensors = (update, callback) ->
            # If normal sensors
            if deviceArgs.device_type_id != DeviceView.MIRROR_DEVICE_ID
                self.sensorView.save(update, callback)
            # Mirror sensors
            else
                #self.mirrorSensorView.save(update, callback)
                pass

        if not self.device # Add
            $.ajax({
                url: '../resources/conf/devices'
                type: 'POST'
                dataType: 'json'
                success: (d) ->
                    $.ajax({
                        url: '..'+d.xlink[0]
                        type: 'GET'
                        dataType: 'json'
                        success: (device) ->
                            self.device=device
                            self.device.sensors=[]
                            saveSensors(false, () -> self.cancel())
                    })
                data : deviceArgs
            })
        else # Update
            $.ajax({
                url: '../resources/conf/devices/'+self.device.id
                type: 'PUT'
                dataType: 'text'
                success: () ->
                    update = deviceArgs.device_type_id == self.device.device_type_id
                    saveSensors(update, () -> self.cancel())
                data: deviceArgs
            })


    cancel: () ->
        self=this
        self.spinner(false)
        self.hide()
        self.deviceTableView.show().refresh()
        return self

    spinner: (toggled) ->
        self=this
        if toggled
            $('#bin_lightbox_adddevice_cancel', self.$element).hide()
            $('#bin_lightbox_adddevice_save', self.$element).hide()
            $('#bin_lightbox_adddevice_save_spinner', self.$element).show()
            $('input, select', self.$element).each( (index, value) ->
                $(value).attr('disabled', 'true')
            )
        else
            $('#bin_lightbox_adddevice_cancel', self.$element).show()
            $('#bin_lightbox_adddevice_save', self.$element).show()
            $('#bin_lightbox_adddevice_save_spinner', self.$element).hide()
            $('input, select', self.$element).each((index, value) ->
                $(value).removeAttr('disabled')
            )
        return self

    
    show: () ->
        self=this
        self.$element.show()
        return self
        
    hide: () ->
        self=this
        self.$element.hide()
        return self
        
    deleteDeviceSensors: (callback) ->
        self=this
        $.ajax({
            url : '../resources/conf/sensors-fast'
            type : 'DELETE'
            dataType : 'text'
            data : { device_id: self.device.id }
            success : () ->
                if callback
                    callback()
        })

    refresh: (device) ->
        self=this
        self.device=device
        #Remove Errors
        $('#bin_lightbox_adddevice div.errors', self.$element).empty().hide()
        console?.info?('device='+self.device)
        console?.log?(self.device)
        sectionSelect = HTMLHelper.makeSelect(IsadoreData.binSections, 'name', 'id')
        sectionSelect.attr('id', 'bin_lightbox_adddevice_section')
        $('#bin_lightbox_adddevice_section', self.$element).replaceWith(sectionSelect)
        deviceTypeSelect = HTMLHelper.makeSelect(IsadoreData.deviceTypes, 'name', 'id')
        deviceTypeSelect.attr('id', 'bin_lightbox_adddevice_device')
        $('#bin_lightbox_adddevice_device', self.$element).replaceWith(deviceTypeSelect)
        $('#bin_lightbox_adddevice_device', self.$element).change(() -> self.updateSensorView_())
        if not self.device
            $('#bin_lightbox_adddevice_device', self.$element).change()
            $('#bin_lightbox_adddevice h1:first', self.$element).html('Add Device')
            $('#bin_lightbox_adddevice_address', self.$element).val('')
            $('#bin_lightbox_adddevice_port', self.$element).val('')
            $('#bin_lightbox_adddevice_midname', self.$element).val('')
            $('#bin_lightbox_adddevice_name', self.$element).val('')
            $('#bin_lightbox_adddevice_info', self.$element).val('')
            # Set to default values.
        else
            $('#bin_lightbox_adddevice_section', self.$element).val(self.device.bin_section_id)
            $('#bin_lightbox_adddevice_device', self.$element).val(self.device.device_type_id)
            $('#bin_lightbox_adddevice_device', self.$element).change()
            $('#bin_lightbox_adddevice_address', self.$element).val(self.device.address)
            $('#bin_lightbox_adddevice_port', self.$element).val(self.device.port)
            $('#bin_lightbox_adddevice_midname', self.$element).val(self.device.mid_name)
            $('#bin_lightbox_adddevice_name', self.$element).val(self.device.name)
            $('#bin_lightbox_adddevice_info', self.$element).val(self.device.info)
            $('#bin_lightbox_adddevice h1:first', self.$element).html('Edit Device')
        return self
        
        
# Lists sensor for device
class SensorView
    constructor: (deviceView, parentElement) ->
        self=this
        self.deviceView=deviceView
        self.$element = $('<table id="bin_lightbox_adddevice_sensors">
            <thead>
                <tr>
                    <th class="adddfirst">Enabled</th>
                    <th class="adddsecond">Sensor</th>
                    <th class="adddthird">Convert</th>
                    <th class="adddfourth">Bias</th>
                    <th class="adddfifth">Extra Info (JSON)</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        </table>')
        parentElement.append(self.$element)
        
    getErrors: () ->
        return []
        
    save: (update, callback) ->
        self=this
        if not update
            # Delete sensors & sensor_mirror
            self.deviceView.deleteDeviceSensors(() ->
                self.save2_(callback)
            )
        else
            self.save2_(callback)
        return self
            
    save2_: (callback) ->
        self=this

        trs = $('#bin_lightbox_adddevice_sensors tbody tr')
        self.sensorLength = trs.length
        self.sensorCount = 0
        
        for tr in trs
            sensorArgs = {
                device_id: self.deviceView.device.id
                sensor_type_id: _.parseInt($(tr).attr('data-sensor_type_id'))
                convert_py: $('input[name="sensor_convert"]', tr).val()
                bias: $('input[name="sensor_bias"]', tr).val()
                extra_info: $('input[name="sensor_extrainfo"]', tr).val()
                enabled_p: $('input[type="checkbox"]', tr).is(':checked')
            }
            sensor = _.findWhere(self.deviceView.device.sensors, {'sensor_type_id': sensorArgs.sensor_type_id})
            if sensor # Update
                $.ajax({
                    url : '../resources/conf/sensors/'+sensor.id
                    type : 'PUT'
                    dataType : 'text'
                    data : sensorArgs
                    success : () ->
                        self.sensorCount++
                        if self.sensorCount == self.sensorLength
                            if callback
                                callback()
                })
            else # Add
                $.ajax({
                    url : '../resources/conf/sensors'
                    type : 'POST'
                    dataType : 'json'
                    data : sensorArgs
                    success : () ->
                        self.sensorCount++
                        if self.sensorCount == self.sensorLength
                            if callback
                                callback()
                })

    hide: () ->
        self=this
        self.$element.hide()
        return self
    
    show: () ->
        self=this
        self.$element.show()
        return self
        
    refresh: (device_type_id) ->
        self=this
        sensor_types = IsadoreData.deviceTypesIdMap[device_type_id].sensor_types
        $tbody = $('<tbody></tbody')
        for sensor_type in sensor_types
            enabled=true
            convert_py = sensor_type.default_convert_py
            bias = 0
            if self.deviceView.device && device_type_id == self.deviceView.device.device_type_id
                dsensor = _.findWhere(self.deviceView.device.sensors, {'sensor_type_id': sensor_type.id})
                if dsensor
                    enabled = dsensor.enabled_p
                    convert_py = dsensor.convert_py
                    if not convert_py
                        convert_py = sensor_type.default_convert_py
                    bias = dsensor.bias.toFixed(2)
                    extra_info = dsensor.extra_info
                else
                    enabled = false
            $tr = $('<tr data-sensor_type_id="'+sensor_type.id+'">')
            $tr.append('<td class="adddfirst"><input name="enabled" type="checkbox"></td>')
            if enabled
                $('input', $tr).prop('checked', true)

            $td2 = $('<td class="adddsecond">')
            $td2.text(sensor_type.name)
            $tr.append($td2)

            $td3 = $('<td class="adddthird"><input type="text" name="sensor_convert"></td>')
            $('input', $td3).val(convert_py)
            $tr.append($td3)

            $td4 = $('<td class="adddfourth"><input type="text" name="sensor_bias" value="'+bias+'"/></td>')
            $('input', $td4).val(bias)
            $tr.append($td4)

            $td5 = $('<td class="adddfifth"><input type="text" name="sensor_extrainfo"/></td>')
            $('input', $td5).val(extra_info)
            $tr.append($td5)
            $tbody.append($tr)

        $('#bin_lightbox_adddevice_sensors tbody').replaceWith($tbody)


class SensorMirrorView
    constructor: (deviceTableView) ->
        self=this
        self.deviceTableView = deviceTableView
        self.$element = $('<div id="bin_lightbox_addsensor_mirror">
                <h1>Add Sensor Mirror</h1>
                <div class="errors"></div>
                <div class="float">
                    <div class="label"><label for="bin_lightbox_addsensor_mirror_frombin">From Bin</label></div>
                    <div>
                        <select id="bin_lightbox_addsensor_mirror_frombin"></select>
                    </div>
                    <div class="label"><label for="bin_lightbox_addsensor_mirror_frombinsection">From Bin Section</label></div>
                    <div>
                        <select id="bin_lightbox_addsensor_mirror_frombinsection"></select>
                    </div>
                    <div class="label"><label for="bin_lightbox_addsensor_mirror_fromdevice">From Device</label></div>
                    <div>
                        <select id="bin_lightbox_addsensor_mirror_fromdevice"></select>
                    </div>
                    <div class="label"><label for="bin_lightbox_addsensor_mirror_fromsensor">From Sensor</label></div>
                    <div>
                        <select id="bin_lightbox_addsensor_mirror_fromsensor"></select>
                    </div>
                </div>
                <div class="float">
                    <div class="label"><label>To Bin</label></div>
                    <div>
                        <span id="bin_lightbox_addsensor_mirror_tobin"></span>
                    </div>
                    <div class="label"><label for="bin_lightbox_addsensor_mirror_tobinsection">To Bin Section</label></div>
                    <div>
                        <select id="bin_lightbox_addsensor_mirror_tobinsection"></select>
                    </div>
                </div>
                <div class="clears"></div>
                <div class="label">
                    <img id="bin_lightbox_addsensor_mirror_save_spinner" class="spinner"
                        src="imgs/ajax-loader.gif" alt="Loading Spinner" />
                    <button id="bin_lightbox_addsensor_mirror_save" type="button"
                        value="Save">Save</button>
                    <button id="bin_lightbox_addsensor_mirror_cancel" type="button"
                        value="Cancel">Cancel</button>
                </div>
            </div>')
        self.deviceTableView.$element.append(self.$element)
        self.hide()
        $('#bin_lightbox_addsensor_mirror_save', self.$element).click(() -> self.save())
        $('#bin_lightbox_addsensor_mirror_cancel', self.$element).click(() -> self.cancel())

    show: () ->
        self=this
        self.$element.show()
        return self


    hide: () ->
        self=this
        self.$element.hide()
        return self

    spinner: (toggled) ->
        self=this
        if toggled
            $('#bin_lightbox_addsensor_mirror_cancel', self.$element).hide()
            $('#bin_lightbox_addsensor_mirror_save', self.$element).hide()
            $('#bin_lightbox_addsensor_mirror_save_spinner', self.$element).show()
            $('input, select', self.$element).each( (index, value) ->
                $(value).attr('disabled', 'true')
            )
        else
            $('#bin_lightbox_addsensor_mirror_cancel', self.$element).show()
            $('#bin_lightbox_addsensor_mirror_save', self.$element).show()
            $('#bin_lightbox_addsensor_mirror_save_spinner', self.$element).hide()
            $('input, select', self.$element).each((index, value) ->
                $(value).removeAttr('disabled')
            )
        return self

    cancel: () ->
        self = this
        self.spinner(false)
        self.hide()
        self.deviceTableView.show().refresh()

    save: () ->
        self = this
        sensorId = _.parseInt($('#bin_lightbox_addsensor_mirror_fromsensor', self.$element).val())
        if isNaN(sensorId)
            $('div.errors', self.$element).text('Invalid sensor.').show()
            return
        $('div.errors', self.$element).empty()
        binId = self.deviceTableView.setupTab.bin.id
        binSectionId = _.parseInt($('#bin_lightbox_addsensor_mirror_tobinsection', self.$element).val())
        $.ajax({
            url: '../resources/conf/sensor_mirrors'
            type: 'POST'
            dataType: 'json'
            data: {sensor_id: sensorId, bin_id: binId, bin_section_id: binSectionId}
            success: () ->
                self.cancel()
        })

    _updateDevice: () ->
        self=this
        #When device changes change sensor
        IsadoreData.getDevices(_.parseInt($('#bin_lightbox_addsensor_mirror_frombin', self.$element).val()), (devices) =>
            fromBinSectionId = _.parseInt($('#bin_lightbox_addsensor_mirror_frombinsection').val())
            devices = _.where(devices, {bin_section_id: fromBinSectionId})
            fromDevicesSelect = $('<select id="bin_lightbox_addsensor_mirror_fromdevice"></select>')
            for d in devices
                $option = $('<option></option>')
                $option.attr('value', d.id)
                $option.text(d.name+' - '+IsadoreData.deviceTypesIdMap[d.device_type_id].name)
                fromDevicesSelect.append($option)
            $('#bin_lightbox_addsensor_mirror_fromdevice', self.$element).replaceWith(fromDevicesSelect)
            fromDevicesSelect.change(()->
                self._updateSensors(devices)
            ).change()
        )

    _updateSensors: (devices) ->
        deviceId = _.parseInt($('#bin_lightbox_addsensor_mirror_fromdevice', self.$element).val())
        if not isNaN(deviceId)
            d = _.findWhere(devices, {id: deviceId})
            fromSensorsSelect = $('<select id="bin_lightbox_addsensor_mirror_fromsensor"></select>')
            for sensor in d.sensors
                $option = $('<option></option>')
                $option.attr('value', sensor.id)
                $option.text(IsadoreData.sensorTypesIdMap[sensor.sensor_type_id].name)
                fromSensorsSelect.append($option)
            $('#bin_lightbox_addsensor_mirror_fromsensor', self.$element).replaceWith(fromSensorsSelect)
        else
            $('#bin_lightbox_addsensor_mirror_fromsensor', self.$element).empty()


    refresh: () ->
        self=this
        $('#bin_lightbox_addsensor_mirror div.errors', self.$element).empty().hide()
        fromBinsSelect = HTMLHelper.makeSelect(IsadoreData.bins, 'name', 'id')
        fromBinsSelect.attr('id', 'bin_lightbox_addsensor_mirror_frombin')
        fromBinSectionsSelect = HTMLHelper.makeSelect(IsadoreData.binSections, 'name', 'id')
        fromBinSectionsSelect.attr('id', 'bin_lightbox_addsensor_mirror_frombinsection')

        $('#bin_lightbox_addsensor_mirror_tobin').text(self.deviceTableView.setupTab.bin.name)
        toBinSectionsSelect = HTMLHelper.makeSelect(IsadoreData.binSections, 'name', 'id')
        toBinSectionsSelect.attr('id', 'bin_lightbox_addsensor_mirror_tobinsection')

        $('#bin_lightbox_addsensor_mirror_frombin', self.$element).replaceWith(fromBinsSelect)
        $('#bin_lightbox_addsensor_mirror_frombinsection', self.$element).replaceWith(fromBinSectionsSelect)
        $('#bin_lightbox_addsensor_mirror_tobinsection', self.$element).replaceWith(toBinSectionsSelect)

        #When bin or bin_sections change, change device
        $(fromBinsSelect).change(() ->
            self._updateDevice()
        ).change()
        $(fromBinSectionsSelect).change(() ->
            self._updateDevice()
        ).change()
