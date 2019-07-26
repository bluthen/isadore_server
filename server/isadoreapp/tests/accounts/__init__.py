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
import unittest
from restkit import Resource, BasicAuth, request, Unauthorized
import json
import ConfigParser
import util
import random
from passgen import generatePassword


class TestAccounts(TestIsadore):
	def testAccountsGet(self):
		path = '/resources/accounts'
		for user in [self.testpoweruser, self.testsuperuser]:
			accounts = self.getJSONResource(path, user)
			#TODO: Check that power user got no super users.

		self.unauthorizedChecks([None, self.testuser, self.testfilluser, self.testconfiguser], path)

	def testAccountsGetId(self):
		path = "/resources/accounts/" + str(self.dbuser.id)
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			account = self.getJSONResource(path, user)
			self.assertEqual(self.dbuser.email, account['email'], "Wrong account retrieved as " + user.credentials[0])
		path = "/resources/accounts/" + str(self.dbsuperuser.id)
		self.unauthorizedChecks([None, self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser], path)

	def testAccountsUpdate(self):
		path = "/resources/accounts/" + str(self.dbfilluser.id)
		for user in [self.testfilluser, self.testpoweruser, self.testsuperuser]:
			name = user.credentials[0]
			res = Resource(self.baseurl, filters=[user])
			phone = str(random.randrange(10000000000, 99999999999))
			params = {"name": self.dbfilluser.name, "email":self.dbfilluser.email, "phone":phone, "privilege_id":self.dbfilluser.privilege_id}
			output = res.request("PUT", path=path, params_dict=params)
			self.assertEqual(204, output.status_int, "Wrong response code: " + name)
			self.dbfilluser = util.getAccountByEmail(self.dbfilluser.email)
			self.assertEqual(self.dbfilluser.phone, phone, "Account not updated.")
		self.unauthorizedChecks([None, self.testuser, self.testconfiguser], path, method='PUT', params_dict=params)

	def testAccountsNewDelete(self):
		path = "/resources/accounts"
		user = self.testpoweruser
		res = Resource(self.baseurl, filters=[user])
		email = "newusertest@exotericanalytics.com"
		self.assertEqual(None, util.getAccountByEmail(email), "Account to add already exists.")
		params = {"name": "New User Test", "email": "newusertest@exotericanalytics.com", "phone": "15555555555", "privilege_id": 100}
		output = res.request("POST", path=path, params_dict=params)
		self.assertEqual(200, output.status_int, "Wrong response code from post.")
		xlink = json.loads(output.body_string())

		#check account got created.
		new_account = util.getAccountByEmail(email)
		self.assertNotEqual(None, new_account, "New account was not created")

		#Check link returned is correct.
		path = xlink["xlink"][0]
		self.assertEquals("/resources/accounts/" + str(new_account.id), path, "Link returned does not match new account")

		#DELETE new account
		output = res.request("DELETE", path=path)
		self.assertEqual(204, output.status_int, "Wrong response code from delete.")
		new_account = util.getAccountByEmail(email)
		self.assertEqual(None, util.getAccountByEmail(email), "Failed to delete account.")

		#authorized checks
		#new
		self.unauthorizedChecks([None, self.testuser, self.testfilluser, self.testconfiguser], "/resources/accounts", "POST", params_dict=params)
		#delete
		self.unauthorizedChecks([None, self.testuser, self.testfilluser, self.testconfiguser], "/resources/accounts/1", "DELETE")



# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
