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


#Other View format
#"other_views": [  #Array of view objects
#    {
#        "title": "Fill View", #display title of view
#        "type": "fill_view|diagnostics|sensor_view",  #Type of view
#        #The view object for fill_view
#        "view": {
#            "fill_view_list": [ # Array list of fill_views, will do it in order
#                {
#                    "view": "fill_view", #name of the view there are fill_view and fill_view_cell# as possibilities
#                                         # fill_view goes through a list of bins and fill_view_cell# is more standalone.
#                                         # you can have multiple fill_view with different bins it goes through.
#                                         # You might want to do fill_view, some fill_view_cells, and fill_view again.
#                    "bin_ids": [ # Array of bin ID's to go through in the "fill_view" view
#                        12, 13, 14, ...
#                    ],
#                    "options": { # Fill view options
#                        "table_class": "original_fill_view"  #What class this fill_view table should have original_fill_view or pleasent_fill_view for example
#                        "hide_labels": true,  #default false, this hides the left side labels of a fill_view
#                        "column_class": [ #Allows settings column css class based off result of a function See "FillViewStyler"
#                           {
#                                "func": "fillStatusStyle", #Function to use to determine column css class
#                                "keys": [ #data keys that go with the function.
#                                     "fill.filled_datetime", "fill.emptied_datetime", "fill.air_begin_datetime", ...
#                                ]
#                            }
#                        ],
#                        "hover": { #Hoover options
#                            "row_disable": true, #Disable row hovering, default false
#                            "thead_enable": true, #Enable hovering head when novered over column default false
#                        }
#                        "clickfunc": "fillDialog|binLightBoxClick,.." #Which function in CurrentDataClick to use when clicking on a the table, default 'binLightboxClick'
#                    }
#                },
#                {
#                    "view": "fill_view_cell1",  #Id for a cell view to go through
#                    "options": {
#                        "table_class": "original_fill_view"  #What class this cell view table will have
#                    }
#                }
#                {
#                    "view": "raw1", #Just display some raw html, no key below that needs to match.
#                    "html": "<table class=\"fill_view_legend\"><tr><td class=\"bolded\" colspan=\"2\">Legend</td></tr><tr><td>Up Air</td><td class=\"fv_upair\">Value</td></tr><tr><td>Down Air</td><td class=\"fv_downair\">Value</td></tr><tr><td>Burners</td><td>PV (SP)</td></tr><tr><td>Full/Drying</td><td class=\"fv_full\"></td></tr><tr><td>Empty</td><td class=\"fv_empty\"></td></tr><tr><td>Shelling</td><td class=\"fv_shelling\"></td></tr><tr><td>Filling</td><td class=\"fv_filling\"></td></tr></table>" #html as a string
#                }
#                ... other fill_view_cells, or fill_views, or raw lists...
#            ],
#            "fill_view": [   #What to show in the fill_view
#                {
#                    "label": "Fill #",  #Lable to display on the left of fill_view table
#                    "keys": [  #Array of data keys, could be fill.fill_column or readings.binsection_sensorshortname
#                        "fill.fill_number"
#                        "readings.top_temp",
#                        "readings.bottom_temp"
#                    ],
#                    "format": null,  #Which format function to send data to. See object "FillViewFormater"
#                    "class": [  #Which classes the contents of a colum in a fill_view should have
#                        {
#                            "func": "upDownAirStyle", #Function to call in "FillViewStyler"
#                            "keys": [ #data keys that go to function
#                                "readings.top_temp", "readings.bottom_temp", ...
#                            ]
#                        },
#                        ... More class functions or string for static class...
#                    ]
#                },
#                ... more stuff to show in fill_view
#            ],
#            "fill_view_cell1": [  #What to display in the cell table
#                {
#                    "label": "Burner&nbsp;1",  #Cell name
#                    "class": "bolded"  #Class content should have in cell. Can also be a array with object.func object.keys like in fill_view
#                },
#                {
#                    "label": "Burner&nbsp;SP",
#                    "bin_id": 100, #Which bins can be array of multiple binIds, data keys then being readings0, readings1, ..., instead of just readings
#                    "colspan": 3,  # How many columns the cell should take up, default is 1
#                    "keys": [  #Data keys  similar to fill_view keys
#                        "readings.burner.sp"
#                    ],
#                    "format": "fixed1T"  #format function see "FillViewFormater"
#                    "display": "adjacent"  #if "adjacent, there should be no linebreak between label and value
#                    "readings_func": "upBinsCount" # should get value using a entire readings function, instead of bin/fill based, see "FillViewFunc"
#                },
#                ... More cells to display ...
#            ],
#           ... More fill_view_cell# ...
#        }
#        # diagnostics view
#        "view": {
#            "interval": 1500   #refresh_in_milliseconds
#        }
#        # sensor_view
#        "view": {
#            block: [  #Can have any number of types in any order
#                #Type table
#                {
#                    "type": "table",
#                    "row_type": "bin|section",
#                    "alignment": "full|left|right",
#                    "columns": [
#                        {
#                            "bin_section_id": int, # If 'bin' row_type, or null if just want a label column
#                            "read_type_id": int, # Can be null if just want a label column
#                            "column_label": string, #keys: $bin_section_name$, $read_type_short_name$, $read_type_units$, $read_type_name$
#                            "value": string # keys: $bin_number$, $bin_name$, $bin_section_name$, $valueF1$, $valueF2$
#                        }, ...
#                    ],
#                    "bin_ids": [int, int, ...], # if 'bin' row_type
#
#                    "bin_id": int, # if 'section' row_type
#                    "bin_section_ids": [int, int, ...], # if 'section' row_type
#
#                    "header": { # or can be null
#                        "label": string,
#                        "class": string
#                    }
#                },
#                #Type diagram
#                {
#                    "type": "diagram",
#                    "yindexes": [int, int, ...], # or "all"
#                    "header": { # or can be null
#                        "label": string,
#                        "class": string
#                    }
#                },
#                {
#                   "type": "config"
#                }
#                ...
#            ]
#        }
#    }



