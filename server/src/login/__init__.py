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

from bottle import route #@UnresolvedImport
from bottle import abort, request, HTTPResponse, response
from authentication import authorized, get_account
from passgen import generatePassword
from cache import noCache
import hashlib
import util
import time

@route('/resources/login', method=["POST"])
def login():
	email = request.params.get('email', None)
	password = request.params.get('password', None)
	if(not email or not password):
		abort(401, 'Wrong credentials')
	request.user = util.getAccount(email, password)
	if(not request.user):
		abort(401, 'Wrong credentials')
	session_hash = hashlib.sha1(generatePassword() + request.user.email).hexdigest()
	util.insertRow("account_session", {'account_id': request.user.id, 'hash': session_hash})
	request.user.session_hashes.append(session_hash)
	#Deleting cookies first seems to cause an issue
	#response.delete_cookie("exemail", path='/')
	#response.delete_cookie("exrhash", path='/')
	if(request.params.get("remember", "").lower() == 'true'):
		response.set_cookie('exemail', request.user.email, path='/', max_age=2678400)
		response.set_cookie('exrhash', session_hash, path='/', max_age=2678400)
	else:
		response.set_cookie('exemail', request.user.email, path='/')
		response.set_cookie('exrhash', session_hash, path='/')
	return HTTPResponse(output="Logged in", status=204)

@route('/resources/login/check', method=["POST"])
@authorized('User')
def check():
#	time.sleep(5)
	return HTTPResponse(output="Good login", status=204)
	

@route('/resources/login/logout', method="PUT")
def logout():
	try:
		account = get_account('User')
	except:
		response.delete_cookie("exemail", path='/')
		response.delete_cookie("exrhash", path='/')
		return HTTPResponse(output="Logged out", status=204)
	#TODO: Remove hash from session table?
	response.delete_cookie("exemail", path='/')
	response.delete_cookie("exrhash", path='/')
	return HTTPResponse(output="Logged out", status=204)
	


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
