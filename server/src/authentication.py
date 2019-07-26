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
from bottle import response, request, HTTPError
import util
import logging

# TODO: Hashing + seed auth scheme

mid_info = {}
alarms_pass = None

def init():
    global mid_info, alarms_pass
    row = util.getRowFromTableById("general_config", 1, columns="mid_pass,enabled_p")
    mid_info["mid_pass"] = row["mid_pass"]
    mid_info["mid_enabled"] = row["enabled_p"]
    if alarms_pass in row:
        alarms_pass = row["alarms_pass"]

init()


def unauthorized():
    # response.header['WWW-Authenticate'] = 'Basic realm="isadore"'
    raise HTTPError(401, 'Unauthorized')


def get_account(privilege):
    email, passhash = request.auth or (None, None)
    account = None
#    if hasattr(request, 'user'):
#        account = request.user
    if not account:
        if not email or not passhash:
            email = request.get_cookie("exemail")
            passhash = request.get_cookie("exrhash")
        account = util.getAccount(email, passhash)
    if not account or not account.has_privilege(privilege):
        if account and not account.has_privilege(privilege):
            logging.debug('DEBUG: Failed login: does not have privilege %s', (privilege,))
        unauthorized()
    return account


def authorized(privilege):
    """
    Annotation checks for valid privilege if not prompts for authentication. Sets response.user
    if proper authorization
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            request.user = get_account(privilege)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def alarmsauthorized(privilage):
    """
    Annotation checks for valid privilege if not prompts for authentication. Sets response.user
    if proper authorization
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            reqalarms_pass = request.params.get('alarms_pass')
            if not alarms_pass or alarms_pass != reqalarms_pass:
                request.user = get_account(privilage)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def midauthorized():
    """
    Annotation checks for valid privilege if not prompts for authentication. Sets response.user
    if proper authorization
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            mid_pass = request.params.get('mid_pass')
            if not mid_info["mid_enabled"] or mid_pass != mid_info["mid_pass"]:
                unauthorized()
            return func(*args, **kwargs)

        return wrapper

    return decorator


def alarmsauth():
    """
    Annotation checks for valid privilege if not prompts for authentication. Sets response.user
    if proper authorization
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            reqalarms_pass = request.params.get('alarms_pass')
            if not alarms_pass or alarms_pass != reqalarms_pass:
                unauthorized()
            return func(*args, **kwargs)

        return wrapper

    return decorator


# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