FillViewStyler = {
    upDownAirStyle: (topTemp, bottomTemp) ->
        if topTemp > bottomTemp
            return "fv_downair"
        else if(topTemp < bottomTemp)
            return "fv_upair"
        return null
    fillStatusStyle: (type, filled, emptied, air_begin, air_end, roll) ->
        if type == 2
            return "fv_bypass"
        else
            if air_end and !emptied
                return "fv_shelling"
            if air_begin and !air_end
                return "fv_drying"
            if filled and !air_begin
                return "fv_filling"
            if not filled
                return "fv_empty"
            return "fv_unknown"
}


FillViewFormater = {
    lastSample: (during_mc) ->
        last = null
        for mcd in during_mc
            mc = mcd[0]
            d = newDate(mcd[1])
            if not last or d > last[1]
                last = [mc, d]
        if last
            return last[0].toFixed(1)
    lastSampleDate: (during_mc) ->
        last = null
        for mcd in during_mc
            mc = mcd[0]
            d = newDate(mcd[1])
            if not last or d > last[1]
                last = [mc, d]
        if last
            return HTMLHelper.dateToReadableO3(last[1])
    _mean: (array) ->
        if not array
            return null
        if not _.isArray(array)
            return array
        if array.length == 0
            return null
        s = 0
        for a in array
            s += a
        s=s/array.length
        return s
    mean: (array) ->
        if array
            if not _.isArray(array)
                return array.toFixed(2)
            t = @_mean(array)
            if t
                return t.toFixed(2)
        return null
    meanArg: (array...) ->
        return @mean(array)
    timeUpCalc: (begin, roll) ->
        # TODO: Air deducts
        # TODO: Support multiple rolls
        if begin
            begin = newDate(begin)
            if roll and roll.length > 0
                if _.isArray(roll)
                    t = newDate(roll[0])
                else
                    t = newDate(roll)
                return FillViewFormater.timeDiff(t, begin)
            else
                return FillViewFormater.timeDiffNow(begin)
        return null
    timeDiffNow: (time, orend) ->
        # TODO: Air deducts
        # TODO: Support multiple rolls
        if orend and orend != ''
            orend = newDate(orend)
        else
            orend = null
        t = null
        now = new Date()
        if time
            if _.isArray(time)
                t = newDate(time[0])
            else
                t = newDate(time)
            if orend
                t = FillViewFormater.timeDiff(orend, t)
            else
                t = FillViewFormater.timeDiff(now, t)
        return t
    timeDiff: (gr, ls) ->
        if not gr or not ls
            return null
        else
            return ((gr.getTime() - ls.getTime())/(1000.0*60*60)).toFixed(2)
    airDirection: (topt, bott) ->
        t = @_mean(topt)
        b = @_mean(bott)
        if t and b
            r=(b-t)
            if r > 0
                return 'Up'
            else if r < 0
                return 'Down'
        return null
    fixed1T: (t, u) ->
        t2 = @_mean(t)
        if t2
            return t2.toFixed(1)
        return null
    fixed1P: (rh) ->
        t2 = @_mean(rh)
        if t2
            return t2.toFixed(1)
        return null
    numberSplit: (str) ->
        a = str.split(' ')
        for v in a
            i = parseInt(v, 10)
            if(!isNaN(i))
                return i
        return NaN
    twoPerns: (v1, v2) ->
        return v1.toFixed(1)+' ('+v2.toFixed(1)+')'
}

FillViewFunc = {
    _binCount: (up, readings, fills, nameFilter) ->
        upCount = 0
        downCount = 0
        for binId, bin of readings
            binId = parseInt(binId, 10)
            if nameFilter
                bn = _.findWhere(IsadoreData.bins, {id: binId})
                if not bn.name.match(nameFilter)
                    continue
            if bin.top_temp? and bin.bottom_temp?
                fill = CurrentDataUtil.getBinFill(fills, binId, false)
                if not fill.id?
                    continue
                fstyle = FillViewStyler.fillStatusStyle(fill.fill_type_id, fill.filled_datetime, fill.emptied_datetime, fill.air_begin_datetime, fill.air_end_datetime, fill.roll_datetime)
                if fstyle != "fv_drying"
                    continue
                if up and bin.top_temp < bin.bottom_temp
                    upCount++
                if !up and bin.top_temp > bin.bottom_temp
                    downCount++
        if up
            return upCount + " Up Bins"
        else
            return downCount + " Down Bins"


    # Calculates and outputs string of number of bins in up air
    upBinsCount: (readings, fills) ->
        return this._binCount(true, readings, fills)

    # Calculates and ouputs string number of bins in down air
    downBinsCount: (readings, fills) ->
        return this._binCount(false, readings, fills)

    #TODO: Be able to send custom arguments to readings_func
    # Calculates and outputs string of number of bins in up air
    upBinsCountFilter1: (readings, fills) ->
        return this._binCount(true, readings, fills, new RegExp('^Bin 1'))

    # Calculates and ouputs string number of bins in down air
    downBinsCountFilter1: (readings, fills) ->
        return this._binCount(false, readings, fills, new RegExp('^Bin 1'))


    # Calculates and outputs string of number of bins in up air
    upBinsCountFilter2: (readings, fills) ->
        return this._binCount(true, readings, fills, new RegExp('^Bin 2'))

    # Calculates and ouputs string number of bins in down air
    downBinsCountFilter2: (readings, fills) ->
        return this._binCount(false, readings, fills, new RegExp('^Bin 2'))

}

window.CurrentDataUtil = {
    getBinFill: (fills, bin_id, air_end) ->
        now = new Date()
        for fill in fills by -1
            if fill and fill.bin_id == bin_id and not fill.emptied_datetime? and (not air_end || not fill.air_end_datetime?)
                if fill.filled_datetime?
                    fill.filled_datetime = newDate(fill.filled_datetime)
                if fill.air_begin_datetime?
                    fill.air_begin_datetime = newDate(fill.air_begin_datetime)
                #If filled > now and (not emptied) or air_begin > now and not air_end
                if ((fill.filled_datetime? and fill.filled_datetime < now) or (fill.air_begin_datetime? and fill.air_begin_datetime < now))
                    return fill
        return {}
}

