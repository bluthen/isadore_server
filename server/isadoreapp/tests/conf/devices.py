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
Created on Jul 26, 2011

'''


from tests import TestIsadore
from restkit import Resource, ResourceNotFound
import json
import random

class TestDevices(TestIsadore):
	
	def setUp(self):
		TestIsadore.setUp(self)
		self.name = "test device" + str(random.randrange(100, 999))
		self.newparams = {"device_type_id":10, "name": self.name, "enabled_p": True, "address": 321, "port": 3, "enabled_p": True, "bin_id": 22, "bin_section_id":13, "year":2013}
	
	def newDevice(self):
		path = "/resources/conf/devices"
		user = self.testconfiguser
		res = Resource(self.baseurl, filters=[user])
		output = res.request("POST", path, params_dict=self.newparams)
		self.assertEqual(200, output.status_int, "Wrong response code from post.")
		xlink = json.loads(output.body_string())
		return xlink
	
	def deleteDevice(self, id):
		path = "/resources/conf/devices/" + str(id)
		user = self.testconfiguser
		res = Resource(self.baseurl, filters=[user])
		output = res.request("DELETE", path=path)
		self.assertEqual(204, output.status_int, "Wrong response code from delete.")

	def getDevice(self, id):
		path = "/resources/conf/devices/" + str(id)
		user = self.testconfiguser
		device = self.getJSONResource(path, user)
		return device

	def testDevicesGet(self):
		xlink = self.newDevice()
		id = self.getFirstIdFromXLink(xlink)
		path = "/resources/conf/devices"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			devices = self.getJSONResource(path, user, {"year":2013})
			found = False
			for device in devices['xlink']:
				if(int(device[device.rfind("/") + 1:]) == id):
					found = True
					break
			self.assertTrue(found, "Expected device was not found.")
		self.unauthorizedChecks([None], path)
		self.deleteDevice(id)

	def testDevicesNewDelete(self):
		xlink = self.newDevice()
		id = self.getFirstIdFromXLink(xlink)
		device = self.getDevice(id)
		self.assertEqual(self.name, device['name'], "Wrong data in new device.")
		self.unauthorizedChecks([None], "/resources/conf/devices/" + str(id), "GET", params_dict=self.newparams)

		self.unauthorizedChecks([None, self.testuser, self.testfilluser], "/resources/conf/devices/" + str(id), "DELETE")
		self.deleteDevice(id)
		exception = False
		try:
			device = self.getDevice(id)
		except ResourceNotFound:
			exception = True
			
		self.assertTrue(exception, "New device was not deleted.")
		
		self.unauthorizedChecks([None, self.testuser, self.testfilluser], "/resources/conf/devices", "POST", params_dict=self.newparams)

	def testDevicesGetUpdate(self):
		xlink = self.newDevice()
		id = self.getFirstIdFromXLink(xlink)
		self.name = "updated device"
		self.newparams['name'] = self.name
		
		path = "/resources/conf/devices/" + str(id)
		for user in [self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			self.name = "test device" + str(random.randrange(100, 999))
			self.newparams['name'] = self.name
			res = Resource(self.baseurl, filters=[user])
			output = res.request("PUT", path=path, params_dict=self.newparams)
			self.assertEqual(204, output.status_int, "Wrong response code: " + user.credentials[0])
			device = self.getDevice(id)
			self.assertEqual(self.name, device['name'], 'Device was not updated.')
		
		self.unauthorizedChecks([None, self.testuser, self.testfilluser], path, method='PUT', params_dict=self.newparams)
		self.unauthorizedChecks([None], path, method='GET')
		self.deleteDevice(id)
	



# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
