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

#begin_datetime=2013-09-11T19:31:00.000Z
#end_datetime=2013-09-14T12:30:00.000Z
#Test Queries
###

query =
{
    time: {begin_datetime: '2013-09-11T19:31:00.000Z', end_datetime: '2013-09-14T12:30:00.000Z', sample_period: 5},
    labels: {title: 'Test graph', y0label: 'y 0 label', y1label: 'y 1 label'},
    data: [
        {
            value: 'Bin 1.Top.Temp',
            display: {
                label: 'T',
                color: '#FFFF00',
                pattern: null,
                axis: 0
            }
        },
        {
            value: 'Bin 1.Bottom.Temp',
            display: {
                label: 'B',
                color: '#FF0000',
                pattern: [2,2],
                axis: 1
            }
        }

    ]
};
query2 =
{
    time: {begin_datetime: '2013-09-11T19:31:00.000Z', end_datetime: '2013-09-14T12:30:00.000Z', sample_period: 5},
    labels: {y0label: 'y 0 label', y1label: 'y 1 label'},
    data: [
        {
            value: 'Bin 1.Top.Temp',
            display: {
                label: 'T',
                color: '#000000',
                pattern: null,
                axis: 0
            }
        }
    ]
}
$('body').empty(); a = new TimeGraph($('body'), query, {}, {width: '600px', height: '400px', showRangeSelector: false});
b = new TimeGraph($('body'), query2, {}, {width: '600px', height: '200px', showRangeSelector: false});
a.linkGraph(b);
b.linkGraph(a);

###

#QUERY SYNTAX
#{
#    time: {begin_datetime: 'ISO8601'|Date(), end_datetime: 'ISO8601'|Date(), sample_period: int_valid_sample_period_minutes, time_display: null_or_'timestamp'_or_'hours'},
#    labels: {title: 'title', xlabel: null, y0label: 'F (&deg;F)', y1label: '%'},
#    initial_options: {y0range: [60, 130], y1range: [30, 100], minmax: true|false},
#    data: [
#        {value: 'Bin Name.Bin Section Name.Short Name Sensor Type', vname: 'bin1_top_temp', display: {label: 'Top Temp (&deg; F)', color: '#FF0000', pattern: [2, 2], axis: 0}}, ...
#    ],
#    calc: [
#        {value: 'js_code', SAME_AS_data, options: {all_rows: true}}
#    ]
#}
# Instead of 'Bin Section', can use 'inlet|outlet|maxtemp'

#Query to Request logic

#in data sort by bin name in data
#group by bin name
#For each group
#  get bin_id from Bin Name
#  get bin_section_id from 'Bin Section Name' or leaves as inlet|outlet|maxtemp
#  Make REST Query for data
#  {bin_id: bin_id, query: [ [TYPE_STR, [OPTS]], ...], sample_period: int, begin_datetime: 'ISO8601', end_datetime: 'ISO8601'}
#
#Process calc, if variable is needed process data
#Merge data info dygraph form keeping track of indexes
#Use indexes to make dygraph options

