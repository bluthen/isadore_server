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



v1_incoming_voice = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather timeout="120" numDigits="1" action="v1_incoming_voice_response1" method="POST">
            <Say voice="woman">
                Hello, this is the Isadore Alarm Service. Please select an option. Press 1 to call Employee One. Press
                2 to call Employee Two. Press 3 to call Employee three.
            </Say>
        </Gather>
    </Response>"""

v1_sms_help = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Sms>Isadore Alarm Commands:
STOP - to unsubscribe.
</Sms>
    </Response>"""


# Version 2

incoming_voice = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather timeout="120" numDigits="1" action="incoming_voice_response1" method="POST">
            <Say voice="woman">
                Hello, this is the Isadore Alarm Service. Please select an option. Press 8 to unsubscribe from any
                future alarms. Press 1 to call Employee One. Press 2 to call Employee two. Press 7 to pause
                alarms for a number of hours. Press 9 to resume alarms.
            </Say>
        </Gather>
    </Response>"""
dial_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman">
        Connecting you to %s, please wait...
        </Say>
        <Dial>%s</Dial>
    </Response>"""
unsubscribed = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman">
            You have been unsubscribed from future alarms. Thank you.
        </Say>
        <Hangup/>
    </Response>"""
resume = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman">
            Alarms have been resumed. Thank you.
        </Say>
        <Hangup/>
    </Response>"""
resume_but_blacklisted = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman">
            Our records indicate you are on a no contact list. In order to resume fully you must text the word, "START", to
            this number. Thank you and Good-bye.
        </Say>
        <Hangup/>
    </Response>"""
pause_prompt = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather timeout="30" numDigits="3" action="incoming_voice_response_pause" method="POST">
            <Say voice="woman">
                Please enter the number of hours you would like to pause alarms for followed by the pound key.
            </Say>
        </Gather>
    </Response>"""
invalid_choice = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman">
        You selected an invalid option.
        </Say>
        <Redirect method="POST">%s</Redirect>
    </Response>"""
paused = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman">
            All alarms have been paused for %s hours. Thank you.
        </Say>
    </Response>
    """

outgoing = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather timeout="45" numDigits="1" action="../outgoing_response" method="POST">
            <Say voice="woman">
                Hello, this is the Isadore Alarm Service. The following alarm has been triggered: %s Press 8 to
                unsubscribe from any future alarms. Press 7 to pause alarms for a number of hours.
            </Say>
        </Gather>
    </Response>"""

sms_help = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Sms>Isadore Alarm Commands:
STOP - to unsubscribe.
PAUSE XXX - pause alarms for XXX hours.
START - resume all alarms.

For more better control log in to Isadore.</Sms>
    </Response>"""
sms_paused = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Sms>You will receive no further alarms for %d hours. Reply START to resume all alarms before then.</Sms>
    </Response>"""
sms_paused_invalid = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Sms>Invalid pause command.
PAUSE XXX - pause alarms for XXX hours.

Example:
PAUSE 12</Sms>
    </Response>"""
sms_resumed = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Sms>Alarms have been resumed.</Sms>
    </Response>"""
sms_unsubscribe = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Sms>You have been unsubscribed from all alarms.</Sms>
    </Response>"""

sms_verify = """Isadore Alarm verification code: %d"""


voice_verify = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather timeout="45" numDigits="1" action="./voice3" method="POST">
            <Say voice="woman">
                This is the Isadore Alarm system calling to verify your phone number. Please press 1 to enable getting
                alarms at this number. Press 9 to never receive these calls again. Otherwise hang up.
            </Say>
        </Gather>
    </Response>"""

voice_verify_verified = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman">
            Your number has been verified and can receive Isadore Alarms. Thank you, goodbye.
        </Say>
    </Response>"""

voice_verify_stop = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman">
            We will not contact you again. Thank you, goodbye.
        </Say>
    </Response>"""


email_verify_txt = """Hello, please confirm your email going to the link below:

https://alarms.example.com/static/ev.html?%s

Or go to:

https://alarms.example.com/verify_email
Enter your email address and copy and paste the confirmation code:

%s

"""

email_verify_html = """<html><body>
Hello, please confirm your email going to the link below:<br/>
<br/>
<a href="https://alarms.example.com/static/ev.html?%s">https://alarms.example.com/static/ev.html?%s</a><br/>
<br/>
Or go to:<br/>
<br/>
<a href="https://alarms.example.com/static/ev.html">https://alarms.example.com/static/ev.html</a><br/>
Enter your email address and copy and paste the confirmation code:<br/>
<br/>
%s<br/>
<br/>
</body></html>"""
