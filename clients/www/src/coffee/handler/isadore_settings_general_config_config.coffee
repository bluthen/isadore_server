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

class window.GeneralConfigConfig
    _template: '<div class="settings_general_config_config"><h1>General Config Config</h1><div class="gcc_json_editor" style="height: 700px"></div><button type="button">Save JSON</button><span class="save_status"></span></div>'
    constructor: ($parent) ->
        @_$selfdiv = $(@_template)
        $parent.append(@_$selfdiv)
        @_$editordiv = $('.gcc_json_editor', @_$selfdiv)
        @_editor = new JSONEditor(@_$editordiv[0], {modes: ['tree', 'code']})
        @_$button = $('button', @_$selfdiv)
        @_$saveStatus = $('.save_status', @_$selfdiv)
        @_$button.click(() =>
            @save()
        )

    _showError: (e) ->
        $('#error_dialog').html("Error: "+e).dialog({
            zIndex: 99999,
            modal: true,
            buttons: {
                Ok: () ->
                    $(this).dialog('close');
            }
        })


    save: () ->
        #TODO: Put in some check so it is atleast somewhat valid.
        #TODO: Check for client_version existence
        data = @_editor.getText()
        try
            JSON.parse(data)
        catch err
            console.warn('GeneralConfigConfig syntax error in json while attempting to save')
            @_showError('Please fix JSON errors before saving.')
        #Save data
        #TODO: Make button spin
        @_$button.prop('disable', true);
        @_$saveStatus.text('Saving...').fadeIn(0)
        $.ajax({
            url: '../resources/conf/general'
            type: 'PUT'
            dataType: 'text'
            data: {configs: data}
            success: (d) =>
                #TODO: On save stop button spin
                @_$button.prop('disable', false);
                @_$saveStatus.text('Saved!').fadeIn(0).fadeOut(3000)
            error: (jq, txt, err) =>
                @_$button.prop('disable', false);
                @_$saveStatus.text('Error Saving').fadeIn(0).fadeOut(3000)
                @_showError('Error saving General Config Config: '+ txt + " " + err)
        })


    refresh: () ->
        @_$editordiv.hide()
        $.ajax({
            url: '../resources/conf/general',
            type: 'GET',
            dataType: 'json',
            success: (d) =>
                @_editor.setText(d.configs)
                @_$editordiv.show()
            error: (e) =>
                data = "Failed to load config"
                @_editor.set(data)
                @_$editordiv.show()
        })
