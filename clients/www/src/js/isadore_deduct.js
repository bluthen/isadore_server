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

function DeductionLightbox() {
	var self=this;
	var temp={};
	var workingDeduction = null;
	var dialog = null;
	var init = function() {
		$('#deduction_lightbox_begin').change(dateChanged);
		$('#deduction_lightbox_end').change(dateChanged);
		$('#deduction_lightbox_save').click(saveDeduction);
		dialog = new IsadoreDialog($('#deduction_lightbox'), {width: 600});
	};

	var dateChanged = function() {
		var bDate = $('#deduction_lightbox_begin').datetimepicker('getDate');
		var eDate = $('#deduction_lightbox_end').datetimepicker('getDate');
		if(bDate && eDate && !isNaN(bDate.getTime()) && !isNaN(eDate.getTime())) {
			$('#deduction_lightbox_mins').html(parseInt((eDate.getTime() - bDate.getTime())/(1000*60), 10));
		} else {
			$('#deduction_lightbox_mins').html('&nbsp;');
		}
	};
	
	var setSpinning = function(processing) {
		if(processing) {
			$('#deduction_lightbox_save').hide();
			$('#deduction_lightbox_save_spinner').show();
			$('#deduction_lightbox input').each(
				function(index, value) {
					$(value).attr('disabled', 'true');
				}
			);
		} else {
			$('#deduction_lightbox_save').show();
			$('#deduction_lightbox_save_spinner').hide();
			$('#deduction_lightbox input').each(
				function(index, value) {
					$(value).removeAttr('disabled');
				}
			);
		}
	};
	
	var deductionDone = function() {
		$('#deduction_lightbox_save_status').html('Saved.');
		dialog.close();
		pageHandlers.historical.refresh();
	};
	
	var saveDeduction = function() {
		var deductionArgs = {};
		var bDate = $('#deduction_lightbox_begin').datetimepicker('getDate');
		var eDate = null;
		var errors=[];
		if(!bDate || isNaN(bDate.getTime())) {
			errors.push('Start deduction date required.');
			bDate = null;
		}
		if($('#deduction_lightbox_end').val()) {
			eDate = $('#deduction_lightbox_end').datetimepicker('getDate');
			if(!eDate || isNaN(eDate.getTime())) {
				errors.push('End deduction must be in the correct format.');
				eDate = null;
			}
		} else {
			eDate = 'empty';
		}
		
		if(eDate && bDate && eDate != 'empty' && bDate > eDate) {
			errors.push("End date needs to after start date.");
		}

		var errorsDiv = $('#deduction_lightbox_overflow div.errors');
		errorsDiv.empty();
		if(errors.length > 0) {
			errorsDiv.append(HTMLHelper.makeList(errors));
			errorsDiv.show();
			cbResize();
			return;
		}
		errorsDiv.hide();
		deductionArgs.begin_datetime=HTMLHelper.dateToParamString(bDate);
		if(eDate) {
			deductionArgs.end_datetime=HTMLHelper.dateToParamString(eDate);
		}
		$('#deduction_lightbox_save_status').html('');
		

		setSpinning(true);
		if(!workingDeduction) {
			$.ajax({
				url : '../resources/data/air_deductions',
				type : 'POST',
				dataType : 'json',
				success : function(){
					deductionDone();
				},
				data : deductionArgs,
				error: function() {
					setSpinning(false);
					$('#deduction_lightbox_save_status').html('Error');
				}
			});
		} else {
			$.ajax({
				url : '../resources/data/air_deductions/'+workingDeduction.id,
				type : 'PUT',
				dataType : 'text',
				success : function(){
					deductionDone();
				},
				data : deductionArgs,
				error: function() {
					setSpinning(false);
					$('#deduction_lightbox_save_status').html('Error');
				}
			});
			
		}
	};
	
	this.open = function(deduction) {
		workingDeduction = deduction;
		$('#deduction_lightbox_begin, #deduction_lightbox_end').each(
			function(index, value) {
				$(value).val('');
			}
		);
		$('#deduction_lightbox_mins').html('&nbsp;');
		$('#deduction_lightbox_save_status').html('');
		$('#deduction_lightbox_overflow div.errors').empty();
		setSpinning(false);

		
		if (deduction) {
			$('#deduction_lightbox_begin').datetimepicker('setDate',
					(newDate(deduction.begin_datetime)));
			if(deduction.end_datetime) {
				$('#deduction_lightbox_end').datetimepicker('setDate',
					(newDate(deduction.end_datetime)));
			}
		}
		$('#deduction_lightbox_begin').change();
		dialog.open();

	};
	
	init();
}
