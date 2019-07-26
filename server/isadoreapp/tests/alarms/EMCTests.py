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
import datetime
import isadore_web.server.src.alarms.EMC as EMC
import unittest

class TestEMC(unittest.TestCase):
	
	def testComputeTime(self):
		tests=[
				[
					datetime.datetime(2011, 9, 1, 0, 0, 0, 0),
					datetime.datetime(2011, 9, 9, 0, 0, 0, 0),
					datetime.timedelta(days=7, hours=23)
				],
				[
					datetime.datetime(2011, 8, 20, 0, 0, 0, 0),
					datetime.datetime(2011, 8, 21, 0, 0, 0, 0),
					datetime.timedelta(days=1)
				],
				[
					datetime.datetime(2011, 9, 3, 0, 0, 0, 0),
					datetime.datetime(2011, 9, 4, 0, 0, 0, 0),
					datetime.timedelta(days=1)
				],
				[
					datetime.datetime(2011, 9, 1, 11, 0, 0, 0),
					datetime.datetime(2011, 9, 1, 14, 30, 0, 0),
					datetime.timedelta(hours=3)
				],
				[
					datetime.datetime(2011, 9, 1, 12, 0, 0, 0),
					datetime.datetime(2011, 9, 1, 14, 30, 0, 0),
					datetime.timedelta(hours=2)
				],
				[
					datetime.datetime(2011, 9, 1, 12, 15, 0, 0),
					datetime.datetime(2011, 9, 1, 14, 30, 0, 0),
					datetime.timedelta(hours=2)
				],
				[
					datetime.datetime(2011, 9, 1, 12, 15, 0, 0),
					datetime.datetime(2011, 9, 2, 14, 30, 0, 0),
					datetime.timedelta(days=1, hours=1, minutes=30)
				],
				[
					datetime.datetime(2011, 9, 1, 12, 15, 0, 0),
					datetime.datetime(2011, 9, 2, 12, 20, 0, 0),
					datetime.timedelta(hours=23, minutes=30)
				],
		] 
		deductTimes=[
					(datetime.datetime(2011, 9, 1, 12, 0), datetime.datetime(2011, 9, 1, 12, 30)), 
					(datetime.datetime(2011, 9, 2, 12, 0), datetime.datetime(2011, 9, 2, 12, 30)), 
					]
		for idx, test in zip(range(len(tests)), tests):
			a=EMC.computeTime(test[0], test[1], deductTimes)
			self.assertEqual(test[2], a, "Wrong time calculated ("+str(idx)+"): "+str(a)+" != "+str(test[2]))


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
