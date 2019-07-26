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


###
dygraph with slider controls for zoom and position.
###
class window.IsadoreControlGraph
	@SIDE_LEFT: 0
	@SIDE_RIGHT: 1
	@TYPE_POSITION: 0
	@TYPE_MAG: 1
	@CTL_LEFT_POS: 0
	@CTL_LEFT_MAG: 1
	@CTL_RIGHT_MAG: 2
	@CTL_RIGHT_POS: 3
	
	constructor: (element, data, options) ->
		self=this
		icg=IsadoreControlGraph
		@parent = $(element)
		@icgWrapper=$('<div class="icg_wrapper"></div>')
		@controlWrappers=[
			$('<div class="icg_slider_wrapper"></div>')
			$('<div class="icg_slider_wrapper"></div>')
			$('<div class="icg_slider_wrapper"></div>')
			$('<div class="icg_slider_wrapper"></div>')
		]
		@controls=[
			$('<div class="icg_slider"></div>') #Left Position
			$('<div class="icg_slider"></div>') #Left Mag
			$('<div class="icg_slider"></div>') #Right Mag
			$('<div class="icg_slider"></div>') #Right Position
		]
		
		for i in [0...@controlWrappers.length]
			if(i==icg.CTL_RIGHT_MAG)
				#Insert graph between controls
				@graphDiv=$('<div class="icg_graph"></div>')
				@icgWrapper.append(@graphDiv)
			@controlWrappers[i].append(@controls[i])
			@icgWrapper.append(@controlWrappers[i])
		
		@parent.append(@icgWrapper)
		@ranges=[null,null]
		
		@plot = new Dygraph(
			@graphDiv[0]
			data
			options
		)
		
		sliderOptions={
			orientation: 'vertical'
			value: 50
			slide: (event, ui) ->
				self.scrollSlides_(event, ui)
			change: (event, ui) ->
				self.scrollStop_(event, ui)
		}
		
		for control in @controls
			control.slider(sliderOptions)
		@relayout()
		
	###
	  @side Y-axis side
	  @slider the jquery slider object.
	  @param sliderType
	###
	scrollSlidesSide_: (side, slider, sliderType) ->
		icg=IsadoreControlGraph
		if(slider.slider('option', 'value') != 50)
			if(not @ranges[side])
				@ranges[side]=@plot.yAxisRange(side)
			value = (slider.slider('option', 'value')-50)/50
			center = @ranges[side][0] + (@ranges[side][1] - @ranges[side][0])/2
			if(sliderType == icg.TYPE_POSITION)
				range = (@ranges[side][1] - @ranges[side][0])/2
				center = center+range*value
				newRange=[center-range, center+range]
			else
				if(value > icg.TYPE_MAG)
					range = (@ranges[side][1] - @ranges[side][0])/(2+2*value)
					newRange=[center - range, center + range]
				else
					value=-value
					range = ((@ranges[side][1] - @ranges[side][0])/2)*(1+value)
					newRange=[center - range, center + range]
			if(newRange[0] != @ranges[side][0] or newRange[1] != @ranges[side][1])
				ax = {axes: {} }
				ax.axes['y'+(if side then '2' else '')]={valueRange: newRange}
				#ax.axes['y'+(if side then '' else '2')]={valueRange: @plot.yAxisRange(Math.abs(side-1))}
				console.log(ax)
				@plot.updateOptions(ax)

	scrollSlides_: (event, ui) ->
		icg=IsadoreControlGraph
		if(event.target == @controls[icg.CTL_LEFT_POS][0] or event.target == @controls[icg.CTL_LEFT_MAG][0])
			side=icg.SIDE_LEFT
		else
			side=icg.SIDE_RIGHT
		if(event.target == @controls[icg.CTL_LEFT_POS][0] or event.target == @controls[icg.CTL_RIGHT_POS][0])
			sliderType = icg.TYPE_POSITION #Position
		else
			sliderType = icg.TYPE_MAG
		@scrollSlidesSide_(side, $(event.target), sliderType)

	scrollStopSide_: (side, slider) ->
		@ranges[side]=null
		if(slider.slider('option', 'value') != 50)
			slider.slider('option', 'value', 50)
	
	scrollStop_: (event, ui) ->
		icg=IsadoreControlGraph
		if(event.target == @controls[icg.CTL_LEFT_POS][0] or event.target == @controls[icg.CTL_LEFT_MAG][0])
			@scrollStopSide_(icg.SIDE_LEFT, $(event.target))
		else if(event.target == @controls[icg.CTL_RIGHT_POS][0] or event.target == @controls[icg.CTL_RIGHT_MAG][0])
			@scrollStopSide_(icg.SIDE_RIGHT, $(event.target))
	
	relayout: () ->
		icg = IsadoreControlGraph
		h = @icgWrapper.innerHeight()
		bpad=20
		tpad=10
		for controlWrapper in @controlWrappers
			controlWrapper.height(h-bpad-tpad)

		vpad=20
		pos=vpad
		for ii in [0...@controlWrappers.length]
			if(ii == icg.CTL_RIGHT_MAG)
				#size graph
				@graphDiv.height(@icgWrapper.innerHeight()-tpad)
				#TODO: Why do we need the -1 to make it fit?
				@graphDiv.width(@icgWrapper.innerWidth() - 2*pos-1)
				@graphDiv.css({top: tpad, left: pos+'px'})
				@plot.resize(@graphDiv.innerWidth(), @graphDiv.innerHeight())
				pos+=@graphDiv.outerWidth()+vpad
			controlWrapper = @controlWrappers[ii]
			controlWrapper.css({top: tpad, left: pos+'px'})
			pos+=controlWrapper.outerWidth()+vpad
		
	updateOptions: (options) ->
		@plot.updateOptions(options)
		return this
	xAxisRange: () ->
		return @plot.xAxisRange()