CurrentDataClick = {
    _getFillYear: (yfill) ->
        if yfill.filled_datetime?
            year = newDate(yfill.filled_datetime).getFullYear()
        else
            year = newDate(yfill.air_begin_datetime).getFullYear()
        return year

    _openNewFill: (binId) ->
        lightboxHandlers.editFillLightbox.open({
            year: new Date().getFullYear()
            bin_id: binId
        })

    _openEditFill: (fill) ->
        self=this
        lightboxHandlers.editFillLightbox.open({year: self._getFillYear(fill), fill_id: fill.id})

    binLightboxClick: (binId, fill) ->
        lightboxHandlers.binLightbox.open(binId)

    fillDialog: (binId, fill) ->
        #TODO: Check privs do binLightboxClick if not enough privs
        bin = IsadoreData.getBin(binId)
        hasPriv = true
        if not hasPriv or bin.name.indexOf('Bin') != 0
            this.binLightboxClick(binId, fill)
        else
            statusStyle = FillViewStyler.fillStatusStyle(fill.fill_type_id, fill.filled_datetime, fill.emptied_datetime, fill.air_begin_datetime, fill.air_end_datetime, fill.roll_datetime)
            if statusStyle == 'fv_empty'
                this._openNewFill(binId)
            else
                this._openEditFill(fill)
}

