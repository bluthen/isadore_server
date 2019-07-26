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


function SettingsHandler() {
	var self=this;
	
	var account = null;
	var accounts=[];
	var accountsIdMap = {};
	var alarms=[];
	var alarm = null;
	var lutMaxTemp = null;
    var generalConfigConfig = null;
	
	var deleteDialog = new IsadoreDialog('#delete_lightbox', {width: 400, title: 'Delete Confirm'});
	var confirmDialog = new IsadoreDialog('#confirm_lightbox', {width: 400, title: 'Confirm'});
	var okDialog = new IsadoreDialog('#ok_lightbox', {width: 400});
	
	var init = function() {
		lutMaxTemp = new SettingsLUTMaxTemp();
		$('#new_account').click(function() {
			lightboxHandlers.accountLightbox.open();
		});
		$('#new_alarm').click(function() {
			lightboxHandlers.alarmLightbox.open(accounts);
		});
		$('#settings_device_clone_clone').click(function() {
			if (parseInt($('#settings_device_clone_from_year').val()) > 1900 &&
				parseInt($('#settings_device_clone_to_year').val()) > 1900 ) {
				cloneDevices();
			}
		});
		$('#settings_device_clone_from_year').numeric({decimal: false, negative: false});
		$('#settings_device_clone_to_year').numeric({decimal: false, negative: false});
	};
	
	var cloneDevices = function() {
		var fromyear, toyear;
		$('#confirm_lightbox_confirm_spinner').hide();
		$('#confirm_lightbox_confirm').show();
		$('#confirm_lightbox_cancel').show();
		$('#confirm_lightbox h1:first').html('Clone Device Configuration');
		fromyear = $('#settings_device_clone_from_year').val();
		toyear = $('#settings_device_clone_to_year').val();
		$('#confirm_lightbox_top').html('If cloned the configuration of '+toyear+' will be overriden.');
		$('#confirm_lightbox_entry_info').html(
				'Clone year ' + fromyear  + " into " + toyear);
		$('#confirm_lightbox_confirm').unbind('click');
		$('#confirm_lightbox_confirm').html('Clone');
		$('#confirm_lightbox_confirm').click(function() { cloneDevices2(); });
		$('#confirm_lightbox_cancel').unbind('click');
		$('#confirm_lightbox_cancel').click(function() {confirmDialog.close();});
		confirmDialog.open();
	};
	
	var cloneDevices2 = function() {
		$('#confirm_lightbox_confirm').hide();
		$('#confirm_lightbox_cancel').hide();
		$('#confirm_lightbox_confirm_spinner').show();
		fromYear = parseInt($('#settings_device_clone_from_year').val());
		toYear = parseInt($('#settings_device_clone_to_year').val());
		$.ajax({
			url : '../resources/conf/devices_clone',
			type : 'POST',
			data: {from_year: fromYear, to_year: toYear},
			dataType : 'text',
			success : cloneDevicesDone,
			error: cloneDevicesError
		});
	};
	
	var cloneDevicesDone = function () {
		$('#confirm_lightbox_confirm_spinner').hide();
		$('#confirm_lightbox_confirm').show();
		$('#confirm_lightbox_cancel').show();
		confirmDialog.close();
		$('#ok_lightbox_info').html('Device configuration was cloned.');
		$('#ok_lightbox_ok').html('Okay');
		$('#ok_lightbox_ok').unbind('click');
		$('#ok_lightbox_ok').click(function() {okDialog.close();});
		okDialog.open();
	};
	
	var cloneDevicesError = function () {
		$('#confirm_lightbox_confirm_spinner').hide();
		$('#confirm_lightbox_confirm').show();
		$('#confirm_lightbox_cancel').show();
		$('#error_dialog').html("Error: Unable to make clone.").dialog({
			zIndex: 99999,
			modal: true, 
			buttons: {
				Ok: function() { $(this).dialog('close');}
			}
		});
	};
	
	var editAccountClick = function(event) {
		var aid =$(event.currentTarget).closest('tr').attr('data-account_id');
		lightboxHandlers.accountLightbox.open(aid);
	};
	
	var editAlarmClick = function(event) {
		var aid = parseInt(_.parseInt($(event.currentTarget).closest('tr').attr('data-alarm_id')), 10);
		lightboxHandlers.alarmLightbox.open(accounts, _.findWhere(alarms, {'id': aid}));
	};

	
	var deleteAccountDone = function() {
		$('#delete_lightbox_delete_spinner').hide();
		$('#delete_lightbox_delete').show();
		$('#delete_lightbox_cancel').show();
		self.refresh();
		deleteDialog.close();
	};
	
	var deleteAccountConfirmClick = function() {
		$('#delete_lightbox_delete').hide();
		$('#delete_lightbox_cancel').hide();
		$('#delete_lightbox_delete_spinner').show();
		$.ajax({
			url : '../resources/accounts/'+account.id,
			type : 'DELETE',
			dataType : 'text',
			success : deleteAccountDone
		});
	};
	
	var deleteAccountClick = function(event) {
		$('#delete_lightbox_delete_spinner').hide();
		$('#delete_lightbox_delete').show();
		$('#delete_lightbox_cancel').show();
		var aid=parseInt($(event.currentTarget).closest('tr').attr('data-account_id'), 10);
		account = _.findWhere(accounts, {'id': aid});
		$('#delete_lightbox h1:first').html('Delete Account');
		$('#delete_lightbox_entry_info').html(
				'Account: ' + account.name + "&lt;" + account.email + '&gt;.');
		$('#delete_lightbox_delete').unbind('click');
		$('#delete_lightbox_delete').click(deleteAccountConfirmClick);
		$('#delete_lightbox_cancel').unbind('click');
		$('#delete_lightbox_cancel').click(function() {deleteDialog.close();});
		deleteDialog.open();
	};

	var deleteAlarmDone = function() {
		$('#delete_lightbox_delete_spinner').hide();
		$('#delete_lightbox_delete').show();
		$('#delete_lightbox_cancel').show();
		self.refresh();
		deleteDialog.close();
	};
	
	var deleteAlarmConfirmClick = function() {
		$('#delete_lightbox_delete').hide();
		$('#delete_lightbox_cancel').hide();
		$('#delete_lightbox_delete_spinner').show();
		$.ajax({
			url : '../resources/alarms/'+alarm.id,
			type : 'DELETE',
			dataType : 'text',
			success : deleteAlarmDone
		});
	};
	
	var deleteAlarmClick = function(event) {
		$('#delete_lightbox_delete_spinner').hide();
		$('#delete_lightbox_delete').show();
		$('#delete_lightbox_cancel').show();
		var aid= parseInt($(event.currentTarget).closest('tr').attr('data-alarm_id'), 10);
		alarm = _.findWhere(alarms, {'id': aid});
		$('#delete_lightbox h1:first').html('Delete Alarm');
		$('#delete_lightbox_entry_info').html(
				'Alarm: ' + IsadoreData.alarmTypesIdMap[alarm.alarm_type_id].name);
		$('#delete_lightbox_delete').unbind('click');
		$('#delete_lightbox_delete').click(deleteAlarmConfirmClick);
		$('#delete_lightbox_cancel').unbind('click');
		$('#delete_lightbox_cancel').click(function() {deleteDialog.close();});
		deleteDialog.open();
	};
	
	
	var refreshAccountsTable = function(filledArray) {
		var ii;
		accounts=filledArray;
		accountsIdMap= _.indexBy(accounts, 'id');
		var accountsData=[];
		for(ii = 0; ii < accounts.length; ++ii) {
			account = accounts[ii];
			a = [account.name, account.email, account.phone, IsadoreData.privilegesIdMap[account.privilege_id].name, HTMLHelper.actionButtons, account.id];
			accountsData.push(a);
		}
		$('#settings_account_settings_spinner').hide();
		$('#settings_account_settings_wrapper').show();
		$('#settings_accounts_table').dataTable({
			"sScrollY" : "140px",
			"bDestroy" : true,
			"bPaginate" : false,
			"bFilter" : false,
			"aaData" : accountsData,
			"aoColumns" : [
			  {'sTitle': 'Name'},
			  {'sTitle': 'Email'},
			  {'sTitle': 'Phone'},
			  {'sTitle': 'Account Type'},
			  {'sTitle': 'Actions', 'bSortable' : false},
			  {'sTitle': 'data-account_id', 'bVisible' : false} ],
			'fnRowCallback' : function(nRow, aData, ididx, ididxf) {
				nRow.setAttribute('data-account_id', aData[5]);
				return nRow;
			}
		});
		$('#settings_accounts_table span.action[data-action_type="edit"]').click(editAccountClick);
		$('#settings_accounts_table span.action[data-action_type="delete"]').click(deleteAccountClick);
		fixHeights();
		
		//Update alarms
		IsadoreData.getDataAll({
			url: '../resources/alarms',
			callbacks: refreshAlarmsTable
		});
	};
	
	var refreshAlarmsTable = function(fillArray) {
		var ii, alarmsData, alarm, account, alarmType, name, ineq, contacts, jj, alarmContactTypeId;
		alarms=fillArray;
		alarmsData = [];
		for(ii = 0; ii < alarms.length; ++ii) {
			alarm = alarms[ii];
			account = accountsIdMap[alarm.account_id];
			if(account) {
				alarmType = IsadoreData.alarmTypesIdMap[alarm.alarm_type_id];
				name=alarmType.name;
				if(alarmType.threshold_p) {
					ineq = '&lt;';
					if(alarm.greater_than_p) {
						ineq = '&gt;';
					}
					name=name + ' '+ineq+' '+alarm.value.toFixed(2);
				}
				contacts = [];
				for(jj = 0; jj < alarm.alarm_contact_type_ids.length; ++jj) {
					alarmContactTypeId = alarm.alarm_contact_type_ids[jj];
					contacts.push(IsadoreData.alarmContactTypesIdMap[alarmContactTypeId].name);
				}
				alarmsData.push([name, account.name, contacts.join(', '), HTMLHelper.actionButtons, alarm.id]);
			}
		}
		$('#settings_alarms_wrapper').show();
		$('#settings_alarms_spinner').hide();
		$('#settings_alarms_table').dataTable({
			"sScrollY" : "150px",
			"bDestroy" : true,
			"bPaginate" : false,
			"bFilter" : false,
			"aaData": alarmsData,
			'aoColumns': [
			  {'sTitle': 'Alarm'},
			  {'sTitle': 'Contact'},
			  {'sTitle': 'Delivery'},
			  {'sTitle': 'Actions', 'bSortable': false},
			  {'sTitle': 'data-alarm_id', 'bVisible' : false}
			],
			'fnRowCallback' : function(nRow, aData, ididx, ididxf) {
				nRow.setAttribute('data-alarm_id', aData[4]);
				return nRow;
			}
		});
		$('#settings_alarms_table span.action[data-action_type="edit"]').click(editAlarmClick);
		$('#settings_alarms_table span.action[data-action_type="delete"]').click(deleteAlarmClick);
		fixHeights();
	};

	var refreshData = function() {
		$('#settings_account_settings_wrapper').hide();
		$('#settings_account_settings_spinner').show();
		$('#settings_alarms_wrapper').hide();
		$('#settings_alarms_spinner').show();
		if(IsadoreData.selfAccount.hasPrivilege('Power User')) {
			IsadoreData.getDataAll({
				url: '../resources/accounts', 
				callbacks: refreshAccountsTable
			});
		} else {
			accounts=[IsadoreData.selfAccount];
			accountsIdMap={};
			accountsIdMap[accounts[0].id]=accounts[0];
			//Update alarms
			IsadoreData.getDataAll({
				url: '../resources/alarms',
				callbacks: refreshAlarmsTable
			});
		}
        if(IsadoreData.selfAccount.hasPrivilege('Super User')) {
            if (!generalConfigConfig) {
                generalConfigConfig = new GeneralConfigConfig($('#content_settings'))
            }
            generalConfigConfig.refresh()
        }
	};
	
	this.refresh = function() {
		lutMaxTemp.refresh();
		if(!$('#content_settings').is(':visible')) {
			return;
		}
		$('#menu_settings').removeClass('unselected');
		$('#menu_settings').addClass('selected');

		refreshData();
	};
	init();
}
