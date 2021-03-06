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
import random

checklist = {"alpha":False, "special":False, "number":False, "upAlpha":False}

def genAlpha():
	return chr(random.randrange(97, 123));

def genSpecial():
	special=["~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "+", "{", "}", "_", "=", "?", ",", ".",":"];
	return special[random.randrange(0, 21)]

def genNumber():
	return random.randrange(0, 10)

def genUpAlpha():
	return chr(random.randrange(65,91))

def generatePassword():
	done = False
	password = ""
	while (not done):
		if (len(password) > 8):
			if ( not checklist["alpha"] ):
				checklist["alpha"] = True
				password += genAlpha()
			elif ( not checklist["special"] ):
				checklist["special"] = True
				password += genSpecial()
			elif ( not checklist["number"] ):
				checklist["number"] = True
				password += str(genNumber())
			elif ( not checklist["upAlpha"] ):
				checklist["upAlpha"] = True
				password += genUpAlpha()
			else:
				done = True
		else:
			type = random.randrange(0, 4)
			if ( type == 0 ):
				checklist["alpha"] = True
				password += genAlpha()
			if ( type == 1 ):
				checklist["special"] = True
				password += genSpecial()
			if ( type == 2 ):
				checklist["number"] = True
				password += str(genNumber())
			if ( type == 3 ):
				checklist["upAlpha"] = True
				password += genUpAlpha()
	return password
	


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
