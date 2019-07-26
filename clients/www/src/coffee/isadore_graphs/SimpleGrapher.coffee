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

class window.SimpleGrapher
    constructor: ($parent, bin, queries, options, timeRange, title) ->
        @_$parent = $parent
        @_bin = bin
        @_queries = queries
        @_options = options
        @_lastTime = null
        @_title = title

        @_$selfdiv = $('<div></div>')
        @_$parent.append(@_$selfdiv)
        @_graphDivs = []
        @_graphs = []
        @_$graphWrapper = $('<div style="background-color: white;"></div>')
        @_$selfdiv.append(@_$graphWrapper)
        for query in queries
            div = $('<div></div>')
            @_$graphWrapper.append(div)
            @_graphDivs.push(div)
        #TODO: Make this a save icon
        @_$saveLink = $('<button>Download Graph</button>')
        @_$selfdiv.append(@_$saveLink)
        @_$saveLink.click((e) =>
            @_saveGraphBrowser(e)
        )
        @_timeChange(timeRange[0], timeRange[1])

    _saveGraphBrowser: (e) ->
        console.log('Making canvas.')
        #window.bob = @_$graphWrapper
        html2canvas(@_$graphWrapper[0], {
            onrendered: (canvas) =>
                console.log('CanvasRendered.')
                data = canvas.toDataURL("image/png");
                data = data.replace(/^data[:]image\/(png|jpg|jpeg)[;]/i, "data:application/octet-stream;");
                #location.href=data
                if @_$lastsa
                    @_$lastsa.remove()
                    @_$lastsa = null
                $sa = $('<a></a>')
                $sa[0].href = data
                $sa[0].target = '_blank'
                #TODO: Make this the title or something.
                $sa[0].download = 'IsadoreGraphTS_'+@_title+'_'+new Date().getTime()+'.png'
                $sa.text('Save PNG')
                @_$selfdiv.append($sa)
                $sa.hide()
                if $sa[0].click
                    $sa[0].click()
                else
                    event = document.createEvent('MouseEvent')
                    event.initMouseEvent("click", true, true, window,
                        0, 0, 0, 0, 0, false, false, false, false, 0, null);
                    $sa[0].dispatchEvent(event)
                @_$lastsa = $sa
        })
        #e.preventDefault()

    _saveGraphServer: () ->
        html2canvas(@_$graphWrapper[0], {
            onRendered: (canvas) =>
                    data = canvas.toDataURL("image/png");
                    $.ajax() #Save data
                    #Get back a UUID
                    #Use UUID to get image from server in new window.
        })

    _timeChange: (t1, t2) ->
        if !@_lastTime || @_lastTime[0] != t1 || @_lastTime[1] != t2
            @_lastTime = [t1, t2]
            for graph in @_graphs
                graph.delete()
            @_graphs = []
            vars = {'$bin_name$': @_bin.name, "$begin_datetime$": HTMLHelper.dateToParamString(t1), "$end_datetime$": HTMLHelper.dateToParamString(t2)}
            for graph in @_graphs
                graph.delete()
            for i in [0...@_queries.length]
                query = @_queries[i]
                gdiv = @_graphDivs[i]
                #TODO: Other options, height and width
                width = @_$selfdiv.innerWidth()
                if @_options?.total_width?
                    width = @_options.total_width
                th = @_$selfdiv.innerHeight()
                if @_options?.total_height?
                    th = @_options.total_height
                height = Math.floor(th/@_queries.length)
                if @_options?.heights? and @_options.heights.length == @_queries.length
                    height = Math.floor(th*@_options.heights[i])
                graph = new TimeGraph(gdiv, query, vars, {width: width, height: height, highlights: @_options.highlights})
                @_graphs.push(graph)
            for g in @_graphs
                for g2 in @_graphs
                    if g != g2
                        g.linkGraph(g2)

    delete: () ->
        for graph in @_graphs
            graph.delete()
        @_queries = null
        @_$parent = null
        @_$selfdiv.remove()