#otherOptions
# width: '600px'
# height: '400px'
# showRangeSelector: true,
class window.TimeGraph
    @RIGHT_GAP: 60
    constructor: ($parent, query, ourvars, otherOpts) ->
        @_$parent = $parent
        @_$selfdiv = $('<div><img src="./imgs/ajax-loader-big.gif" alt="loading spinner"/></div>')
        @_$parent.append(@_$selfdiv)
        @_query = _.cloneDeep(query)
        @_ourvars = ourvars
        @_dygraph = null
        @_dygraphOptions = null
        @_dygraphData = null
        @_otherOpts = otherOpts
        @_linkedGraphs = []

        if @_otherOpts?.height?
            @_$selfdiv.css('height', @_otherOpts.height)
        if @_otherOpts?.width?
            @_$selfdiv.css('width', @_otherOpts.width)


        @_timeVariableReplace()
        @_generate()


    _timeVariableReplace: () ->
        #Replace variables in datetime
        if _.isString(@_query.time.begin_datetime) && @_ourvars.hasOwnProperty(@_query.time.begin_datetime)
            @_query.time.begin_datetime = @_ourvars[@_query.time.begin_datetime]

        if _.isString(@_query.time.end_datetime) && @_ourvars.hasOwnProperty(@_query.time.end_datetime)
            @_query.time.end_datetime = @_ourvars[@_query.time.end_datetime]

        if @_query.time.begin_datetime instanceof Date
            @_query.time.begin_datetime = HTMLHelper.dateToParamString(@_query.time.begin_datetime)
        if @_query.time.end_datetime instanceof Date
            @_query.time.end_datetime = HTMLHelper.dateToParamString(@_query.time.end_datetime)

    _groupVariableReplaceBins: () ->
        #Group by Bin Name
        binGroups = {}
        for d in @_query.data
            vsplit = d.value.split('.')
            binName = vsplit[0]
            if @_ourvars.hasOwnProperty(binName)
                binName = @_ourvars[binName]
            if binGroups.hasOwnProperty(binName)
                binGroups[binName].push(d)
            else
                binGroups[binName] = []
                binGroups[binName].push(d)
        return binGroups

    _restQueries: (binGroups) ->
        allRestQueries = []
        for binName, groupArray of binGroups
            bin = _.find(IsadoreData.bins, (b) ->
                return b.name == binName
            )
            if bin
                binId = bin.id
                restQuery = {bin_id: binId, sample_period: @_query.time.sample_period, begin_datetime: @_query.time.begin_datetime, end_datetime: @_query.time.end_datetime, query: []}
                restQueryIdxMap = []
                for d in groupArray
                    vsplit = d.value.split('.')
                    binSectionName = vsplit[1]
                    if binSectionName == 'maxtemp'
                        restQuery.query.push(['maxtemp', []])
                        restQueryIdxMap.push(d)
                    else
                        readTypeName = vsplit[2]
                        readTypeId = null
                        readType = _.findWhere(IsadoreData.readTypes, {'short_name': readTypeName})
                        if readType
                            readTypeId = readType.id
                            if binSectionName == 'inlet' || binSectionName == 'outlet'
                                restQuery.query.push([binSectionName, [readTypeId]])
                                restQueryIdxMap.push(d)
                            else
                                binSection = _.find(IsadoreData.binSections, (b) ->
                                    return b.name == binSectionName
                                )
                                if binSection
                                    binSectionId = binSection.id
                                    restQuery.query.push(['sensor', [binSectionId, readTypeId]])
                                    restQueryIdxMap.push(d)
                if restQuery.query.length > 0
                    restQuery.query = JSON.stringify(restQuery.query)
                    allRestQueries.push([restQueryIdxMap, restQuery])
        return allRestQueries

    _generate: () ->
        #TODO: Add Spinner
        binGroups = @_groupVariableReplaceBins()
        allRestQueries = @_restQueries(binGroups)

        #Fetch data
        queryFuncGen = (ourMap, ourQuery) ->
            return (callback) ->
                $.ajax({
                    url: '../resources/data/graph/data'
                    type: 'GET'
                    dataType: 'json'
                    data: ourQuery
                    success: (d) =>
                        callback(null, [ourMap, d])
                    error: (jqXHR, textStatus) =>
                        console?.error('Error getting graph data: '+textStatus)
                        callback(textStatus, [ourMap, null])
                })

        #Get data
        tasks=[]
        for rquery in allRestQueries
            tasks.push(queryFuncGen(rquery[0], rquery[1]))
        console.log(tasks)
        async.parallel(
            tasks,
            (err, results) =>
                @_generate2(err, results)
        )

    _highlights: (canvas, area, g) ->
        if @_otherOpts.highlights?
            for hl in @_otherOpts.highlights
                start = hl.start
                end = hl.end
                if _.isString(start)
                    start = new Date(hl.start)
                if _.isString(end)
                    end = new Date(end)
                if @_query.time.time_display == 'hours'
                    start = (start.getTime() - @_firstDate) / (3600000.0)
                    end = (end.getTime() - @_firstDate) / (3600000.0)

                bl = g.toDomCoords(start, -20)
                tr = g.toDomCoords(end, 20)
                canvas.fillStyle = hl.color
                canvas.fillRect(bl[0], area.y, tr[0] - bl[0], area.h)


    _generate2: (err, results) ->
        #Go through results
        console.log("_generate2")
        console.log(err)
        console.log(results)
        data=[]
        dataVars = {}
        dataMap = []

        #If any errors set to display
        @_dataErrors = []
        if err
            if err instanceof Array
                for er in err
                    if er
                        @_dataErrors.push(er)
            else
                @_dataErrors.push(err)

        if @_dataErrors.length > 0
            @_$selfdiv.html(@_dataErrors.join('</br>'))
            return

        for r in results
            if not r[1] or r[1].length == 0
                continue
            #zip
            zr = _.zip(r[1])
            #merge
            if data.length == 0
                data.push(zr[0])
            if data[0].length != zr[0].length
                console?.warn('Different lengths')
            if zr.length-1 != r[0].length
                console?.warn('Map and data lengths differ')
            for i in [1...zr.length]
                data.push(zr[i])
                #Set new index data map
                dataMap.push(r[0][i-1])
                #Set variable map
                if r[0][i-1].vname?
                    dataVars[r[0][i-1].vname] = zr[i]

        #Go through calc in query
        if @_query.calc?
            for c in @_query.calc
                try
                    #process calc using math.eval  http://mathjs.org
                    res = math.eval(c.value, dataVars)
                    data.push(res)
                    dataMap.push(c)
                    if c.vname?
                        dataVars[c.vname] = res
                catch er
                    console?.error(er)
                    @_dataErrors.push(er)

        if @_dataErrors.length > 0
            @_$selfdiv.html(@_dataErrors.join('</br>'))
            return

        if data.length == 0
            @_$selfdiv.html('No results found.')
            return

        #Make dygraph options using index map
        dygraphOptions = {
            legend: 'always'
            labels: ['Time']
            series: {}
            yAxisLabelWidth: 70
            customBars: true
            labelsSeparateLines: true,
            underlayCallback: (canvas, area, g) =>
                @_highlights(canvas, area, g)
            zoomCallback: (minX, maxX, yRanges) =>
                @_zoomCB(minX, maxX, yRanges)
        }

        if @_otherOpts?.showRangeSelector?
            dygraphOptions.showRangeSelector = @_otherOpts.showRangeSelector
        if @_query.labels?.title?
            title = @_query.labels.title
            if @_ourvars.hasOwnProperty(title)
                title = @_ourvars[title]
            dygraphOptions.title = title
        if @_query.labels?.y0label?
            dygraphOptions.ylabel = @_query.labels?.y0label
        if @_query.labels?.y1label?
            dygraphOptions.y2label = @_query.labels?.y1label
        if @_query.initial_options?.y0range?
            dygraphOptions.axes = {y: @_query.initial_options.y0range}
        if @_query.initial_options?.y1range?
            if not dygraphOptions.axes?
                dygraphOptions.axes = {}
            dygraphOptions.axes.y2 = @_query.initial_options.y1range

        if @_query.time.time_display? and  @_query.time.time_display == 'hours'
            if not dygraphOptions.axes?
                dygraphOptions.axes = {}
            if not dygraphOptions.axes.x
                dygraphOptions.axes.x = {}
            dygraphOptions.axes.x.valueFormatter = (hrs) ->
                hours = Math.floor(hrs)
                mins = Math.floor((hrs - hours)*60.0)
                seconds = Math.floor(((hrs - hours)*60.0 - mins)*60)
                return "#{hours}h#{mins}m#{seconds}s"



        hasY2 = false
        dygraphOptions.series = {}
        for i in [0...dataMap.length]
            m = dataMap[i]
            if m.display?
                if m.display.label?
                    label = m.display.label
                    dygraphOptions.labels.push(label)
                else
                    label = uuid.v4()
                    dygraphOptions.labels.push(label)

                dygraphOptions.series[label] = {}
                if m.display.axis? and m.display.axis == 1
                    dygraphOptions.series[label].axis = 'y2'
                    hasY2 = true
                if m.display.color?
                    dygraphOptions.series[label].color = m.display.color
                if m.display.pattern?
                    dygraphOptions.series[label].strokePattern = m.display.pattern
            else
                # Was just used as a variable
                data.splice(i, 1)

        if !hasY2
            dygraphOptions.rightGap = TimeGraph.RIGHT_GAP
        #unzip
        #First column needs to be date objects
        for i in [0...data[0].length]
            data[0][i] = new Date(data[0][i])
            if @_query.time.time_display? and  @_query.time.time_display == 'hours'
                if ! @_firstDate
                    @_firstDate = new Date(data[0][i]).getTime()
                data[0][i] = (new Date(data[0][i]).getTime() - @_firstDate) / (3600000.0)

        dygraphData = _.unzip(data)
        #Make dygraph

