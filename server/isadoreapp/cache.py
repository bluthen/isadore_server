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

from functools import wraps
from flask import request
import flask
import isadoreapp.util as util
import pytz
from datetime import timedelta, datetime
import time


def confCache():
    """Checks cache request headers. Sets cache response headers. Browser checks etag every request."""

    def decorator(func):
        @wraps(func)
        def wrapper21(*args, **kwargs):
            conf_version = util.getConfVersion()
            ifmatch = request.environ.get('HTTP_IF_NONE_MATCH')
            # logging.debug(str(ifmatch)+", "+str(ifmatch2))
            response = func(*args, **kwargs)
            if ifmatch == str(conf_version[0]):
                h = response.headers
                h['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
                response.status_code = 304
                return response
            last_modified = conf_version[1].astimezone(pytz.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
            h = response.headers
            h['Cache-Control'] = 'private, no-cache, must-revalidate'
            # , max-age=' + str(td.total_seconds())
            h['ETag'] = util.getConfVersion()[0]
            h['Last-Modified'] = last_modified
            td = timedelta(days=30)
            h['Expires'] = (datetime.utcnow() + td).strftime("%a, %d %b %Y %H:%M:%S GMT")
            return response

        return wrapper21

    return decorator


def noCache():
    """Sets response headers to make the browser not cache."""

    def decorator(func):
        @wraps(func)
        def wrapper22(*args, **kwargs):
            response = func(*args, **kwargs)
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = 'Fri, 30 Oct 1998 14:19:41 GMT'
            return response

        return wrapper22

    return decorator
