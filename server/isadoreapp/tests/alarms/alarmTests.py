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

class TestAlarms(TestIsadore):
	"""Tests for base alarm functionality """

	def testGet(self):
		"""Test ability to get list of alarms"""

		path = "/resources/alarms"
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			alarmList = self.getJSONResource(path, user)

		self.unauthorizedChecks([None], path)

	def testGetID(self):
		"""Test ability to get specific alarm"""
		path = "/resources/alarms/" + str(100) # get alarm with id 100
		user = self.testpoweruser
		res = Resource(self.baseurl, filters=[user])
		alarm = self.getJSONResource(path, user) # method has assertion inside

	def testNewByPowerUser(self):
		"""succeed in creating alarm for any user"""
		path = "/resources/alarms"
		user = self.testpoweruser
		res = Resource(self.baseurl, filters=[user])

		exception = False

		# perform request
		try:
			output = res.request("POST",path=path,
								 params_dict = {"alarm_type_id": 10,
												"account_id": 103,
												"greater_than_p": False,
												"value": 0})
		except Unauthorized:
			exception = True
		# check that addition succeeded
		self.assertFalse(exception, "Power user was unable to add alarm for lower level user.")
		# get the returned url
		xlink = json.loads(output.body_string())
		# TODO: should the API check for duplicate alarm entries in the DB?
		# TODO: check that the alarm was, in fact, created with the correct data

	def testNewByUserForSelf(self):
		"""succeed in creating alarm for self"""
		path = "/resources/alarms"
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])

		# perform request
		output = res.request("POST",
							 path=path,
							 params_dict = {"alarm_type_id": 10, # value from DB
											"account_id": 104, # value from DB
											"sensor_type_id": 100, # value from DB
											"greater_than_p": True,
											"value": 100
											}
							 )

		# check that addition succeeded
		self.assertEqual(200, output.status_int, "User was unable to add alarm for self.")

		# get the returned url
		xlink = json.loads(output.body_string())

	def testNewByUserForOthers(self):
		"""fail to create alarm for others"""

		path = "/resources/alarms"
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])

		# perform request
		exception = False
		try:
				output = res.request("POST",
									 path=path,
									 params_dict = {"alarm_type_id": 10, # value from DB
													"account_id": 101, # a differnt user from DB
													"greater_than_p": False,
													"value": 0
													}
									 )
		except Unauthorized:
				exception = True

		# check that addition failed
		self.assertTrue(exception, "User was able to add alarm for another user.")

	def testUpdateByPowerUser(self):
		"""succeed in updating any alarm"""

		path = "/resources/alarms/101"	# alarm id from DB
		user = self.testpoweruser
		res = Resource(self.baseurl, filters=[user])

		# perform request
		output = res.request("PUT",
							 path=path,
							 params_dict = {"alarm_type_id": 13, # changeing from 2 to 1
											"account_id": 100, # std user from the DB
											"sensor_type_id": 100, # value from DB
											"greater_than_p": True,
											"value": 1000
											}
							 )

		# check that update succeeded
		self.assertEqual(202, output.status_int, "Power user was unable to update alarm for another user.")

	def testUpdateByUserForSelf(self):
		"""succeed in updating alarm belonging to self"""

		path = "/resources/alarms/115"	# id taken from DB
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])
		# perform request
		output = res.request("PUT",path=path,
							 params_dict = {"alarm_type_id": 14, # changeing from 2 to 1
											"account_id": 104, # std user from the DB
											"greater_than_p": True,
											"value": 105})
		# check that update succeeded
		self.assertEqual(202, output.status_int, "User was unable to update alarm for self.")

	def testUpdateByUserForOthers(self):
		"""fail to update alarms belonging to others"""
		# TODO: improve test to attempt to update alarm belonging to another user instead of a higher level user
		path = "/resources/alarms/100"	# id taken from DB (belongs to a power user)
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])

		try:
			exception = False

			# perform request
			output = res.request("PUT",
								 path=path,
								 params_dict = {"alarm_type_id": 14, # changeing from 2 to 1
												"account_id": 106, # std user from the DB
												"sensor_type_id": 100, # value from DB
												"greater_than_p": True,
												"value": 100
												}
								 )
		except Unauthorized:
			exception = True

		# check that update failed
		self.assertTrue(exception, "User was able to update alarm for another user.")

	def testDeleteByPowerUser(self):
		"""Power user to succeed in deleting alarm"""

		path = "/resources/alarms/113"	# alarm belonging to a poweruser
		user = self.testpoweruser
		res = Resource(self.baseurl, filters=[user])
		output = res.request("DELETE",path=path)
		self.assertEqual(204,output.status_int,"Power user was unable to delete alarm")

	def testDeleteNonExistantAlarm(self):
		"""Power user to fail in deleting non-existant alarm"""

		path = "/resources/alarms/8"
		user = self.testpoweruser
		res = Resource(self.baseurl, filters=[user])

		try:
			exception = False
			output = res.request("DELETE",path=path)
		except:							# which  exception should I catch?
			exception = True

		self.assertTrue(exception,"Failed to return 404 for missing alarm.")

	def testDeleteByUserForSelf(self):
		"""succeed in deleting own"""

		path = "/resources/alarms/114"	# alarm belonging to this user
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])

		output = res.request("DELETE",path=path)

		self.assertEqual(204,output.status_int, "User was unable to delete alarm belonging to self.")

	def testDeleteByUserForOthers(self):
		"""fail to delete others' alarms"""

		path = "/resources/alarms/100"	# alarm belonging to a poweruser
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])

		try:
			exception = False
			output = res.request("DELETE",path=path)
		except:							# which  exception should I catch?
			exception = True

		self.assertTrue(exception,"Failed to return 404 for missing alarm.")


