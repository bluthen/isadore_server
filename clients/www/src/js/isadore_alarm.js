//   Copyright 2010-2019 Dan Elliott, Russell Valentine
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.

function AlarmLightbox() {
	var self = this;
	var accounts = [];
	var changed = false;
	var alarm = null;
	var dialog = null;

	var init = function() {
		dialog = new IsadoreDialog($('#alarm_lightbox'), {width: 700, height: 325, close: dialogClosed});
		$('#alarm_lightbox_save').click(saveAlarm);
		$('#alarm_lightbox_cancel').click(function() { dialog.close(); });
	};

	var saveAlarmSpinner = function(processing) {
		if(processing) {
			$('#alarm_lightbox_save_spinner').show();
			$('#alarm_lightbox_save').hide();
			$('#alarm_lightbox_cancel').hide();
			$('#alarm_lightbox select, #alarm_lightbox input').each(
				function (index, value) {
					$(value).attr('disabled', 'true');
				});
		} else {
			$('#alarm_lightbox_save_spinner').hide();
			$('#alarm_lightbox_save').show();
			$('#alarm_lightbox_cancel').show();
			$('#alarm_lightbox select, #alarm_lightbox input').each(
				function (index, value) {
					$(value).removeAttr('disabled');
				}
			);
		}
	};
	
	var dialogClosed = function() {
		if(changed) {
			pageHandlers.settings.refresh();
		}
	};
	
	var saveAlarmDone = function() {
		changed = true;
		dialog.close();
		saveAlarmSpinner(false);
	};
	
	var saveAlarm = function() {
		var parameters = {};
		var alarm_type_id = $('#alarm_lightbox_type').val();
		var alarmType = IsadoreData.alarmTypesIdMap[alarm_type_id];
		parameters.alarm_type_id = alarmType.id;
		parameters.account_id = $('#alarm_lightbox_account').val();
		errors=[];
		if(alarmType.threshold_p) {
			parameters.greater_than_p = $('#alarm_lightbox_condition').val();
			parameters.value=parseFloat($('#alarm_lightbox_value').val());
			if(isNaN(parameters.value)) {
				errors.push('Value must be a number.');
			}
		}
		var alarm_contact_type_ids = [];
		$('#alarm_lightbox_contact_types input[type="checkbox"]:checked').each(
			function(index, value) {
				alarm_contact_type_ids.push($(value).val());
			}
		);
		if(alarm_contact_type_ids.length > 0) {
			parameters.alarm_contact_type_ids = alarm_contact_type_ids.join(',');
		} else {
			errors.push('At least one contact type must be selected.');
		}
		var errorsDiv = $('#alarm_lightbox div.errors');
		errorsDiv.empty();
		if(errors.length > 0) {
			errorsDiv.append(HTMLHelper.makeList(errors));
			errorsDiv.show();
			return;
		}
		errorsDiv.hide();
		
		saveAlarmSpinner(true);
		if(alarm) {
			$.ajax({
				url: '../resources/alarms/'+alarm.id,
				type: 'PUT',
				dataType: 'text',
				success: saveAlarmDone,
				data: parameters
			});
		} else {
			$.ajax({
				url : '../resources/alarms',
				type : 'POST',
				dataType : 'json',
				success : saveAlarmDone,
				data : parameters
			});
		}
	};
	
	var alarmTypeChange = function() {
		var alarmTypeId = $('#alarm_lightbox_type').val();
		var alarmType = IsadoreData.alarmTypesIdMap[alarmTypeId];
		if(alarmType.threshold_p) {
			$('#alarm_lightbox_threshold_options').show();
		} else {
			$('#alarm_lightbox_threshold_options').hide();
		}
	};

	var setupAlarmContactTypes = function() {
		var html = [], ii = 0;
		for(ii = 0; ii < IsadoreData.alarmContactTypes.length; ++ii) {
			act = IsadoreData.alarmContactTypes[ii];
			html.push('<input type="checkbox" value="'+act.id+'" id="alarm_lightbox_contact_types_'+act.id+'" />');
			html.push('<label for="alarm_lightbox_contact_types_'+act.id+'">');
			html.push(act.name);
			html.push('</label>');
		}
		$('#alarm_lightbox_contact_types').html(html.join(''));
	};
	
	var setDefaultValues = function() {
		var alarmType, ii;
		if (alarm) {
			$('#alarm_lightbox_type').val(alarm.alarm_type_id);
			alarmType = IsadoreData.alarmTypesIdMap[alarm.alarm_type_id];
			if (alarmType.threshold_p) {
				$('#alarm_lightbox_condition').val(alarm.greater_than_p);
				$('#alarm_lightbox_value').val(alarm.value);
			} else {
				$('#alarm_lightbox_condition').val('true');
				$('#alarm_lightbox_value').val('');
			}
			$('#alarm_lightbox_account').val(alarm.account_id);
			for (ii = 0; ii < alarm.alarm_contact_type_ids.length; ++ii) {
				$('#alarm_lightbox_contact_types_'+ alarm.alarm_contact_type_ids[ii]).prop("checked", true);
			}
		} else {
			$('#alarm_lightbox_condition').val('true');
			$('#alarm_lightbox_value').val('');
		}
	};
	
	
	this.open = function(gaccounts, galarm) {
		var errorsDiv, alarmTypesSelect, alarmAccount;
		alarm=galarm;
		accounts=gaccounts;
		changed = false;
		saveAlarmSpinner(false);
		errorsDiv = $('#alarm_lightbox div.errors');
		errorsDiv.empty().hide();
		if(alarm) {
			dialog.setTitle('Edit Alarm');
		} else {
			dialog.setTitle('Add Alarm');
		}
		//Alarm Types
		alarmTypesSelect = HTMLHelper.makeSelect(IsadoreData.alarmTypes, 'name', 'id');
		$(alarmTypesSelect).attr('id', 'alarm_lightbox_type');
		$('#alarm_lightbox_type').replaceWith(alarmTypesSelect);
		alarmTypesSelect.change(alarmTypeChange);
		
		
		setupAlarmContactTypes();
		alarmAccount = HTMLHelper.makeSelect(accounts, 'name', 'id');
		alarmAccount.attr('id', 'alarm_lightbox_account');
		$('#alarm_lightbox_account').replaceWith(alarmAccount);
		setDefaultValues();
		alarmTypesSelect.change();
		if (!dialog.isOpen()) {
			dialog.open();
		}
	};
	
	init();
}
