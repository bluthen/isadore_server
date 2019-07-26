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

from isadoreapp import app
from flask import abort, request, Response, session
from isadoreapp.authentication import authorized
from isadoreapp.passgen import generatePassword
import hashlib
import isadoreapp.util as util


@app.route('/resources/login', methods=["POST"])
def login():
    email = request.values.get('email', None)
    password = request.values.get('password', None)
    if not email or not password:
        abort(401, 'Wrong credentials')
    request.user = util.getAccount(email, password)
    if not request.user:
        abort(401, 'Wrong credentials')
    session_hash = hashlib.sha1((generatePassword() + request.user.email).encode()).hexdigest()
    util.insertRow("account_session", {'account_id': request.user.id, 'hash': session_hash})
    request.user.session_hashes.append(session_hash)
    # Deleting cookies first seems to cause an issue
    response = Response(response='Logged in', status=204)
    if request.values.get("remember", "").lower() == 'true':
        session['exemail'] = request.user.email
        session['exrhash'] = session_hash
        session.permanent = True
    else:
        session['exemail'] = request.user.email
        session['exrhash'] = session_hash
        session.permanent = False
    return response


@app.route('/resources/login/check', methods=["POST"])
@authorized('User')
def check():
    # time.sleep(5)
    return Response(response="Good login", status=204)


@app.route('/resources/login/logout', methods=["PUT"])
def logout():
    response = Response(response='Logged out', status=204)
    session.pop("exemail")
    session.pop("exrhash")
    return response