class window.CurrentDataFillViewHandler
    constructor: (viewTitle, $selfDiv, viewConfig) ->
        @_fills = []
        @_viewTitle = viewTitle
        @_$selfDiv = $selfDiv
        @_viewConfig = viewConfig

        @_$selfDiv.append("""
                            <h1>
                                #{ viewTitle }<span class="last_update">Sensor Data
                                        Updated <span class="last_update_datetime"></span>
                                    </span>
                            </h1>
        """)
        @_$overlay = $('<div class="fill_view_overlay"></div>')
        @_$selfDiv.append(@_$overlay)



    _getBinReadings: (bin_id) ->
        if @_readings?.hasOwnProperty(bin_id)
            return @_readings[bin_id]
        return {}

    _getCellData: (bin_id) ->
        data = {}
        if _.isArray(bin_id)
            for i in [0...bin_id.length]
                data['fill'+i] = CurrentDataUtil.getBinFill(@_fills, bin_id[i], false)
                data['readings'+i] = @_getBinReadings(bin_id)
                data['bin'+i] = IsadoreData.getBin(bin_id)
        else
            data = {fill: CurrentDataUtil.getBinFill(@_fills, bin_id, false), readings: @_getBinReadings(bin_id), bin: IsadoreData.getBin(bin_id)}


    _getCellValue: (data, onlyIfFill, keys, format) ->
        if onlyIfFill and not data.fill?.id?
            return null
        val = null
        if format
            try
                args = []
                for key in keys
                    obj = data
                    for k in key.split('.')
                        obj = obj[k]
                    args.push(obj)
                val = FillViewFormater[format].apply(FillViewFormater, args)
            catch e
                #console?.error?(e)
                val = null
        else if keys.length > 0
            try
                obj = data
                for k in keys[0].split('.')
                    obj = obj[k]
                val= obj
                if val and k.indexOf('_datetime') == k.length - 9
                    val = HTMLHelper.dateToReadableO3(newDate(val))
            catch e
                #console?.error?(e)
                val = null
        return val

    _makeFillViewCellRow: (row) ->
        if not @_viewConfig.hasOwnProperty(row.view)
            return null
        columns = @_viewConfig[row.view]
        tr = $('<tr></tr>')
        for column in columns
            td = $('<td></td>')
            cell_value = null
            content = null
            if column.label?
                content = column.label
            if column.class?
                td.attr('class', column.class)
            if column.colspan?
                td.attr('colspan', column.colspan)
            if column.keys? and column.bin_id?
                cell_value = @_getCellValue(@_getCellData(column.bin_id), false, column.keys, column.format)
                if cell_value
                    if content and (!column.display? or column.display != 'adjacent')
                        content += "<br/>"+cell_value
                    else
                        content = cell_value
            if column.readings_func?
                try
                    cell_value2 = FillViewFunc[column.readings_func].apply(FillViewFunc, [@_readings, @_fills])
                    if content and (!column.display? or column.display != 'adjacent')
                        content += "<br/>"+cell_value2
                    else
                        content = cell_value2
                catch e
                    if console?.error?
                        console.error(e)
            if content
                td.html(content)
            if column.bin_id?
                td.attr('data-info', ''+column.bin_id)
            tr.append(td)
        return tr

    _getDynamicClass: (classInfo, bin_id) ->
        if _.isString(classInfo)
            return classInfo
        cssClasses = []
        if !_.isArray(classInfo) and _.isObject(classInfo)
            cl = @_getDynamicClassFromObj(classInfo, bin_id)
            if cl
                cssClasses.push(cl)
        else if _.isArray(classInfo)
            for classObj in classInfo
                cl = @_getDynamicClassFromObj(classObj, bin_id)
                if cl
                    cssClasses.push(cl)
        return cssClasses.join(' ')

    _getDynamicClassFromObj: (classObj, bin_id) ->
        if classObj.plain? and _.isString(classObj.plain)
            return classObj.plain
        if classObj.func? and _.isString(classObj.func)
            data = null
            if classObj.bin_id?
                data = @_getCellData(classObj.bin_id)
            else if bin_id
                data = @_getCellData(bin_id)

            try
                args = []
                for key in classObj.keys
                    obj = data
                    for k in key.split('.')
                        obj = obj[k]
                    args.push(obj)
                val = FillViewStyler[classObj.func].apply(FillViewStyler, args)
            catch e
                console?.error?(e)
                val = null
            return val
        return null




    _makeRowTable: (row) ->
        table = $('<table class="fill_view_table"></table>')
        fv = null
        arow = row
        if @_viewConfig.fill_view?
            fv = @_viewConfig.fill_view
        table_data = []
        if row.view == 'fill_view'
            # First row is bin_names
            table_row = [{'data-info': -1, content: "Bin"}]
            for bin_id in row.bin_ids
                if bin_id == "empty"
                    table_row.push({'data-info': -1, content: '&nbsp;', 'data-columnclass': 'fv_nodata'})
                else
                    name = IsadoreData.getBin(bin_id).name.split(" ")
                    if name.length > 1
                        name = name[1]
                    else
                        name = name[0]
                    table_column = {'data-info': bin_id, content: name}
                    if row.options?.column_class?
                        cl = @_getDynamicClass(row.options.column_class, bin_id)
                        if cl
                            table_column['data-columnclass'] = cl
                    table_row.push(table_column)
            table_data.push(table_row)
            for fv_row in fv
                table_row=[]
                table_row.push(fv_row.label)
                for bin_id in row.bin_ids
                    if bin_id == "empty"
                        table_row.push('&nbsp;')
                    else
                        cell_value = @_getCellValue(@_getCellData(bin_id), true, fv_row.keys, fv_row.format)
                        cell_class = null
                        if fv_row.class?
                            cell_class = @_getDynamicClass(fv_row.class, bin_id)
                        table_row.push({'data-info': bin_id, content: cell_value, class: cell_class})

                table_data.push(table_row)
        #Make HTML from table_data
        firstRow = true
        thead = $('<thead></thead>')
        table.append(thead)
        tbody = $('<tbody></tbody>')
        table.append(tbody)

        for row in table_data
            if firstRow
                tr = $('<tr></tr>')
                thead.append(tr)
            else
                tr = $('<tr></tr>')
                tbody.append(tr)
            firstColumn = true
            for column in row
                if firstColumn or firstRow
                    td = $('<th></th>')
                else
                    td = $('<td></td>')
                if _.isObject(column)
                    if column.hasOwnProperty('data-columnclass')
                        td.attr('data-columnclass', column['data-columnclass'])
                    if column.hasOwnProperty('data-info')
                        td.attr('data-info', column['data-info'])
                    if column.content?
                        td.html(column.content)
                    if column.class?
                        td.addClass(column.class)
                else
                    td.html(column)
                if not firstColumn or !(arow.options?.hide_labels)
                    tr.append(td)
                firstColumn = false
            firstRow = false
        return table

    _makeColumnClass: ($table) ->
        $tr = $('tr:first-child', $table)
        $('th, td', $tr).each( (index, element) ->
            rc = $(element).attr('data-columnclass')
            $(element).addClass(rc)
            if rc
                $('tbody tr', $table).each( (index2, element2) ->
                    $('th,td', element2).eq(index).addClass(rc)
                )
        )

    _makeHover: (table, hoverOptions) ->
        table.delegate('tbody th,tbody td', 'mouseover mouseleave', (e) ->
            $ourTd=$(this)
            if e.type == 'mouseover'
                if not hoverOptions?.row_disable
                    $('th,td', $ourTd.parent()).addClass('hover')
                if $ourTd.index() != 0
                    $('tbody tr', table).each( (index, element) ->
                        $('th,td', element).eq($ourTd.index()).addClass('hover')
                    )
                    if hoverOptions?.thead_enable
                        $('thead tr', table).each( (index, element) ->
                            $('th,td', element).eq($ourTd.index()).addClass('hover')
                        )
                    $ourTd.removeClass('hover').addClass('super_hover')
            else
                $('th,td', $ourTd.parent()).removeClass('hover')
                $ourTd.removeClass('super_hover')
                $('tbody tr', table).each( (index, element) ->
                    $('th,td', element).eq($ourTd.index()).removeClass('hover')
                )
                $('thead tr', table).each( (index, element) ->
                    $('th,td', element).eq($ourTd.index()).removeClass('hover')
                )
        )

    _makeClick: (table, clickfunc) ->
        self = this
        $('tbody td, thead th', table).click((e) ->
            console.log(this)
            console.log(clickfunc)
            $ourTd=$(this)
            idx = $ourTd.index()
            bin_id = $ourTd.attr('data-info')
            if not bin_id
                bin_id = $('thead tr th', table).eq(idx).attr('data-info')
            if not clickfunc
                clickfunc = 'binLightboxClick'
            if bin_id
                bin_id = parseInt(bin_id, 10)
                console?.log?("Click bin_id #{bin_id}")
                fill = CurrentDataUtil.getBinFill(self._fills, bin_id, false)
                CurrentDataClick[clickfunc](bin_id, fill)
                e.preventDefault()
        )

    _updateReadingMap: () ->
        # _readings has structure
        # { binid#: {'lcsection_sshortname': value, ...}, ..}
        @_readings = {}
        noOldData = true
        hourAgo = HTMLHelper.datetimeDelta({date: new Date(), hours: -1})
        if noOldData and (not IsadoreData.lastReadingsDatetime? or IsadoreData.lastReadingsDatetime < hourAgo)
            console?.log?('Last Reading too long ago for fill view.')
        else
            for bin in IsadoreData.bins
                @_readings[bin.id] = {}
                if bin.readings?
                    for reading in bin.readings
                        if reading.value? and reading.datetime > hourAgo
                            readTypeName = IsadoreData.readTypesIdMap[reading.read_type_id].short_name.toLowerCase()
                            binSectionName = IsadoreData.binSectionsIdMap[reading.bin_section_id].name.toLowerCase()
                            key = binSectionName+'_'+readTypeName
                            if not @_readings[bin.id].hasOwnProperty(key)
                                @_readings[bin.id][key] = reading.value
                            else if _.isArray(@_readings[bin.id][key])
                                @_readings[bin.id][key].push(reading.value)
                            else
                                @_readings[bin.id][key] = [@_readings[bin.id][key], reading.value]

    _makeFillViewCellHover: () ->
        $('.fill_view_cell_table', @_$overlay).delegate('td', 'mouseover mouseleave', (e) ->
            $ourTd=$(this)
            dataInfo = $ourTd.attr('data-info')
            if e.type == 'mouseover'
                $('.fill_view_cell_table td[data-info="'+dataInfo+'"]', @_$overlay).addClass('hover')
            else
                $('.fill_view_cell_table td[data-info="'+dataInfo+'"]', @_$overlay).removeClass('hover')
        )

    _makeFillViewCellClick: () ->
        $('.fill_view_cell_table td', @_$overlay).click((e) ->
            $ourTd=$(this)
            bin_id = $ourTd.attr('data-info')
            if bin_id
                bin_id = parseInt(bin_id, 10)
                console?.log?("Click bin_id #{bin_id}")
                lightboxHandlers.binLightbox.open(bin_id)
        )

    _makeFixedWidthCols: ($table) ->
        $colgroup = $('<colgroup></colgroup')
        s = $('tbody tr:first-child > td, tbody tr:first-child > th', $table).length
        p=100.0/s
        for i in [0...s]
            $colgroup.append($('<col style="width: '+p+'%"/>'))
        $table.prepend($colgroup)


    refresh: (fills) ->
        @_fills = fills
        console?.log?('Fill view refresh')
        @_$overlay.empty()
        @_updateReadingMap()
        fillViewCellTable = null
        if @_viewConfig?.fill_view_list?
            for row in @_viewConfig.fill_view_list
                if row.view == 'fill_view'
                    fillViewCellTable = null
                    table = @_makeRowTable(row)
                    if row.options?.table_class?
                        #TODO: Extended class option
                        $(table).addClass(row.options.table_class)
                    @_makeFixedWidthCols(table)
                    @_$overlay.append(table)
                    @_makeHover(table, row.options?.hover)
                    @_makeColumnClass(table)
                    @_makeClick(table, row.options?.clickfunc)
                else if row.view.indexOf('fill_view_cell') == 0
                    if not fillViewCellTable
                        fillViewCellTable = $('<table class="fill_view_cell_table"></table>')
                        if row.options?.table_class?
                            #TODO: Extended class option
                            $(fillViewCellTable).addClass(row.options.table_class)
                        @_$overlay.append(fillViewCellTable)
                    cellRow = @_makeFillViewCellRow(row)
                    if cellRow?
                        fillViewCellTable.append(cellRow)
                else if row.view.indexOf('raw') == 0
                    rawTable = $(row.html)
                    @_$overlay.append(rawTable)
            @_makeFillViewCellHover()
            @_makeFillViewCellClick()
        else
            @_$overlay.html('Contact Exoteric Analytics if you would like a Fill View.')
        fixHeights()


