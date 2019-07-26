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

class window.GraphsTabCustom
    constructor: () ->
        @_currentSimpleGrapher = null
        @_$selfdiv = $('#bin_lightbox_tabs-graph_new')
        @_$select = $('<select></select>')
        @_$selectDiv = $('<div style="text-align: center"></div>')
        @_$selectDiv.append(@_$select)
        @_$selfdiv.append(@_$selectDiv)
        @_lastBin = null
        @_$select.change(() =>
            @refresh(@_lastBin, true)
        )

        @_$grapherdiv = $('<div></div>')
        @_$selfdiv.append(@_$grapherdiv)

        @_controls = null

    _updateTimeControls: (bin, soft) ->
        if @_controls and soft and @_lastBin and bin.id == @_lastBin.id
            return
        if @_controls != null
            $(@_controls).off('timeChange')
            @_controls.delete()
            @_controls = null

        @_controls = new _SimpleGrapherTimeControls(@_$selfdiv, bin.id)
        $(@_controls).on('timeChange', (e, t1, t2) =>
            @refresh(bin, true)
        )
        @_controls.refreshFills(() =>
            @_controls.setLastFill()
        )


    _updateSelector: (bin) ->
        if @_lastBin and bin.id == @_lastBin.id
            return
        else
            oldval = @_$select.val()
            ovexists = false
            @_$select.empty()
            @_lastBin = bin
            for dgname, dg of IsadoreData.general.configs.dialog_graphs
                matches = true
                if dg.name_match?
                    re = new RegExp(dg.name_match)
                    if !bin.name.match(re)
                        matches = false
                if matches
                    @_$select.append('<option value="'+dgname+'">'+dgname+'</option>')
                    if oldval == dgname
                        ovexists = true
            if ovexists
                @_$select.val(oldval)

    _getTitle: (bin) ->
        title = $('option:selected', @_controls.fillSelect).text()
        if title
            return bin.name+'_fill'+(title.replace(' ', '-'))
        else
            return bin.name


    refresh: (bin, soft=false) ->
        console?.log("GraphsTabCustom refresh")
        if @_currentSimpleGrapher
            @_currentSimpleGrapher.delete()

        @_updateSelector(bin)
        @_updateTimeControls(bin, soft)
        title = @_getTitle(bin)

        tr = @_controls.getTimeRange()
        if isNaN(tr[0].getTime()) || isNaN(tr[0].getTime())
            @_$grapherdiv.text('Invalid time range.')
            return
        else
            @_$grapherdiv.empty()

        name = @_$select.val()
        if name
            dg = IsadoreData.general.configs.dialog_graphs[name]
            if dg.type? and dg.type == "image_heatmap"
                @_currentSimpleGrapher = new ImageHeatmap(
                    @_$grapherdiv,
                    bin.id,
                    dg.bin_section_ids,
                    dg.read_type_id,
                    dg.sample_period,
                    dg.options,
                    @_controls.getTimeRange()
                )
                return
            else
                highlights = @_controls.getHighlights()
                options = _.clone(dg.options, true)
                if options.highlights?
                    options.highlights.concat(highlights)
                else
                    options.highlights = highlights
                console.log(options)
                if dg
                    @_currentSimpleGrapher = new SimpleGrapher(@_$grapherdiv, bin, dg.queries, options, @_controls.getTimeRange(), title)
                    return
        @_$selfdiv.text('Graphs have not been set up for this bin.')




