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

from bottle import response, request, HTTPError, HTTPResponse, static_file
import util
import logging
import pytz
from datetime import timedelta, datetime
import time

def confCache():
	'''Checks cache request headers. Sets cache response headers. Browser checks etag every request.'''
	def decorator(func):
		def wrapper(*args, **kwargs):
			confVersion = util.getConfVersion()
			ifmatch = request.environ.get('HTTP_IF_NONE_MATCH')
			ifmatch2 = request.environ.get('HTTP_IF_MODIFIED_SINCE')
			#logging.debug(str(ifmatch)+", "+str(ifmatch2))
			if(ifmatch == str(confVersion[0])):
				header = {}
				header['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
				return HTTPResponse(status=304, header=header)
			lastModified = confVersion[1].astimezone(pytz.utc).strftime("%a, %d %b %Y %H:%M:%S GMT") 
			response.headers['Cache-Control'] = 'private, no-cache, must-revalidate'
			#, max-age=' + str(td.total_seconds())
			response.headers['ETag'] = util.getConfVersion()[0]
			response.headers['Last-Modified'] = lastModified
			td = timedelta(days=30)
			response.headers['Expires'] = (datetime.utcnow() + td).strftime("%a, %d %b %Y %H:%M:%S GMT")
			return func(*args, **kwargs)
		return wrapper
	return decorator


def noCache():
	'''Sets response headers to make the browser not cache.'''
	def decorator(func):
		def wrapper(*args, **kwargs):
			response.headers['Pragma']='no-cache'
			response.headers['Expires']='Fri, 30 Oct 1998 14:19:41 GMT'
			return func(*args, **kwargs)
		return wrapper
	return decorator
	
def static_file_expires_monday(filename, root, mimetype='auto', guessmime=True, download=False):
	'''Service a static file that expires next monday.'''
	now = util.getDateFromParam('now')
	cacheTime = datetime.date.today()
	cacheTime = cacheTime + datetime.timedelta(days=-cacheTime.weekday(), weeks=1)
	cacheTime = datetime.datetime(cacheTime.year, cacheTime.month, cacheTime.day, 00, 00, tzinfo=now.tzinfo)
	dt=cacheTime-now
	seconds = dt.days*86400 + dt.seconds 
	response.headers['Cache-Control'] = 'private, max-age='+str(seconds)
	response.headers['Expires']=cacheTime.astimezone(pytz.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
	return static_file(filename, root, mimetype, guessmime, download)


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
