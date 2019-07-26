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

from flask import request, abort, Response, jsonify
from isadoreapp import app
from isadoreapp.authentication import authorized, unauthorized
import isadoreapp.util as util
import json
from isadoreapp.passgen import generatePassword
import hashlib


@app.route('/resources/accounts/self', methods=["GET"])
@authorized('User')
def get_own_account():
    return jsonify({'xlink': ['/resources/accounts/' + str(request.user.id)]})


@app.route('/resources/accounts/self-fast', methods=["GET"])
@authorized('User')
def get_own_account_fast():
    return jsonify(r_accounts_get(request.user.id))


@app.route('/resources/accounts', methods=["GET"])
@authorized('Power User')
def accounts():
    ids = util.getIdsFromTable("account",
                               extraWhere="privilege_id <= %s",
                               extraArgs=(request.user.privilege_id,),
                               checkEnabled=True)
    return jsonify({'xlink': ['/resources/accounts/' + str(account_id) for account_id in ids]})


@app.route('/resources/accounts', methods=["POST"])
@authorized('Power User')
def accounts_new():
    name = request.values.get('name')
    email = request.values.get('email')
    # TODO: Check phone format
    phone = request.values.get('phone')
    try:
        privilege_id = int(request.values.get('privilege_id'))
    except ValueError:
        return abort(400, 'Invalid privilege_id')
    if privilege_id > request.user.privilege_id:
        unauthorized()
    # TODO: Check for lengths, instead of relying on db?
    password = generatePassword()
    seed = generatePassword() + generatePassword()
    password_hash = hashlib.sha1((seed + password).encode()).hexdigest()
    row_data = {"name": name, "email": email, "password": password_hash, "seed": seed, "privilege_id": privilege_id}
    if phone:
        row_data["phone"] = phone
    account_id = util.insertRow("account", row_data)

    # TODO: Send new account email
    util.sendEmail(email, 'info@example.com', 'Welcome to Isadore',
                   "Welcome to the Isadore system. You can login by going to https://" + request.urlparts[1] + "\n\n" +
                   "To login use the following\n\nEmail:   " + email + "\nPassword:   " + password + "\n\n")
    return jsonify({'xlink': ['/resources/accounts/' + str(account_id)]})


@app.route('/resources/accounts/<int:account_id>', methods=["GET"])
@authorized('User')
def accounts_get(account_id):
    return jsonify(r_accounts_get(account_id))


def r_accounts_get(account_id):
    if request.user.id == int(account_id) or request.user.is_power_user():
        row = util.getRowFromTableById('account', int(account_id),
                                       columns="id, name, email, phone, privilege_id, configs, contact_news",
                                       checkEnabled=True)
        if row:
            if int(row['privilege_id']) > request.user.privilege_id:
                unauthorized()
            else:
                return row
        else:
            abort(404, 'Account not found.')
    else:
        unauthorized()


@app.route('/resources/accounts/<int:account_id>', methods=["DELETE"])
@authorized('Power User')
def accounts_delete(account_id):
    row = util.getRowFromTableById('account', int(account_id), checkEnabled=True)
    if row:
        if int(row['privilege_id']) > request.user.privilege_id:
            unauthorized()
        else:
            util.deleteRowFromTableById('account', int(account_id), deleteIsDisable=True)
            return Response(response="Account removed.", status=204)
    else:
        abort(404, 'Account not found.')


@app.route('/resources/accounts/password', methods=["PUT"])
@authorized('User')
def accounts_change_password():
    old_password = request.values.get('old_password', None)
    new_password = request.values.get('new_password', None)
    if not old_password or not new_password:
        abort(400, 'Missing parameters')
    if not util.getAccount(request.user.email, old_password):
        abort(400, 'Invalid old password')

    seed = generatePassword() + generatePassword()
    password_hash = hashlib.sha1((seed + new_password).encode()).hexdigest()
    util.updateRowById("account", request.user.id, {'seed': seed, 'password': password_hash})
    return Response(response="Password updated", status=204)


