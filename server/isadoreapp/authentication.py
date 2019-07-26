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

from flask import request, Response, abort, session
import isadoreapp.util as util
import logging
from functools import wraps


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
    return abort(Response('Unauthorized', status=401))


def get_account(privilege):
    account = None
#    if hasattr(request, 'user'):
#        account = request.user
    if not account:
        email = session.get("exemail")
        passhash = session.get("exrhash")
        account = util.getAccount(email, passhash)
    if not account or not account.has_privilege(privilege):
        if account and not account.has_privilege(privilege):
            logging.debug('DEBUG: Failed login: does not have privilege %s', (privilege,))
        return None
    return account


def authorized(privilege):
    """
    Annotation checks for valid privilege if not prompts for authentication. Sets response.user
    if proper authorization
    """

    def decorator(func):
        @wraps(func)
        def wrapper1(*args, **kwargs):
            user = get_account(privilege)
            if user is None:
                return unauthorized()
            request.user = user
            return func(*args, **kwargs)
        return wrapper1
    return decorator


def alarmsauthorized(privilage):
    """
    Annotation checks for valid privilege if not prompts for authentication. Sets response.user
    if proper authorization
    """

    def decorator(func):
        @wraps(func)
        def wrapper2(*args, **kwargs):
            reqalarms_pass = request.values.get('alarms_pass')
            if not alarms_pass or alarms_pass != reqalarms_pass:
                user = get_account(privilage)
                if user is None:
                    return unauthorized()
                request.user = user
            return func(*args, **kwargs)
        return wrapper2
    return decorator


def midauthorized():
    """
    Annotation checks for valid privilege if not prompts for authentication. Sets response.user
    if proper authorization
    """
    def midauthorized_wrapped(func):
        @wraps(func)
        def wrapper3(*args, **kwargs):
            mid_pass = request.values.get('mid_pass')
            if not mid_info["mid_enabled"] or mid_pass != mid_info["mid_pass"]:
                return unauthorized()
            return func(*args, **kwargs)
        return wrapper3
    return midauthorized_wrapped


def alarmsauth():
    """
    Annotation checks for valid privilege if not prompts for authentication. Sets response.user
    if proper authorization
    """

    def decorator(func):
        @wraps(func)
        def wrapper4(*args, **kwargs):
            reqalarms_pass = request.values.get('alarms_pass')
            if not alarms_pass or alarms_pass != reqalarms_pass:
                return unauthorized()
            return func(*args, **kwargs)
        return wrapper4
    return decorator