#        dygraphOptions = {
#            legend: 'follow',
#            animatedZooms: true,
#            title: 'dygraphs chart template',
#            customBars: true,
#            labels: ['Xdog', 'Y', 'Z'],
#            series: {
#                'Z': { color: 'green'},
#                'Y': {
#                    strokePattern: [5,5],
#                    color: '#FF0000'
#                }
#            }
#        }
        @_dygraphOptions = dygraphOptions

        console.log('Data length = '+dygraphData.length)


#        dygraphData = [
#            [1,[0, 0, 0],[1, 2, 3]],
#            [2,[2, 2, 2],[6, 6, 6]],
#            [3,[4, 4, 4],[8, 8, 8]],
#            [4,[6, 6, 6],[9, 9, 9]],
#            [5,[8, 8, 8],[9, 9, 9]],
#            [6,[10, 10, 10],[8, 8, 8]],
#            [7,[12, 12, 12],[6, 6, 6]],
#            [8,[14, 14, 14],[3, 3, 3]]]



        @_dygraphData = dygraphData
        checkData = false
        #Lets check the data
        if checkData
            if not @_debugData(dygraphData)
                console.error('Aborting bad data.')


        @_$selfdiv.empty()
        @_dygraph = new Dygraph(@_$selfdiv[0], dygraphData, dygraphOptions)

    _debugData: (dygraphData) ->
        oursize = 0
        for i in [0...dygraphData.length]
            if i == 0
                oursize = dygraphData[i].length
            if dygraphData[i].length != oursize
                console.error('Column wrong size, '+oursize+" != "+dygraphData[i].length);
                return false
            for j in [0...dygraphData[i].length]
                if j == 0
                    if not dygraphData[i][j] instanceof Date
                        console.error('First column is not date '+i+" "+j)
                        return false
                else
                    if not _.isArray(dygraphData[i][j])
                        console.error('column is not array '+i+" "+j)
                        return false
                    if dygraphData[i][j].length != 3
                        console.error('in column not size 3: '+i+" "+j)
                        return false
                    for k in [0...3]
                        if not _.isNumber(dygraphData[i][j][k])
                            console.error('in column not number'+i+" "+j+' '+k)
                            return false
        return true


    _zoomCB: (minX, maxX, yRanges) ->
        console.log(minX)
        console.log(maxX)
        console.log(yRanges)
        for g in @_linkedGraphs
            g.update({dateWindow: [minX, maxX]})

    delete: () ->
        if @_dygraph
            @_dygraph.destroy()
            @_dygraph = null
        @_$selfdiv.remove()

    update: (opts) ->
        if @_dygraph
            @_dygraph.updateOptions(opts)

    linkGraph: (graph) ->
        if graph
            @_linkedGraphs.push(graph)

    unlinkGraph: (graph) ->
        idx = _.indexOf(@_linkedGraphs, graph)
        if idx > -1
            @_linkedGraphs.splice(idx, 1)
