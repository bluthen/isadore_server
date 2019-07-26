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

class window.IsadoreDialog
	constructor: (element, options) ->
		self=this
		self.element = $(element)
		if options.autoOpen == undefined
			options.autoOpen = false
#		if options.zIndex == undefined
#			options.zIndex = 9999
		if options.modal == undefined
			options.modal = true
		if options.closeOnEscape == undefined
			options.closeOnEscape = true
		if options.resizable == undefined
			options.resizable = false
		self.element.dialog(options)

	destroy: () ->
		self=this
		self.element.dialog('destroy')
		return self

	open: () ->
		self=this
		self.element.dialog('open')
		return self

	close: () ->
		self=this
		self.element.dialog('close')
		return self

	setTitle: (title) ->
		self=this
		self.setOption('title', title)
		return self
		
	isOpen: () ->
		self=this
		return self.element.dialog('isOpen')

	# @param width null for auto, 0 to leave unchanged, > 0 to set manually
	# @param height See width
	resize: (width, height) ->
		self=this
		# TODO: If no width and height auto detect?
		if width == null
			width = self.element.innerWidth()
		if height == null
			height = self.element.innerHeight()
		if width > 0
			self.setOption('width', width)
		if height > 0
			self.setOption('height', height)
		return self
		
	bind: (event, method) ->
		self=this
		self.element.on(event, method)
		return self
		
	getOption: (name) ->
		self=this
		return self.element.dialog('option', name)

	setOption: (name, value) ->
		self=this
		self.element.dialog('option', name, value)
		return self
