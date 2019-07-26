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

class window.ImageAnimator
    constructor: ($parent, $images, plannedMaxFrames) ->
        @_SPEED=1500
        @_$parent = $parent
        @_$images = $images
        @_plannedMaxFrames = plannedMaxFrames
        @_$selfdiv = $('<div></div>')
        @_$parent.append(@_$selfdiv)
        #Add div to hold image
        @_$imagediv = $('<div style="text-align: center;"></div>')
        @_$selfdiv.append(@_$imagediv)
        #Add div to hold controls
        @_$controldiv = $('<div></div>')
        @_$selfdiv.append(@_$controldiv)
        @_makeControls()
        #@play()
        @_update()

    _makeControls: () ->
        # In controls is slider
        # In controls is pause/play button
        # In controls is speed control
        @_$slider = $('<div></div>')
        @_$playpauseButtonDiv = $('<div style="text-align:center"></div>')
        @_$selfdiv.append(@_$slider)
        @_$selfdiv.append(@_$playpauseButtonDiv)
        @_$playpauseButton = $('<button>&gt;</button>')
        @_$playpauseButtonDiv.append(@_$playpauseButton)
        @_$progressDiv = $('<div style="text-align:center"></div>')
        @_$selfdiv.append(@_$progressDiv)
        @_$slider.slider({
            orientation: 'horizontal',
            max: 0,
            min: 0,
            step: 1,
            change: (event, ui) =>
                @_update(ui.value)
            slide: (event, ui) =>
                @_update(ui.value)
        })
        @_$playpauseButton.click(() =>
            if @isPlaying()
                @pause()
            else
                @play()
        )

    _update: (v) ->
        if not v
            v = @_$slider.slider('value')
        @_$imagediv.empty().append(@_$images[v])

    addFrame: ($image, prepend) ->
        v = @_$slider.slider('value')
        if not prepend
            @_$images.push($image)
        else
            @_$images.unshift($image)
            v = v + 1
        #console.log('Slider length: ' + @_$images.length)
        @_$slider.slider("option", "max", @_$images.length-1)
        @_$slider.slider('value', v % @_$images.length)
        if @_$images.length != @_plannedMaxFrames
            @_$progressDiv.text('Loading Frames: ' + ((@_$images.length/@_plannedMaxFrames)*100).toFixed(0) + '%')
        else
            @_$progressDiv.empty()

    play: () ->
        if @isPlaying()
            return
        @_playInterval = setInterval(
            () =>
                if @_$selfdiv.is(":visible")
                    v = @_$slider.slider('value')
                    @_$slider.slider('value', (v+1) % @_$images.length)
            @_SPEED
        )
        @_$playpauseButton.html('||')

    pause: () ->
        if @_playInterval
            clearInterval(@_playInterval)
            @_playInterval = null
            @_$playpauseButton.html('&gt;')

    isPlaying: () ->
        if @_playInterval
            return true
        return false

    delete: () ->
        # Stop interval
        @pause()
        # remove elements from parent
        @_$selfdiv.remove()

