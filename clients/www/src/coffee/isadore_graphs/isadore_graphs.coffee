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


DEFAULT_COLORS=['ff0000', '0010a5', 'ff6600', '6300a5']

# Dialog with color picker in it. Will update a color field when color is 
# chosen. it knows when color field be looking for .ig_color_field[data-focused="true"].
class IsadoreGraphColorPicker_
	# @param igElem jQuery element of the main IsadoreGraph wrapper.
	constructor: (@igElem, parent) ->
		self = this
		self.igcpDiv = $('#igcp')
		if self.igcpDiv.length > 0
			self.cpDiv = $('#igcp > div').first()
		else
			self.igcpDiv = $('<div id="igcp"></div>')
			self.cpDiv = $('<div></div>')
			self.igcpDiv.append(@cpDiv)
			$('body').append(@igcpDiv)
			self.cpDiv.jPicker(
				{
					clientPath: parent.igOptions.resourcePath+'s/imgs/jpicker/'
				},
				(color, context) ->
					all = color.val('all')
					if all
						console.log('Ok clicked', all.hex)
						colorField = $('.ig_color_field[data-focused="true"]', self.igElem)
						colorField.val(color.val('all').hex)
						colorField.attr('data-focused', '')
						colorField.change()
					self.igcpDiv.dialog('close')
				null
				(color, context) ->
					$('.ig_color_field[data-focused="true"]', self.igElem).attr('data-focused', '')
					self.igcpDiv.dialog('close')
			)
			self.igcpDiv.hide()
			self.igcpDiv.dialog({
				modal: true
				width: 590
				height: 400
				zIndex: 10000
				autoOpen: false
				open: () ->
					colorField = $('.ig_color_field[data-focused="true"]', self.igElem)
					color = colorField.val()
					$.jPicker.List[0].color.active.val('hex', color, this);
					$.jPicker.List[0].color.current.val('hex', color, this);
			})
		
	# Show the dialog with the color picker in it.
	show: () ->
		self=this
		self.igcpDiv.dialog('open')