class TestAlarmTypes(TestIsadore):
	"""Tests for alarm_type functionality """

	def testGet(self):
		"""Test ability to get list of alarm types"""

		path = "/resources/alarms/alarm_types"
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			alarmList = self.getJSONResource(path, user)

		self.unauthorizedChecks([None], path)

	def testGetID(self):
		"""Test ability to get specific alarm type info"""

		path = "/resources/alarms/alarm_types/" + str(10) # get alarm_type with id 1
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			alarm = self.getJSONResource(path, user)

		self.unauthorizedChecks([None], path)

	# def testGetIDmissing(self):
	# 	"""Test ability to get specific alarm"""
	# 	path = "/resources/alarms/" + str(1) # get alarm with id 1
	# 	user = self.testpoweruser
	# 	res = Resource(self.baseurl, filters=[user])

	# 	alarm = self.getJSONResource(path, user)

	# 	# check that addition succeeded
	# 	self.assertTrue(200, alarm, "Alarm not found.")


class TestAlarmContactTypes(TestIsadore):
	"""Tests for alarm_contact_type functionality """

	def testGet(self):
		"""Test ability to get list of alarm contact types"""

		path = "/resources/alarms/alarm_contact_types"
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			alarmList = self.getJSONResource(path, user)

		self.unauthorizedChecks([None], path)

	def testGetID(self):
		"""Test ability to get specific alarm contact type info"""

		path = "/resources/alarms/alarm_contact_types/" + str(100) # get alarm_type with id 1
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			alarm = self.getJSONResource(path, user)

		self.unauthorizedChecks([None], path)

	# def testGetIDmissing(self):
	# 	"""Test ability to get specific alarm"""
	# 	path = "/resources/alarms/" + str(1) # get alarm with id 1
	# 	user = self.testpoweruser
	# 	res = Resource(self.baseurl, filters=[user])

	# 	alarm = self.getJSONResource(path, user)

	# 	# check that addition succeeded
	# 	self.assertTrue(200, alarm, "Alarm not found.")


class TestAlarmContacts(TestIsadore):
	"""Tests for alarm contacts functionality """