class window.DiagnosticsViewHandler
    constructor: (viewTitle, $selfDiv, viewConfig) ->
        @_viewTitle = viewTitle
        @_$selfDiv = $selfDiv
        @_viewConfig = viewConfig

        @_$selfDiv.append("""
                            <h1>
                                #{ viewTitle }<span class="last_update">Sensor Data
                                        Updated <span class="last_update_datetime"></span>
                                    </span>
                                <button class="reset_diag priv_config">Reset</button>
                            </h1>
        """)
        if not IsadoreData.selfAccount.hasPrivilege('Config User')
            $('.priv_config', @_$selfDiv).hide()

        $('.reset_diag', @_$selfDiv).click(() =>
            $.ajax(
                {
                    url: "../resources/data/diagnostics_sensor_data_latest_reset"
                    type: 'DELETE',
                    dataType: 'text'
                }
            )
        )

        @_$overlay = $('<div class="diagnostics_view_overlay"></div>')
        @_$selfDiv.append(@_$overlay)
        @_$spinner = $('<img class="center_margins spinner" src="imgs/ajax-loader.gif" alt="Loading Spinner"/>')
        @_$overlay.append(@_$spinner)
        @_$table = $('<table class="diagnostics_table display hover" rules="rows"></table>')
        @_$overlay.append(@_$table)
        @_selfVisible = false
        @_$selfDiv.on('DOMAttrModified', () =>
            if @_$selfDiv.is(':visible') and not @_$selfVisible
                console.log('Diag div visible')
                @_$selfVisible = true
                @refresh()
            else if not @_$selfDiv.is(':visible')
                @_$selfVisible = false
        );

    _update: () ->
        if not @_$overlay.closest(document.documentElement)
            return
        if not @_$overlay.is(':visible')
            @_$table.hide()
            @_$spinner.show()
            return
        @_fetchData(
            () =>
                return
        )

    _fetchData: (cb) ->
        $.ajax(
            {
                url: "../resources/data/diagnostics_sensor_data_latest"
                type: 'GET',
                dataType: 'json'
                success: (d) =>
                    @_refreshTable(d.results, cb)
                error: () ->
                    cb()
            }
        )

    _refreshTable: (d, cb) ->
        console.log('_refreshTable')
        tableColumns = [
            {sTitle: 'dT'},
            {sTitle: 'MID Name'},
            {sTitle: 'Port'},
            {sTitle: 'Address'},
            {sTitle: 'Info'},
            {sTitle: 'Bin'},
            {sTitle: 'Bin Section'},
            {sTitle: 'Read Type'},
            {sTitle: 'Err'},
            {sTitle: 'Value'},
            {sTitle: 'Raw'}
        ]
        tableData = []
        now = new Date()
        for row in d
            tableData.push([
                ((now - newDate(row.datetime))/1000.0).toFixed(1)
                row.mid_name
                row.port
                row.address
                row.device_info
                row.bin_name
                row.bin_section_name
                row.read_type_short_name
                row.error_code
                row.value
                row.raw_data
            ])
        #@_$spinner.hide()
        @_$table.show()
        dt = @_$table.dataTable({
            bPaginate: false
            bRetrieve: true
            bFilter: true
#            aaData: tableData
            aoColumns: tableColumns
        })
        dt.fnClearTable()
        dt.fnAddData(tableData)
        fixHeights()
        cb()

    refresh: () ->
        @_$spinner.hide()
        #@_$table.hide()
        @_update()


