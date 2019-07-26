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
import matplotlib
from matplotlib.pyplot import figure, show
import matplotlib.pyplot as pyplot
import datetime as dt
import sys
import logging
import threading
import StringIO
import numpy
import time

graphLock = threading.RLock()


#
# Example Usage:
# plotter = Plotter(dataTop, dataBottom, options)
# plotter.plot()
# fig = plotter.getFigure()
# fig.savefig(stream, format="png")
# plotter.close()
class Plotter():
	TOP = 0
	BOTTOM = 1
	LEFT = 0
	RIGHT = 1

	# @param dataTop [[datetime, [line1PtTop, line1PtLine, line1PtBot], [line2PtTop, ...], ...], ...] 
	# @param dataBottom Same as dataTop, can be None if only plotting one graph.
	# @param options {'axisColors':[[topLeftColor, topRightColor], [bottomLeftColor, bottomRightColor]],
	#				'axisLabels':[[topLeftLabel, topRightLabel], [bottomLeftLabel, bottomRightLabel]],
	#				'seriesLabels':[[topline1Label, topline2Label,...], [bottomline1label, ...]]
	#				'dataAxisMap':[[topline1axis, topline2axis,...], [bottomline1axis, ...]]
	#				'minMaxAreas': [[topline1havearea, ...], [bottomelin1havearea, ...]]}
	#
	#				topline1side 0 for left 1 for right
	# @param displayTZ The timezone tz database string to display dates in (ex. 'America/Chicago')
	def __init__(self, dataTop, dataBottom, options, graphDims, displayTZ):
		self.options=options
		self.dataTop = dataTop
		self.dataBottom = dataBottom
		self.xaxis = []
		self.xaxisi=[]
		self.yaxis = [[]]
		self.fig=None
		self.pngBuffer=None
		self.graphDims = graphDims
		self.displayTZ=displayTZ

		z = zip(*dataTop)

		self.xaxis.append(z[0])
		self.xaxisi.append(map(lambda x: int(time.mktime(x.timetuple()) * 1000), z[0]))

		ys = z[1:]
		for y in ys:
			self.yaxis[0].append(zip(*y))
		if dataBottom:
			self.yaxis.append([])
			z = zip(*dataBottom)
			self.xaxis.append(z[0])
			self.xaxisi.append(map(lambda x: int(time.mktime(x.timetuple()) * 1000), z[0]))
			ys = z[1:]
			for y in ys:
				self.yaxis[1].append(zip(*y))
		self.plotLock_()

	# @param graph Either TOP=0 or BOTTOM=1
	# @param side Either LEFT = 0 or RIGHT=1
	# @param axis The axis object to draw on
	def plotAxis_(self, graph, side, axis):
		damap = self.options['dataAxisMap'][graph]
		color = self.options['axisColors'][graph][side]
		lineSymbols = ['-', '-.', ':', '--']
		legendLines = []
		legendLabels = []
		count = 0
		ymin = sys.maxint
		ymax = -sys.maxint-1
		noData=False
		for s, idx in zip(damap, range(len(damap))):
			if s != side:
				continue
			tmin = sys.maxint
			tmax = -sys.maxint-1
			if self.options['minMaxAreas'][graph][idx] == 1:
				try:
					tmin = min(value for value in self.yaxis[graph][idx][0] if value is not None)
					tmax = max(self.yaxis[graph][idx][2])
					#axis.fill_between(self.xaxis[graph], self.yaxis[graph][idx][0], self.yaxis[graph][idx][2], color=color, alpha=0.3)
					#nan's are should be masked in 1.2 matplotlib when that comes out.
					x=numpy.array(self.xaxisi[graph])
					yt = numpy.array(self.yaxis[graph][idx][0], dtype=numpy.double)
					yb = numpy.array(self.yaxis[graph][idx][2], dtype=numpy.double)
					dos = numpy.logical_and(numpy.logical_not(numpy.isnan(yt)), numpy.logical_not(numpy.isnan(yb)))
					axis.fill_between(x[dos], yt[dos], yb[dos], color=color, alpha=0.3)
				except ValueError: #If all nones in area
					try:
						tmin = min(value for value in self.yaxis[graph][idx][1] if value is not None)
						tmax = max(self.yaxis[graph][idx][1])
					except ValueError: #No avg data
						noData = True
						tmin = 0
						tmax = 0
			else:
				try:
					tmin = min(value for value in self.yaxis[graph][idx][1] if value is not None)
					tmax = max(self.yaxis[graph][idx][1])
				except ValueError: #No avg data
					noData = True
					tmin = 0
					tmax = 0
			lineSymbol = lineSymbols[count % len(lineSymbols)]
			legendLines.append(pyplot.Line2D((0,0),(0,0),color=color,linestyle=lineSymbol))
			legendLabels.append(self.options['seriesLabels'][graph][idx])
			if noData:
				nn = [None]*len(self.xaxisi[graph])
				nn[0] = 0
				nn[1] = 0
				axis.plot(self.xaxisi[graph], nn, lineSymbol, color=color)
			else:
				axis.plot(self.xaxisi[graph], self.yaxis[graph][idx][1], lineSymbol, color=color)
			count+=1
			if tmin < ymin:
				ymin = tmin
			if tmax > ymax:
				ymax = tmax

		#YTick labels
		yticklabels = []
		yticks = axis.get_yticks()
		ytickf = "%.1f"
		if len(yticks) > 2:
			ytickd = abs(yticks[1]-yticks[2])
			if ytickd.is_integer():
				ytickf = "%.0f"
			if yticks[1] > 1000:
				ytickf = "%.3e"
			elif ytickd < 0.1:
				ytickf = "%.2e"
		for tick in yticks:
			yticklabels.append(ytickf % (tick,))
		#For some reason you have to set yticks this otherwise it screws up
		axis.set_yticks(yticks)
		axis.set_yticklabels(yticklabels)

		axis.set_ylabel(self.options['axisLabels'][graph][side], color=color)
		r = (ymax - ymin)*0.10
		axis.set_ylim(ymin-r, ymax+r)
		return (legendLines, legendLabels)

	def plotLock_(self):
		try:
			graphLock.acquire()
			self.plot_()
		finally:
			graphLock.release()
	# makes figure and makes plot.
	def plot_(self):
		fig = figure()
		if len(self.yaxis) > 1:
			axTopLeft = pyplot.subplot(211)
			axBottomLeft = pyplot.subplot(212, sharex=axTopLeft)
		else:
			axTopLeft = pyplot.subplot(111)
		#fig, (axTopLeft, axBottomLeft) = pyplot.subplots(nrows=2, ncols=1)
		
		# TOP:
		legendLines, legendLabels = self.plotAxis_(self.TOP, self.LEFT, axTopLeft)

		if 1 in self.options['dataAxisMap'][self.TOP]:
			axTopRight = axTopLeft.twinx()
			lines, labels = self.plotAxis_(self.TOP, self.RIGHT, axTopRight)
			legendLines.extend(lines)
			legendLabels.extend(labels)

		axTopLeft.get_xaxis().grid(True)
		axTopLeft.legend(legendLines, legendLabels,
						loc=3,
						ncol=5,
						prop=matplotlib.font_manager.FontProperties(size=9),
						handlelength=3,
						bbox_to_anchor=(0., 1.02, 1., 1.02), 
						mode='expand', 
						borderaxespad=0.)

		if len(self.yaxis) > 1:
			# BOTTOM
			legendLines, legendLabels = self.plotAxis_(self.BOTTOM, self.LEFT, axBottomLeft)

			if 1 in self.options['dataAxisMap'][self.BOTTOM]:
				axBottomRight = axBottomLeft.twinx()
				lines, labels = self.plotAxis_(self.BOTTOM, self.RIGHT, axBottomRight)
				legendLines.extend(lines)
				legendLabels.extend(labels)
			
			axBottomLeft.get_xaxis().grid(True)
			
			axBottomLeft.legend(legendLines, legendLabels,
							loc=3,
							ncol=5,
							prop=matplotlib.font_manager.FontProperties(size=9),
							handlelength=3,
							bbox_to_anchor=(0., 1.02, 1., 1.02),
							mode='expand',
							borderaxespad=0.)
		d=[item for sublist in self.xaxis for item in sublist]
		begin=min(d)
		end=max(d)
		td=(end-begin)/6
		xtickDates = [begin, begin+td, begin+2*td, begin+3*td, begin+4*td, begin+5*td, end]
		xticks = map(lambda x: int(time.mktime(x.timetuple()) * 1000), xtickDates)
		xtickLabels = map(lambda x: x.astimezone(self.displayTZ).strftime("%m-%d\n%H:%M:%S"), xtickDates)

		axTopLeft.xaxis.set_ticks(xticks)
		axTopLeft.xaxis.set_ticklabels(xtickLabels)
		axTopLeft.set_xlim((xticks[0], xticks[-1]))

		self.pngBuffer=StringIO.StringIO()
		fig.set_dpi(80)
		dpi=fig.get_dpi()
		fig.set_size_inches(float(self.graphDims[0])/dpi, float(self.graphDims[1])/dpi)
		fig.savefig(self.pngBuffer, format="png", dpi=80)
		pyplot.close(fig)
		self.pngBuffer.seek(0)

	# Get the figure
	def getPNGBuffer(self):
		return self.pngBuffer

