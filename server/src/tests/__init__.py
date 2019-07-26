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
import unittest
from restkit import Resource, BasicAuth, Unauthorized 
import ConfigParser
import json
import util



class TestIsadore(unittest.TestCase):
	"""Unit test that tests restian api, not-individual methods. Method unit 
	tests should be done in a different class."""
	def setUp(self):
		config = ConfigParser.ConfigParser()
		config.read('test.cfg')
		self.baseurl = config.get('tests', 'baseurl')
		
		email, password = config.get('tests', 'testsuperuser').split(",", 1)
		self.dbsuperuser = util.getAccountByEmail(email)
		self.testsuperuser = BasicAuth(email, password)
		
		email, password = config.get('tests', 'testpoweruser').split(",", 1)
		self.dbpoweruser = util.getAccountByEmail(email)
		self.testpoweruser = BasicAuth(email, password)
		
		email, password = config.get('tests', 'testconfiguser').split(",", 1)
		self.dbconfiguser = util.getAccountByEmail(email)
		self.testconfiguser = BasicAuth(email, password)
		
		email, password = config.get('tests', 'testfilluser').split(",", 1)
		self.dbfilluser = util.getAccountByEmail(email)
		self.testfilluser = BasicAuth(email, password)
		
		email, password = config.get('tests', 'testuser').split(",", 1)
		self.dbuser = util.getAccountByEmail(email)
		self.testuser = BasicAuth(email, password)
	
	def tearDown(self):
		unittest.TestCase.tearDown(self)
	
	def unauthorizedChecks(self, users, path, method="GET", params_dict=None):
		""":param users: list of BasicAuths to try, expecting Unauthorized"""
		for user in users:
			name = "None"
			if(user):
				name = user.credentials[0]
			exception = False
			try:
				res = Resource(self.baseurl, filters=[user])
				output = res.request(method, path, params_dict=params_dict)
			except Unauthorized:
				exception = True
			self.assertTrue(exception, "No unauthorized exception for " + name)
	
	def getJSONResource(self, path, user, params_dict=None):
		name = user.credentials[0]
		res = Resource(self.baseurl, filters=[user])
		output = res.get(path, None, params_dict=params_dict)
		self.assertEqual(200, output.status_int, "Wrong response code: " + name)
		response = json.loads(output.body_string())
		return response
	
	def getFirstIdFromXLink(self, xlink):
		a=xlink['xlink'][0]
		return int(a[a.rfind("/")+1:]) 




# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
