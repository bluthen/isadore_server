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
from restkit import Resource, ResourceNotFound
import json
import random


class TestSensors(TestIsadore):
	
	def setUp(self):
		TestIsadore.setUp(self)
		self.convert_py = "5 +" + str(random.randrange(100, 999))
		self.newparams = {"device_id":10, "sensor_type_id":10, "enabled_p": True, "convert_py": self.convert_py, "bias": 3, "enabled_p": True}
	
	def newSensor(self):
		path = "/resources/conf/sensors"
		user = self.testconfiguser
		res = Resource(self.baseurl, filters=[user])
		output = res.request("POST", path, params_dict=self.newparams)
		self.assertEqual(200, output.status_int, "Wrong response code from post.")
		xlink = json.loads(output.body_string())
		return xlink
	
	def deleteSensor(self, id):
		path = "/resources/conf/sensors/" + str(id)
		user = self.testconfiguser
		res = Resource(self.baseurl, filters=[user])
		output = res.request("DELETE", path=path)
		self.assertEqual(204, output.status_int, "Wrong response code from delete.")

	def getSensor(self, id):
		path = "/resources/conf/sensors/" + str(id)
		user = self.testconfiguser
		sensor = self.getJSONResource(path, user)
		return sensor


	def testSensorsGet(self):
		xlink = self.newSensor()
		id = self.getFirstIdFromXLink(xlink)
		path = "/resources/conf/sensors"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			sensors = self.getJSONResource(path, user, params_dict={'device_id': self.newparams['device_id']})
			found = False
			for sensor in sensors['xlink']:
				if(int(sensor[sensor.rfind("/") + 1:]) == id):
					found = True
					break
			self.assertTrue(found, "Expected sensor was not found.")
		self.unauthorizedChecks([None], path)
		self.deleteSensor(id)


	def testSensorsNewDelete(self):
		xlink = self.newSensor()
		id = self.getFirstIdFromXLink(xlink)
		sensor = self.getSensor(id)
		self.assertEqual(self.convert_py, sensor['convert_py'], "Wrong data in new sensor.")
		self.unauthorizedChecks([None], "/resources/conf/sensors/" + str(id), "GET", params_dict=self.newparams)

		self.unauthorizedChecks([None, self.testuser, self.testfilluser], "/resources/conf/sensors/" + str(id), "DELETE")
		self.deleteSensor(id)
		exception = False
		try:
			sensor = self.getSensor(id)
		except ResourceNotFound:
			exception = True
			
		self.assertTrue(exception, "New sensor was not deleted.")
		
		self.unauthorizedChecks([None, self.testuser, self.testfilluser], "/resources/conf/sensors", "POST", params_dict=self.newparams)

	def testSensorsGetUpdate(self):
		xlink = self.newSensor()
		id = self.getFirstIdFromXLink(xlink)
		self.convert_py = "8 + 20"
		self.newparams['convert_py'] = self.convert_py
		
		path = "/resources/conf/sensors/" + str(id)
		for user in [self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			self.convert_py = "5 +" + str(random.randrange(100, 999))
			self.newparams['convert_py'] = self.convert_py
			res = Resource(self.baseurl, filters=[user])
			output = res.request("PUT", path=path, params_dict=self.newparams)
			self.assertEqual(204, output.status_int, "Wrong response code: " + user.credentials[0])
			sensor = self.getSensor(id)
			self.assertEqual(self.convert_py, sensor['convert_py'], 'Sensor was not updated.')
		
		self.unauthorizedChecks([None, self.testuser, self.testfilluser], path, method='PUT', params_dict=self.newparams)
		self.unauthorizedChecks([None], path, method='GET')
		self.deleteSensor(id)


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
