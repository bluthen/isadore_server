
INSERT INTO cache_versions (id, conf_version, conf_datetime) values (1, NEXTVAL('conf_version'), CURRENT_TIMESTAMP);

-- PRIVILEGES

insert into privilege (id, name) VALUES (2000, 'Super User');
insert into privilege (id, name) VALUES (1000, 'Power User');
insert into privilege (id, name) VALUES (500, 'Config User');
insert into privilege (id, name) VALUES (250, 'Fill User');
insert into privilege (id, name) VALUES (100, 'User');

-- Super users (passwords should probably change on first login)
-- Change password on actuall deploy so if someone gets this file they dont have super user access.
insert into account (email, password, seed, name, phone,  privilege_id) VALUES ('changeme@example.com', encode(digest('someseed_some_password', 'sha1'), 'hex'), 'someseed', 'Admin Account','15555555555', 2000);


INSERT INTO fill_type (id, name, short_name) VALUES (1, 'Normal', 'normal');
INSERT INTO fill_type (id, name, short_name) VALUES (2, 'Bypass', 'bypass');


INSERT INTO alarm_contact_type (id, name) VALUES (100, 'Email');
INSERT INTO alarm_contact_type (id, name) VALUES (101, 'SMS');
-- INSERT INTO alarm_contact_type (name) VALUES ('Carrier Pidgeon');

INSERT INTO read_type (id, name, short_name, units) VALUES (4, 'Absolute Humidity', 'abshum', 'g/m^3');
INSERT INTO read_type (id, name, short_name, units) VALUES (5, 'Dew Point', 'Dew', '&deg;F');
INSERT INTO read_type (id, name, short_name, units) VALUES (6, 'Jody Factor', 'jfactor', 'NA');
INSERT INTO read_type (id, name, short_name, units) VALUES (7, 'Gauge Pressure', 'gpressure', 'inH2O');
INSERT INTO read_type (id, name, short_name, units) VALUES (10, 'Temperature', 'Temp', '&deg;F');
INSERT INTO read_type (id, name, short_name, units) VALUES (11, 'Relative Humidity', 'RH', '%');
INSERT INTO read_type (id, name, short_name, units) VALUES (12, 'Wind Speed', 'Wind', 'MPH');
INSERT INTO read_type (id, name, short_name, units, value_type) VALUES (13, 'Wind Direction', 'Wind Dir', '', 'boolean');
INSERT INTO read_type (id, name, short_name, units) VALUES (14, 'Barometric Pressure', 'Pressure', 'kPa');
INSERT INTO read_type (id, name, short_name, units) VALUES (20, 'Process Variable', 'PV', '&deg;F');
INSERT INTO read_type (id, name, short_name, units) VALUES (21, 'Set Point', 'SP', '&deg;F');
INSERT INTO read_type (id, name, short_name, units) VALUES (22, 'Actuator Output', 'Output', 'NA');
INSERT INTO read_type (id, name, short_name, units) VALUES (40, 'Fan RPM', 'Fan RPM', 'r/min');
INSERT INTO read_type (id, name, short_name, units) VALUES (50, 'VFD RPM', 'VFD RPM', 'r/min');
INSERT INTO read_type (id, name, short_name, units) VALUES (51, 'VFD Amps Out', 'VFD Out', 'A');
INSERT INTO read_type (id, name, short_name, units) VALUES (52, 'Tachometer Feedback', 'Fan RPM', 'r/min');
INSERT INTO read_type (id, name, short_name, units) VALUES (60, 'VFD RPM', 'VFD RPM', 'r/min');
INSERT INTO read_type (id, name, short_name, units) VALUES (61, 'VFD Amps Out', 'VFD Out', 'A');
INSERT INTO read_type (id, name, short_name, units) VALUES (131, 'Wet Bulb', 'Wet Bulb', '&deg;F');
INSERT INTO read_type (id, name, short_name, units) VALUES (200, 'Moisture Content Predict A', 'MCP A', '%');
INSERT INTO read_type (id, name, short_name, units) VALUES (201, 'Moisture Content Predict Change A', 'dMCP/dt A', '%/hr');
INSERT INTO read_type (id, name, short_name, units) VALUES (202, 'Moisture Content Predict B', 'MCP B', '%');
INSERT INTO read_type (id, name, short_name, units) VALUES (203, 'Moisture Content Predict Change B', 'dMCP/dt B', '%/hr');
INSERT INTO read_type (id, name, short_name, units) VALUES (204, 'Moisture Content Predict C', 'MCP C', '%');
INSERT INTO read_type (id, name, short_name, units) VALUES (205, 'Moisture Content Predict Change C', 'dMCP/dt C', '%/hr');
INSERT INTO read_type (id, name, short_name, units) VALUES (300, 'Moisture Content', 'MC', '%');



