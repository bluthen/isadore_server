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
import string
from bottle import route #@UnresolvedImport
from bottle import response, request, abort, HTTPResponse
from authentication import authorized, unauthorized
import util
import json
from passgen import generatePassword
import hashlib
import random
from datetime import datetime, timedelta
import logging


@route('/resources/accounts/self', method=["GET"])
@authorized('User')
def get_own_account():
    return {'xlink': ['/resources/accounts/'+str(request.user.id)]}

@route('/resources/accounts/self-fast', method=["GET"])
@authorized('User')
def get_own_account_fast():
    return r_accounts_get(request.user.id)


@route('/resources/accounts', method=["GET"])
@authorized('Power User')
def accounts():
    ids = util.getIdsFromTable("account",
                               extraWhere="privilege_id <= %s",
                               extraArgs=(request.user.privilege_id,),
                               checkEnabled=True)
    return {'xlink': ['/resources/accounts/' + str(id) for id in ids]}

@route('/resources/accounts', method=["POST"])
@authorized('Power User')
def accounts_new():
    name = request.params.get('name')
    email = request.params.get('email')
    #TODO: Check phone format
    phone = request.params.get('phone')
    try:
        privilege_id = int(request.params.get('privilege_id'))
    except ValueError:
        abort(400, 'Invalid privilege_id')
    if privilege_id > request.user.privilege_id:
        unauthorized()
    #TODO: Check for lengths, instead of relying on db?
    password = generatePassword()
    seed = generatePassword() + generatePassword()
    passwordHash = hashlib.sha1(seed + password).hexdigest()
    rowData = {"name":name, "email":email, "password": passwordHash, "seed": seed, "privilege_id": privilege_id};
    if(phone):
        rowData["phone"]=phone
    id = util.insertRow("account", rowData)
    
    #TODO: Send new account email
    util.sendEmail(email, 'info@exotericanalytics.com', 'Welcome to Isadore', 
                "Welcome to the Isadore system. You can login by going to https://"+request.urlparts[1]+"\n\n"+
                "To login use the following\n\nEmail:   "+email+"\nPassword:   "+password+"\n\n")
    return {'xlink': ['/resources/accounts/' + str(id)]}

@route('/resources/accounts/:id#[0-9]+#', method=["GET"])
@authorized('User')
def accounts_get(id):
    return r_accounts_get(id)


def r_accounts_get(id):
    if request.user.id == int(id) or request.user.is_power_user():
        row = util.getRowFromTableById('account', int(id), columns="id, name, email, phone, privilege_id, configs, contact_news", checkEnabled=True)
        if(row):
            if int(row['privilege_id']) > request.user.privilege_id:
                unauthorized()
            else:
                return row
        else:
            abort(404, 'Account not found.')
    else:
        unauthorized()


@route('/resources/accounts/:id#[0-9]+#', method=["DELETE"])
@authorized('Power User')
def accounts_delete(id):
    row = util.getRowFromTableById('account', int(id), checkEnabled=True)
    if(row):
        if int(row['privilege_id']) > request.user.privilege_id:
            unauthorized()
        else:
            util.deleteRowFromTableById('account', int(id), deleteIsDisable=True)
            return HTTPResponse(output="Account removed.", status=204)
    else:
        abort(404, 'Account not found.')


@route('/resources/accounts/password', method=["PUT"])
@authorized('User')
def accounts_change_password():
    old_password = request.params.get('old_password', None)
    new_password = request.params.get('new_password', None)
    if not old_password or not new_password:
        abort(400, 'Missing parameters')
    if not util.getAccount(request.user.email, old_password):
        abort(400, 'Invalid old password')

    seed = generatePassword() + generatePassword()
    password_hash = hashlib.sha1(seed + new_password).hexdigest()
    util.updateRowById("account", request.user.id, {'seed': seed, 'password': password_hash})
    return HTTPResponse(output="Password updated", status=204)