def plotterTest():
	data = [
			[dt.datetime.strptime("2011-06-09T18:46:21", '%Y-%m-%dT%H:%M:%S'),[3,5.5,6], [30.5,30.5,30.5], [.003,.003,.003]],
			[dt.datetime.strptime("2011-06-09T18:56:21", '%Y-%m-%dT%H:%M:%S'),[7,8.9,9], [50.2,50.2,50.2], [.004,.004,.004]],
			[dt.datetime.strptime("2011-06-09T18:58:21", '%Y-%m-%dT%H:%M:%S'),[12,12.34,13], [44,44.2,45], [.006,.007,.008]],
			[dt.datetime.strptime("2011-06-09T19:05:41", '%Y-%m-%dT%H:%M:%S'),[2,2.34,3], [12,12.8,13], [.009,.009,.009]],
			[dt.datetime.strptime("2011-06-09T19:55:41", '%Y-%m-%dT%H:%M:%S'),[1,2.34,3], [12,12.8,13], [.007,.009,.010]]
		]
	data2 = [
			[dt.datetime.strptime("2011-06-09T18:46:21", '%Y-%m-%dT%H:%M:%S'),[5.5,5.5,5.5],[30.5,30.5,30.5],[.003,.003,.003]],
			[dt.datetime.strptime("2011-06-09T18:56:21", '%Y-%m-%dT%H:%M:%S'),[8.9,8.9,8.9],[50.2,50.2,50.2],[.004,.004,.004]],
			[dt.datetime.strptime("2011-06-09T18:58:21", '%Y-%m-%dT%H:%M:%S'),[12.34,12.24,12.24],[44.2,44.2,44.2],[.007,.007,.007]],
			[dt.datetime.strptime("2011-06-09T18:59:21", '%Y-%m-%dT%H:%M:%S'),[2.34,2.34,2.34],[12.8,12.8,12.8],[.009,.009,.009]],
		]
	
	options={
			'axisColors':[['#FF0000', '#0010A5'], ['#FF6600', '#6300A5']],
			'axisLabels':[['Temperature (F)', 'Humidity (%)'], ['Wind Speed (MPH)', 'JFactor']],
			'seriesLabels':[['Top', 'Bottom', 'TopH'], ['Inline', 'Outlet', 'Inlet']],
			'dataAxisMap':[[0, 0, 1], [1, 1, 0]],
			'minMaxAreas':[[1, 1, 1], [1, 1, 1]]
		}
	
	p = Plotter(data, data2, options, (600, 400))
	#p = Plotter(data, None, options)
	import PIL
	im = PIL.Image.open(p.getPNGBuffer())
	im.show()

