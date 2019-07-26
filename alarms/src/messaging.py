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

from twilio.rest import TwilioRestClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import alarm_config
import logging
import json

phone_logger = logging.getLogger('isadore_alarms.phone_logger')

class BadPhoneNumberError(Exception):
    def __init__(self, number):
        Exception.__init__(self)
        self.msg = "Invalid phone number format %s (+XXXXXXXX)" + (str(number),)

    def __str__(self):
        return self.msg


class BadTxtBody(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class FailedTxtError(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.msg = "Failed to send txt: to=%s, body=%s" % (message.to, message.body)

    def __str__(self):
        return self.msg


def txtSplit(msg, readableSplit=True):
    if len(msg) < 160:
        return [msg]
    if not readableSplit:
        if len(msg) > 1440:
            raise BadTxtBody('Split message greater than 1440 characters.')
        msgs = []
        for i in range(0, len(msg), 160):
            end = i + 160
            if end > len(msg):
                end = len(msg)
            msgs.append(msg[i:end])
        return msgs
    else:
        if len(msg) > 1395:  # No more than 10 messages split.
            raise BadTxtBody('Readable split message greater than 1395 characters.')
        msgs = []
        words = msg.split(' ')
        m = ""
        for word in words:
            if (len(m) + len(word + " ") > 155):
                msgs.append(m)
                m = ""
            m += word + " "
        if m != "":
            msgs.append(m)
        if len(msgs) > 9:
            raise BadTxtBody('Readable split message is greater than 9 splits.')
        for i in range(0, len(msgs)):
            msgs[i] = "(%d/%d)" % (i + 1, len(msgs)) + msgs[i]
        return msgs


def sendTxt(toTxt, msg, readableSplit=True):
    client = TwilioRestClient(alarm_config.config.get("twilio", "account"), alarm_config.config.get("twilio", "token"))
    if str(toTxt)[0] != '+':
        toTxt = '+' + toTxt
    if len(toTxt) != 12:
        raise BadPhoneNumberError(toTxt)

    txts = txtSplit(msg, readableSplit)

    messages = []
    for txt in txts:
        message = client.sms.messages.create(to=toTxt, from_="+17852465982", body=txt)
        messages.append(message)
        phone_logger.info(json.dumps({'url': 'sendTxt', 'message': txt, 'tonumber': toTxt, 'status': message.status}))
        if message.status == 'failed':
            raise FailedTxtError(message)
    return messages


def sendEmail(toemail, fromemail, subject, messageTXT, messageHTML=None):
    if messageHTML:
        msg = MIMEMultipart('alternative')
    else:
        msg = MIMEText(messageTXT)
    if (not subject):
        msg['Subject'] = 'None'
    else:
        msg['Subject'] = subject
    msg['From'] = fromemail
    msg['To'] = toemail

    if messageHTML:
        part1 = MIMEText(messageTXT, 'plain')
        part2 = MIMEText(messageHTML, 'html')
        msg.attach(part1)
        msg.attach(part2)

    s = smtplib.SMTP('localhost')
    s.sendmail(fromemail, [toemail], msg.as_string())
    s.quit()


def makeCall(tonumber, url):
    phone_logger.info(json.dumps({"url": 'makeCall', 'tonumber': tonumber, 'nextUrl': url}))
    client = TwilioRestClient(alarm_config.config.get("twilio", "account"), alarm_config.config.get("twilio", "token"))
    call = client.calls.create(to=tonumber, from_=alarm_config.config.get("twilio", "post"),
                               url=url,
                               method="POST")


def makeAlarmCall(tonumber, outgoing_alarm_id):
    phone_logger.info(json.dumps({"url": 'makeAlarmCall', 'tonumber': tonumber, 'outgoing_alarm_id': outgoing_alarm_id}))
    client = TwilioRestClient(alarm_config.config.get("twilio", "account"), alarm_config.config.get("twilio", "token"))
    call = client.calls.create(to=tonumber, from_=alarm_config.config.get("twilio", "post"),
                               url="https://alarms.example.com/outgoing_alarm/%d" % (outgoing_alarm_id,),
                               method="POST")
