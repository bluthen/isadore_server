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


loginSuccess = ->
	console.log("Login good.")
	#TODO: Do check till success then go to main.
	window.location.replace("./main.html")
	
loginSuccessCheck = ->
	$.ajax({
		url : "../resources/login/check"
		type : 'POST'
		success : loginSuccess
		error : () ->
			setTimeout(loginSuccessCheckFail, 3000)
	})
	
loginSuccessCheckFail = ->
	if window.lsc_count == undefined
		window.lsc_count = 0
	else
		window.lsc_count = window.lsc_count+1
	if window.lsc_count > 2
		window.lsc_count = 0
		login()
	else
		loginSuccessCheck()
		
	
loginFailed = (xhr, status) ->
	$('#login').show()
	$('div.login_button img.spinner').hide()
	if xhr.status == 401
		$('#login401').show()
	else if xhr.status == 0
		$('#loginOther').html('Unable to contact server, check network connection.').show()
	else
		$('#loginOther').html('Error: '+xhr.status+", "+ status).show()

login = ->
	$('div.errors').hide()
	$('#login').hide()
	$('#good').hide()
	$('div.login_button img.spinner').show()
	email = $('#email').val()
	password = $('#password').val()
	parameters = {
		'email': $.trim(email),
		'password': $.trim(password),
		'remember' : $('#remember').is(':checked')
	}
	$.ajax({
		url : "../resources/login"
		type : 'POST'
		success : loginSuccessCheck
		error : loginFailed
		data : parameters
	})

cookieLoginCheck = ->
	email = $.cookie('exemail')
	hash = $.cookie('exrhash')
	if email and hash
		$.ajax({
			url : "../resources/login/check"
			type : 'POST'
			success : loginSuccess
			error : checkFailed
		})
	else
		checkFailed()
	

checkFailed = ->
	$('#spinner_step').hide()
	h = window.location.hash or '#login_step'
	if h != '#fs1' and h != '#fs2'
		$('#login_step').show()
	$('#email').focus()
	window.cookieCheck=true

fs1ContinueClick = ->
	if not $('#forgot_step1_email').val()
		$('#forgot_step1_error').html("Email address is required.")
		$('#forgot_step1_error').show()
		return
	$('div.errors').hide()
	$('#forgot_step1_continue').hide()
	$('div.login_button img.spinner').show()
	$.ajax({
		url : "../resources/accounts/recover"
		type: 'POST'
		success : () ->
			$('div.errors').hide()
			$('#forgot_step1_continue').show()
			$('div.login_button img.spinner').hide()
			window.location.replace("#fs2")
		error: (jqXHR, statusText, errorThrown) ->
			$('div.login_button img.spinner').hide()
			$('#forgot_step1_continue').show()
			$('#forgot_step1_error').html(jqXHR.responseText)
			$('#forgot_step1_error').show()
		data: {'email': $.trim($('#forgot_step1_email').val())}
	})

fs2ContinueClick = ->
	if not $('#forgot_step2_code').val()
		$('#forgot_step2_error').html("Code is required.")
		$('#forgot_step2_error').show()
		return
	if !$('#forgot_step2_password').val() or $('#forgot_step2_password').val() != $('#forgot_step2_password_retype').val()
		$('#forgot_step2_error').html("Re-typed password does not match.")
		$('#forgot_step2_error').show()
		return
	$('div.errors').hide()
	$('#forgot_step2_continue').hide()
	$('div.login_button img.spinner').show()
	$.ajax({
		url : "../resources/accounts/recover"
		type: 'PUT'
		success : () ->
			$('div.errors').hide()
			$('#forgot_step2_continue').show()
			$('div.login_button img.spinner').hide()
			$('#good').html('Password changed.')
			$('#good').show()
			window.location.replace("#login")
		error: (jqXHR, statusText, errorThrown) ->
			$('div.login_button img.spinner').hide()
			$('#forgot_step2_continue').show()
			$('#forgot_step2_error').html(jqXHR.responseText)
			$('#forgot_step2_error').show()
		data: {
			'code': $.trim($('#forgot_step2_code').val())
			'new_password': $('#forgot_step2_password').val()
		}
	})

hideSteps = ->
	steps = ['#login_step', '#forgot_step1', '#forgot_step2', '#forgot_step3']
	for step in steps
		$(step).hide();


$(document).ready ->
	$('#login').click(login)
	window.cookieCheck=false
	
	$(window).bind('hashchange', () ->
		hash = window.location.hash or '#login'
		hideSteps();
		switch hash
			when '#fs1'
				$('#forgot_step1_email').val($('#email').val())
				$('#forgot_step1').show()
			when '#fs2'
				$('#forgot_step2_code').val('')
				$('#forgot_step2_password').val('')
				$('#forgot_step2_retype').val('')
				gets=getQueryParams(document.location.search)
				if gets["c"]
					$('#forgot_step2_code').val(gets["c"])
				$('#forgot_step2').show()
			else
				hideSteps()
				if window.cookieCheck
					$('#login_step').show()
	)
	
	$('#forgot_step1_continue').click(fs1ContinueClick)
	$('#forgot_step2_continue').click(fs2ContinueClick)
	$(window).triggerHandler('hashchange')
	cookieLoginCheck()

