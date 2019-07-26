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
'''
Created on Jul 25, 2011

'''

from tests import TestIsadore

class TestDeviceTypes(TestIsadore):
	def testDeviceTypesGet(self):
		path = "/resources/conf/device_types"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			binSections = self.getJSONResource(path, user)
			self.assertEqual(6, len(binSections['xlink']), "Wrong number of device types.")
		self.unauthorizedChecks([None], path)
		
	def testDeviceTypesGetId(self):
		path = "/resources/conf/device_types/10"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			binSection = self.getJSONResource(path, user)
			self.assertEquals(binSection['id'], 10, "Got unexpected device type.")
			self.assertEquals(binSection['name'], 'EA Sensor Unit v2.03')
		path = "/resources/conf/device_types/11"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			binSection = self.getJSONResource(path, user)
			self.assertEquals(binSection['id'], 11, "Got unexpected device type.")
			self.assertEquals(binSection['name'], 'Fuji PXR4-REY1-GVVA1')
			
		self.unauthorizedChecks([None], path)


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