# The actual class that makes and handles the color, unit, sensor fields. One
# class per graph.
class IsadoreGraphHeaderYAxisControl_
	# @param parentControl The control this object is in.
	# @parentElem The jquery element to put itself in.
	# @yaxisIdx The yaxis index these controls are for.
	constructor: (@parentControl, @parentElem, @yaxisIdx) ->
		self=this
		self.sensorSelectChangeHandlers_ = []
		# Unit selector
		self.wrapperDiv = $('<div style="display: inline-block; width: 50%;"></div>')
		self.initUnit_()
		self.initSensor_()
		self.initColor_()
		self.parentElem.append(@wrapperDiv)
		# Update the sensor select when unit select changes.
		self.unitSelect.change((eventObject) ->
			select = $(eventObject.target)
			value=select.val()
			options=self.parentControl.parentControls.parentIG.binHeaderOptions[value][1]
			optionsStr=''
			for i in [0...options.length]
				optionsStr+="<option value=\"#{i}\">#{options[i][0]}</option>"
			self.sensorSelect.html(optionsStr)
			#self.sensorSelect.multiselect('refresh')
		)
		
		# Use custom multiselect
		#self.sensorSelect.multiselect({
		#	noneSelectedText: 'Select data'
		#})
		
		# Color click event
		self.colorField.click((eventObject) ->
			$(eventObject.target).attr('data-focused', 'true')
			options=self.parentControl.parentControls.parentIG.igcp.show()
		)
		
		# Change color field background color when it has changed.
		self.colorField.change( (eventObject) ->
			cf = $(eventObject.target)
			color = cf.val()
			cf.css({ 'background-color': '#'+color })
		)
		
		self.sensorSelect.change( (eventObject) ->
			clearTimeout(self.sensorSelectChangeTimeout_)
			self.sensorSelectChangeTimeout_ = setTimeout(() ->
				for handler in self.sensorSelectChangeHandlers_
					handler(eventObject, self.parentControl.graphIdx, self.yaxisIdx, self)
			, 2000)
		)
		
		
		self.colorField.change()
		
	initUnit_: () ->
		self=this
		unitDiv = $('<div class="ig_unit_selector"></div>')
		self.unitSelect = HTMLHelper.makeSelect([{ id: -1, name: 'Loading...' }], 'name', 'id')
		unitDiv.append(@unitSelect)
		self.wrapperDiv.append(unitDiv)
		
	initSensor_: () ->
		self=this
		# Sensor selector
		sensorDiv = $('<div class="ig_sensor_selector"></div>')
		self.sensorSelect = HTMLHelper.makeSelect([
			{ id: -1, name: 'Loading...' }
		], 'name', 'id', true)
		sensorDiv.append(@sensorSelect)
		self.wrapperDiv.append(sensorDiv)
	
	initColor_: () ->
		self=this
		ig = IsadoreGraph
		colorIdx = @parentControl.graphIdx*2+@yaxisIdx
		colorDiv = $('<div class="ig_color_selector"></div>')
		self.colorField = $('<input type="text" class="ig_color_field" value="'+
			DEFAULT_COLORS[colorIdx]+'"/>')
		colorDiv.append(@colorField)
		self.wrapperDiv.append(colorDiv)
		
	# Updates unitSelect with new options in parentIG.
	refresh: () ->
		self=this
		optionStr=''
		options = self.parentControl.parentControls.parentIG.binHeaderOptions
		for i in [0...options.length]
			optionStr+="<option value=\"#{i}\">#{options[i][0]}</option>"
		self.unitSelect.html(optionStr)
		self.unitSelect.change()

	# add event handler for color change event on the color text field.
	# handler(eventObject, graphIdx, yaxisIdx, yaxisControl)
	colorChange: (handler) ->
		self=this
		if not handler
			self.colorField.change()
		else
			self.colorField.change( (eventObject) ->
				handler(eventObject, self.parentControl.graphIdx, self.yaxisIdx, self)
			)
		return self

	# add event handler for when sensor selection has changed.
	# handler(eventObject, graphIdx, yaxisIdx, yaxisControl)
	# if handler is null the change event gets triggered.
	# Has delay on change to squash multiple changes.
	# TODO: Squash events if multiple changes on different graph
	sensorChange: (handler) ->
		self=this
		if not handler
			self.sensorSelect.change()
		else
			self.sensorSelectChangeHandlers_.push(handler)
		return self
	
	# Returns the selected unit.
	getUnit: () ->
		self=this
		unitIdx = @unitSelect.val()
		return self.parentControl.parentControls.parentIG.binHeaderOptions[unitIdx][0]

	# Returns the selected sensor data.
	getSensors: () ->
		self=this
		unitIdx = self.unitSelect.val()
		sensorIndexes = self.sensorSelect.val()
		sensors=self.parentControl.parentControls.parentIG.binHeaderOptions[unitIdx][1]
		s=[]
		if sensorIndexes
			for sensorIdx in sensorIndexes
				s.push(sensors[sensorIdx])
		return s
	
	getColor: () ->
		self=this
		return self.colorField.val()
	

