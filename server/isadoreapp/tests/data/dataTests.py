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

class dataTests (TestIsadore):
	"""Tests for base reading and reading data functionality """

	def testGetLatest(self):
		"""Test ability to get latest reading"""

		path = "/resources/data/readings/last"
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			latestReading = self.getJSONResource(path, user)

		self.unauthorizedChecks([None], path)

	def testGetReadingData(self):
		"""Test ability to get data associated with a given reading."""

		path = "/resources/data/readings/100"

		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			res = Resource(self.baseurl, filters=[user])
			output = res.request("GET",path=path,
								 params_dict = {"bin_id": 102,
												"bin_section_id": 103,
												"sensor_type_id": 10})

		self.unauthorizedChecks([None], path)

class fillTests (TestIsadore):
	"""Tests for base fill functionality """

	def testGet(self):
		"""Test ability to get list of fills"""

		path = "/resources/data/fills"
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			res = Resource(self.baseurl, filters=[user])
			# test with all of the parameters present
			output = res.request("GET",path=path,
								 params_dict = {"bin_id": 100,
												"field_code": "100A",
												"hybrid_code": "100A",
												"storage_bin_number": 100,
												"storage_bin_code": "100A",
												"begin_datetime": "010110080910",
												"end_datetime": "120111080910"})
			try:
				exception_p = False
				output = res.request("GET",path=path,
									 params_dict = {"bin_id": 100,
													"field_code": "100A",
													"hybrid_code": "100A",
													"storage_bin_number": 100,
													"storage_bin_code": "100A",
													"begin_datetime": "010111080910",
													"end_datetime": "120111080910"})
			except:
				exception_p = True
			self.assertFalse(exception_p,"Wrongfully, matching fills were found.")
		self.unauthorizedChecks([None], path)

	def testNew(self):
		"""succeed in creating fill"""
		path = "/resources/data/fills"
		user = self.testfilluser
		res = Resource(self.baseurl, filters=[user])

		# perform request
		output = res.request("POST",
							 path=path,
							 params_dict = {"fill_number": 100,
											"air_begin_datetime": "010110080910",
											"end_datetime":  "110110080910",
											"start_datetime": "010110080910",
											"rotation_number": 100,
											"bin_id": 14,
											"hybrid_code":"100A",
											"field_code":"100A",
											"storage_bin_number":100,
											"storage_bin_code":"100A",
											"pre_mc_count":2,
											"pre_mc": "33,31.2",
											"post_mc_count":3,
											"post_mc":"17,16,17.2",
											"bushels":42}
								 )

		self.unauthorizedChecks([None,self.testuser], path, method="POST")

	def testUpdate(self):
		"""succeed in updating fill"""
		path = "/resources/data/fills/101"
		user = self.testfilluser
		res = Resource(self.baseurl, filters=[user])

		# perform request
		output = res.request("PUT",
							 path=path,
							 params_dict = {"fill_number": 100,
											"begin_datetime": "010110080910",
											"end_datetime":  "110110080910",
											"rotation_number": 100,
											"bin_id": 13,
											"hybrid_code":"100A",
											"field_code":"100A",
											"storage_bin_number":100,
											"storage_bin_code":"100A",
											"pre_mc_count":2,
											"pre_mc": "33,31.2",
											"post_mc_count":3,
											"post_mc":"17,16,17.2",
											"bushels":42}
								 )

		self.unauthorizedChecks([None,self.testuser], path)

		# TODO: verify output return code indicates update occured

	def testGetID(self):
		"""Test ability to get info for a particular fills"""

		path = "/resources/data/fills/101"
		for user in [self.testuser, self.testpoweruser, self.testsuperuser]:
			# test with all of the parameters present
			readingData = self.getJSONResource(path, user)

		self.unauthorizedChecks([None], path)

	def testDelete(self):
		"""Succeed in deleting fill."""

		path = "/resources/data/fills/100"
		user = self.testpoweruser
		res = Resource(self.baseurl, filters=[user])

		output = res.request("DELETE",path=path)

		self.assertEqual(204,output.status_int,"Fill user was unable to delete fill.")



# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