class window.SensorViewHandler
    constructor: (viewTitle, $selfDiv, viewConfig) ->
        @_viewTitle = viewTitle
        @_$selfDiv = $selfDiv
        @_viewConfig = viewConfig

        @_$selfDiv.append("""
                            <h1>
                                #{ viewTitle }<span class="last_update">Sensor Data
                                        Updated <span class="last_update_datetime"></span>
                                    </span>
                            </h1>
        """)
        @_$overlay = $('<div class="diagnostics_view_overlay"></div>')
        @_$selfDiv.append(@_$overlay)
        @_$spinner = $('<img class="center_margins spinner" src="imgs/ajax-loader.gif" alt="Loading Spinner"/>')
        @_$overlay.append(@_$spinner)
        @_selfVisible = false
        @_$selfDiv.on('DOMAttrModified', () =>
            if @_$selfDiv.is(':visible') and not @_$selfVisible
                console.log('Diag div visible')
                @_$selfVisible = true
                @refresh()
            else if not @_$selfDiv.is(':visible')
                @_$selfVisible = false
        );

    _replace: (str, replaceMap) ->
        if str
            for key, value of replaceMap
                str2 = null
                while str != str2
                    if str2
                        str = str2
                    str2 = str.replace(key, value)
        return str

    _header: (header, $div) ->
        $header = $('h2', $div)
        if not $header[0]
            cssclass=''
            label=''
            if header.label?
                label = header.label
            if header.class?
                cssclass = header.class
            $header = $("<h2 class=\"#{cssclass}\"><span>#{label}</span></h2>")
        $div.append($header)

    _findWindDirection: (bin_id, readings) ->
        if not readings
            return 0
        if IsadoreData?.general?.configs?.sensor_view?.no_fill_no_arrows? and IsadoreData.general.configs.sensor_view.no_fill_no_arrows and not CurrentDataUtil.getBinFill(@_fills, bin_id, true).id?
            return 0
        top_temp = 0
        bottom_temp = 0
        for reading in readings
            if IsadoreData.readTypesIdMap[reading.read_type_id].name == 'Temperature'
                if IsadoreData.binSectionsIdMap[reading.bin_section_id].name == "Bottom"
                    bottom_temp = reading.value
                else if IsadoreData.binSectionsIdMap[reading.bin_section_id].name == "Top"
                    top_temp = reading.value
        if top_temp != 0 and bottom_temp != 0
            return (bottom_temp - top_temp)
        return 0

    _tableRowClass: (binId) ->
        for al in IsadoreData.selfAlarms
            # TODO: Fix hard code
            if al.alarm_type_id == 14
                if al.greater_than_p
                    alarmReadings = _.filter(IsadoreData.readings, (o) ->
                       return o.bin_id == binId && (o.bin_section_id == 13 || o.bin_section_id == 14) && o.read_type_id == 10 && o.value > al.value
                    );
                    if alarmReadings.length > 0
                        return 'red'
                else
                    alarmReadings = _.filter(IsadoreData.readings, (o) ->
                        return o.bin_id == binId && (o.bin_section_id == 13 || o.bin_section_id == 14) && o.read_type_id == 10 && o.value <= al.value
                    );
                    if alarmReadings.length > 0
                        return 'red'
        return null

    _updateTable: (i, block) ->
        $div = $('div[name="block'+i+'"]', @_$selfDiv)
        if not $div[0]
            divclass = ''
            if block.alignment == 'left'
                $specificDiv = $('<div class="specific"></div>')
                @_$selfDiv.append($specificDiv)
                $spleft = $('<div class="spleft"></div>')
                $specificDiv.append($spleft)
                $div = $('<div name="block'+i+'" style="margin-right: 3.5%;"></div>')
                $spleft.append($div)
            else if block.alignment == 'right'
                $specificDiv = $('div[name="block'+(i-1)+'"]', @_$selfDiv).parent().parent()
                divclass = 'spright'
                $div = $('<div name="block'+i+'" class="'+divclass+'"></div>')
                $specificDiv.append($div)
            else
                @_$selfDiv.append($('<div class="clears"></div>'))
                $div = $('<div name="block'+i+'" class="'+divclass+'"></div>')
                @_$selfDiv.append($div)
            if block.header?
               @_header(block.header, $div)

        $table = $('table', $div)
        if not $table[0]
            $table = $('<table class="display hover" rules="rows"></table>')
            $div.append($table)

        #First lets make columns
        aoColumns = []
        for column in block.columns
            stringReplacements = {
                $bin_section_name$: ''
                $read_type_name$: ''
                $read_type_short_name$: ''
                $read_type_units$: ''
            }
            if block.row_type == 'bin' and column.bin_section_id?
                bin_section = IsadoreData.binSectionsIdMap[column.bin_section_id]
                stringReplacements['$bin_section_name$'] = bin_section.name
            if column.read_type_id?
                read_type = IsadoreData.readTypesIdMap[column.read_type_id]
                stringReplacements.$read_type_name$ = read_type.name
                stringReplacements.$read_type_short_name$ = read_type.short_name
                stringReplacements.$read_type_units$ = read_type.units
            sTitle = @_replace(column.column_label, stringReplacements)
            aoColumns.push({sTitle: sTitle})
        aoColumns.push({sTitle: 'data-bin_id', bVisible: false})

        #Now data
        tableData = []
        if block.row_type == 'bin'
            for bin_id in block.bin_ids
                bin = _.find(IsadoreData.bins, {id: bin_id})
                if not bin
                    console.log('Could not find bin id: '+bin_id)
                row = @_updateTable2(block, bin, null)
                row.push(bin_id)
                tableData.push(row)
        else # 'section' row_type
            bin =_.find(IsadoreData.bins, {id: block.bin_id})
            for bin_section_id in block.bin_section_ids
                bin_section = IsadoreData.binSectionsIdMap[bin_section_id]
                row = @_updateTable2(block, bin, bin_section)
                row.push(bin.id)
                tableData.push(row)

        dt = $table.dataTable({
            bPaginate: false
            bRetrieve: true
            bFilter: false
            aoColumns: aoColumns
            fnRowCallback: (nRow, aData, ididx, ididxf) =>
                nRow.setAttribute('data-bin_id', aData[aData.length-1])
                rowClass = @_tableRowClass(aData[aData.length-1])
                if rowClass
                    $(nRow).addClass(rowClass)
                    $('td', $(nRow)).addClass(rowClass)
                return nRow
        })
        dt.fnClearTable()
        dt.fnAddData(tableData)
        elems = $('tbody tr', $table)
        elems.unbind('click', lightboxHandlers.binLightbox.binClick)
        elems.click(lightboxHandlers.binLightbox.binClick)
        fixHeights()

    _updateTable2: (block, bin, bin_section) ->
        rowData = []
        hourAgo = HTMLHelper.datetimeDelta({date: new Date(), hours: -1})

        for column in block.columns
            stringReplacements = {
                $bin_number$: ''
                $bin_name$: ''
                $bin_section_name$: ''
                $valueF1$: 'NA'
                $valueF2$: 'NA'
            }
            stringReplacements.$bin_name$ = bin.name
            binNameSegments = bin.name.split(' ')
            bin_section_id = null
            read_type_id = null
            if binNameSegments.length > 1
                stringReplacements.$bin_number$ = binNameSegments[1]
            if block.row_type == 'bin' and column.bin_section_id?
                bin_section = IsadoreData.binSectionsIdMap[column.bin_section_id]
                bin_section_id = bin_section.id
                stringReplacements['$bin_section_name$'] = bin_section.name
            else if block.row_type == 'section'
                bin_section_id = bin_section.id
                stringReplacements['$bin_section_name$'] = bin_section.name
            if column.read_type_id?
                read_type = IsadoreData.readTypesIdMap[column.read_type_id]
                read_type_id = read_type.id
            reading = _.find(IsadoreData.lastReadings, {bin_id: bin.id, bin_section_id: bin_section_id, read_type_id: read_type_id})
            if reading && reading.value && reading.datetime > hourAgo
                stringReplacements.$valueF1$ = reading.value.toFixed(1)
                stringReplacements.$valueF2$ = reading.value.toFixed(2)
            rowData.push(@_replace(column.value, stringReplacements))
        return rowData

    _updateDiagram: (i, block) ->
        $div = $('div[name="block'+i+'"]', @_$selfDiv)
        if not $div[0]
            $div = $('<div name="block'+i+'"></div>')
            @_$selfDiv.append($div)
            if block.header?
                @_header(block.header, $div)

        # reference: jQuery cookbook 5.1
        html = []
        html[html.length] = '<table class="layout_table" rules="rows" style="table-layout: fixed">'
        html[html.length] = '<tbody>'

        miny = 999999999
        if not IsadoreData.general.configs.hasOwnProperty('bin_layout_empties') or IsadoreData.general.configs.bin_layout_empties
            maxy = 0
            maxx = 0
            for bin in IsadoreData.bins
                if bin.y < 0 or not (block.yindexes == 'all' or bin.y in block.yindexes)
                    continue
                if bin.y < miny
                    miny = bin.y
                if bin.y > maxy
                    maxy = bin.y
                if bin.x > maxx
                    maxx = bin.x
            td=[]
            for x in [0..maxx]
                td[td.length] = '<td class="empty"></td>'
            td = td.join('')
            # Lets make grid first
            for y in [miny..maxy]
                if y % 2 == 0
                    html[html.length] = '<tr class="layout_top">'+td+'</tr>'
                    html[html.length] = '<tr class="layout_top_labels">'+td+'</tr>'
                else if y % 2 == 1
                    html[html.length] = '<tr class="layout_bottom_labels">'+td+'</tr>'
                    html[html.length] = '<tr class="layout_bottom">'+td+'</tr>'
        else
            sortedBins = _.sortBy(IsadoreData.bins, ['y', 'x'])
            y = -1
            tds = []
            miny = 0
            if block.yindexes != 'all'
                miny = _.min(block.yindexes)
            for bin in sortedBins
                if (block.yindexes == 'all' or bin.y in block.yindexes) and bin.y >= 0 and y != bin.y
                    tds.push([])
                    y = bin.y
                if bin.y >= 0 and bin.x >= 0
                    tds[tds.length-1].push('<td class="empty"></td>')
            for y in [0...tds.length]
                td = tds[y].join('')
                if y % 2 == 0
                    html.push('<tr class="layout_top">'+td+'</tr>')
                    html.push('<tr class="layout_top_labels">'+td+'</tr>')
                else if y % 2 == 1
                    html.push('<tr class="layout_bottom_labels">'+td+'</tr>')
                    html.push('<tr class="layout_bottom">'+td+'</tr>')


        html[html.length] = '</tbody>'
        html[html.length] = '</table>'

        table = $(html.join(''))
        # Then fill in the grid.
        for bin in IsadoreData.bins
            if (block.yindexes == 'all' or bin.y in block.yindexes) and bin.y >= 0
                name = bin.name
                if name == 'empty'
                    continue
                imgStr=''
                # TODO: Check for red status. If so add class="red" in td
                # top/bottom
                if name.indexOf('Fan') >= 0
                    imgStr = '<img src="imgs/icon_fan_gray.png" alt="Fan"/>'
                else if name.indexOf('Burner') >= 0
                    imgStr = '<img src="imgs/icon_burner_gray.png" alt="Fan"/>'
                else  # Normal bin