@app.route('/resources/accounts/<int:account_id>', methods=["PUT"])
@authorized('User')
def accounts_update(account_id):
    if request.user.id == int(account_id) or request.user.is_power_user():
        row = util.getRowFromTableById('account', int(account_id), checkEnabled=True)
        if row:
            if int(row['privilege_id']) > request.user.privilege_id:
                unauthorized()
            else:
                parameters = {'name': request.values.get('name', None),
                              'email': request.values.get('email', None),
                              'contact_news': request.values.get('contact_news', None)
                              }
                configs = request.values.get('configs', None)
                if configs:
                    try:
                        json.loads(configs)
                    except json.decoder.JSONDecodeError:
                        abort(400, 'Invalid configs')
                    parameters['configs'] = configs
                password = request.values.get('password', None)
                if password:
                    parameters['seed'] = generatePassword() + generatePassword()
                    parameters['password'] = hashlib.sha1((parameters['seed'] + password).encode()).hexdigest()
                # TODO: Check phone format
                privilege_id = request.values.get('privilege_id', None)
                # TODO: Check for lengths, instead of relying on db?
                if privilege_id:
                    try:
                        privilege_id = int(privilege_id)
                    except ValueError:
                        abort(400, 'Invalid privilege_id')
                    if privilege_id > request.user.privilege_id:
                        unauthorized()
                    parameters['privilege_id'] = privilege_id
                new_parameters = {}
                for key, value in parameters.items():
                    if value:
                        new_parameters[key] = value
                parameters = new_parameters
                parameters['phone'] = request.values.get('phone', None)
                # This 400 will never happen because will always assume phone should be removed.
                if not parameters:
                    abort(400, 'No parameters given.')

                # TODO: What about password?
                util.updateRowById('account', account_id, parameters)
                # TODO: Send email to account that got change informing them?
                return Response(response="Account updated.", status=204)
        else:
            abort(404, 'Account not found.')
    else:
        unauthorized()


@app.route('/resources/accounts/recover', methods=['POST'])
def accounts_recover():
    email = request.values.get('email', None)
    if not email:
        abort(400, 'Email parameter not given.')
    user = util.getAccountByEmail(email)
    # TODO: See if recovery has been tried lately and refuse new one if so?
    if not user:
        abort(400, 'Email does not exist.')

    recovery_hash = hashlib.sha1((generatePassword() + user.email).encode()).hexdigest()
    while (len(util.getRowsFromTable(table="account", columns="id", extraWhere="recovery_hash = %s",
                                     extraArgs=(recovery_hash,), checkEnabled=True)) > 0):
        recovery_hash = hashlib.sha1((generatePassword() + user.email).encode()).hexdigest()
    util.updateRowById("account", user.id, {'recovery_hash': recovery_hash})
    message = """%s:
    
A request has been sent to reset the password to your Isadore account. If you did not intend to reset your password \
you may ignore this message. To continue the reset process follow the instructions below:

Do one of the following:
  1) Goto the following:
    https://%s/isadore/s/login.html?c=%s#fs2
OR
  2) Type in the reset code in the form at:
    https://%s/isadore/s/login.html#fs2
    Using the code:
     %s


After 24 hours the reset code will expire and will have to send a new reset request if you wish to reset your \
password.\n\n""" % \
              (user.name, request.urlparts[1], recovery_hash, request.urlparts[1], recovery_hash)

    #    logging.debug(message)
    util.sendEmail(user.email, 'info@example.com', 'Isadore Password Recovery', message)
    return Response(response="Recovery Email Sent", status=204)


@app.route('/resources/accounts/recover', methods=['PUT'])
def accounts_recover_update():
    recovery_hash = request.values.get('code', None)
    new_password = request.values.get('new_password', None)
    if not recovery_hash or not new_password:
        abort(400, 'Missing parameters.')
    rows = util.getRowsFromTable(table="account", columns="id",
                                 extraWhere="recovery_hash=%s AND recovery_datetime > now() - interval '24h'",
                                 extraArgs=(recovery_hash,), checkEnabled=True)
    if not rows:
        abort(400, 'Invalid code')
    user = rows[0]
    seed = generatePassword() + generatePassword()
    password_hash = hashlib.sha1((seed + new_password).encode()).hexdigest()
    util.updateRowById("account", user["id"],
                       {'seed': seed, 'password': password_hash, 'recovery_hash': None, 'recovery_datetime': None})
    return Response(response="Password updated", status=204)


@app.route('/resources/accounts/recover', methods=['GET'])
def accounts_recover_check():
    code = request.values.get("code", None)
    if not code:
        abort(400, 'Missing code parameter.')
    rows = util.getRowsFromTable(table="account", columns="id",
                                 extraWhere="recovery_hash=%s AND recovery_datetime > now() - interval '24h'",
                                 extraArgs=(code,), checkEnabled=True)
    if rows:
        return Response(response="Valid code.", status=204)
    else:
        abort(404, "Invalid code.")
