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
from bottle import request, abort, HTTPResponse
from util import sendEmail
from authentication import authorized

@route('/resources/contact', method=['POST'])
@authorized('User')
def contact():
	name = request.params.get('name', None)
	email = request.params.get('email', None)
	subject = request.params.get('subject', None)
	message = request.params.get('message', None)
	
	if(not message):
		abort(400, 'Missing message.')
	
	realMessage = ''
	realMessage += 'Account Name<Email>: '
	realMessage += request.user.name + "<" + request.user.email + ">\n"
	realMessage += 'Form Name<Email>: '
	realMessage += name + "<" + email + ">\n"
	realMessage += 'Subject: ' + subject
	realMessage += '\nUser Agent:' + request.headers['User-Agent']
	realMessage += "\n\n"+message
	
	sendEmail('info@exotericanalytics.com', 'info@exotericanalytics.com', 'Isadore Contact Form', realMessage)
	
	return HTTPResponse(output="Email sent", status=204)


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
