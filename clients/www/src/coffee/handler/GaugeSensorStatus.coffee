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

#
# general.conf.gauge_warn
# [
# {"red": milliseconds, "yellow": milliseconds}, // Global color config
# {"bin_id":, "bin_section_id: number, "read_type_id": number, "red": milliseconds, "yellow": milliseconds} //Specific color config
# ]
#

class window.GaugeSensorStatus
    @_TEMPLATE: """
        <div class="gauge_sensor_status">
        </div>
"""
    @_ICON_RED: '<img src="imgs/gauge_red.png" width="20" height="20" style="position: relative; top:6px;"/>'
    @_ICON_YELLOW: '<img src="imgs/gauge_yellow.png" width="20" height="20" style="position: relative; top:6px;"/>'
    @_ICON_GREEN: '<img src="imgs/gauge_green.png" width="20" height="20" style="position: relative; top:6px;"/>'
    constructor: ($parentWrap) ->
        # Add click binds to bring up dialog
        $('.info_header > .gauge_status_open').click(() =>
            @show()
        )
        $(IsadoreData).on('ReadingsUpdated', () =>
            @_gaugeUpdate()
        )
        @_$selfdiv = $(window.GaugeSensorStatus._TEMPLATE)
        $parentWrap.append(@_$selfdiv)
        @_dialog = new IsadoreDialog(@_$selfdiv, {width: 700, title: 'Gauge Sensor Status'})
        setInterval(
            () =>
                @_gaugeUpdate()
        2500)

    _getGaugeWarnTimes: (gwc, rd) ->
        largeTime = 999999999;
        globalConfig = null
        for c in gwc
            # bin & section & rt
            if c.bin_id? and c.bin_section_id? and c.read_type_id? and c.bin_id == rd.bin_id and c.bin_section_id == rd.bin_section_id and c.read_type_id == rd.read_type_id
                return c
            # bin & !section & !readtype
            else if c.bin_id? and c.bin_id == rd.bin_id and not c.bin_section_id? and not c.read_type_id?
                return c
            # bin & section & !readtype
            else if c.bin_id? and c.bin_id == rd.bin_id and c.bin_section_id? and c.bin_section_id == rd.bin_section_id and not c.read_type_id?
                return c
            # bin & !section & readtype
            else if c.bin_id? and c.bin_id == rd.bin_id and not c.bin_section_id? and c.read_type_id? and c.read_type_id == rd.read_type_id
                return c
            # !bin & section & readtype
            else if not c.bin_id? and c.bin_section_id? and c.bin_section_id == rd.bin_section_id and c.read_type_id? and c.read_type_id == rd.read_type_id
                return c
            # !bin & section & !readtype
            else if not c.bin_id? and c.bin_section_id? and c.bin_section_id == rd.bin_section_id and not c.read_type_id?
                return c
            # !bin & !section & readtype
            else if not c.bin_id? and not c.bin_section_id and c.read_type_id? and c.read_type_id == rd.read_type_id
                return c
            # !bin & !section & !readtype
            else if not c.bin_id? and not c.bin_section_id? and not c.read_type_id?
                globalConfig = c
        return globalConfig

    _gaugeUpdate: () ->
        #TODO: Spinner?
        overallStatusIcon = GaugeSensorStatus._ICON_GREEN
        if IsadoreData.general.configs.gauge_warn
            gwc = IsadoreData.general.configs.gauge_warn

            overallStatus = "green"
            html = ['<table style="width:100%"><thead><tr><td>State</td><td>Bin</td><td>Section</td><td>dT</td><td>Type</td><td>Value</td></tr></thead>']
            now = new Date()
            #Update info in dialog
            for rd in IsadoreData.lastReadings
                times = @_getGaugeWarnTimes(gwc, rd)
                if not times
                    continue
                delta = now - rd.datetime
                show = false
                if delta >= times.red
                    overallStatus = 'red'
                    overallStatusIcon = GaugeSensorStatus._ICON_RED
                    html.push('<tr>')
                    html.push('<td>')
                    html.push(GaugeSensorStatus._ICON_RED)
                    html.push('</td>')
                    show = true
                else if delta >= times.yellow
                    if overallStatus != 'red'
                        overallStatus = 'yellow'
                        overallStatusIcon = GaugeSensorStatus._ICON_YELLOW
                    html.push('<tr>')
                    html.push('<td>')
                    html.push(GaugeSensorStatus._ICON_YELLOW)
                    html.push('</td>')
                    show = true
                if show
                    binName = IsadoreData.getBin(rd.bin_id).name
                    binSectionName = IsadoreData.binSectionsIdMap[rd.bin_section_id].name
                    delta = (delta/1000.0).toFixed(0)+"s"
                    readType = IsadoreData.readTypesIdMap[rd.read_type_id]
                    html.push('<td>'+binName+'</td>')
                    html.push('<td>'+binSectionName+'</td>')
                    html.push('<td>'+delta+'</td>')
                    html.push('<td>'+readType.name+'</td>')
                    #TODO: should use formating option instead of just toFixed(2)
                    if not rd.value
                        html.push('<td>NA '+readType.units+'</td>')
                    else
                        html.push('<td>'+rd.value.toFixed(2)+readType.units+'</td>')
                    html.push('</tr>')
            html.push('</table>')


            if @_dialog.isOpen()
                @_$selfdiv.html(html.join(''))

        else
            @_$selfdiv.text('No gauge warnings are configured.')

        #Update status icons on fill views/sensor view, based on overallStatus
        $('.gauge_overall_status_icon').html(overallStatusIcon)

    show: () ->
        if !@_dialog.isOpen()
            @_dialog.open()
            @_gaugeUpdate()