@route('/resources/accounts/:id#[0-9]+#', method=["PUT"])
@authorized('User')
def accounts_update(id):
    if request.user.id == int(id) or request.user.is_power_user():
        row = util.getRowFromTableById('account', int(id), checkEnabled=True)
        if(row):
            if int(row['privilege_id']) > request.user.privilege_id:
                unauthorized()
            else:
                parameters = {}
                parameters['name'] = request.params.get('name', None)
                parameters['email'] = request.params.get('email', None)
                parameters['contact_news'] = request.params.get('contact_news', None)
                configs = request.params.get('configs', None)
                if configs:
                    try:
                        json.loads(configs)
                    except:
                        abort(400, 'Invalid configs')
                    parameters['configs'] = configs
                password = request.params.get('password', None)
                if(password):
                    parameters['seed'] = generatePassword() + generatePassword()
                    parameters['password'] = hashlib.sha1(parameters['seed'] + password).hexdigest()
                #TODO: Check phone format
                privilege_id = request.params.get('privilege_id', None)
                #TODO: Check for lengths, instead of relying on db?
                if privilege_id:
                    try:
                        privilege_id = int(privilege_id)
                    except:
                        abort(400, 'Invalid privilege_id')
                    if privilege_id > request.user.privilege_id:
                        unauthorized()
                    parameters['privilege_id'] = privilege_id
                newParameters = {}
                for key, value in parameters.items():
                    if(value):
                        newParameters[key] = value
                parameters = newParameters
                parameters['phone'] = request.params.get('phone', None)
                #This 400 will never happen because will always assume phone should be removed.
                if(not parameters):
                    abort(400, 'No parameters given.')
                
                #TODO: What about password?
                util.updateRowById('account', id, parameters)
                #TODO: Send email to account that got change informing them?
                return HTTPResponse(output="Account updated.", status=204)
        else:
            abort(404, 'Account not found.')
    else:
        unauthorized()

@route('/resources/accounts/recover', method=['POST'])
def accounts_recover():
    email = request.params.get('email', None)
    if(not email):
        abort(400, 'Email parameter not given.')
    user = util.getAccountByEmail(email)
    #TODO: See if recovery has been tried lately and refuse new one if so?
    if(not user):
        abort(400, 'Email does not exist.')
    
    recovery_hash = hashlib.sha1(generatePassword() + user.email).hexdigest()
    while(len(util.getRowsFromTable(table="account", columns="id", extraWhere="recovery_hash = %s", extraArgs=(recovery_hash,), checkEnabled=True)) > 0):
        recovery_hash = hashlib.sha1(generatePassword() + user.email).hexdigest()
    util.updateRowById("account", user.id, {'recovery_hash': recovery_hash})
    message = """%s:
    
A request has been sent to reset the password to your Isadore account. If you did not intend to reset your password you may ignore this message. To continue the reset process follow the instructions below:

Do one of the following:
  1) Goto the following:
    https://%s/isadore/s/login.html?c=%s#fs2
OR
  2) Type in the reset code in the form at:
    https://%s/isadore/s/login.html#fs2
    Using the code:
     %s


After 24 hours the reset code will expire and will have to send a new reset request if you wish to reset your password.\n\n""" % \
    (user.name, request.urlparts[1], recovery_hash, request.urlparts[1], recovery_hash)
    
#    logging.debug(message)
    util.sendEmail(user.email, 'info@exotericanalytics.com', 'Isadore Password Recovery', message)
    return HTTPResponse(output="Recovery Email Sent", status=204)

@route('/resources/accounts/recover', method=['PUT'])
def accounts_recover_update():
    recovery_hash = request.params.get('code', None)
    new_password = request.params.get('new_password', None)
    if(not recovery_hash or not new_password):
        abort(400, 'Missing parameters.')
    rows = util.getRowsFromTable(table="account", columns="id", extraWhere="recovery_hash=%s AND recovery_datetime > now() - interval '24h'", extraArgs=(recovery_hash,), checkEnabled=True)
    if not rows:
        abort(400, 'Invalid code')
    user = rows[0]
    seed = generatePassword() + generatePassword()
    passwordHash = hashlib.sha1(seed + new_password).hexdigest()
    util.updateRowById("account", user["id"], {'seed': seed, 'password':passwordHash, 'recovery_hash': None, 'recovery_datetime': None})
    return HTTPResponse(output="Password updated", status=204)

@route('/resources/accounts/recover', method=['GET'])
def accounts_recover_check():
    code = request.params.get("code", None)
    if not code:
        abort(400, 'Missing code parameter.')
    rows = util.getRowsFromTable(table="account", columns="id", extraWhere="recovery_hash=%s AND recovery_datetime > now() - interval '24h'", extraArgs=(code,), checkEnabled=True)
    if rows:
        return HTTPResponse(output="Valid code.", status=204)
    else:
        abort(404, "Invalid code.")



# Local Variables:
# indent-tabs-mode: nil
# python-indent: 4
# tab-width: 4
# End:
