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

function ControlTab() {
	var self=this;
	var devices = [];
	var currentBin = null;
	var controls = []; //device, sensor, control_data
	var temp={};
	var init = function() {
		$('#bin_lightbox_control_save').click(saveControls);
	};
	
	var saveControlsSpinner = function(processing) {
		if(processing) {
			$('#bin_lightbox_control_save').hide();
			$('#bin_lightbox_control_save_spinner').show();
			$('#bin_lightbox_control_exist input').each(
				function(index, value) {
					$(value).attr('disabled', 'true');
				});
		} else {
			$('#bin_lightbox_control_save').show();
			$('#bin_lightbox_control_save_spinner').hide();
		}
	};
	
	var saveControls = function(event) {
		var mParams, errorDiv, ii, valueStr, value, controlsSuccessFunc;
		
		mParams = [];
		errorDiv = $('#bin_lightbox_control_exist div.errors');
		for(ii = 0; ii < controls.length; ++ii) {
			valueStr = $('#bin_lightbox_control_set_'+controls[ii][1].id).val().trim();
			value = parseFloat(valueStr);
			if(valueStr && isNaN(value)) {
				errorDiv.html('Values must be blank or a number.');
				errorDiv.show();
				return;
				//TODO: Error must have numbers
			} else if(value) {
				mParams.push({'sensor_id': controls[ii][1].id, 'value': value});
			}
		}
		errorDiv.hide();

		if(mParams.length == 0) {
			return;
		}
		
		temp.saveControlsSize = mParams.length;
		temp.saveControlsCount = 0;
		saveControlsSpinner(true);
		
		controlsSuccessFunc = function(d) {
			temp.saveControlsCount++;
			if(temp.saveControlsCount == temp.saveControlsSize) {
				self.refresh(currentBin);
			}
		};
		for(ii = 0; ii < mParams.length; ++ii) {
			$.ajax({
				url : '../resources/controls',
				type: 'POST',
				dataType: 'json',
				success: controlsSuccessFunc,
				data: mParams[ii]
			});
		}
	};
	
	var getControl2 = function(c, control) {
		if(c.length > 0) {
			control.push(c[0]);
		} else {
			control.push(null);
		}
		temp.controlCount++;
		if(temp.controlCount == temp.controlSize) {
			refresh2();
		}
	};
	
	var getControls = function(d) {
		var ii, jj, device, sensor, sensorType;
		devices=d;
		controls=[];
		temp.controlCount = 0;
		for(ii = 0; ii < devices.length; ++ii) {
			device = devices[ii];
			for(jj = 0; jj < device.sensors.length; ++jj) {
				sensor = device.sensors[jj];
				sensorType = IsadoreData.sensorTypesIdMap[sensor.sensor_type_id];
				if(sensorType.controllable) {
					// Currently only support reals
					control = [device, sensor];
					controls.push(control);
				}
			}
		}
		if (controls.length > 0) {
			temp.controlSize = controls.length;
			temp.controlCount = 0;
			for (ii = 0; ii < controls.length; ++ii) {
				control = controls[ii];
				IsadoreData.getDataAll({
					url:'../resources/controls/last', 
					callbacks: getControl2, 
					parameters: {'sensor_id' : control[1].id}, //Sensor id
					extraArgs: control
				});
			}
		} else {
			refresh2();
		}
	};
	
	var refresh2 = function(d) {
		var html, controllableFound, ii;
		devices=d;
		html=[];
		controllableFound = false;
		for(ii = 0; ii < controls.length; ++ii) {
			controllableFound = true;
			control=controls[ii];
			device = control[0];
			sensor = control[1];
			sensorType = IsadoreData.sensorTypesIdMap[sensor.sensor_type_id];
			deviceType = IsadoreData.deviceTypesIdMap[device.device_type_id];
			controlStatus = control[2];
			devName = deviceType.name;
			binName = IsadoreData.binSectionsIdMap[device.bin_section_id].name;
			senName = sensorType.name;
			html.push('<h2>');
			html.push(devName+' - '+binName);
			html.push('</h2>');
			html.push('<div class="float"><div class="label"><label for="bin_lightbox_control_set_'+sensor.id+'">');
			html.push(senName);
			html.push('</label></div>');
			html.push('<input type="text" class="control_set" id="bin_lightbox_control_set_'+sensor.id+'" data-sensor_id="'+sensor.id+'" />');
			html.push('</div>');
			
			html.push('<div class="float"><div class="label"><label>Last Set Value');
			html.push('</label>');
			html.push('</div>');
			if(controlStatus) {
				html.push(controlStatus.value.toFixed(2));
			} else {
				html.push('None');
			}
			html.push('</div>');
			
			html.push('<div class="float"><div class="label"><label>Last Submit Time</label></div>');
			if(controlStatus) {
				html.push(HTMLHelper.dateToReadableO2(newDate(controlStatus.posted_datetime)));
			} else {
				html.push('None');
			}
			html.push('</div>');
			
			html.push('<div class="float"><div class="label"><label>Processed</label></div>');
			if(controlStatus && controlStatus.fetched_datetime) {
				html.push('Recieved</br>');
				html.push(HTMLHelper.dateToReadableO2(newDate(controlStatus.fetched_datetime)));
			} else {
				html.push('Not Recieved');
			}
			html.push('</div>');
			html.push('<div class="clears"></div>');
		}
		if(controllableFound) {
			$('#bin_lightbox_control_fields').html(html.join(''));
			$('#bin_lightbox_control_noexist').hide();
			$('#bin_lightbox_control_exist').show();
			$('#bin_lightbox_control_spinner').hide();
		} else {
			$('#bin_lightbox_control_noexist').show();
			$('#bin_lightbox_control_exist').hide();
			$('#bin_lightbox_control_spinner').hide();
		}
		cbResize();
	};
	
	this.refresh = function(bin) {
		var errorDiv;
		currentBin = bin;
		devices=[];
		saveControlsSpinner(false);
		errorDiv = $('#bin_lightbox_control_exist div.errors');
		errorDiv.hide();
		$('#bin_lightbox_control_noexist').hide();
		$('#bin_lightbox_control_exist').hide();
		$('#bin_lightbox_control_spinner').show();
		IsadoreData.getDevices(bin.id, getControls);
	};
	init();
}