def plotterTest2():
	data = [
			[dt.datetime.strptime("2011-06-09T18:46:21", '%Y-%m-%dT%H:%M:%S'),[3,5.5,6], [30.5,30.5,30.5], [.003,.003,.003]],
			[dt.datetime.strptime("2011-06-09T18:56:21", '%Y-%m-%dT%H:%M:%S'),[7,8.9,9], [50.2,50.2,50.2], [.004,.004,.004]],
			[dt.datetime.strptime("2011-06-09T18:58:21", '%Y-%m-%dT%H:%M:%S'),[None, None, None], [None, None, None], [None, None, None]],
			[dt.datetime.strptime("2011-06-09T19:05:41", '%Y-%m-%dT%H:%M:%S'),[2,2.34,3], [12,12.8,13], [.009,.009,.009]],
			[dt.datetime.strptime("2011-06-09T19:55:41", '%Y-%m-%dT%H:%M:%S'),[1,2.34,3], [12,12.8,13], [.007,.009,.010]]
		]
	data2 = [
			[dt.datetime.strptime("2011-06-09T18:46:21", '%Y-%m-%dT%H:%M:%S'),[5.5,5.5,5.5],[30.5,30.5,30.5],[.003,.003,.003]],
			[dt.datetime.strptime("2011-06-09T18:56:21", '%Y-%m-%dT%H:%M:%S'),[8.9,8.9,8.9],[50.2,50.2,50.2],[.004,.004,.004]],
			[dt.datetime.strptime("2011-06-09T18:58:21", '%Y-%m-%dT%H:%M:%S'),[12.34,12.24,12.24],[44.2,44.2,44.2],[.007,.007,.007]],
			[dt.datetime.strptime("2011-06-09T18:59:21", '%Y-%m-%dT%H:%M:%S'),[2.34,2.34,2.34],[12.8,12.8,12.8],[.009,.009,.009]],
		]
	
	options={
			'axisColors':[['#FF0000', '#0010A5'], ['#FF6600', '#6300A5']],
			'axisLabels':[['Temperature (F)', 'Humidity (%)'], ['Wind Speed (MPH)', 'JFactor']],
			'seriesLabels':[['Top', 'Bottom', 'TopH'], ['Inline', 'Outlet', 'Inlet']],
			'dataAxisMap':[[0, 0, 1], [1, 1, 0]],
			'minMaxAreas':[[1, 1, 1], [1, 1, 1]]
		}
	
	#p = Plotter(data, data2, options, (600, 400))
	p = Plotter(data, None, options, (600, 400))
	import PIL
	im = PIL.Image.open(p.getPNGBuffer())
	im.show()

