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

from flask import Flask, Response, request, abort
import twiml_messages
import alarm_config
import string
import logging
import json
import db
import random
import datetime
import messaging
import hashlib
import os
import urllib

app = Flask(__name__)

phone_logger = logging.getLogger('isadore_alarms.phone_logger')

version2_enabled = False


def responseJSON(obj):
    '''Sets content type to json, and uses customJSONHandler for conversions.'''
    Response(json.dumps(obj, default=db.customJSONHandler), mimetype='application/json')


def twilio_check():
    account = request.form.get('AccountSid')
    if alarm_config.config.get("twilio", "account") != account:
        abort(401)
    digits = request.form.get('Digits')
    fromphone = request.form.get('From')
    body = request.form.get('Body')
    url = request.url
    phone_logger.info(json.dumps({"from": fromphone, "url": url, "digits": digits, "body": body}))


@app.route('/test', methods=["GET"])
def test():
    return "Test"


@app.route('/v1_incoming_voice_response1', methods=["POST"])
def v1_uncoming_voice_response1():
    twilio_check()
    digits = int(request.form.get('Digits'))
    fromphone = request.form.get('From')
    if digits == 1:
        xml = twiml_messages.dial_xml % ('Employee One', '+15555555555')
    elif digits == 2:
        xml = twiml_messages.dial_xml % ('Employee Two', '+15555555555')
    elif digits == 3:
        xml = twiml_messages.dial_xml % ('Employee Three', '+15555555555')
    else:
        xml = twiml_messages.invalid_choice % ("incoming_voice",)

    return Response(xml, mimetype="text/xml")


@app.route('/incoming_voice', methods=["POST"])
def uncoming_voice():
    twilio_check()
    if version2_enabled:
        xml = twiml_messages.incoming_voice
    else:
        xml = twiml_messages.v1_incoming_voice
    return Response(xml, mimetype="text/xml")


@app.route('/outgoing_alarm/<int:outgoing_alarm_id>', methods=["POST"])
def outgoing_alarm(outgoing_alarm_id):
    twilio_check()
    msg = db.get_outgoing_alarm_msg(outgoing_alarm_id)
    xml = twiml_messages.outgoing % (msg,)
    return Response(xml, mimetype="text/xml")


@app.route('/outgoing_response', methods=["POST"])
def outgoing_response():
    twilio_check()
    digits = int(request.form.get('Digits'))
    fromphone = request.form.get('From')
    if digits == 8:
        xml = twiml_messages.unsubscribed
        db.unsubscribe(phone=fromphone)
    elif digits == 7:
        blacklist = db.is_sms_blacklisted(phone=fromphone)
        if blacklist:
            xml = twiml_messages.resume_but_blacklisted
        else:
            xml = twiml_messages.pause_prompt
    else:
        xml = twiml_messages.invalid_choice % ("incoming_voice",)
    return Response(xml, mimetype="text/xml")


@app.route('/incoming_voice_response1', methods=["POST"])
def uncoming_voice_response1():
    twilio_check()
    digits = int(request.form.get('Digits'))
    fromphone = request.form.get('From')
    if digits == 8:
        xml = twiml_messages.unsubscribed
        db.unsubscribe(phone=fromphone)
    elif digits == 9:
        blacklist = db.is_sms_blacklisted(phone=fromphone)
        if not blacklist:
            xml = twiml_messages.resume
            db.resume(phone=fromphone)
        else:
            xml = twiml_messages.resume_but_blacklisted
            db.resume(phone=fromphone)
    elif digits == 1:
        xml = twiml_messages.dial_xml % ('Employee One', '+15555555555')
    elif digits == 2:
        xml = twiml_messages.dial_xml % ('Employee Two', '+15555555555')
    #    elif digits == 3:
    elif digits == 7:
        blacklist = db.is_sms_blacklisted(fromphone)
        if blacklist:
            xml = twiml_messages.resume_but_blacklisted
        else:
            xml = twiml_messages.pause_prompt
    else:
        xml = twiml_messages.invalid_choice % ("incoming_voice",)

    return Response(xml, mimetype="text/xml")


@app.route('/incoming_voice_response_pause', methods=["POST"])
def incoming_voice_response_pause():
    twilio_check()
    fromphone = request.form.get('From')
    digits = int(request.form.get('Digits'))
    xml = twiml_messages.paused % (str(digits),)
    db.pause(phone=fromphone, hours=digits)
    return Response(xml, mimetype="text/xml")


@app.route('/incoming_sms', methods=["POST"])
def incoming_sms():
    twilio_check()
    fromnumber = request.form.get('From')
    body = request.form.get('Body')
    cmd = string.strip(body).upper()

    if version2_enabled:
        if cmd.find('PAUSE') == 0:
            try:
                hrs = int(cmd.split(' ')[1])
                xml = twiml_messages.sms_paused % (hrs,)
                db.pause(phone=fromnumber, hours=hrs)
            except:
                xml = twiml_messages.sms_paused_invalid
        elif cmd.find('START') == 0:
            xml = twiml_messages.sms_resumed
            db.sms_unblacklist(phone=fromnumber)
        elif cmd.find('STOP') == 0 or cmd.find('UNSUBSCRIBE') == 0 or cmd.find('BLOCK') == 0 or cmd.find('CANCEL') == 0:
            xml = twiml_messages.sms_unsubscribe
            db.sms_blacklist(phone=fromnumber)
        else:  # Help
            # TODO: Check that last help message was > 5 min ago
            xml = twiml_messages.sms_help
    else:
        xml = twiml_messages.v1_sms_help
    return Response(xml, mimetype="text/xml")

# TODO: Email commands


