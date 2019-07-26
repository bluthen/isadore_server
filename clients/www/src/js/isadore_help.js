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

function HelpHandler() {
	var self = this;
	var emailErrorsDiv = null;
	var pastEvents = [];
	var allAlarms=[];
	var init = function() {
		manualURL='http://exotericanalytics.com/IsadoreOperationsManual_generic.pdf';
		emailErrorsDiv = $('#help_contact div.errors');
		$('#help_contact_clear').click(clearEmail);
		$('#help_contact_send').click(sendEmail);
		$('#help_user_manual').show();
		$('#help_user_manual a').attr('href', manualURL);
		$('#help_user_manual button').click(function() {
			window.location=manualURL;
		});
	};
	
	var sendEmailDone = function() {
		sendEmailSpinner(false);
		clearEmail();
		$('#help_contact_send_status').html('Email Sent');
	};
	
	var sendEmailFail = function() {
		sendEmailSpinner(false);
		$('#help_contact_send_status').html('Failure, email not sent.');
	};
	
	var sendEmailSpinner = function(processing) {
		if(processing) {
			$('#help_contact_spinner').show();
			$('#help_contact_send').hide();
			$('#help_contact_clear').hide();
			$('#help_contact input, #help_contact textarea').each(
				function(index, value) {
					$(value).attr('disabled', 'true');
				});
		} else {
			$('#help_contact_spinner').hide();
			$('#help_contact_send').show();
			$('#help_contact_clear').show();
			$('#help_contact input, #help_contact textarea').each(
				function(index, value) {
					$(value).removeAttr('disabled');
				});
		}
	};

	var sendEmail=function() {
		$('#help_contact_send_status').empty();
		parameters={
			'name': $('#help_contact_name').val(),
			'email': $('#help_contact_email').val(),
			'subject': $('#help_contact_subject').val(),
			'message': $('#help_contact_message').val()
		};
		if(!parameters.message) {
			emailErrorsDiv.html('Message is required.').show();
			return;
		}
		emailErrorsDiv.hide();
		sendEmailSpinner(true);
		$.ajax({
			url: '../resources/contact',
			type: 'POST',
			dataType: 'text',
			success: sendEmailDone,
			error: sendEmailFail,
			data: parameters
		});
	};
	
	var clearEmail=function() {
		emailErrorsDiv.hide();
		$('#help_contact_name').val(IsadoreData.selfAccount.name);
		$('#help_contact_email').val(IsadoreData.selfAccount.email);
		$('#help_contact_subject').val('');
		$('#help_contact_message').val('');
	};
	
	var refreshAlarms = function() {
		var alarms, alarm, event, alarmObj, ii;
		//TODO: Add non-current alarms to.
		alarms=[];
		for(ii = 0; ii < IsadoreData.currentAlarmEvents.length; ++ii) {
			alarm = ["NA", "-", "-"];
			event = IsadoreData.currentAlarmEvents[ii];
			if(event.alarm_id) {
				alarmObj = _.findWhere(allAlarms, {'id': event.alarm_id});
				if(alarmObj) {
					if(alarmObj.alarm_type_id==14) {
						alarm[0]=IsadoreData.alarmTypesIdMap[alarmObj.alarm_type_id].name;
						if(alarmObj.greater_than_p) {
							alarm[0] += " &gt; ";
						} else {
							alarm[0] += " &lt; ";
						}
						alarm[0]+= alarmObj.value.toFixed(2);
					} else {
						alarm[0]=IsadoreData.alarmTypesIdMap[alarmObj.alarm_type_id].name;
						if (event.extra_info) {
							alarm[0]+=event.extra_info;
						}
					}
				}
			} else {
				alarm[0]=IsadoreData.alarmTypesIdMap[event.alarm_type_id].name;
				if (event.extra_info) {
					alarm[0]+=event.extra_info;
				}
			}
			alarm[1]=HTMLHelper.dateToReadableO2(newDate(event.begin_datetime));
			if(event.end_datetime) {
				alarm[2]=HTMLHelper.dateToReadableO2(newDate(event.end_datetime));
			} else {
				alarm[2]="-";
			}
			alarms.push(alarm);
		}
		for(ii = 0; ii < pastEvents.length; ++ii) {
			alarm = ["NA", "-", "-"];
			event = pastEvents[ii];
			alarm[0]=IsadoreData.alarmTypesIdMap[event.alarm_type_id].name;
			if (event.extra_info) {
				alarm[0]+=event.extra_info;
			}
			alarm[1]=HTMLHelper.dateToReadableO2(newDate(event.begin_datetime));
			if(event.end_datetime) {
				alarm[2]=HTMLHelper.dateToReadableO2(newDate(event.end_datetime));
			} else {
				alarm[2]="-";
			}
			alarms.push(alarm);
		}
		$('#help_alarms').show();
		$('#help_alarms_spinner').hide();
		$('#help_alarms_table').dataTable({
			"sScrollY": "200px",
			"bPaginate": false,
			"bDestroy": true,
			"bFilter": false,
			"aaData": alarms,
			"aoColumns": [
			  {'sTitle': 'Alarm'},
			  {'sTitle': 'Started'},
			  {'sTitle': 'Stopped'}
			],
			'fnRowCallback': function(nRow, aData, ididx, ididxf) {
				if(aData[2] == '-') {
					$(nRow).addClass("red");
				}
				return nRow;
			},
			"aaSorting": [[1, 'desc']]
		});
		$('#content_help .dataTables_info').hide();
	};
	
	this.refresh = function() {
		$('#help_contact_send_status').empty();
		sendEmailSpinner(false);
		if (!$('#content_help').is(':visible')) {
			return;
		}
		$('#menu_help').removeClass('unselected');
		$('#menu_help').addClass('selected');
		// $('#help_errors_table').dataTable({
		// "sScrollY" : "140px",
		// "bDestroy" : true,
		// "bPaginate" : false,
		// "bFilter" : false,
		// "aoColumnDefs" : [ {
		// "bSortable" : false,
		// "aTargets" : [ 4 ]
		// } ]
		//	});
		clearEmail();
		year = new Date().getFullYear();
		afterDatetime = new Date(year, 0, 1, 0, 0, 0, 0);
		pastEvents=[];
		$('#help_alarms').hide();
		$('#help_alarms_spinner').show();
		$.ajax({
			url: '../resources/alarms-fast',
			type: 'GET',
			dataType: 'json',
			error: function () { refreshAlarms(); },
			success: function (d)  {
				allAlarms = d.alarms;
				$.ajax({
					url: '../resources/alarms/pastEvents-fast',
					type: 'GET',
					dataType: 'json',
					data: {'after_datetime': HTMLHelper.dateToParamString(afterDatetime)},
					error: function () { refreshAlarms(); },
					success: function (de) {
						pastEvents=de.events;
						refreshAlarms();
					}
				});
			}
		});
	};
	
	init();
}
