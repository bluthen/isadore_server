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
import random
from restkit import Resource


class TestGeneral(TestIsadore):
	
	def testGeneralGet(self):
		path = "/resources/conf/general"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			general = self.getJSONResource(path, user)
			self.assertTrue("alarm_clear_interval" in general, "Couldn't get general config: " + user.credentials[0])
		self.unauthorizedChecks([None], path)
	
	def testGeneralUpdate(self):
		path = "/resources/conf/general"
		for user in [self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			newinterval = random.randrange(300, 600)
			general = self.getJSONResource(path, user)
			general['interval'] = newinterval
			res = Resource(self.baseurl, filters=[user])
			output = res.request("PUT", path=path, params_dict=general)
			self.assertEqual(204, output.status_int, "Wrong response code: " + user.credentials[0])
			general = self.getJSONResource(path, user)
			self.assertEquals(newinterval, int(general['interval']), "General not updated.")
		
		self.unauthorizedChecks([None, self.testuser, self.testfilluser], path, method="PUT")


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