# Check air flow direction
                    if bin.readings
                        windDir = @_findWindDirection(bin.id, bin.readings)
                        if windDir > 0
                            imgStr = '<img src="imgs/icon_arrowUP_gray.png" alt="Bin Up" />'
                        else if windDir < 0
                            imgStr = '<img src="imgs/icon_arrowDOWN_gray.png" alt="Bin Down" />'
                $('tr:eq('+(bin.y*2 - miny)+') td:eq('+bin.x+')', table).removeClass('empty')
                $('tr:eq('+(bin.y*2 - miny)+') td:eq('+bin.x+')', table).attr('data-bin_id', bin.id)
                $('tr:eq('+(bin.y*2 - miny)+') td:eq('+bin.x+')', table).attr('colspan', bin.display_colspan)
                $('tr:eq('+(bin.y*2+1 - miny)+') td:eq('+bin.x+')', table).attr('data-bin_id', bin.id)
                $('tr:eq('+(bin.y*2+1 - miny)+') td:eq('+bin.x+')', table).attr('colspan', bin.display_colspan)
                $('tr:eq('+(bin.y*2+1 - miny)+') td:eq('+bin.x+')', table).removeClass('empty')
                if bin.y % 2 == 0
                    $('tr:eq('+(bin.y*2 - miny)+') td:eq('+bin.x+')', table).html(imgStr)
                    $('tr:eq('+(bin.y*2+1 - miny)+') td:eq('+bin.x+')', table).html(name)
                    $('tr:eq('+(bin.y*2+1 - miny)+') td:eq('+bin.x+')', table).attr('colspan', bin.display_colspan);
                else
                    $('tr:eq('+(bin.y*2 - miny)+') td:eq('+bin.x+')', table).html(name)
                    $('tr:eq('+(bin.y*2+1 - miny)+') td:eq('+bin.x+')', table).html(imgStr)
                    $('tr:eq('+(bin.y*2 - miny)+') td:eq('+bin.x+')', table).attr('colspan', bin.display_colspan);
        $div.empty()
        $div.append($('<div name="wind_instructions">Arrows indicate air direction</div>'))
        $div2 = $('<div class="layout"></div>')
        $div.append($div2)
        $div2.append(table)
        elems = $('.layout_table td[data-bin_id]', $div)
        elems.unbind('click', lightboxHandlers.binLightbox.binClick)
        elems.click(lightboxHandlers.binLightbox.binClick)
        tableSize = $('.layout_table', $div).width()
        #$('.layout_table td').width(tableSize/(maxx+1))

    _updateConfig: (i, block) ->
        $div = $('div[name="block'+i+'"]', @_$selfDiv)
        if not $div[0]
            $div = $('<div name="block'+i+'"></div>')
            $div.append($("""
                <h1>
                    <span>Sensor View Config</span>
                </h1>
                <input data-key="no_fill_no_arrow" type="checkbox"/> <label for="sensor_view_config_no_fill_no_arrows">Only display arrows when open fill.</label>
        """))

            @_$selfDiv.append($div)
            no_fill_no_arrows_checkbox = $('input', $div);
            if IsadoreData.general?.configs?.sensor_view?.no_fill_no_arrows? and IsadoreData.general.configs.sensor_view.no_fill_no_arrows
                no_fill_no_arrows_checkbox.prop('checked', true)
            else
                no_fill_no_arrows_checkbox.prop('checked', false)
            no_fill_no_arrows_checkbox.change(() =>
                if(no_fill_no_arrows_checkbox.attr('checked'))
                    val = true
                else
                    val = false
                IsadoreData.general?.configs?.sensor_view?.no_fill_no_arrows = val
                if not IsadoreData.selfAccount.configs?
                    IsadoreData.selfAccount.configs = {}
                if not IsadoreData.selfAccount.configs.sensor_view?
                    IsadoreData.selfAccount.configs.sensor_view = {}
                IsadoreData.selfAccount.configs.sensor_view.no_fill_no_arrows = val
                newConfigs = _.cloneDeep(IsadoreData.selfAccount.configs)
                $.ajax({
                    url: "../resources/accounts/#{IsadoreData.selfAccount.id}"
                    type: 'PUT'
                    dataType: 'text'
                    data: {configs: JSON.stringify(newConfigs)}
                })
                @refresh()
            )



    _update: () ->
        for i in [0...@_viewConfig.block.length]
            block = @_viewConfig.block[i]
            if block.type == 'table'
                @_updateTable(i, block)
            else if block.type == 'diagram'
                @_updateDiagram(i, block)
            else if block.type == 'config'
                @_updateConfig(i, block)
        @_$spinner.hide()

    refresh: () ->
        @_$spinner.show()
        #@_$table.hide()
        #@_update()
        DataManager.getFills({
            year: new Date().getFullYear(),
            callback: (d)=>
                @_fills = d.fills
                @_update()
        })