-- TODO: Don't think we need computed sensor types, we just need the read_types they represent.
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (5, 'Dew Point', 'x', 5); --  Computed
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (6, 'Jody Factor', 'x', 6); -- Computed
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (7, 'Gauge Pressure', 'x', 7); -- Computed

INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (10, 'Temperature', '(-40.2)+0.018*x', 10);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (11, 'Relative Humidity', '(( (t-32.0)/1.8)-25)*(0.01+0.00008*x) + -2.0468+0.0367*x+-1.5955e-6*x**2', 11);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (12, 'Wind Speed', '26.1*(5.0*(x/1024.0)+0.0148*t - 3.16)**2.0 + 6.78', 12);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (13, 'Wind Direction', 'x', 13);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (14, 'Barometric Pressure', 'x/1000.0', 14);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (15, 'Multiple-point temperature cable', 'x', 10);

-- Temperature controller sensor types
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (20, 'Process Variable', 'x', 20);
INSERT INTO sensor_type (id, name, default_convert_py, controllable, read_type_id) VALUES (21, 'Set Point', 'x', true, 21);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (22, 'Actuator Output', 'x', 22);

INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (40, 'Fan RPM', 'x', 40);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (41, 'Temperature A', '(1023.75*x/4096.0)*9.0/5.0+32.0', 10);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (42, 'Temperature B', '(1023.75*x/4096.0)*9.0/5.0+32.0', 10);

INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (50, 'VFD RPM', 'x', 50);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (51, 'VFD Amps Out', 'x', 51);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (52, 'Tachometer Feedback', 'x', 52);
INSERT INTO sensor_type (id, name, default_convert_py, controllable, read_type_id) VALUES (60, 'VFD RPM', 'x', true, 50);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (61, 'VFD Amps Out', 'x', 61);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (131, 'Wet Bulb', 'x', 131);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (300, 'DM Moisture Content', '((x-800.0)/3295.0)*100.0', 300);
INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (301, 'DM Temperature', '((x-800.0)/3295.0)*100.0', 10);

INSERT INTO sensor_type (id, name, default_convert_py, read_type_id) VALUES (400, 'RTM2000 Sensor', 'x', 10);


INSERT INTO device_type (id, name) VALUES (5, 'Mirror Device');
INSERT INTO device_type (id, name) VALUES (10, 'EA Sensor Unit v2.03');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (10, 10); --Temperature
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (10, 11); --Humidity
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (10, 12); --Wind Speed
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (10, 13); --Wind direction
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (10, 14); --Barometric pressure
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (10, 15); --Multi-pt T

-- Fuji
INSERT INTO device_type (id, name) VALUES (11, 'Fuji PXR4-REY1-GVVA1');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (11, 20); -- PV
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (11, 21); -- SP
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (11, 22); -- output

-- Honeywell UDC3300
INSERT INTO device_type (id, name) VALUES (12, 'Honeywell UDC3300');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (12, 20); -- PV
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (12, 21); -- SP
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (12, 22); -- output

-- Honeywell UDC3500
INSERT INTO device_type (id, name) VALUES (16, 'Honeywell UDC3500');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (16, 20); -- PV
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (16, 21); -- SP
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (16, 22); -- output

-- Honeywell UDC2500
INSERT INTO device_type (id, name) VALUES (19, 'Honeywell UDC2500');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (19, 20); -- PV
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (19, 21); -- SP
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (19, 22); -- output

-- dummy Ethernet/MODBUS burner controller
INSERT INTO device_type (id, name) VALUES (17, 'Dummy Eth burner controller');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (17, 20); -- PV
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (17, 21); -- SP
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (17, 22); -- output