# A top graph or bottom graph control.
class IsadoreGraphHeaderGraphControl_
	@YAXIS_LEFT=0
	@YAXIS_RIGHT=1
	# @param parentControls The header control this is in.
	# @param parentElem the element to put itself in.
	# @param graphIdx the graph index (top, bottom) of this control.
	constructor: (@parentControls, @parentElem, @graphIdx) ->
		self=this
		staticSelf=IsadoreGraphHeaderGraphControl_
		if self.graphIdx == IsadoreGraphHeaderControls_.GRAPH_TOP
			label = 'Top'
		else
			label = 'Bottom'
		self.wrapperElem = $('<div class="ig_header_control_wrapper" style="display: inline-block; width: 50%"><h3>'+label+'</h3></div>')
		self.parentElem.append(@wrapperElem)
		self.hControls = [
			new IsadoreGraphHeaderYAxisControl_(self, self.wrapperElem, staticSelf.YAXIS_LEFT)
			new IsadoreGraphHeaderYAxisControl_(self, self.wrapperElem, staticSelf.YAXIS_RIGHT)
		]
		
	refresh: () ->
		self=this
		for control in self.hControls
			control.refresh()
		return this

	# add event handler for color change event on the color text field.
	# handler(eventObject, graphIdx, yaxisIdx, hControl)
	colorChange: (handler) ->
		self=this
		for control in self.hControls
			control.colorChange(handler)
		return this

	# add event handler for when sensor selection has changed.
	# handler(eventObject, graphIdx, yaxisIdx, yaxisControl)
	# if handler is null the change event gets triggered.
	# Has delay on change to squash multiple changes.
	sensorChange: (handler) ->
		self=this
		for control in self.hControls
			control.sensorChange(handler)
		return this
		
		
	# @returns [unitlabel left, unitlabel right]
	getUnits: () ->
		self=this
		units=[]
		for control in self.hControls
			units.push(control.getUnit())
		return units 
	
	# Returns selected sensors from top controls.
	# @returns [ [ [leftgraph_selection1_name, type, [bin_section, sensor_type_id]], ...], [[rightgraph..], ...]]
	getSensors: () ->
		self=this
		sensors = []
		for control in self.hControls
			sensors.push(control.getSensors())
		return sensors
		
	getColors: () ->
		self=this
		colors = []
		for control in self.hControls
			colors.push(control.getColor())
		return colors
		

# The header controls for both graphs.
class IsadoreGraphHeaderControls_
	@GRAPH_TOP = 0
	@GRAPH_BOTTOM = 1
	constructor: (@parentIG, @parentElem) ->
		self=this
		staticSelf=IsadoreGraphHeaderControls_
		self.wrapperElem = $('<div class="ig_header_wrapper"></div>')
		self.parentElem.append(@wrapperElem)
		
		self.controls = [
			new IsadoreGraphHeaderGraphControl_(self, @wrapperElem, staticSelf.GRAPH_TOP)
			new IsadoreGraphHeaderGraphControl_(self, @wrapperElem, staticSelf.GRAPH_BOTTOM)
		]
	refresh: () ->
		self=this
		for hControls in self.controls
			hControls.refresh()
		return this
	
	getUnits: (graphIdx) ->
		self=this
		if not graphIdx
			units=[]
			units.push(self.controls[IsadoreGraphHeaderControls_.GRAPH_TOP].getUnits())
			units.push(self.controls[IsadoreGraphHeaderControls_.GRAPH_BOTTOM].getUnits())
			return units
		return self.controls[graphIdx].getUnits()
	
	# Get sensor selection for graph
	# @param graphIdx Which sensors to get, if null then all.
	getSensors: (graphIdx) ->
		self=this
		if not graphIdx
			sensors = []
			sensors.push(self.controls[IsadoreGraphHeaderControls_.GRAPH_TOP].getSensors())
			sensors.push(self.controls[IsadoreGraphHeaderControls_.GRAPH_BOTTOM].getSensors())
			return sensors
		return self.controls[graphIdx].getSensors()
		
	getColors: (graphIdx) ->
		self=this
		if not graphIdx
			colors=[]
			colors.push(self.controls[IsadoreGraphHeaderControls_.GRAPH_TOP].getColors())
			colors.push(self.controls[IsadoreGraphHeaderControls_.GRAPH_BOTTOM].getColors())
			return colors
		return self.controls[graphIdx].getColors()
	
	# add event handler for color change event on the color text field.
	# handler(eventObject, graphIdx, yaxisIdx, yaxisControl)
	colorChange: (handler) ->
		self=this
		for hControls in self.controls
			hControls.colorChange(handler)
		return this
		
	# add event handler for when sensor selection has changed.
	# handler(eventObject, graphIdx, yaxisIdx, yaxisControl)
	# if handler is null the change event gets triggered.
	# Has delay on change to squash multiple changes.
	sensorChange: (handler) ->
		self=this
		for hControls in self.controls
			hControls.sensorChange(handler)
		return this

