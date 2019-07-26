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
import sys
import prediction_runner2017a
from dateutil import parser
import datetime
import copy

class TestPredictionRunner(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            'datetime': [
                parser.parse(u'2015-09-07T18:00:00-04:00'),
                parser.parse(u'2015-09-07T18:15:00-04:00'),
                parser.parse(u'2015-09-07T18:30:00-04:00'),
                parser.parse(u'2015-09-07T18:45:00-04:00'),
                parser.parse(u'2015-09-07T19:00:00-04:00'),
                parser.parse(u'2015-09-07T19:15:00-04:00'),
                parser.parse(u'2015-09-07T19:30:00-04:00'),
                parser.parse(u'2015-09-07T19:45:00-04:00'),
                parser.parse(u'2015-09-07T20:00:00-04:00'),
                parser.parse(u'2015-09-07T20:15:00-04:00'),
                parser.parse(u'2015-09-07T20:30:00-04:00'),
                parser.parse(u'2015-09-07T20:45:00-04:00'),
                parser.parse(u'2015-09-07T21:00:00-04:00'),
                parser.parse(u'2015-09-07T21:15:00-04:00'),
                parser.parse(u'2015-09-07T21:30:00-04:00')
            ],
            'top_abshum': [28.9393197527523, 25.3559162667185, 24.0595228395655, 23.4599211204521, 23.2701220521954,
                           23.2111342798733, 23.1979244321183, 23.2477746865068, 23.3293109605416, 23.3581077258809,
                           23.4357316008085, 23.3001239473792, 23.3690545882063, 23.3943652563225, 23.3691103977483],
            'bottom_abshum': [17.8770932500147, 17.6229495714787, 18.234052771453, 18.0978866456067, 18.3702957891779,
                              18.3446814766031, 18.4736510433659, 18.5480017602588, 18.7316009731911, 18.8451166918032,
                              19.001897558278, 19.0196842664122, 19.1474616792495, 19.1853125027211, 19.1052811013127],
            'top_temp': [92.9856, 90.0408, 87.3696, 85.6416, 84.396, 83.4708, 82.9632, 82.7256, 82.524, 82.3296,
                         82.2576, 82.0236, 81.93, 81.7716, 81.6564],
            'bottom_temp': [102.252, 103.3572, 103.5228, 103.3392, 103.0908, 102.7416, 102.4032, 102.0108, 101.6184,
                            101.1612, 100.7436, 100.3368, 100.0704, 99.9372, 99.84]
        }

    def tearDown(self):
        pass

    def test_next_not_none(self):
        ourlist = [0, None, 2, 3, 4, None, None, 6, 4, 3, 2]
        ret = prediction_runner2017a.next_not_none(ourlist, 5)
        self.assertEqual(ret, 7)

    def test_interpolate(self):
        td15 = datetime.timedelta(minutes=15)
        self.test_data['top_temp'][3] = None
        self.test_data['top_temp'][4] = None
        prediction_runner2017a.interpolate({
            'datetime': self.test_data['datetime'][2],
            'top_temp': self.test_data['top_temp'][2]}, self.test_data, 'top_temp', 3, True)
        self.assertEqual(self.test_data['top_temp'][3],
                         self.test_data['top_temp'][2] +
                         (self.test_data['top_temp'][5] - self.test_data['top_temp'][2])/3.0)
        self.assertEqual(self.test_data['datetime'][3], self.test_data['datetime'][2] + td15)

        del self.test_data['datetime'][4]
        del self.test_data['datetime'][3]
        del self.test_data['top_temp'][4]
        del self.test_data['top_temp'][3]
        prediction_runner2017a.interpolate({
            'datetime': self.test_data['datetime'][2],
            'top_temp': self.test_data['top_temp'][2]}, self.test_data, 'top_temp', 3, False)
        self.test_data['datetime'].insert(3, self.test_data['datetime'][2] + td15)
        prediction_runner2017a.interpolate({
            'datetime': self.test_data['datetime'][3],
            'top_temp': self.test_data['top_temp'][3]}, self.test_data, 'top_temp', 4, False)
        self.test_data['datetime'].insert(4, self.test_data['datetime'][3] + td15)

        self.assertEqual(self.test_data['top_temp'][3],
                         self.test_data['top_temp'][2] +
                         (self.test_data['top_temp'][5] - self.test_data['top_temp'][2]) / 3.0)
        self.assertEqual(self.test_data['datetime'][3], self.test_data['datetime'][2] + td15)

    def test_none_data_around_rolls(self):
        prediction_runner2017a.none_data_around_rolls([parser.parse(u'2015-09-07T19:13:30-04:00')], self.test_data)
        for key in self.test_data.keys():
            if key == 'datetime':
                for i in range(10):
                    self.assertIsNotNone(self.test_data[key][i])
            else:
                self.assertIsNotNone(self.test_data[key][0])
                for i in range(1, 8):
                    self.assertIsNone(self.test_data[key][i])
                self.assertIsNotNone(self.test_data[key][9])

    def test_cut_to_alldata(self):
        test_data = copy.deepcopy(self.test_data)
        test_data['top_temp'][0] = None
        test_data['top_temp'][1] = None
        test_data['top_temp'][2] = None
        prediction_runner2017a.cut_to_alldata(test_data)
        self.assertEqual(len(test_data['datetime']), len(self.test_data['datetime'])-3)

    def test_repair_data(self):
        td15 = datetime.timedelta(minutes=15)
        test_data = copy.deepcopy(self.test_data)
        for key in self.test_data.keys():
            if key == 'datetime':
                continue
            self.test_data[key][4] = None
            self.test_data[key][3] = None
        prediction_runner2017a.repair_data(self.test_data)
        self.assertEqual(self.test_data['top_temp'][3],
                         self.test_data['top_temp'][2] +
                         (self.test_data['top_temp'][5] - self.test_data['top_temp'][2]) / 3.0)
        self.assertEqual(self.test_data['datetime'][3], self.test_data['datetime'][2] + td15)
        for key in test_data.keys():
            del test_data[key][4]
            del test_data[key][3]
        prediction_runner2017a.repair_data(test_data)
        self.assertEqual(test_data['top_temp'][3],
                         test_data['top_temp'][2] +
                         (test_data['top_temp'][5] - test_data['top_temp'][2]) / 3.0)
        self.assertEqual(test_data['datetime'][3], test_data['datetime'][2] + td15)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]])