# XXX: ability to get this information alone appears to have been removed
	# def testGet(self):
	# 	"""Test ability to get list of alarm contacts for a particular alarm.  testfilluser and testuser are currently excluded b/c alarm_id belongs to higher level user."""

	# 	path = "/resources/alarms/alarm_contact"

	# 	for user in [self.testpoweruser, self.testsuperuser]:
	# 		# perform request
	# 		res = Resource(self.baseurl, filters=[user])
	# 		output = res.request("GET",path=path,
	# 							 params_dict = {"alarm_id": 101})

	# 		self.assertEqual(200,output.status_int, "User, " + str(user) + " was unable to obtain list of alarm contacts.")

	# 	self.unauthorizedChecks([None], path)

# XXX: ability to get this information alone appears to have been removed
	# def testGetID(self):
	# 	"""Test ability to get specific alarm contact info.  testuser and testfilluser are currently excluded from this test b/c alarm belongs to higher level user."""

	# 	path = "/resources/alarms/alarm_contacts/" + str(102) # get alarm_contact for alarm 102
	# 	for user in [self.testpoweruser, self.testsuperuser]:
	# 		alarm = self.getJSONResource(path, user)

	# 	self.unauthorizedChecks([None], path)

	
	def testNewByUserForSelf(self):
		"""create alarm contact for self"""
		path = "/resources/alarms"
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])
		# perform request
		output = res.request("POST",path=path,
							 params_dict = {"alarm_type_id": 10,
											"account_id":104,
											"alarm_contact_type_ids": 100})
		# check if addition failed
		self.assertEqual(200, output.status_int, "User was unable to add alarm contact for self.")
		# get the returned url
		xlink = json.loads(output.body_string())

	def testNewByUserForOthers(self):
		"""create alarm contact for another user"""

		path = "/resources/alarms/alarm_contacts"
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])

		try:
			exception_p = False

			# perform request
			output = res.request("POST",
								 path=path,
								 params_dict = {"alarm_id": 1, # value from DB
												"contact_type_id": 1, # value from DB
												}
								 )
		except:
			exception_p = True
			
		# check that addition failed
		self.assertTrue(exception_p, "User was able to add alarm contact for another user.")

	def testDeleteByUserForSelf(self):
		"""succeed in deleting own alarm contact"""

		path = "/resources/alarms/104"	# alarm contact belonging to this user
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])

		output = res.request("DELETE",path=path)

		self.assertEqual(204,output.status_int, "User was unable to delete alarm belonging to self.")

	def testDeleteByUserForOthers(self):
		"""fail to delete other's alarm contact"""

		path = "/resources/alarms/alarm_contacts/100"	# alarm belonging to a poweruser
		user = self.testuser
		res = Resource(self.baseurl, filters=[user])

		try:
			exception = False
			output = res.request("DELETE",path=path)
		except:							# which  exception should I catch?
			exception = True

		self.assertTrue(exception,"Failed to return 404 for missing alarm.")

	def testDeleteByPowerUserForOthers(self):
		"""succeed in deleting other's alarm contact"""

		path = "/resources/alarms/112"	# alarm contact belonging to another user
		user = self.testpoweruser
		res = Resource(self.baseurl, filters=[user])

		output = res.request("DELETE",path=path)

		self.assertEqual(204,output.status_int, "Power user was unable to delete alarm belonging to lower level user.")


class TestAlarmEvents(TestIsadore):
	"""Tests for alarm events functionality """

	def testGet(self):
		"""Test ability to get list of alarm events"""

		path = "/resources/alarms/events"
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			# perform request
			res = Resource(self.baseurl, filters=[user])
			output = res.request("GET",path=path,
								 params_dict = {"begin": "010111134553",
												"end": "120111134553"})

			self.assertEqual(200,output.status_int, "User, " + str(user) + " was unable to obtain list of alarm events.")

		self.unauthorizedChecks([None], path)

	def testGetID(self):
		"""Test ability to get info for a specific alarm event"""
		path = "/resources/alarms/events/" + str(100) # get alarm_event with id 100
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			alarm = self.getJSONResource(path, user)
		self.unauthorizedChecks([None], path)

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