-- dummy RS485/MODBUS burner controller
INSERT INTO device_type (id, name) VALUES (18, 'Dummy RS485 burner controller');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (18, 20); -- PV
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (18, 21); -- SP
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (18, 22); -- output

--EA Tach
INSERT INTO device_type (id, name) VALUES (13, 'EA Tachometer Unit v1.00');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (13, 40); --EA Tach RPMs
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (13, 41); --EA Thermo A 
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (13, 42); --EA Thermo B

--AB Powerflex
INSERT INTO device_type (id, name) VALUES (14, 'AB PowerFlex 700');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (14, 50); --AB Powerflex RPMs Set
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (14, 51); --AB Powerflex Amps Out
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (14, 52); --AB Powerflex Tachometer Feedback 
--Yaskawa
INSERT INTO device_type (id, name) VALUES (15, 'Yaskawa P7');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (15, 60); --Yaskawa RPMs Set
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (15, 61); --Yaskawa Amps Out

--Dryer Master M2 2Sensor version
INSERT INTO device_type (id, name) VALUES (981, 'Dryer Master M2 2 Sensor Version');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (981, 300); --DM MC
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (981, 301); --DM Temp 

--RTM2000
INSERT INTO device_type (id, name) VALUES (21945, 'RTM2000 Device');
INSERT INTO device_type_to_sensor_type (device_type_id, sensor_type_id) VALUES (21945, 400); --RTM2000 Temp


INSERT INTO alarm_type (id, name, threshold_p) VALUES (10, 'No communication from MID', FALSE);
INSERT INTO alarm_type (id, name, threshold_p) VALUES (11, 'Fan VFD Hz mismatch', FALSE);
INSERT INTO alarm_type (id, name, threshold_p) VALUES (12, 'Burner pilot out', FALSE);
INSERT INTO alarm_type (id, name, threshold_p) VALUES (13, 'Burner PV temperature', TRUE);
INSERT INTO alarm_type (id, name, threshold_p) VALUES (14, 'Sensor Temperature', TRUE);
INSERT INTO alarm_type (id, name, threshold_p) VALUES (15, 'Sensor error', FALSE);
INSERT INTO alarm_type (id, name, threshold_p) VALUES (16, 'Temperature-MC', TRUE);

-- Default subsamples
INSERT INTO default_subsample (subsample) values (5);
INSERT INTO default_subsample (subsample) values (10);
INSERT INTO default_subsample (subsample) values (15);
INSERT INTO default_subsample (subsample) values (20);
INSERT INTO default_subsample (subsample) values (30);
INSERT INTO default_subsample (subsample) values (45);
INSERT INTO default_subsample (subsample) values (60);
INSERT INTO default_subsample (subsample) values (120);
INSERT INTO default_subsample (subsample) values (240);
INSERT INTO default_subsample (subsample) values (360);

INSERT INTO bin_section (id, name) VALUES (9, 'Outdoor');
INSERT INTO bin_section (id, name) VALUES (10, 'Fan');
INSERT INTO bin_section (id, name) VALUES (11, 'Burner');
INSERT INTO bin_section (id, name) VALUES (12, 'VFD');
INSERT INTO bin_section (id, name) VALUES (13, 'Top');
INSERT INTO bin_section (id, name) VALUES (14, 'Bottom');
INSERT INTO bin_section (id, name) VALUES (15, 'North');
INSERT INTO bin_section (id, name) VALUES (16, 'South');
INSERT INTO bin_section (id, name) VALUES (17, 'East');
INSERT INTO bin_section (id, name) VALUES (18, 'West');
INSERT INTO bin_section (id, name) VALUES (19, 'Center');
INSERT INTO bin_section (id, name) VALUES (20, 'North Center');
INSERT INTO bin_section (id, name) VALUES (21, 'South Center');
INSERT INTO bin_section (id, name) VALUES (22, 'East Center');
INSERT INTO bin_section (id, name) VALUES (23, 'West Center');
INSERT INTO bin_section (id, name) VALUES (801, 'One');
INSERT INTO bin_section (id, name) VALUES (802, 'Two');

INSERT INTO bin (id, name, x, y) VALUES (9, 'Outdoor', -1, -1);
