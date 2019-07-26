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


testFrames = [
    {
        label: "test1",
        framedata: {
            min: 80.0,
            max: 110.0,
            data: [
                {x: 0, y: 50, value: 81.0},
                {x: 100, y: 50, value: 95.0},
                {x: 200, y: 50, value: 98.0},
                {x: 300, y: 50, value: 81.0}
            ]
        }
    },
    {
        label: "test2",
        framedata: {
            min: 80.0,
            max: 110.0,
            data: [
                {x: 0, y: 50, value: 105.0},
                {x: 100, y: 50, value: 98.0},
                {x: 200, y: 300, value: 81.0},
                {x: 300, y: 50, value: 90.0}
            ]
        }
    }
]

class window.HeatmapGraph
    constructor: ($parent, query, ourvars, otherOpts) ->
        @_$parent = $parent
        @_$selfdiv = $("""<div>
<div class="heatmap" style="width: 800px; height: 400px;"></div>
<div>Legend Title</div>
<span class="heatmap_legend_min"></span>
<span class="heatmap_legend_max"></span>
<img class="heatmap_legend_gradient" style="width: 100%"/>
<div class="heatmap_legend_value"></div>
</div>""")
        @_$parent.append(@_$selfdiv)
        @_heatmap = h337.create(
            {
                container: $('.heatmap', @_$selfdiv)[0],
                radius: 100,
                onExtremaChange: (data) =>
                    @_updateLegend(data)
            }
        )
        $('.heatmap', @_$selfdiv).mousemove((ev ) =>
            offset = $('.heatmap', @_$selfdiv).offset()
            x = ev.pageX - offset.left
            y = ev.pageY - offset.top
            v = @_heatmap.getValueAt({x: x, y: y})
            @_legend.$value.text('V: '+v)
        )
        @_legend = {
            legend: $('<canvas></canvas>')[0],
            $value: $('.heatmap_legend_value', @_$selfdiv)
        }
        @_legend.legendCtx = @_legend.legend.getContext('2d')
        @_legend.gradientCfg = null
        @_legend.gradientImg = $('.heatmap_legend_gradient', @_$selfdiv)[0]

        @_legend.legend.width=100
        @_legend.legend.height=10

        # @_heatmap.configure()

        @_frames = testFrames
        @_currentFrame = -1
        # frame = {label: string, data: data}

        # data = { min = number, max = number, data = [{xnumber, ynumber, valuenumber}, ...] }

    _updateLegend: (data) ->
        $('.heatmap_legend_min', @_$selfdiv).text(data.min)
        $('.heatmap_legend_max', @_$selfdiv).text(data.max)
        if data.gradient != @_legend.gradientCfg
            @_legend.gradientCfg = data.gradient
            gradient = @_legend.legendCtx.createLinearGradient(0, 0, 100, 1)
            console.log(@_legend.gradientCfg)
            for key, value of @_legend.gradientCfg
                console.log(key, @_legend.gradientCfg[key])
                gradient.addColorStop(key, value)

            @_legend.legendCtx.fillStyle = gradient
            @_legend.legendCtx.fillRect(0, 0, 100, 10)
            console.log('setting gradientimg')
            @_legend.gradientImg.src = @_legend.legend.toDataURL()

    addFrame: (frame) ->
        # Frames probably part of constructor
        @_frames.push(frame)

    run: () ->
        setInterval(
            () =>
                @_currentFrame = (@_currentFrame+1) % @_frames.length
                @_heatmap.setData(@_frames[@_currentFrame].framedata)
                #@_heatmap.repaint()
            3000
        )