###
  Dual control graphs with range selector.
  @param element The elemnt to put the dual graph in
  @param The data [topdata, bottomdata, rangeselectordata]
  @param IDCGOptions object with the following:
    {
		axisColors:[[topY1color, topY2color], [bottomY1color, bottomY2color]]
		axisLabels:[[topY1Label, topY2Label], [bottomY1Label, bottomY2Label]]
		seriesLabels:[[topSeries1label, topSeries2label,...], [bottomSeries1Label, ...]]
		dataAxisMap:[[topSeries1AxisIndex, ...], [bottomSeries1AxisIndex, ...]]
	}
	Colors are html hex #FFAB02
	AxisIndex 0 for y axis, 1 for y2 axis.
###
class window.IsadoreDualControlGraph
	@GRAPH_TOP: 0
	@GRAPH_BOTTOM: 1
	constructor: (element, data, IDCGOptions) ->
		self=this
		idcg=IsadoreDualControlGraph
		@parent = $(element)
		@idcgWrapper = $('<div class="idcg_wrapper"></div>')
		@graphDivs = [
			$('<div class="idcg_graph idcg_graph_top"></div>'), 
			$('<div class="idcg_graph idcg_graph_bottom"></div>')
			$('<div class="idcg_graph idcg_graph_range_selector"></div>')
		]
		for div in @graphDivs
			@idcgWrapper.append(div)
		
		@parent.append(@idcgWrapper)
		
		options=[
			@genDygraphOptions_(IDCGOptions, idcg.GRAPH_TOP),
			@genDygraphOptions_(IDCGOptions, idcg.GRAPH_BOTTOM),
			@genRangeSelectorOptions_(IDCGOptions)
		]

		iModel= {
			mousedown: (event, g, context) ->
				context.initializeMouseDown(event, g, context)
				Dygraph.startPan(event, g, context)
			mousemove: (event, g, context) ->
				if (context.isPanning)
					Dygraph.movePan(event, g, context)
			mouseup: (event, g, context) ->
				if (context.isPanning)
					Dygraph.endPan(event, g, context)
		}
		
		options[0].interactionModel=iModel
		options[1].interactionModel=iModel

		@plots=[]
		for i in [0...2]
			@plots.push(
				new IsadoreControlGraph(
					@graphDivs[i]
					data[i]
					options[i]
				)
			)
		#Range selector
		@plots.push(
			new Dygraph(
				@graphDivs[2][0]
				data[2]
				options[2]
			)
		)

		for i in [0...@graphDivs.length]
			altCallback = options[i].drawCallback
			@plots[i].updateOptions({
				drawCallback: (graph, inited) ->
					range=graph.xAxisRange()
					
					for plot in self.plots
						if(plot != graph)
							orange = plot.xAxisRange()
							if(range[1] - range[0] < 0)
								graph.updateOptions({dateWindow: [orange[0], orange[1]]})
								break
							if(orange[0] != range[0] or orange[1] != range[1])
								plot.updateOptions({dateWindow: [range[0], range[1]]})
					if(altCallback)
						altCallback(graph, inited)
			})
		
		@icons = [
			$('<img class="idcg_icons" src="imgs/icon_position.png" alt="position"/>')
			$('<img class="idcg_icons" src="imgs/icon_magnify.png" alt="magnify"/>')
			$('<img class="idcg_icons" src="imgs/icon_magnify.png" alt="magnify"/>')
			$('<img class="idcg_icons" src="imgs/icon_position.png" alt="position"/>')
		]
		for icon in @icons
			@idcgWrapper.append(icon)
			
		@relayout()
	
	updateOptions: (options) ->
		idcg=IsadoreDualControlGraph
		optionsA = [
			@genDygraphOptions_(options, idcg.GRAPH_TOP)
			@genDygraphOptions_(options, idcg.GRAPH_BOTTOM)
		]
		@plots[idcg.GRAPH_TOP].updateOptions(optionsA[idcg.GRAPH_TOP])
		@plots[idcg.GRAPH_BOTTOM].updateOptions(optionsA[idcg.GRAPH_BOTTOM])
		
	# Add number to end of label if there are duplicates.
	fixedSeriesLabel_: (labels, idx) ->
		label = labels[idx]
		count = 1
		for i in [0...idx]
			if labels[i] == label
				count++
		if count > 1
			return (label + count)
		else
			return label
		
	genDygraphOptions_: (options, graph) ->
		idcg=IsadoreDualControlGraph
		patterns=[null, Dygraph.DASHED_LINE, Dygraph.DOTTED_LINE, Dygraph.DOT_DASH_LINE]
		newOptions={
			legend: 'always'
			panEdgeFraction: .0001
			customBars: true
			axes: {
				y2: {}
			}
			ylabel: '<span style="color: '+options.axisColors[graph][0]+'">'+options.axisLabels[graph][0]+'</span>'
			y2label: '<span style="color: '+options.axisColors[graph][1]+'">'+options.axisLabels[graph][1]+'</span>'
			yAxisLabelWidth: 70
		}
		newOptions.colors=[]
		for i in [0...options.seriesLabels[graph].length]
			newOptions.colors.push(options.axisColors[graph][options.dataAxisMap[graph][i]])
		newOptions.labels=['Date']

		firstY2Label=null
		ycount = 0
		y2count = 0
		for i in [0...options.seriesLabels[graph].length]
			label=@fixedSeriesLabel_(options.seriesLabels[graph], i)
			newOptions.labels.push(label)
			if(options.dataAxisMap[graph][i]==1)
				if(firstY2Label)
					newOptions[label]={axis:firstY2Label, strokePattern: patterns[y2count%patterns.length]}
				else
					newOptions[label]={axis:{}, strokePattern: patterns[y2count%patterns.length]}
					firstY2Label=label
				y2count++
			else
				newOptions[label]={strokePattern: patterns[ycount%patterns.length]}
				ycount++
		if(graph == idcg.BOTTOM_GRAPH)
			newOptions.xAxisLabelWidth = 0
		console.log('newOptions='+newOptions)
		return newOptions
		
	genRangeSelectorOptions_: (options) ->
		newOptions = {
			drawYAxis: false
			drawXAxis: false
			customBars: true
			showRangeSelector: true
			rangeSelectorHeight: 40
			xAxisLabelWidth: 0
		}
		return newOptions
		
	relayout: () ->
		rsHeight = $('.dygraph-rangesel-fgcanvas').height()
		h=(@idcgWrapper.innerHeight()-rsHeight)/2
		@graphDivs[0].height(h)
		@graphDivs[1].height(h)
		@graphDivs[2].height(rsHeight)
		
		@plots[0].relayout()
		@plots[1].relayout()
		
		for ii in [0...@icons.length]
			icon = @icons[ii]
			wrapper = @plots[0].controlWrappers[ii] #slider wrapper
			icon.css({top: wrapper.position().top+wrapper.height()+5, left: wrapper.position().left-3})
			
		#Range selector position
		@graphDivs[2].width(@plots[0].graphDiv.width()-110)
		@graphDivs[2].css({top: -20, left: @plots[0].graphDiv.position().left+55})
		@plots[2].resize(@graphDivs[2].width(), @graphDivs[2].height())
