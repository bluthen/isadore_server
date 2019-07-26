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

#python basic_seed_test.py > seed_test.sql

#Then run seed_test.sql in the db.

from datetime import datetime, timedelta
import random


std_bins = [12,13,30,31]
fan_bins=[10, 27, 28, 45]
burner_bins=[11, 26, 29, 44]

s_outside=9
s_fan = 10
s_burner = 11
s_vfs = 12
s_top = 13
s_bottom = 14


reading_info=[]

d_id=1
s_id=1
addr=100
# burner controls
# PXR4 1
pxr4_1_d_id = d_id
print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 11, 'PXR4 1', 2, 0, 11, 11,2012);"
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 20);"
s_id+=1
pxr4_1_SP_id = s_id
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 21);"
s_id+=1
addr+=1
d_id+=1
# # PXR4 2
# print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 11, 'PXR4 2', "+str(addr)+", 0, 26, 11,2012);"
# print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 20);"
# s_id+=1
# print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 21);"
# s_id+=1
# addr+=1
# d_id+=1
# # PXR4 3
# print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 11, 'PXR4 3', "+str(addr)+", 0, 29, 11,2012);"
# print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 20);"
# s_id+=1
# print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 21);"
# s_id+=1
# addr+=1
# d_id+=1

	# #Sensor unit
	# print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id) VALUES ("+str(d_id)+", 10, 'NA', "+str(addr)+", 5, "+str(burner_bin)+", "+str(s_burner)+");"
	# print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 10);"
	# reading_info.append([burner_bin, s_burner, 10])
	# s_id+=1
	# print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 11);"
	# reading_info.append([burner_bin, s_burner, 11])
	# s_id+=1
	# addr+=1
	# d_id+=1

#Outside bin
print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 10, 'NA', 202, 5, 9, 9,2012);"
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 10);"
# reading_info.append([9, s_bottom, 10])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 11);"
# reading_info.append([9, s_bottom, 11])
s_id+=1
addr+=1
d_id+=1

# bin 1
#Sensor unit - top
print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 10, 'NA', 404, 1, 12, "+str(s_top)+",2012);"
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 10);"
# reading_info.append([abin, s_top, 10])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 11);"
# reading_info.append([abin, s_top, 11])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 12);"
# reading_info.append([abin, s_top, 12])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 13);"
# reading_info.append([abin, s_top, 13])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 14);"
# reading_info.append([abin, s_top, 14])
s_id+=1
d_id+=1

#Sensor unit - bottom 
print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 10, 'NA', 387, 1, 12, "+str(s_bottom)+",2012);"
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 10);"
# reading_info.append([abin, s_bottom, 10])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 11);"
# reading_info.append([abin, s_bottom, 11])
s_id+=1
d_id+=1

# bin 2
#Sensor unit - top
print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 10, 'NA', 388, 1, 13, "+str(s_top)+",2012);"
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 10);"
# reading_info.append([abin, s_top, 10])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 11);"
# reading_info.append([abin, s_top, 11])
s_id+=1
addr+=1
d_id+=1

#Sensor unit - bottom 
print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 10, 'NA', 391, 1, 13, "+str(s_bottom)+",2012);"
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 10);"
# reading_info.append([abin, s_bottom, 10])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 11);"
# reading_info.append([abin, s_bottom, 11])
s_id+=1
d_id+=1

# bin 15
#Sensor unit - top
print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 10, 'NA', 346, 1, 30, "+str(s_top)+",2012);"
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 10);"
# reading_info.append([abin, s_top, 10])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 11);"
# reading_info.append([abin, s_top, 11])
s_id+=1
d_id+=1

#Sensor unit - bottom 
print "INSERT INTO device (id, device_type_id, name, address, port, bin_id, bin_section_id,year) VALUES ("+str(d_id)+", 10, 'NA', 312, 1, 30, "+str(s_bottom)+",2012);"
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 10);"
# reading_info.append([abin, s_bottom, 10])
s_id+=1
print "INSERT INTO sensor (id, device_id, sensor_type_id) VALUES ("+str(s_id)+", "+str(d_id)+", 11);"
# reading_info.append([abin, s_bottom, 11])
s_id+=1
d_id+=1

# #Readings
# t = datetime.now() - timedelta(hours=9)
# rdid = 1;
# for i in xrange(99):
# 	t=t+timedelta(minutes=5)
# 	print "INSERT INTO reading (id, datetime) VALUES ("+str(i)+", TIMESTAMP '"+t.strftime('%Y-%m-%d %H:%M:%S')+"');"
# 	for r in reading_info:
# 		rv = random.random()*50.0+80.0
# 		if(r[2] == 13):
# 			rv=int(rv)%2
# 		print "INSERT INTO reading_data (reading_id, bin_id, bin_section_id, sensor_type_id, value) VALUES ("+str(i)+", "+str(r[0])+", "+str(r[1])+", "+str(r[2])+", "+str(rv)+");"

