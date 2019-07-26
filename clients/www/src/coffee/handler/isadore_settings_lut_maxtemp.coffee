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


class window.SettingsLUTMaxTemp
	constructor: () ->
		self=this
		@maxTempLightbox_ = new SettingsLUTMaxTempLightbox()
		$('#settings_new_lut_mc_maxtemp').click( () ->
			self.maxTempLightbox_.open(null, () -> self.refresh())
		)
		self.deleteDialog = new IsadoreDialog('#delete_lightbox', { width: 400, title: 'Delete Confirm' })
		
		
	updateTable_: () ->
		self=this
		$('#settings_lut_mc_maxtemp_spinner').hide()
		$('#settings_lut_mc_maxtemp_table').show()
		tableData = []
		for lut in @luts_
			tableData.push([lut.name, lut.hours_per_mc, HTMLHelper.actionButtons, lut.id])
		$('#settings_lut_mc_maxtemp_table').dataTable({
			bDestroy: true
			bPaginate: false
			bFilter: false
			aaData: tableData
			aoColumns: [
				{ sTitle: 'Name' }
				{ sTitle: 'Hrs/MCPt' }
				{ sTitle: 'Actions', bSortable: false }
				{ sTitle: 'data-lut_id', bVisible: false }
			]
			fnRowCallback: (nRow, aData, ididx, ididxf) ->
				nRow.setAttribute('data-lut_id', aData[3])
				$('td:eq(2)', nRow).addClass('action')
				return nRow
		})
		
		$('#settings_lut_mc_maxtemp_table span.action[data-action_type="edit"]').click((event) ->
			self.editLUT_(event)
		)
		$('#settings_lut_mc_maxtemp_table span.action[data-action_type="delete"]').click((event) ->
			self.deleteLUT_(event)
		)
		fixHeights()
		
	editLUT_: (event) ->
		self=this
		id=parseInt($(event.currentTarget).closest('tr').attr('data-lut_id'))
		@maxTempLightbox_.open(id, () -> self.refresh())
	
	deleteLUT_: (event) ->
		self=this
		id=_.parseInt($(event.currentTarget).closest('tr').attr('data-lut_id'))
		lut = _.findWhere(@luts_, {'id': id})
		$('#delete_lightbox_delete_spinner').hide()
		$('#delete_lightbox_delete').show()
		$('#delete_lightbox_cancel').show()
		$('#delete_lightbox h1:first').html('Delete MC Maxtemp LUT')
		$('#delete_lightbox_entry_info').html('LUT Name: '+lut.name)
		$('#delete_lightbox_delete').unbind('click')
		$('#delete_lightbox_delete').click(() -> self.deleteLUTConfirmed_(lut))
		$('#delete_lightbox_cancel').unbind('click')
		$('#delete_lightbox_cancel').click(() -> self.deleteDialog.close())
		self.deleteDialog.open();
		
	deleteLUTConfirmed_: (lut) ->
		self=this
		$('#delete_lightbox_delete').hide()
		$('#delete_lightbox_cancel').hide()
		$('#delete_lightbox_delete_spinner').show()
		$.ajax({
			url : '../resources/luts/mc_maxtemp/'+lut.id,
			type : 'DELETE',
			dataType : 'text',
			success : () -> self.deleteLUTDone_()
		})
	
	deleteLUTDone_: () ->
		self=this
		$('#delete_lightbox_delete_spinner').hide()
		$('#delete_lightbox_delete').show()
		$('#delete_lightbox_cancel').show()
		@refresh()
		self.deleteDialog.close()
		
		
	refresh: () ->
		self=this
		$('#settings_lut_mc_maxtemp_table').hide()
		$('#settings_lut_mc_maxtemp_spinner').show()
		$.ajax({
			url: '../resources/luts/mc_maxtemp-fast'
			type: 'GET'
			dataType: 'json'
			success: (d) ->
				self.luts_ = d.luts
				self.updateTable_()
		})
		
		
