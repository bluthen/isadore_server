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

class window.GraphTab
	constructor: (parent) ->
		self=this
		self.parent = parent
		self.tabElement = $('#bin_lightbox_tabs-graph')
		self.tabElement.empty()
		self.graph = new IsadoreGraph(self.tabElement[0], { resourcePath: '../' })
		
	setDefaultSensors: () ->
		self=this
		#Set top left and right options
		options = self.graph.getHeaderOptions()
		
		temps = null
		tIdx = -1
		hums = null
		hIdx = -1
		
		for uIdx in [0...options.length]
			unit = options[uIdx]
			if unit[0] == '&deg;F'
				temps = unit[1]
				tIdx = uIdx
			else if unit[0] == '%'
				hums = unit[1]
				hIdx = uIdx
			
		
		leftSet=false
		#Set temperature and humidity if availible
		if temps
			ioIdxs = []
			tbIdxs = []
			for sIdx in [0...temps.length]
				sensor = temps[sIdx][0]
				if sensor == 'Inlet Temp'
					ioIdxs.push(sIdx)
				else if sensor == 'Outlet Temp'
					ioIdxs.push(sIdx)
				else if sensor == 'Top Temp'
					tbIdxs.push(sIdx)
				else if sensor == 'Bottom Temp'
					tbIdxs.push(sIdx)
			if ioIdxs.length > 0 #if inlet and outlet
				#Set top left tIdx, ioIdxs
				self.graph.setUnit(IsadoreGraph.GRAPH_TOP, IsadoreGraph.YAXIS_LEFT, tIdx)
				self.graph.setSensors(IsadoreGraph.GRAPH_TOP, IsadoreGraph.YAXIS_LEFT, ioIdxs)
			else if tbIdxs.length > 0 #else if top or bottom
				#set top left tIdx, tbIdxs
				self.graph.setUnit(IsadoreGraph.GRAPH_TOP, IsadoreGraph.YAXIS_LEFT, tIdx)
				self.graph.setSensors(IsadoreGraph.GRAPH_TOP, IsadoreGraph.YAXIS_LEFT, tbIdxs)
			else #else index 0
				self.graph.setUnit(IsadoreGraph.GRAPH_TOP, IsadoreGraph.YAXIS_LEFT, tIdx)
				self.graph.setSensors(IsadoreGraph.GRAPH_TOP, IsadoreGraph.YAXIS_LEFT, [0])
			leftSet = true
		
		if hums
			ioIdxs = []
			tbIdxs = []
			for sIdx in [0...hums.length]
				sensor = hums[sIdx][0]
				if sensor == 'Inlet RH'
					ioIdxs.push(sIdx)
				else if sensor == 'Outlet RH'
					ioIdxs.push(sIdx)
				else if sensor == 'Top RH'
					tbIdxs.push(sIdx)
				else if sensor == 'Bottom RH'
					tbIdxs.push(sIdx)
			axis = IsadoreGraph.YAXIS_RIGHT
			if not leftSet
				axis = IsadoreGraph.YAXIS_LEFT
			if ioIdxs.length > 0 #if inlet and outlet
				#Set top left tIdx, ioIdxs
				self.graph.setUnit(IsadoreGraph.GRAPH_TOP, axis, hIdx)
				self.graph.setSensors(IsadoreGraph.GRAPH_TOP, axis, ioIdxs)
			else if tbIdxs.length > 0 #else if top or bottom
				#set top left tIdx, tbIdxs
				self.graph.setUnit(IsadoreGraph.GRAPH_TOP, axis, hIdx)
				self.graph.setSensors(IsadoreGraph.GRAPH_TOP, axis, tbIdxs)
			else #else index 0
				self.graph.setUnit(IsadoreGraph.GRAPH_TOP, axis, hIdx)
				self.graph.setSensors(IsadoreGraph.GRAPH_TOP, axis, [0])
			leftSet = true
			
		if not leftSet #if nothing set, set first option
			self.graph.setUnit(IsadoreGraph.GRAPH_TOP, IsadoreGraph.YAXIS_LEFT, 0)
			self.graph.setSensors(IsadoreGraph.GRAPH_TOP, IsadoreGraph.YAXIS_LEFT, [0])
			
		return self
		
	refresh: (bin) ->
		self=this
		self.graph.clear()
		self.graph.changeBin(bin.id, () ->
			ih = self.tabElement.innerHeight()
			if ih < 700
				ih = 700
			$('div', self.tabElement).first().height(ih)
			self.graph.vertStretch()
			#self.parent.dialog.resize()
			self.graph.setLastFill()
			self.setDefaultSensors()
		)
		
