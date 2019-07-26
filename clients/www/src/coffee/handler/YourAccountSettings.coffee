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

class window.YourAccountSettings
    @_TEMPLATE: """
        <div class="your_account_settings">
            <ul>
                <li><a href="#your_account_settings_details">Details</a></li>
                <li><a href="#your_account_settings_alarms">Alarms</a></li>
            </ul>
            <div id="your_account_settings_details">
                <h1>Change Password</h1>
                <div><ul id="your_account_settings_chpw_msgs"></ul></div>
                <div class="label">
                    <label for="your_account_settings_old_pw">Current Password</label>
                </div>
                <div>
                    <input type="password" id="your_account_settings_old_pw"/>
                </div>
                <div class="label">
                    <label for="your_account_settings_new_pw">New Password</label>
                </div>
                <div>
                    <input type="password" id="your_account_settings_new_pw"/>
                </div>
                <div class="label">
                    <label for="your_account_settings_new_pw2">Re-typed New Password</label>
                </div>
                <div>
                    <input type="password" id="your_account_settings_new_pw2"/>
                </div>

                <div class="label">
                    <button id="your_account_settings_save_pw" type="button" value="Save">Change Password</button><span class="pwsave_status"></span>
                </div>
                <h1>Contact Settings</h1>
                <div class="label">Note: This setting does not effect alarms.</div>
                <div>
                    <input type="checkbox" id="your_account_contact_preference_news"/><label for="your_account_contact_preference_news" class="label"> Contact me about Isadore news, status, and updates.</label>
                </div>
                <div class="label">
                    <button id="your_account_settings_save_contact" type="button" value="Save">Save</button><span class="contact_save_status"></span>
                </div>
            </div>
            <div id="your_account_settings_alarms">
                <input id="your_account_settings_alarms_disable_all" type="checkbox"/><label for="your_account_settings_alarms_disable_all">Disable all notifications</label>
                <span style="font-weight: bold">Alarm:</span><select id="your_account_settings_alarms_select"></select>
                <div id="your_account_settings_alarms_levels"></div>
                <button id="your_account_settings_alarms_save" type="button" value="Save">Save</button><span class="ya_alarms_save_status"></span>
            </div>
        </div>
"""
    constructor: ($parentWrap) ->
        #TODO: Somewhere need to contact alarms system to get blacklist like things
        $('.info_header > .account').html('<img src="imgs/icon_profile.png" style="position: relative; top: 6px;"/>'+IsadoreData.selfAccount.name).click(() =>
            @show()
        )
        @_$selfdiv = $(window.YourAccountSettings._TEMPLATE)
        $parentWrap.append(@_$selfdiv)

        @_workingAlarmSettings = {}
        @_$selfdiv.tabs({activate: () =>
            if IsadoreData.selfAccount.configs.alarm_settings?
                @_workingAlarmSettings = _.deepCopy(IsadoreData.selfAccount.configs.alarm_settings)
            else
                @_workingAlarmsSettings = {"alarm_setup": {}}
            @_alarmSelect()
        })

        @_$selfdiv.tabs("option", "disabled", [1])


        @_dialog = new IsadoreDialog(@_$selfdiv, {width: 700, title: 'Account Settings'});
        @_$pwtab = $('#your_account_settings_details', @_$selfdiv)
        @_$almtab = $('#your_account_settings_alarms', @_$selfdiv)
        $('#your_account_settings_save_pw', @_$pwtab).click(() =>
            @saveNewPassword()
        )
        $('#your_account_settings_old_pw, #your_account_settings_new_pw, #your_account_settings_new_pw2', @_$pwtab).on('input keypress focus blur change', () =>
            @_validatePasswords()
        )

        $('#your_account_settings_save_contact', @_$pwtab).click(() =>
            @_saveContactPrefs()
        )

        $("#your_account_settings_alarms_disable_all", @_$pwtab).change(() =>
            @_updateWorkingAlarmSettings()
        )

        $select = $('#your_account_settings_alarms_select', @_$almtab)
        if IsadoreData.general.configs.alarms?
            for alarm_name, alarm_info of IsadoreData.general.configs.alarms
                $select.append('<option value="'+alarm_name+'">'+alarm_name+'</option>')

        $select.change(() =>
            @_alarmSelect()
        )


    _alarmSelect: () ->
        levels = ['Info', 'Warn', 'Concern', 'Urgent']
        level_options= '<select multiple><option value="email">Email</option><option value="sms">SMS</option><option value="voice">Voice</option></select>'

        $select = $('#your_account_settings_alarms_select', @_$almtab)
        $alarmLevelDiv = $('#your_account_settings_alarms_levels', @_$almtab).empty()
        alarmName = $select.val()

        alarm = IsadoreData.general.configs.alarms[alarmName]

        $alarmLevelDiv.append("<h1>#{alarmName}</h1>")
        for level in levels
            lclevel = level.toLowerCase()
            if alarm.condition?.hasOwnProperty(lclevel)
                $leveldiv = $('<div style="margin-left: 2ex;"></div>')
                label_for = "your_account_settings_alarms_#{lclevel}"
                $leveldiv.append('<div style="display:inline-block; vertical-align: top; margin-right: 2ex;">'+level+': <input id="#{label_for}_enabled" data-level="#{lclabel}" type="checkbox"/><label for="#{label_for}_enabled">Enabled</label></div>')
                $select_level = $(level_options)
                $select_level.attr('id', label_for+"_"+lclevel)
                $select_level.attr('data-level', lclevel)

                $leveldiv.append($select_level)
                if alarm.level_descriptions?.hasOwnProperty(lclevel)
                    $leveldiv.append('<div style="display:inline-block; vertical-align: top; margin-left: 2ex;">'+alarm.level_descriptions[lclevel]+'</div>')
                $alarmLevelDiv.append($leveldiv)

                $select_level.change(() =>
                    @_updateWorkingAlarmSettings()
                )
                $('input', $leveldiv).change( () =>
                    @_updateWorkingAlarmSettings()
                )

        if @_workingAlarmSettings.alarm_setup?.hasOwnProperty(alarmName)
            as = @_workingAlarmSettings.alarm_setup[alarmName]
            for level, values of as
                label_for = "your_account_settings_alarms_#{lclevel}"
                $select_level = $('#'+label_for+"_"+level, $alarmLevelDiv)
                if values.enabled
                    $('#'+label_for+'_enabled', $alarmLevelDiv).prop('checked', true)
                selected = []
                if values.email
                    selected.push('email')
                if values.sms
                    selected.push('sms')
                if values.voice
                    selected.push('voice')
                $select_level.val(values)

    _updateWorkingAlarmSettings: () ->
        alarmName = $('#your_account_settings_alarms_select', @_$almtab).val()

        if not @_workingAlarmSettings.alarm_setup.hasOwnProperty(alarmName)
            @_workingAlarmSettings.alarm_setup[alarmName] = {}
        $('input[type="checkbox"]', $alarmLevelDiv).each((index, value) =>
            $value = $(value)
            level = $value.attr('data-level')
            if not @_workingAlarmSettings.alarm_setup[alarmName].hasOwnProperty(level)
                @_workingAlarmSettings.alarm_setup[alarmName][level] = {}
            level_enabled = $value.is(':checked')
            @_workingAlarmSettings.alarm_setup[alarmName][level].enabled = level_enabled
        )
        $('select', $alarmLevelDiv).each((index, value) =>
            $value = $(value)
            level = $value.attr('data-level')
            selects = $value.val()
            @_workingAlarmSettings.alarm_setup[alarmName][level].sms = false
            @_workingAlarmSettings.alarm_setup[alarmName][level].email = false
            @_workingAlarmSettings.alarm_setup[alarmName][level].voice = false
            for s in selects
                @_workingAlarmSettings.alarm_setup[alarmName][level][s]=true
        )

    _saveAlarmSettings: () ->
        i = 1
        #TODO: save account config with new alarm_setup
        #TODO: Update IsadoreData.selfAccount

    _validatePasswords: (hard=false) ->
        console.log('_validatePasswords')
        #TODO: Add zxcvbn password strength meter
        #https://github.com/dropbox/zxcvbn
        oldPW = $('#your_account_settings_old_pw', @_$pwtab).val()
        newPW = $('#your_account_settings_new_pw', @_$pwtab).val()
        newPW2 = $('#your_account_settings_new_pw2', @_$pwtab).val()
        errors = []
        if (!oldPW)
            errors.push('Please enter your old password.')
        console.log(newPW)
        console.log(newPW2)
        $ul = $('ul#your_account_settings_chpw_msgs', @_$pwtab)
        if (!newPW || !newPW2 || newPW != newPW2)
            errors.push('New password and Re-typed Password must match.')
        if errors.length == 0
            $('#your_account_settings_save_pw', @_$pwtab).prop('disabled', false)
            $ul.empty()
        else
            $('#your_account_settings_save_pw', @_$pwtab).prop('disabled', true)
            msg = ''
            for err in errors
                msg += '<li>'+err+'</li>'
            $ul.html(msg)



    _clearPasswords: () ->
        $('ul#your_account_settings_chpw_msgs', @_$pwtab).empty()
        $('input[type="password"]', @_$pwtab).empty()
        $('#your_account_settings_save_pw', @_$pwtab).prop('disabled', true)
        $('.contact_save_status', @_$pwtab).empty()
        $('#your_account_settings_save_contact', @_$pwtab).prop('disabled', false)
        $('#your_account_contact_preference_news', @_$pwtab).prop('checked', IsadoreData.selfAccount.contact_news)



    saveNewPassword: () ->
        oldPW = $('#your_account_settings_old_pw', @_$pwtab).val()
        newPW = $('#your_account_settings_new_pw', @_$pwtab).val()
        #send current password and new password to change password server side
        $('.pwsave_status', @_$pwtab).text('Saving...').fadeIn(0)
        $('#your_account_settings_save_pw', @_$pwtab).prop('disabled', true)
        $.ajax({
            url: "../resources/accounts/password"
            type: "PUT"
            dataType: 'text'
            data: {old_password: oldPW, new_password: newPW}
            success: (d) =>
                $('.pwsave_status', @_$pwtab).text('Password Changed!').fadeIn(0).fadeOut(3000)
                @_clearPasswords()
            error: (jqXHR, textStatus, errorThrown) =>
                $('.pwsave_status', @_$pwtab).text('Failed').fadeIn(0).fadeOut(3000)
                $ul = $('ul#your_account_settings_chpw_msgs', @_$pwtab)
                $ul.html('<li>Please enter the correct current password.</li>')
        })

    _saveContactPrefs: () ->
        $('.contact_save_status', @_$pwtab).empty()
        contact_prefs = $('#your_account_contact_preference_news', @_$pwtab).is(':checked')
        #send current password and new password to change password server side
        $('.contact_save_status', @_$pwtab).text('Saving...').fadeIn(0)
        $('#your_account_settings_save_contact', @_$pwtab).prop('disabled', true)
        $.ajax({
            url: "../resources/accounts/"+IsadoreData.selfAccount.id
            type: "PUT"
            dataType: 'text'
            data: {contact_news: contact_prefs}
            success: (d) =>
                $('.contact_save_status', @_$pwtab).text('Saved!').fadeIn(0).fadeOut(3000)
                $('#your_account_settings_save_contact', @_$pwtab).prop('disabled', false)
            error: (jqXHR, textStatus, errorThrown) =>
                $('.contact_save_status', @_$pwtab).text('Failed')
                $('#your_account_settings_save_contact', @_$pwtab).prop('disabled', false)
        })


    show: () ->
        if !@_dialog.isOpen()
            #Clear password fields.
            @_clearPasswords()
            @_dialog.open()
