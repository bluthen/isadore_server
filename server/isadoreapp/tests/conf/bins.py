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

class TestBins(TestIsadore):
	def testBinsGet(self):
		path = "/resources/conf/bins"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			binItems = self.getJSONResource(path, user)
			self.assertEqual(37, len(binItems['xlink']), "Wrong number of bins.")
		self.unauthorizedChecks([None], path)
	
	def testBinsGetId(self):
		path = "/resources/conf/bins/12"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			binItem = self.getJSONResource(path, user)
			self.assertEquals(binItem['id'], 12, "Got unexpected bin id.")
			self.assertEquals(binItem['name'], 'Bin 1')
		path = "/resources/conf/bins/10"
		for user in [self.testuser, self.testfilluser, self.testconfiguser, self.testpoweruser, self.testsuperuser]:
			binItem = self.getJSONResource(path, user)
			self.assertEquals(binItem['id'], 10, "Got unexpected bin id.")
			self.assertEquals(binItem['name'], 'Fan 1')
		self.unauthorizedChecks([None], path)

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