class window.SettingsLUTMaxTempLightbox
	constructor: () ->
		self=this
		$('#settings_luc_mc_maxtemp_edit_hours_per_mc').numeric({ negative: false })
		$('#settings_luc_mc_maxtemp_edit_more').click(() -> self.moreTable())
		$('#settings_lut_mc_maxtemp_edit_save').click(() -> self.save())
		self.lutDialog = new IsadoreDialog('#settings_lut_mc_maxtemp_lightbox', { width: 550, close: () -> self.close() })
	
	empty: () ->
		$('#settings_luc_mc_maxtemp_edit_hours_per_mc').val('')
		$('#settings_luc_mc_maxtemp_edit_name').val('')
		$('#settings_luc_mc_maxtemp_edit_table tbody').html('')
		
	update_: (lutId) ->
		self=this
		$('#settings_lut_mc_maxtemp_edit_open_spinner').show()
		$('#settings_lut_mc_maxtemp_lightbox_wrapper').hide()
		if lutId
			$.ajax({
				url: '../resources/luts/mc_maxtemp/'+lutId
				type: 'GET'
				dataType: 'json'
				success: (d) ->
					self.lut_ = d
					self.update2_()
			})
		else
			self.update2_()
		
	update2_: () ->
		self=this
		if @lut_
			$('#settings_luc_mc_maxtemp_edit_name').val(@lut_.name)
			$('#settings_luc_mc_maxtemp_edit_hours_per_mc').val(@lut_.hours_per_mc.toFixed(2))
			for v in @lut_.values
				$('#settings_luc_mc_maxtemp_edit_table tbody').append('<tr><td><input type="text"/></td><td><input type="text"/><td></tr>')
				inputs = $('#settings_luc_mc_maxtemp_edit_table tbody tr:last input')
				$(inputs[0]).val(v.mc.toFixed(2)).numeric({ negative: false })
				$(inputs[1]).val(v.maxtemp.toFixed(2)).numeric({ negative: false })
			
		@moreTable()
		$('#settings_lut_mc_maxtemp_edit_open_spinner').hide()
		$('#settings_lut_mc_maxtemp_lightbox_wrapper').show()
		cbResize()
			
	moreTable: () ->
		self=this
		for i in [0..5]
			$('#settings_luc_mc_maxtemp_edit_table tbody').append('<tr><td><input type="text"/></td><td><input type="text"/><td></tr>')
			inputs = $('#settings_luc_mc_maxtemp_edit_table tbody tr:last input')
			$(inputs[0]).numeric({ negative: false })
			$(inputs[1]).numeric({ negative: false })
		
		cbResize()

	close: () ->
		self=this
		if @closeCallback_
			@closeCallback_()
			
	save: () ->
		self=this
		$('#settings_lut_mc_maxtemp_lightbox .success').empty().stop().animate({ opacity: '100' }).stop()
		$('#settings_lut_mc_maxtemp_lightbox .errors').empty().show()
		
		name = $('#settings_luc_mc_maxtemp_edit_name').val()
		hours_per_mc = parseFloat($('#settings_luc_mc_maxtemp_edit_hours_per_mc').val())
		if not name
			$('#settings_lut_mc_maxtemp_lightbox .errors').html('Name is required.').show()
			return
		if isNaN(hours_per_mc)
			$('#settings_lut_mc_maxtemp_lightbox .errors').html('MC/hour is required.').show()
			return
		inputs = $('#settings_luc_mc_maxtemp_edit_table tbody input')
		mcs=[]
		maxtemps=[]
		for i in [0..inputs.length] by 2
			mc = parseFloat($(inputs[i]).val())
			maxtemp = parseFloat($(inputs[i+1]).val())
			if not isNaN(mc)and not isNaN(maxtemp)
				mcs.push(mc)
				maxtemps.push(maxtemp)
		
		adata = {
			name: name
			hours_per_mc: hours_per_mc
			mcs:mcs.join(',')
			maxtemps: maxtemps.join(',')
		}
		
		$('#settings_lut_mc_maxtemp_edit_save_spinner').show()
		$('#settings_lut_mc_maxtemp_edit_save').hide()
		$('#settings_lut_mc_maxtemp_lightbox input, #settings_luc_mc_maxtemp_edit_table button').attr('disabled', true)
		
		if not @lut_
			$.ajax({
				url: '../resources/luts/mc_maxtemp'
				type: 'POST'
				dataType: 'json'
				data: adata
				success: (d) ->
					lutId = d.xlink[0].split('/')[4]
					self.saveSuccess_(lutId)
				error: () ->
					self.saveFailed_()
			})
		else
			$.ajax({
				url: '../resources/luts/mc_maxtemp/'+@lut_.id
				type: 'PUT'
				dataType: 'text'
				data: adata
				success: (d) ->
					self.saveSuccess_(self.lut_.id)
				error: () ->
					self.saveFailed_()
			})
			
	saveSuccess_: (lutId) ->
		self=this
		$('#settings_lut_mc_maxtemp_edit_save_spinner').hide()
		$('#settings_lut_mc_maxtemp_edit_save').show()
		$('#settings_lut_mc_maxtemp_lightbox input, #settings_luc_mc_maxtemp_edit_table button').removeAttr('disabled')
		$('#settings_lut_mc_maxtemp_lightbox .success').html('Saved.').show().fadeOut(3000)
		@empty()
		@update_(lutId)
		
		
	saveFailed_: () ->
		self=this
		$('#settings_lut_mc_maxtemp_edit_save_spinner').hide()
		$('#settings_lut_mc_maxtemp_edit_save').show()
		$('#settings_lut_mc_maxtemp_lightbox input, #settings_luc_mc_maxtemp_edit_table button').removeAttr('disabled')
		$('#settings_lut_mc_maxtemp_lightbox .errors').html('Error occurred during saving.').show()
		cbResize()
	
	open: (lutId, closeCallback) ->
		self=this
		$('#settings_lut_mc_maxtemp_lightbox .errors').empty().show()
		@lut_ = null
		@closeCallback_ = closeCallback
		@empty()
		@update_(lutId)
		self.lutDialog.open()