class window.CurrentDataHandler
    constructor: () ->
        $('#content_current_data').tabs({activate: () -> fixHeights()})

    _refresh: () ->
        if @fillSub?
            DataManager.dataUnSub(@fillSub)
            @fillSub = null
        @fillSub = DataManager.dataSub({
            key: "fill",
            type: ['edit', 'add', 'delete'],
            year: parseInt(new Date().getFullYear(), 10)
            callback: () =>
                @refresh()
        })
        $('.last_update_datetime').html(IsadoreData.lastReadingsTime)
        for otherView in @_otherViews
            otherView.refresh(@_fills)
        fixHeights()

    _populateOtherTabs: () ->
        if @_otherViews?
            return
        #Make other tabs and views
        if IsadoreData.general.configs?.other_views?
            @_otherViews = []
            for view in IsadoreData.general.configs.other_views
                viewTitle = view.title
                viewType = view.type
                viewUUID = uuid.v4()

                if viewType == "fill_view"

                    #Make tab and tab div
                    $viewDiv = $('<div id="' + viewUUID + '"></div>')
                    $viewUl = $('<li><a href="#' + viewUUID + '">'+viewTitle+'</a></li>')
                    $('#content_current_data').append($viewDiv)
                    $('#content_current_data ul').append($viewUl)

                    #Make object in tab
                    otherView = new CurrentDataFillViewHandler(viewTitle, $viewDiv, view.view)
                    @_otherViews.push(otherView)
                else if viewType == "diagnostics"
                    #Make tab and tab div
                    $viewDiv = $('<div id="' + viewUUID + '"></div>')
                    $viewUl = $('<li><a href="#' + viewUUID + '">'+viewTitle+'</a></li>')
                    $('#content_current_data').append($viewDiv)
                    $('#content_current_data ul').append($viewUl)

                    #Make object in tab
                    otherView = new DiagnosticsViewHandler(viewTitle, $viewDiv, view.view)
                    @_otherViews.push(otherView)
                else if viewType == 'sensor_view'
                    #Make tab and tab div
                    $viewDiv = $('<div id="' + viewUUID + '"></div>')
                    $viewUl = $('<li><a href="#' + viewUUID + '">'+viewTitle+'</a></li>')
                    $('#content_current_data').append($viewDiv)
                    $('#content_current_data ul').append($viewUl)

                    #Make object in tab
                    otherView = new SensorViewHandler(viewTitle, $viewDiv, view.view)
                    @_otherViews.push(otherView)
            $('#content_current_data').tabs('refresh')
            $('#content_current_data').tabs('select', 0)
        else
            $('#content_current_data').tabs('refresh')

    # Update the current data page if visible.
    refresh: () ->
        if not $('#content_current_data').is(':visible')
            return

        @_populateOtherTabs()
        checkClientVersion()
        console?.log?('Current Data refresh')
        $('#menu_current_data').removeClass('unselected')
        $('#menu_current_data').addClass('selected')

        DataManager.getFills({
            year: new Date().getFullYear(),
            callback: (d)=>
                @_fills = d.fills
                @_refresh()
        })
