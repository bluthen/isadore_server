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

function AccountLightbox() {
	var self=this;
	var account = null;
	var changed = false;
	var dialog = null;
	var init = function() {
		$('#account_lightbox_cancel, #account_lightbox_done_close').click(function() {
			dialog.close();
		});
		$('#account_lightbox_save').click(saveAccount);
		dialog = new IsadoreDialog($('#account_lightbox'), {width: 700, close: dialogClosed});
	};

	var saveAccountSpinning = function(processing) {
		if(processing) {
			$('#account_lightbox_save_spinner').show();
			$('#account_lightbox_save').hide();
			$('#account_lightbox_cancel').hide();
			$('#account_lightbox_active input, #account_lightbox_active select').each(
				function(index, value) {
					$(value).attr('disabled', 'true');
				});
		} else {
			$('#account_lightbox_save_spinner').hide();
			$('#account_lightbox_save').show();
			$('#account_lightbox_cancel').show();
			$('#account_lightbox_active input, #account_lightbox_active select').each(
				function(index, value) {
					$(value).removeAttr('disabled');
				});
		}
	};
	
	var saveAccountDone = function() {
		changed=true;
		saveAccountSpinning(false);
		if(!account) {
			$('#account_lightbox_done_new').show();
		} else {
			$('#account_lightbox_done_new').hide();
		}
		$('#account_lightbox_done').show();
		$('#account_lightbox_active').hide();
		console.info('account save done');
	};
	
	var saveAccount = function() {
		var accountArgs = {
			'name' : $('#account_lightbox_name').val().trim(),
			'email' : $('#account_lightbox_email').val().trim(),
			'privilege_id' : parseInt($('#account_lightbox_privilege').val(), 10)
		};
		
		var errors = [];
		if(!accountArgs.name) {
			errors.push('Name is required.');
		}
		if(!accountArgs.email || !HTMLHelper.validEmail(accountArgs.email)) {
			errors.push('Email is required and must be a valid email address.');
		}
		
		//Phone is optional
		var phone = $('#account_lightbox_phone').val().trim();
		var phoneP = HTMLHelper.phoneToParam(phone);
		if (phone && !phoneP) {
			errors.push('Phone number need to be a 11 digit phone number.');
		} else if (phoneP) {
			accountArgs.phone = phoneP;
		}
		
		var errorsDiv = $('#account_lightbox div.errors');
		errorsDiv.empty();
		if(errors.length > 0) {
			errorsDiv.append(HTMLHelper.makeList(errors));
			errorsDiv.show();
			return;
		}
		errorsDiv.hide();
		saveAccountSpinning(true);
		if(account) {
			//Update
			$.ajax({
				url: '../resources/accounts/'+account.id,
				type: 'PUT',
				dataType: 'text',
				success: saveAccountDone,
				data: accountArgs
			});
		} else {
			//New
			$.ajax({
				url: '../resources/accounts',
				type: 'POST',
				dataType: 'text',
				success: saveAccountDone,
				data: accountArgs
			});
		}
	};
	
	var refresh = function() {
		if(account) {
			$('#account_lightbox h1').html('Edit Account');
			$('#account_lightbox_name').val(account.name);
			$('#account_lightbox_email').val(account.email);
			$('#account_lightbox_phone').val(HTMLHelper.phoneToReadable(account.phone)); //Format
			$('#account_lightbox_privilege').val(account.privilege_id);
		} else {
			$('#account_lightbox h1').html('Add Account');
			$('#account_lightbox_name').val('');
			$('#account_lightbox_email').val('');
			$('#account_lightbox_phone').val('');
			$('#account_lightbox_privilege').val('User');
		}
	};
	
	var dialogClosed = function() {
		if(changed) {
			pageHandlers.settings.refresh();
		}
	};
	
	var open2 = function() {
		refresh();
		dialog.open();
	};
	
	this.open = function(accountId) {
		changed=false;
		var privSelect = HTMLHelper.makeSelect(IsadoreData.privileges, 'name', 'id');
		privSelect.attr('id', 'account_lightbox_privilege');
		$('#account_lightbox_privilege').replaceWith(privSelect);
		$('#account_lightbox div.errors').empty().hide();
		$('#account_lightbox_done').hide();
		$('#account_lightbox_active').show();
		saveAccountSpinning(false);

		if(!accountId) {
			account = null;
			open2();
			return;
		}
		//Get account call open2 after
		$.ajax({
			url: '../resources/accounts/'+accountId,
			type: 'GET',
			dataType: 'json',
			success: function(acc) {
				account=acc;
				open2();
			}
		});
		
	};
	
	init();
}