# TODO: Copied and Pasted -- Refactor/Consolidate
# Based on isadore_graphs.IsadoreGraphFooterControls_
class _SimpleGrapherTimeControls
    constructor: (@_$parentDiv, @_binId) ->
        @_timeRangeChangeHandlers = []
        @_$selfdiv = $('<div class="ig_footer_wrapper"></div>')
        @_$parentDiv.append(@_$selfdiv)
        @_highlights = []

        @_initTimeSelect()

        @fillSelect.change( (eventObject) =>
            fill = @getSelectedFill()
            if fill
                start = fill.air_begin_datetime
                end = fill.air_end_datetime
                if not start
                    start = fill.filled_datetime
                if not end
                    end = fill.emptied_datetime
                $(@timeRangeFields[0]).datetimepicker('setDate', new Date(start))
                if end
                    $(@timeRangeFields[1]).datetimepicker('setDate', new Date(fill.air_end_datetime))
                else
                    $(@timeRangeFields[1]).datetimepicker('setDate', new Date())
        )

        @agoSelect.change( (eventObject) =>
            v = @agoSelect.val()
            n = new Date()
            if v == '-1'
                return
            else
                tu = v[v.length-1]
                tv = -parseInt(v.substring(0, v.length-1), 10)
                if tu == 'd'
                    st = HTMLHelper.datetimeDelta({ 'date': n, 'days': tv })
                else
                    st = HTMLHelper.datetimeDelta({ 'date': n, 'hours': tv })
            $(@timeRangeFields[0]).datetimepicker('setDate', new Date(st))
            $(@timeRangeFields[1]).datetimepicker('setDate', new Date(n))
        )

        @timeRangeFields.change( (eventObject) =>
            clearTimeout(@timeRangeChangeTimeout_)
            @timeRangeChangeTimeout_ = setTimeout( () =>
                times = [$(@timeRangeFields[0]).datetimepicker('getDate'), $(@timeRangeFields[1]).datetimepicker('getDate')]
                @_highlights = []
                fill = @getSelectedFill()
                if fill
                    fillTimes = [new Date(fill.air_begin_datetime), new Date(fill.air_end_datetime)]
                    if not times[0] or fillTimes[0].getTime() != times[0].getTime() or not times[1] or fillTimes[1].getTime() != times[1].getTime()
                        @fillSelect.val(-1)
                        @agoSelect.val(-1)
                    else
                        @_generateHighlights(fill)
                $(@).triggerHandler('timeChange', [times[0], times[1]])
            , 2000)
        )

    #Returns the currently selected fill or null if none
    getSelectedFill: () ->
        fill = null
        fillIdx = Number(@fillSelect.val())
        if fillIdx >= 0
            fill=@fills[fillIdx]
        return fill

    getSelectedAgo: () ->
        v = @agoSelect.val()
        return v

    _generateHighlights: (fill) ->
        highlightColor = '#BFBFBF'
        @_highlights = []
        if fill.air_end_datetime?
            endd = new Date(fill.air_end_datetime)
        else
            endd = new Date()
        if fill.roll_datetime?
            if _.isArray(fill.roll_datetime)
                rolls = []
                for roll in fill.roll_datetime
                    rolls.push(new Date(roll))
                rolls = _.sortBy(rolls)

                for i in [0...rolls.length]
                    if (i % 2) == 0
                        if rolls.length > i+1
                            @_highlights.push({color: highlightColor, start: rolls[i], end: rolls[i+1]})
                        else
                            @_highlights.push({color: highlightColor, start: rolls[i], end: endd})
            else
                @_highlights.push({color: highlightColor, start: new Date(fill.roll_datetime), end: endd})

    getHighlights: () ->
        return @_highlights


    _initTimeSelect: () ->
        #Fill Selector
        timeDiv = $('<div class="ig_footer_time_wrapper"></div>')
        timeDiv.append($('<label>Fill:</label>'))
        @fillSelect = $('<select class="ig_footer_fill_select"><option value="-1">Loading...</option></select>')
        timeDiv.append(@fillSelect)
        @agoSelect=$('<select>
			<option value="-1"></option>
			<option value="1h">1h</option>
			<option value="3h">3h</option>
			<option value="6h">6h</option>
			<option value="12h">12h</option>
			<option value="1d">1d</option>
			<option value="2d">2d</option>
			<option value="3d">3d</option>
			<option value="4d">4d</option>
			</select>')
        timeDiv.append($('<label>Time Ago:</label>'))
        timeDiv.append(@agoSelect)
        #Time selector
        @_$selfdiv.append(timeDiv)
        @_initTimeRange(timeDiv)


    _initTimeRange: (timeDiv) ->
        div = $('<div class="ig_timeselector_wrapper"></div>')
        div.append($('<label>Time Range:</label>'))
        for idCount in [0...2]
            id = "ig_timeselector_#{uuid.v4()}"
            div.append($('<input type="text" class="calendar ig_timeselector" id="'+id+'"/><img src="imgs/icon_calendar.gif" data-date_id="'+id+'" alt="Pick date/time" />'))
            if idCount == 0
                div.append(document.createTextNode(' - '))
        calendarRegister($('.calendar', div))
        calendarImageRegister($('img[src="imgs/icon_calendar.gif"]', div));
        timeDiv.append(div)
        @timeRangeFields = $('input', div)


    _updateFillSelector: () ->
        select = $('select.ig_footer_fill_select', @_$selfdiv)
        options='<option value="-1"> </option>'
        for i in [0...@fills.length]
            fill = @fills[i]
            start = fill.air_begin_datetime
            if not start
                start = fill.filled_datetime
            options += "<option value=\"#{i}\">#{fill.fill_number} #{new Date(start).getFullYear()}</option>"
        select.html(options)

    refreshFills: (callback) ->
        prefixPath = "../"
        $.ajax({
            url: prefixPath + 'resources/data/fills-fast'
            type: 'GET'
            dataType: 'json'
            success: (data) =>
                @fills=data.fills
                @_updateFillSelector()
                if callback
                    callback()
            data: {
                'bin_id' : @_binId
            }
        })
        return this

    # @returns [beginDate, endDate]
    getTimeRange: () ->
        return [
            $(@timeRangeFields[0]).datetimepicker('getDate')
            $(@timeRangeFields[1]).datetimepicker('getDate')
        ]

    # If fill1 starts after fill2 return true
    _laterFill: (fill1, fill2) ->
        if fill1.air_begin_datetime?
            f1start = newDate(fill1.air_begin_datetime)
        else
            f1start = newDate(fill1.filled_datetime)
        if fill2.air_begin_datetime?
            f2start = newDate(fill2.air_begin_datetime)
        else
            f2start = newDate(fill2.filled_datetime)
        if f1start > f2start
            return true
        return false

    _getYearFill: (fill) ->
        d = null
        if fill1.air_begin_datetime?
            d = newDate(fill.air_begin_datetime)
        else
            d = newDate(fill.filled_datetime)
        if d
            return d.getFullYear();
        return null


    delete: () ->
        @_$selfdiv.remove()

    setLastFill: () ->
        lastFill = null
        if not @fills
            @agoSelect.val('3h')
            @agoSelect.change()
            return
        for fill in @fills
            if not lastFill
                lastFill = fill
            else if @_laterFill(fill, lastFill)
                lastFill = fill
        if lastFill and @_getYearFill(lastFill) == new Date().getFullYear()
            idx = @fills.indexOf(lastFill)
            console.log('last fill idx = '+idx)
            @fillSelect.val(idx)
            @fillSelect.change()
        else
            @agoSelect.val('3h')
            @agoSelect.change()
