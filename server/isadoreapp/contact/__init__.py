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
from flask import request, abort, Response, jsonify
from isadoreapp.util import sendEmail
from isadoreapp.authentication import authorized


@app.route('/resources/contact', methods=['POST'])
@authorized('User')
def contact():
    name = request.values.get('name', None)
    email = request.values.get('email', None)
    subject = request.values.get('subject', None)
    message = request.values.get('message', None)

    if not message:
        abort(400, 'Missing message.')

    real_message = ''
    real_message += 'Account Name<Email>: '
    real_message += request.user.name + "<" + request.user.email + ">\n"
    real_message += 'Form Name<Email>: '
    real_message += name + "<" + email + ">\n"
    real_message += 'Subject: ' + subject
    real_message += '\nUser Agent:' + request.headers['User-Agent']
    real_message += "\n\n" + message

    sendEmail('info@example.com', 'info@example.com', 'Isadore Contact Form', real_message)

    return Response(response="Email sent", status=204)