@app.route('/alarm_contact_info_email/<email>', methods=["GET"])
def alarm_contact_info():
    # TODO: Authenticate
    info = db.get_info(email=email)
    return responseJSON(info[1])


@app.route('/alarm_contact_info_phone/<phone>', methods=["GET"])
def alarm_contact_info():
    # TODO: Authenticate Isadore instance
    info = db.get_info(phone=phone)
    return responseJSON(info[1])

# TODO: Static confirm page
# TODO: Static unsubscribe page, can put in email to send unsubscribe message (email), can put in code, or takes code from arg
# TODO: Unsubscribe link using email hash sent as link in alarm emails.
# TODO: Email pause link
# TODO: Check confirms


@app.route('/alarm_contact_info_phone/<email>/confirm', methods=["POST"])
def alarm_contact_info_email_post():
    """
    Generate email with link to confirm.
    :return:
    """
    # TODO: Authenticate Isadore Instance
    # TODO: Limit number of times can confirm?
    # TODO: Confirm expire date?
    # TODO: Implement
    info = db.get_info(email=email)
    oneday = datetime.timedelta(days=1)
    if info["email_verify"]:
        last_try_date = info["email_verify"]["last_try"]
        if datetime.datetime.now() - last_try_date < oneday:
            abort(400)
    confirm_code = hashlib.sha1()
    confirm_code.update(os.urandom(24))
    confirm_code = confirm_code.hexdigest()
    email_verify = {"last_try": datetime.datetime.now(), "confirm_code": confirm_code}
    db.update_info(info_update=email_verify, email=email)
    urlparams = urllib.urlencode({"email": email, "confirm_code": email_verify["confirm_code"]})
    msgtxt = twiml_messages.email_verify_txt % (urlparams, email_verify(["confirm_code"]))
    msghtml = twiml_messages.email_verify_html % (urlparams, urlparams, email_verify["confirm_code"])
    messaging.sendEmail(toemail=email, fromemail='info@example.com', messageTXT=msgtxt, messageHTML=msghtml)
    return ('Sent', 204)


@app.route('/alarm_contact_info_phone/confirm/voice3', methods=["POST"])
def alarm_contact_info_confirm_voice3():
    twilio_check()
    digits = int(request.form.get('Digits'))
    fromnumber = request.form.get('From')
    if digits == 1:
        db.set_verified(phone=fromnumber)
        xml = twiml_messages.voice_verify_verified
    elif digits == 9:
        xml = twiml_messages.voice_verify_stop
        db.voice_blacklist(phone=fromnumber)
    else:
        xml = twiml_messages.voice_verify
    return Response(xml, mimetype="text/xml")


@app.route('/alarm_contact_info_phone/confirm/voice2', methods=["POST"])
def alarm_contact_info_confirm_voice2():
    twilio_check()
    fromnumber = request.form.get('From')
    xml = twiml_messages.voice_verify
    return Response(xml, mimetype="text/xml")




@app.route('/alarm_contact_info_phone/<phone>/confirm/voice', methods=["POST"])
def alarm_contact_info_confirm_voice():
    """
    Generate confirm code and send call voice phone number.
    :return:
    """
    # TODO: Authenticate Isadore Instance
    # TODO: Limit number of times can confirm?
    # TODO: Confirm expire date?
    # TODO: Implement
    info = db.get_info(phone=phone)
    oneday = datetime.timedelta(days=1)
    if info["phone_verify"]:
        last_try_date = info["phone_verify"]["last_try"]
        if datetime.datetime.now() - last_try_date < oneday:
            abort(400)
    phone_verify = {"last_try": datetime.datetime.now(), "confirm_code": None}
    db.update_info(info_update=phone_verify, phone=phone)
    messaging.makeCall(phone, 'https://alarms.example.com/alarm_contact_info_phone/confirm/voice2')
    return ('Sent', 204)


@app.route('/alarm_contact_info_phone/<phone>/confirm/sms', methods=["POST"])
def alarm_contact_confirm_sms_post():
    """
    Generate confirm code and send out confirm sms message.
    :return:
    """
    # TODO: Authenticate Isadore Instance
    # TODO: Limit number of times can confirm?
    # TODO: Confirm expire date?
    # TODO: Implement
    info = db.get_info(phone=phone)
    oneday = datetime.timedelta(days=1)
    if info["phone_verify"]:
        last_try_date = info["phone_verify"]["last_try"]
        if datetime.datetime.now() - last_try_date < oneday:
            abort(400)
    phone_verify = {"last_try": datetime.datetime.now(), "confirm_code": random.randint(100000, 999999)}
    db.update_info(info_update=phone_verify, phone=phone)
    msg = twiml_messages.sms_verify % (phone_verify["confirm_code"])
    messaging.sendTxt(phone, msg)
    return ('Sent', 204)


@app.route('/alarm_contact_info_phone/<phone>/confirm/sms', methods=["PUT"])
def alarm_contact_confirm_sms_put():
    """
    Confirm phone that was done through SMS.
    :return:
    """
    # TODO: Authenticate Isadore Instance
    # TODO: Limit number of times can confirm?
    # TODO: Confirm expire date?
    info = db.get_info(phone=phone)
    oneday = datetime.timedelta(days=1)
    if info["phone_verify"] and info["phone_verify"]["last_try"] < oneday:
        verify_key = request.form.get("confirm_code")
        if info["phone_verify"]["confirm_code"] == verify_key:
            db.set_verified(phone=phone)
            return ('Verified', 204)
    abort(400)


@app.route('/isadore_instance_info/', methods=["GET"])
def isadore_instance_info():
    pass




if __name__ == '__main__':
    app.run()
