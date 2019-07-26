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

from tests import TestIsadore
from restkit import Resource, BasicAuth, request, Unauthorized
import json
import ConfigParser
import util

class TestPrivileges(TestIsadore):
	def testPrivilegesGet(self):
		path = '/resources/privileges'
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			privileges = self.getJSONResource(path, user)
			self.assertEquals(5, len(privileges['xlink']), "Wrong number of privileges back: " + user.credentials[0])
		
		self.unauthorizedChecks([None], path)
		
	def testPrivilegesGetId(self):
		path = "/resources/privileges/100"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			privilege = self.getJSONResource(path, user)
			name = user.credentials[0]
			self.assertTrue(privilege['name'] == 'User', "Got bad privilege info: " + name)
		self.unauthorizedChecks([None], path)


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
