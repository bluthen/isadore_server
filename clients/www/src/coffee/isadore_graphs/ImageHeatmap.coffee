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

class window.ImageHeatmap
    @MAX_FRAMES = 15
    constructor: ($parent, binId, binSectionIds, readTypeId, samplePeriod, options, timeRange) ->
        @_$parent = $parent
        @_binId = binId
        @_binSectionsIds = binSectionIds
        @_options = options
        @_stop = null
        @_tempRangeTimeout = null
        @_results = null

        @_binInfo = _.findWhere(IsadoreData.bins, {id: @_binId}).extra_info
        if @_binInfo
            @_binInfo = JSON.parse(@_binInfo)
        @_binSectionInfos = []
        for binSectionId in @_binSectionsIds
            bsX = IsadoreData.binSectionsIdMap[binSectionId].extra_info
            if bsX
                bsX = JSON.parse(bsX)
            @_binSectionInfos.push(bsX)

        @_samplePeriod = samplePeriod
        @_readTypeId = readTypeId
        @_$selfdiv = $('<div></div>')
        @_$animationdiv = $('<div></div>')
        @_$temprdiv = @_setupTempRange()
        @_$selfdiv.append(@_$animationdiv)
        @_$selfdiv.append(@_$temprdiv)
        @_$parent.append(@_$selfdiv)
        @_imageAnimator = null

        @_timeChange(timeRange[0], timeRange[1])

    _setupTempRange: () ->
        $tr = $('<div style="text-align: center"></div>')
        $lowerBound = $('<input style="width: 5ex"></input>').numeric({decimal: true, negative: false})
        $upperBound = $('<input style="width: 5ex"></input>').numeric({decimal: true, negative: false})
        $tr.append('<span>Temperature Range: </span>')
        $tr.append($lowerBound)
        $tr.append($upperBound)
        $('input', $tr).on('input', () =>
            if @_tempRangeTimeout
                clearTimeout(@_tempRangeTimeout)
            @_tempRangeTimeout = setTimeout(
                () =>
                    if @_results
                        tr = [parseInt($($('input', $tr)[0]).val(), 10), parseInt($($('input', $tr)[1]).val(), 10)]
                        if @_stop
                            @_stop()
                            @_stop=null
                        @_generate(null, @_results, tr)
                1500)
        )
        return $tr


    _timeChange: (t1, t2) ->
        if not @_binInfo.shape?
            return
        if @_stop
            @_stop()
            @_stop=null
        @_$animationdiv.append('<div><img src="./imgs/ajax-loader-big.gif" alt="loading spinner"/><br/><span></span></div>')
        restQuery = {
            bin_id: @_binId,
            sample_period: @_samplePeriod,
            begin_datetime: HTMLHelper.dateToParamString(t1),
            end_datetime: HTMLHelper.dateToParamString(t2),
            query: []}
        for binSectionId in @_binSectionsIds
            restQuery.query.push(['sensor', [binSectionId, @_readTypeId]])
        restQuery.query = JSON.stringify(restQuery.query)
        $.ajax({
            url: '../resources/data/graph/data'
            type: 'GET'
            dataType: 'json'
            data: restQuery
            success: (d) =>
                @_results = d
                @_generate(null, d, @_lastTempRange)
            error: (jqXHR, textStatus) =>
                console?.error('Error getting heatmap graph data: '+textStatus)
                @_generate(textStatus, null, @_lastTempRange)
        })

    _generate: (err, results, tempRange) ->
        self = this
        if @_imageAnimator
            @_imageAnimator.delete()
        if results
            x = Math.ceil(results.length/ImageHeatmap.MAX_FRAMES)
            # Should we check for extra info before query? YES TODO
            loadCount = 0
            totalCount = 1
            stopFetch = false
            @_stop = () ->
                stopFetch=true
            genImg = (heatmapArgs) ->
                f = (callback) ->
                    if not self._$selfdiv.is(":visible") or stopFetch
                        return
                    url = '../resources/data/heatmap?'+HTMLHelper.makeParameters(heatmapArgs)
                    #console.log(url)
                    $('<image src="'+url+'"/>').load(() ->
                        loadCount = loadCount + 1
                        callback(null, $(this))
                    ).error(() ->
                        loadCount = loadCount + 1
                        callback('Failed to load image', null)
                    ).attr('src', url)
                return f

            imgFuncs = []
            resultsIdx = []
            for i in [0...results.length] by x
                resultsIdx.push(i)
            if resultsIdx[resultsIdx.length-1] != (results.length-1)
                resultsIdx.push(results.length-1)

            totalCount = resultsIdx.length

            hmax = -9999999
            hmin = 9999999
            hargs = []
            for i in resultsIdx
                result = results[i]
                heatmapArgs = {
                    bin_desc: {shape: @_binInfo.shape},
                    values: {values: []},
                    options: {graph_dims: @_options.graph_dims},
                    bin_per_ft: 5
                    title: HTMLHelper.dateToReadableO2(new Date(result[0]))
                    ts: new Date().getTime()
                }
                if heatmapArgs.bin_desc.shape == 'circle'
                    heatmapArgs.bin_desc.radius = @_binInfo.radius
                else
                    heatmapArgs.bin_desc.xlen = @_binInfo.xlen
                    heatmapArgs.bin_desc.ylen = @_binInfo.ylen
                for j in [0...@_binSectionsIds.length]
                    if result[j+1][1]
                        heatmapArgs.values.values.push({pos: @_binSectionInfos[j].pos, eng: result[j+1][1]})
                        console.log(result[j+1][1], hmax)
                        if result[j+1][1] > hmax
                            hmax = result[j+1][1]
                        if result[j+1][1] < hmin
                            hmin = result[j+1][1]

                hargs.push(heatmapArgs)

            for heatmapArgs in hargs
                if tempRange
                    heatmapArgs.options.temp_range=[tempRange[0], tempRange[1]]
                    @_lastTempRange = tempRange
                else
                    heatmapArgs.options.temp_range=[hmin, hmax]
                    @_lastTempRange = [hmin, hmax]
                    $($('input', @_$temprdiv)[0]).val(hmin)
                    $($('input', @_$temprdiv)[1]).val(hmax)
                #JSON THEM
                #console.log(heatmapArgs)
                heatmapArgs.bin_desc = JSON.stringify(heatmapArgs.bin_desc)
                heatmapArgs.values = JSON.stringify(heatmapArgs.values)
                heatmapArgs.options = JSON.stringify(heatmapArgs.options)
                #TOOD: Get image
                imgFuncs.push(genImg(heatmapArgs))

            #Do the last one first:
            first = imgFuncs.pop()
            if first
                first((err, $image) =>
                    @_$animationdiv.empty()
                    @_imageAnimator = new ImageAnimator(@_$animationdiv, [$image], imgFuncs.length+1)

                    ifnr = (err, $image) =>
                        @_imageAnimator.addFrame($image, true)
                        ifn = imgFuncs.pop()
                        if ifn
                            ifn(ifnr)

                    ifn = imgFuncs.pop()
                    if ifn
                        ifn(ifnr)
                )


    delete: () ->
        @_$parent = null
        if @_imageAnimator
            @_imageAnimator.delete()
        @_$selfdiv.remove()