class IsadoreGraphFooterControls_
	constructor: (@parentIG, @parentElem) ->
		self = this
		self.timeRangeChangeHandlers_ = []
		self.wrapperElem = $('<div class="ig_footer_wrapper"></div>')
		self.parentElem.append(@wrapperElem)
		
		self.initAvg_()
		self.initTimeSelect_()
		self.initSubsampleData_()
		
		self.fillSelect.change( (eventObject) ->
			fill = self.getSelectedFill()
			if fill
				start = fill.air_begin_datetime
				end = fill.air_end_datetime
				if not start
					start = fill.filled_datetime
				if not end
					end = fill.emptied_datetime
				$(self.timeRangeFields[0]).datetimepicker('setDate', new Date(start))
				if end
					$(self.timeRangeFields[1]).datetimepicker('setDate', new Date(fill.air_end_datetime))
				else
					$(self.timeRangeFields[1]).datetimepicker('setDate', new Date())
		)
		
		self.agoSelect.change( (eventObject) ->
			v = self.agoSelect.val()
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
			$(self.timeRangeFields[0]).datetimepicker('setDate', new Date(st))
			$(self.timeRangeFields[1]).datetimepicker('setDate', new Date(n))
		)
		
		self.timeRangeFields.change( (eventObject) ->
			clearTimeout(self.timeRangeChangeTimeout_)
			self.timeRangeChangeTimeout_ = setTimeout( () ->
				times = [$(self.timeRangeFields[0]).datetimepicker('getDate'), $(self.timeRangeFields[1]).datetimepicker('getDate')]
				fill = self.getSelectedFill()
				if fill
					fillTimes = [new Date(fill.air_begin_datetime), new Date(fill.air_end_datetime)]
					if not times[0] or fillTimes[0].getTime() != times[0].getTime() or not times[1] or fillTimes[1].getTime() != times[1].getTime()
						self.fillSelect.val(-1)
						self.agoSelect.val(-1)
				for handler in self.timeRangeChangeHandlers_
					handler(eventObject, times[0], times[1], self)
			, 2000)
		)
	
	#Returns the currently selected fill or null if none
	getSelectedFill: () ->
		self=this
		fill = null
		fillIdx = Number(self.fillSelect.val())
		if fillIdx >= 0
			fill=self.fills[fillIdx]
		return fill
		
	getSelectedAgo: () ->
		self=this
		v = self.agoSelect.val()
		return v
		
	initAvg_: () ->
		self=this
		#Avg
		avgDiv = $('<div class="ig_footer_avg_wrapper"></div>')
		avgDiv.append($('<label>Avg:</label>'))
		self.avgSelect = $('<select><option value="0">Loading...</option></select>')
		avgDiv.append(self.avgSelect)
		label = $('<label><input type="checkbox" checked="true"/> Show Min/Max Areas</label>')
		self.minMaxArea = $('input', label)
		avgDiv.append(label)
		
		
		self.wrapperElem.append(avgDiv)
		

	initTimeSelect_: () ->
		self=this
		#Fill Selector
		timeDiv = $('<div class="ig_footer_time_wrapper"></div>')
		timeDiv.append($('<label>Fill:</label>'))
		self.fillSelect = $('<select class="ig_footer_fill_select"><option value="-1">Loading...</option></select>')
		timeDiv.append(@fillSelect)
		self.agoSelect=$('<select>
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
		timeDiv.append(self.agoSelect)
		#Time selector
		self.wrapperElem.append(timeDiv)
		self.initTimeRange_(timeDiv)
		
		
	initTimeRange_: (timeDiv) ->
		self=this
		div = $('<div class="ig_timeselector_wrapper"></div>')
		div.append($('<label>Time Range:</label>'))
		for idCount in [0...2]
			id = "ig_timeselector_#{@parentIG.igRandomId}_#{idCount}"
			div.append($('<input type="text" class="calendar ig_timeselector" id="'+id+'"/><img src="imgs/icon_calendar.gif" data-date_id="'+id+'" alt="Pick date/time" />'))
			if idCount == 0
				div.append(document.createTextNode(' - '))
		calendarRegister($('.calendar', div))
		calendarImageRegister($('img[src="imgs/icon_calendar.gif"]', div));
		timeDiv.append(div)
		self.timeRangeFields = $('input', div)
		
		
	updateAvg_: () ->
		self=this
		#TODO: Hide the ones below pixel threshold.
		options='<option value="0">auto</option>'
		for subsample in @subsamples
			if subsample > 60
				label = subsample/60.0 + ' hrs'
			else
				label = subsample + ' min'
			options+="<option value=\"#{subsample}\">#{label}</option>"
		$('.ig_footer_avg_wrapper select', self.wrapperElem).html(options)
		
	initSubsampleData_: () ->
		self=this
		$.ajax({
			url: self.parentIG.igOptions.resourcePath+'resources/conf/subsamples'
			type: 'GET'
			dataType: 'json'
			success: (data) ->
				self.subsamples = data.subsamples
				self.updateAvg_()
		})

	updateFillSelector_: () ->
		self=this
		select = $('select.ig_footer_fill_select', self.wrapperElem)
		options='<option value="-1"> </option>'
		for i in [0...self.fills.length]
			fill = self.fills[i]
			start = fill.air_begin_datetime
			if not start
				start = fill.filled_datetime
			options += "<option value=\"#{i}\">#{fill.fill_number} #{new Date(start).getFullYear()}</option>"
		select.html(options)
		
	refreshFills: (callback) ->
		self=this
		binId = self.parentIG.binId
		prefixPath = self.parentIG.igOptions.resourcePath
		$.ajax({
			url: prefixPath + 'resources/data/fills-fast'
			type: 'GET'
			dataType: 'json'
			success: (data) ->
				self.fills=data.fills
				self.updateFillSelector_()
				if callback
					callback()
			data: {
				'bin_id' : binId
			}
		})
		return self
		
	# handler(eventObject, beginDate, endDate, footerControls)
	timeRangeChange: (handler) ->
		self=this
		if not handler
			self.timeRangeFields.change()
		else
			self.timeRangeChangeHandlers_.push(handler)
		return this
		
	# handler(eventObject, value_mins, footerControls)
	avgChange: (handler) ->
		self=this
		if not handler
			self.avgSelect.change()
		else
			self.avgSelect.change( (eventObject) ->
				handler(eventObject, $(eventObject.target).val())
			)
		return self
		
	getAvg: () ->
		self=this
		return self.avgSelect.val()
		
	minMaxAreaChange: (handler) ->
		self=this
		if not handler
			self.minMaxArea.change()
		else
			self.minMaxArea.change( (eventObject) ->
				handler(eventObject, $(eventObject.target).prop('checked'))
			)
		return self
		
	getMinMaxArea: () ->
		self=this
		return self.minMaxArea.prop('checked')
		
	# @returns [beginDate, endDate]
	getTimeRange: () ->
		self=this
		return [
			$(self.timeRangeFields[0]).datetimepicker('getDate')
			$(self.timeRangeFields[1]).datetimepicker('getDate')
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


	setLastFill: () ->
		self=this
		lastFill = null
		lastFillTime = null
		if not self.fills
			return
		for fill in self.fills
			if not lastFill
				lastFill = fill
			else if @_laterFill(fill, lastFill)
					lastFill = fill
		if lastFill
			idx = self.fills.indexOf(lastFill)
			console.log('last fill idx = '+idx)
			self.fillSelect.val(idx)
			self.fillSelect.change()


class window.IsadorePNGRenderer
	constructor: (@element, @parent) ->
		self=this
		self.img = $('<img />')
		$(this.element).append(self.img)
		self.updateTimeout=null
		updateFunc = () ->
			clearTimeout(self.updateTimeout)
			self.updateTimeout = setTimeout(
				() ->
						self.refresh()
				500
			)
		self.parent.headerControls.colorChange( updateFunc )
		self.parent.headerControls.sensorChange( updateFunc )
		self.parent.footerControls.timeRangeChange( updateFunc )
		self.parent.footerControls.avgChange( updateFunc )
		self.parent.footerControls.minMaxAreaChange( updateFunc )
	
	refresh: () ->
		self=this
		qo = self.genQueryAndOptions_()
		
		params = { bin_id: self.parent.binId }
		params.query_top = JSON.stringify(qo.queryTop)
		params.query_bottom = JSON.stringify(qo.queryBottom)
		params.sample_period = self.parent.footerControls.getAvg()
		times = self.parent.footerControls.getTimeRange()
		if not times[0] or not times[1]
			return
		if qo.options.dataAxisMap[0].length == 0 and qo.options.dataAxisMap[1].length == 0
			return
		params.begin_datetime = HTMLHelper.dateToParamString(times[0])
		params.end_datetime = HTMLHelper.dateToParamString(times[1])
		params.plot_options = JSON.stringify(qo.options)
		params.display_tz = jstz.determine().name()
		params.ts = new Date().getTime()

		$(self.element).empty().append($('<img/>').attr('src', self.parent.igOptions.resourcePath+'s/imgs/ajax-loader-bigimg.gif'))
		url =  self.parent.igOptions.resourcePath+'resources/data/graphq?'+HTMLHelper.makeParameters(params)
		newImg = $('<img/>').attr('src', url).load( () ->
			$(self.element).empty().append(newImg)
		).error( () ->
			self.clear()
		)
		console.log('Updated image')
		
	clear: () ->
		self=this
		$(self.element).empty()
		
	genQueryAndOptions_: () ->
		self=this
		query = []
		first=true
		
		options={}
		options.dataAxisMap = []
		options.axisLabels = []
		options.minMaxAreas = []
		options.seriesLabels = []

		minMax = self.parent.footerControls.getMinMaxArea()
		if minMax
			minMax = 1
		else
			minMax = 0

		sensors = self.parent.headerControls.getSensors()
		for i in [0...sensors.length]
			query.push([])
			options.dataAxisMap.push([])
			options.seriesLabels.push([])
			options.minMaxAreas.push([])
			for j in [0...sensors[i].length]
				for sensor in sensors[i][j]
					query[i].push([sensor[1], sensor[2]])
					options.seriesLabels[i].push(sensor[0])
					options.dataAxisMap[i].push(j)
					options.minMaxAreas[i].push( minMax )
		options.axisLabels = self.parent.headerControls.getUnits()
		options.graphDims = [$(self.parent.graphDiv).width(), $(self.parent.graphDiv).height()]
		options.axisColors = self.parent.headerControls.getColors()
		
		retVal={}
		retVal.queryTop=query[0]
		retVal.queryBottom=query[1]
		retVal.options=options
		
		console.log(retVal)
		return retVal


class window.IsadoreGraph
	
	#Left axis used for set methods
	@YAXIS_LEFT=0
	#Right axis used for set methods
	@YAXIS_RIGHT=1
	
	#Top graph constant used for set methods.
	@GRAPH_TOP = 0
	#Bottom graph constant used for set methods.
	@GRAPH_BOTTOM = 1
	
	constructor: (element, @igOptions) ->
		self=this
		self.prevTimeRange_ =[[null, null], [null, null]]
		self.prevSamplePeriod_ = [null, null]
		ig=IsadoreGraph
		# Get unique id for this object (There could be more than one IsadoreGraph)
		self.igRandomId = Math.ceil(Math.random()*1679615).toString(36)
		while ($('#ig_'+self.igRandomId).length > 0)
			self.igRandomId = Math.ceil(Math.random()*1679615).toString(36)
		self.parentElem = $(element)
		if not self.igOptions
			self.igOptions={ resourcePath:'../' }
		else if not self.igOptions.resourcePath
			self.igOptions.resourcePath = '../'
		
		self.binHeaderOptions = {}
		self.wrapperElem = $('<div class="ig_wrapper" id="ig_'+self.igRandomId+'"></div>')
		self.parentElem.append(self.wrapperElem)
		# Make the colorpicker
		self.igcp = new IsadoreGraphColorPicker_(self.wrapperElem, self)

		self.headerControls = new IsadoreGraphHeaderControls_(self, self.wrapperElem)
		# Graph
		self.graphDiv = $('<div class="ig_graph" style="text-align: center;width: 100%;"></div>')
		self.wrapperElem.append(self.graphDiv)
		self.footerControls = new IsadoreGraphFooterControls_(self, self.wrapperElem)

		# Initial data and options
		self.options={
			axisColors:[[DEFAULT_COLORS[0], DEFAULT_COLORS[1]], [DEFAULT_COLORS[2], DEFAULT_COLORS[3]]]
			axisLabels:[['NA', 'NA'], ['NA', 'NA']]
			seriesLabels:[['NA', 'NA'], ['NA', 'NA']]
			dataAxisMap:[[0, 1], [0, 1]]
		}

		self.vertStretch()
		@graph = new IsadorePNGRenderer(self.graphDiv[0], self)
		#@graph = new IsadoreDualControlGraph(@graphDiv[0], [@data, @data, @data], @options)

		self.headerControls.colorChange( (eventObject, graphIdx, yaxisIdx) ->
			color = $(eventObject.target).val()
			console.log('ColorChange: '+color)
		)

		self.headerControls.sensorChange( (eventObject, graphIdx, yaxisIdx, yaxisControl) ->
			sensors = yaxisControl.getSensors()
			console.log('SensorChange: ')
			console.log(sensors)
		)
		
		self.footerControls.timeRangeChange( (eventObject, startDate, endDate) ->
			console.log(startDate+' - '+endDate)
		)
		
		self.footerControls.avgChange( (eventObject, value) ->
			console.log('avg: '+value)
		)
		
		self.footerControls.minMaxAreaChange( (eventObject, value) ->
			console.log('minMaxArea: '+value)
		)

	clear: () ->
		self=this
		self.graph.clear()
		return self
		
	vertStretch: () ->
		self=this
		self.graphDiv.css({ height: self.wrapperElem.outerHeight()-self.headerControls.wrapperElem.outerHeight()-self.footerControls.wrapperElem.outerHeight() })
		return self

	changeBin: (binId, callback) ->
		self=this
		$.ajax({
			url : self.igOptions.resourcePath+'resources/data/graph/selections/'+binId
			type : 'GET'
			dataType : 'json'
			success : (data) ->
				self.binId = binId
				self.binHeaderOptions=data.options
				self.headerControls.refresh()
				self.footerControls.refreshFills(() ->
					if callback
						callback()
				)
		})
		

	# Makes the graph use the last fill for a time period.
	setLastFill: () ->
		self=this
		self.footerControls.setLastFill()
		return self
		
	# returns the current header unit and sensor data structure.
	getHeaderOptions: () ->
		self=this
		return self.binHeaderOptions

	# Set the unit for a particular graph and axis.
	setUnit: (graph, axis, val) ->
		self=this
		self.headerControls.controls[graph].hControls[axis].unitSelect.val(val)
		self.headerControls.controls[graph].hControls[axis].unitSelect.change()
		return self
	
	#Set the sensor for a particular graph and axis.
	setSensors: (graph, axis, valArray) ->
		self=this
		self.headerControls.controls[graph].hControls[axis].sensorSelect.val(valArray)
		self.headerControls.controls[graph].hControls[axis].sensorSelect.change()
		return self
		
