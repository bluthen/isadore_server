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
import iso8601
import traceback
import itertools

import psycopg2 as dbapi2
import psycopg2.extras as dbapi2extras


conn = None
dbname = None
dbusername = None
dbpassword = None
dbhost = None


def get_conn(dbname, dbuser, dbpass, dbhost):
    conn = dbapi2.connect(database=dbname, user=dbuser, password=dbpass, host=dbhost)
    return conn

def get_cursor():
    return conn.cursor(cursor_factory=dbapi2extras.DictCursor)


class TestSensorData(unittest.TestCase):
    def setUp(self):
        global conn
        conn = get_conn(dbname, dbusername, dbpassword, dbhost)

    def tearDown(self):
        global conn
        conn.rollback()
        cur = get_cursor()
        cur.execute("DELETE FROM sensor_data")
        cur.execute("DELETE FROM sensor_data_latest")
        cur.execute("DELETE FROM reading_subsample")
        cur.execute("DELETE FROM reading_data_latest")
        conn.commit()
        cur.close()
        conn.close()
        conn = None

    def _reset_valid(self, valids):
        for sample, srows in valids.iteritems():
            for vrows in srows:
                vrows['_checked'] = False

    def _verify(self, name, cur, valids, verbose=False):
        cur.execute("SELECT rs.datetime, rs.sample_period, rds.bin_id, rds.bin_section_id, rds.read_type_id, rds.avg_value, rds.min, rds.max, rds.current_count FROM reading_data_subsample rds, reading_subsample rs WHERE rs.id = rds.reading_subsample_id")
        for row in cur:
            sample_period = str(row['sample_period'])
            if sample_period in valids:
                for vrows in valids[sample_period]:
                    if row['datetime'] == vrows['datetime'] and row['bin_id'] == vrows['bin_id'] and row['bin_section_id'] == vrows['bin_section_id'] and row['read_type_id'] == vrows['read_type_id']:
                        for key, val in vrows.iteritems():
                            if not key.startswith('_'):
                                if verbose and key == 'avg_value':
                                    print row['read_type_id'], row[key], val
                                self.assertAlmostEqual(row[key], val, 7, '%s: %s: %s != %s, row=%s' % (name, key, str(row[key]), str(val), str(row)))
                        self.assertFalse(vrows['_checked'], 'Duplicate reading_data_subsample rows')
                        vrows['_checked'] = True
        #print valids
        for sample, srows in valids.iteritems():
            for vrows in srows:
                if verbose:
                    print vrows['read_type_id'], vrows['_checked']
                self.assertTrue(vrows['_checked'], '%s: %s sample period failed' % (name, sample))

    def test_simple_subsample(self):
        # This tests plain subsamples get created. by themselves, no groups no calcs.
        # Bin 5 - Bottom - Temp
        cur = get_cursor()
        try:
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (316, 70.0, '1980-01-01T18:07:00Z'))

            #Check subsamples were made
            cur.execute("SELECT rs.datetime, rs.sample_period, rds.bin_id, rds.bin_section_id, rds.read_type_id, rds.avg_value, rds.min, rds.max, rds.current_count FROM reading_data_subsample rds, reading_subsample rs WHERE rs.id = rds.reading_subsample_id")
            #TODO: Add other sample tests
            valids = {'5': [{'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 70.0, 'min': 70.0, 'max': 70.0, 'current_count': 1, "_checked": False}], '10': [{'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 70.0, 'min': 70.0, 'max': 70.0, 'current_count': 1, "_checked": False}]}
            self._verify('1 insert', cur, valids)

            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (316, 72.0, '1980-01-01T18:08:00Z'))
            conn.commit()

            #TODO: Add other sample tests
            valids = {
                '5': [
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 70.0, 'min': 70.0, 'max': 70.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 72.0, 'min': 72.0, 'max': 72.0, 'current_count': 1, "_checked": False}
                ],
                '10': [
                    {'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 71.0, 'min': 70.0, 'max': 72.0, 'current_count': 2, "_checked": False}
                ]
            }
            self._verify('2 insert', cur, valids)

            cur.close()
            cur = None
        finally:
            conn.rollback()
            if cur:
                cur.close()

    def test_calc_guage_pressure(self):
        # insert pressure into outdoor
        cur = get_cursor()
        try:
            cur.execute('INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)', (299, 96.5, '1980-01-01T18:07:00Z'))
            # insert pressure into a bin
            cur.execute('INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)', (320, 97.5, '1980-01-01T18:07:00Z'))
            valids = {'5': [{'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 14, 'avg_value': 97.5, 'min': 97.5, 'max': 97.5, 'current_count': 1, "_checked": False}, {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 9, 'bin_section_id': 9, 'read_type_id': 14, 'avg_value': 96.5, 'min': 96.5, 'max': 96.5, 'current_count': 1, "_checked": False}, {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 7, 'avg_value': 4.0186, 'min': 4.0186, 'max': 4.0186, 'current_count': 1, "_checked": False}]}
            self._verify('calc_guage_pressure', cur, valids)


            #insert pressure into a bins time2
            cur.execute('INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)', (321, 97.5, '1980-01-01T19:07:00Z'))
            cur.execute('INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)', (320, 98.5, '1980-01-01T19:07:00Z'))
            # insert pressure into outdoor time2
            cur.execute('INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)', (299, 96.5, '1980-01-01T19:07:00Z'))
            valids = {'5': [
                {'datetime': iso8601.parse_date('1980-01-01T13:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 14, 'avg_value': 98.5, 'min': 98.5, 'max': 98.5, 'current_count': 1, "_checked": False},
                {'datetime': iso8601.parse_date('1980-01-01T13:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 13, 'read_type_id': 14, 'avg_value': 97.5, 'min': 97.5, 'max': 97.5, 'current_count': 1, "_checked": False},
                {'datetime': iso8601.parse_date('1980-01-01T13:05:00-06:00'), 'bin_id': 9, 'bin_section_id': 9, 'read_type_id': 14, 'avg_value': 96.5, 'min': 96.5, 'max': 96.5, 'current_count': 1, "_checked": False},
                {'datetime': iso8601.parse_date('1980-01-01T13:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 7, 'avg_value': 8.0372, 'min': 8.0372, 'max': 8.0372, 'current_count': 1, "_checked": False},
                {'datetime': iso8601.parse_date('1980-01-01T13:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 13, 'read_type_id': 7, 'avg_value': 4.0186, 'min': 4.0186, 'max': 4.0186, 'current_count': 1, "_checked": False}
            ]}
            self._verify('calc_guage_pressure odl', cur, valids)
        finally:
            if cur:
                cur.close()
                cur = None



    def test_calc_wetbulb(self):
        cur = get_cursor()
        try:
            # Iterate through these different order combinations

            inserts = [
                "INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (299, 96.5, '1980-01-01T18:07:00Z')",
                "INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (316, 100.0, '1980-01-01T18:07:00Z')",
                "INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (317, 80.0, '1980-01-01T18:07:00Z')"
            ]

            valids = {'5': [
                {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 131, 'avg_value': 94.04024, 'min': 94.04024, 'max': 94.04024, 'current_count': 1, "_checked": False}
            ]}

            for perm in itertools.permutations(inserts, 3):
                cur.execute(perm[0])
                cur.execute(perm[1])
                cur.execute(perm[2])
                self._reset_valid(valids)
                self._verify('calc_wetbulb', cur, valids)
                cur.execute("DELETE FROM sensor_data")
                cur.execute("DELETE FROM reading_subsample")


            inserts.append("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, '%s')" % (316, 99.0, '1980-01-01T18:08:00Z'))

            valids = {'5': [
                {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 131, 'avg_value': 94.04024, 'min': 94.04024, 'max': 94.04024, 'current_count': 1, "_checked": False},
                {'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 99.0, 'min': 99.0, 'max': 99.0, 'current_count': 1, "_checked": False}],
                '10': [{'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 131, 'avg_value': 93.56540000000004, 'min': 93.56540000000004, 'max': 93.56540000000004, 'current_count': 1, "_checked": False}]
            }

            for perm in itertools.permutations(inserts, 4):
                cur.execute(perm[0])
                cur.execute(perm[1])
                cur.execute(perm[2])
                cur.execute(perm[3])
                self._reset_valid(valids)
                self._verify('calc_wetbulb multi', cur, valids)
                cur.execute("DELETE FROM sensor_data")
                cur.execute("DELETE FROM reading_subsample")

        finally:
            if cur:
                cur.close()

    def test_sensor_mirror(self):
        # Lets temp in bottom bin 4, it should also be in bottom of 'Reflection Bin'
        cur = get_cursor()
        try:
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (312, 70.0, '1980-01-01T18:07:00Z'))
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (312, 72.0, '1980-01-01T18:08:00Z'))
            valids = {
                '5': [
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 15, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 70.0, 'min': 70.0, 'max': 70.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 15, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 72.0, 'min': 72.0, 'max': 72.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 201, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 70.0, 'min': 70.0, 'max': 70.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 201, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 72.0, 'min': 72.0, 'max': 72.0, 'current_count': 1, "_checked": False}
                ],
                '10': [
                    {'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 15, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 71.0, 'min': 70.0, 'max': 72.0, 'current_count': 2, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:10:00-06:00'), 'bin_id': 201, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 71.0, 'min': 70.0, 'max': 72.0, 'current_count': 2, "_checked": False}
                ]
            }
            self._verify('sensor_mirror', cur, valids, verbose=False)

        finally:
            if cur:
                cur.close()

    def test_bin_section_group(self):
        # Insert into position 1 and 2 in Bin 5, should go to bin 5 bottom
        # Insert into Bottom pos 1 and bottom of Bin 4, pos 1 and 2 in bin 5 should have no affect on bin 4
        cur = get_cursor()
        try:
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (312, 71.0, '1980-01-01T18:07:00Z')) # Bin 4 Bottom Temp
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (324, 72.0, '1980-01-01T18:07:00Z')) # Bin 4 Pos 1 MT
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (322, 73.0, '1980-01-01T18:07:00Z')) # Bin 5 Pos 1 MT
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (323, 74.0, '1980-01-01T18:07:00Z')) # Bin 5 Pos 2 MT
            valids = {
                '5': [
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 15, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 71.5, 'min': 71.0, 'max': 72.0, 'current_count': 2, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 15, 'bin_section_id': 200, 'read_type_id': 10, 'avg_value': 72.0, 'min': 72.0, 'max': 72.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 200, 'read_type_id': 10, 'avg_value': 73.0, 'min': 73.0, 'max': 73.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 201, 'read_type_id': 10, 'avg_value': 74.0, 'min': 74.0, 'max': 74.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 73.5, 'min': 73.0, 'max': 74.0, 'current_count': 2, "_checked": False}
                ]
            }
            self._verify('bin_section_group', cur, valids, verbose=False)
        finally:
            if cur:
                cur.close()

    def test_bin_group(self):
        # Insert into bin 1 and bin 2 bottom, should go to Dryer bottom
        cur = get_cursor()
        try:
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (302, 71.0, '1980-01-01T18:07:00Z')) # Bin 1 Bottom Temp
            cur.execute("INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (%s, %s, %s)", (308, 72.0, '1980-01-01T18:07:00Z')) # Bin 3 Bottom Temp
            valids = {
                '5': [
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 12, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 71.0, 'min': 71.0, 'max': 71.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 14, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 72.0, 'min': 72.0, 'max': 72.0, 'current_count': 1, "_checked": False},
                    {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 200, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 71.5, 'min': 71.0, 'max': 72.0, 'current_count': 2, "_checked": False}
                ]
            }
            self._verify('bin_group', cur, valids, verbose=False)
        finally:
            if cur:
                cur.close()

    def test_bin_bin_section_group(self):
        # Insert into bin 1 and bin 2 pos 1, should go to dryer bottom
        pass

    def test_calc_bin_group(self):
        pass

    def test_calc_bin_section_group(self):
        pass

    def test_error_status_no_reading(self):
        # Insert with error status, there should be nothing added to reading_data
        cur = get_cursor()
        try:
            inserts = [
                "INSERT INTO sensor_data(sensor_id, value, datetime) VALUES (316, 100.0, '1980-01-01T18:07:00Z')",
                "INSERT INTO sensor_data(sensor_id, value, datetime, error_code) VALUES (316, 500.0, '1980-01-01T18:07:00Z', 1)"
            ]

            valids = {'5': [
                {'datetime': iso8601.parse_date('1980-01-01T12:05:00-06:00'), 'bin_id': 16, 'bin_section_id': 14, 'read_type_id': 10, 'avg_value': 100.0, 'min': 100.0, 'max': 100.0, 'current_count': 1, "_checked": False}
            ]}

            for perm in itertools.permutations(inserts, 2):
                cur.execute(perm[0])
                cur.execute(perm[1])
                self._reset_valid(valids)
                self._verify('error_status', cur, valids)
                cur.execute("DELETE FROM sensor_data")
                cur.execute("DELETE FROM reading_subsample")
        finally:
            if cur:
                cur.close()


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print "Usage: %s dbname dbusername dbpassword dbhost" % (sys.argv[0],)
        sys.exit(55)

    dbname = sys.argv[1]
    dbusername = sys.argv[2]
    dbpassword = sys.argv[3]
    dbhost = sys.argv[4]

    conn = get_conn(dbname, dbusername, dbpassword, dbhost)
    unittest.main(argv=[sys.argv[0]])
    conn.close()