def plotterTest3():
	data = [
			[dt.datetime.strptime("2011-06-09T18:46:21", '%Y-%m-%dT%H:%M:%S'),[3,5.5,6]],
			[dt.datetime.strptime("2011-06-09T18:56:21", '%Y-%m-%dT%H:%M:%S'),[7,8.9,9]],
			[dt.datetime.strptime("2011-06-09T18:58:21", '%Y-%m-%dT%H:%M:%S'),[12,12.34,13]],
			[dt.datetime.strptime("2011-06-09T19:05:41", '%Y-%m-%dT%H:%M:%S'),[2,2.34,3]],
			[dt.datetime.strptime("2011-06-09T19:55:41", '%Y-%m-%dT%H:%M:%S'),[1,2.34,3]]
		]
	data2 = [
			[dt.datetime.strptime("2011-06-09T18:46:21", '%Y-%m-%dT%H:%M:%S'),[5.5,5.5,5.5],[30.5,30.5,30.5],[.003,.003,.003]],
			[dt.datetime.strptime("2011-06-09T18:56:21", '%Y-%m-%dT%H:%M:%S'),[8.9,8.9,8.9],[50.2,50.2,50.2],[.004,.004,.004]],
			[dt.datetime.strptime("2011-06-09T18:58:21", '%Y-%m-%dT%H:%M:%S'),[12.34,12.24,12.24],[44.2,44.2,44.2],[.007,.007,.007]],
			[dt.datetime.strptime("2011-06-09T18:59:21", '%Y-%m-%dT%H:%M:%S'),[2.34,2.34,2.34],[12.8,12.8,12.8],[.009,.009,.009]],
		]
	
	options={
			'axisColors':[['#FF0000', '#0010A5'], ['#FF6600', '#6300A5']],
			'axisLabels':[['Temperature (F)', 'Humidity (%)'], ['Wind Speed (MPH)', 'JFactor']],
			'seriesLabels':[['Top', 'Bottom', 'TopH'], ['Inline', 'Outlet', 'Inlet']],
			'dataAxisMap':[[0], [1, 1, 0]],
			'minMaxAreas':[[1], [1, 1, 1]]
		}
	
	p = Plotter(data, data2, options, (600, 400))
	#p = Plotter(data, None, options)
	import PIL
	im = PIL.Image.open(p.getPNGBuffer())
	im.show()


	
#plotterTest()
#plotterTest2()

#plotterTest3()