# print "ALTER SEQUENCE sensor_seq RESTART "+str(s_id)+";";

# ##################################################
# # insert alarms
# ##################################################

# # no MID communication alarm for users 100-104
# for u in range(100,105):
# 	print "INSERT INTO alarm (id,alarm_type_id,account_id) VALUES ("+str(u)+",10,"+str(u)+");"
# print "INSERT INTO alarm (id,alarm_type_id,account_id) VALUES (110,10,104);"
# print "INSERT INTO alarm (id,alarm_type_id,account_id) VALUES (111,10,103);"
# print "INSERT INTO alarm (id,alarm_type_id,account_id) VALUES (112,10,103);"
# print "INSERT INTO alarm (id,alarm_type_id,account_id) VALUES (113,10,101);"
# print "INSERT INTO alarm (id,alarm_type_id,account_id) VALUES (114,10,104);"
# print "INSERT INTO alarm (id,alarm_type_id,account_id) VALUES (115,10,104);"
# print "ALTER SEQUENCE alarm_seq RESTART 116;"
# # instance of no MID communication alarms
# tstart = datetime.now() - timedelta(hours=5)
# tend = datetime.now() - timedelta(hours=4)
# print "INSERT INTO alarm_event (id,alarm_id, begin_datetime, end_datetime) VALUES (100,100, TIMESTAMP '"+tstart.strftime('%Y-%m-%d %H:%M:%S')+"', TIMESTAMP '"+tend.strftime('%Y-%m-%d %H:%M:%S')+"');"
# print "ALTER SEQUENCE alarm_event_seq RESTART 101;"
# # add contact methods of SMS and email for the three users for this alarm
# acCounter = 100
# for a in range(100,104):
# 	print "INSERT INTO alarm_contact (id,alarm_id,alarm_contact_type_id) VALUES ("+str(acCounter)+","+str(a)+",100);"
# 	acCounter+=1
# 	print "INSERT INTO alarm_contact (id,alarm_id,alarm_contact_type_id) VALUES ("+str(acCounter)+","+str(a)+",101);"
# 	acCounter+=1
# print "ALTER SEQUENCE alarm_contact_seq RESTART "+str(acCounter)+";"

# add a couple fills to DB
tstart = datetime(2011,8,1,0,0,0,0)
tstartair = datetime(2011,8,1,0,30,0,0)
print "INSERT INTO fill (id,fill_number,filled_datetime,air_begin_datetime,rotation_number,bin_id,hybrid_code,field_code,truck) VALUES (100,1,TIMESTAMP '"+tstart.strftime('%Y-%m-%d %H:%M:%S')+"',TIMESTAMP '"+tstartair.strftime('%Y-%m-%d %H:%M:%S')+"',1,12,'hybrid1','field1','truck1');"
# tstart = datetime.now() - timedelta(hours=8)
# tstartair = tstart + timedelta(minutes=20)
# print "INSERT INTO fill (id,fill_number,filled_datetime,air_begin_datetime,rotation_number,bin_id,hybrid_code,field_code,truck) VALUES (100,1,TIMESTAMP '"+tstart.strftime('%Y-%m-%d %H:%M:%S')+"',TIMESTAMP '"+tstartair.strftime('%Y-%m-%d %H:%M:%S')+"',1,12,'hybrid1','field1','truck1');"
# tstart = tstart + timedelta(minutes=45)
# tstartair = tstart + timedelta(minutes=15)
# print "INSERT INTO fill (id,fill_number,filled_datetime,air_begin_datetime,rotation_number,bin_id,hybrid_code,field_code,truck) VALUES (101,2,TIMESTAMP '"+tstart.strftime('%Y-%m-%d %H:%M:%S')+"',TIMESTAMP '"+tstartair.strftime('%Y-%m-%d %H:%M:%S')+"',1,13,'hybrid1','field1','truck1');"
# print "ALTER SEQUENCE fill_seq RESTART 102;"

# add a remote control setting
rc_id = 100
postedTime = tstartair
print "INSERT INTO control (id,sensor_id,sensor_type_id,value,posted_datetime) VALUES ("+str(rc_id)+","+str(pxr4_1_SP_id)+",21,99,TIMESTAMP '"+postedTime.strftime('%Y-%m-%d %H:%M:%S')+"');"
rc_id += 1
postedTime = postedTime + timedelta(minutes=20)
fetchedTime = postedTime + timedelta(minutes=2)
print "INSERT INTO control (id,sensor_id,sensor_type_id,value,posted_datetime,fetched_datetime) VALUES ("+str(rc_id)+","+str(pxr4_1_SP_id)+",21,99,TIMESTAMP '"+postedTime.strftime('%Y-%m-%d %H:%M:%S')+"',TIMESTAMP '"+fetchedTime.strftime('%Y-%m-%d %H:%M:%S')+"');"
