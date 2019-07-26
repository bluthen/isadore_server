-- Needed seed to run unit tests on a new database.

-- Our unit tests will have dates of 1980.


-- Bin and Bin section

INSERT INTO bin (id, name, x, y) VALUES (12, 'Bin 1', 2, 0);
INSERT INTO bin (id, name, x, y) VALUES (13, 'Bin 2', 3, 0);
INSERT INTO bin (id, name, x, y) VALUES (14, 'Bin 3', 4, 0);
INSERT INTO bin (id, name, x, y) VALUES (15, 'Bin 4', 5, 0);
INSERT INTO bin (id, name, x, y) VALUES (16, 'Bin 5', 5, 0);

INSERT INTO bin (id, name, x, y) VALUES (200, 'Dryer', 6, 0);

INSERT INTO bin (id, name, x, y) VALUES (201, 'Reflection Bin', 6, 0);

INSERT INTO bin_section (id, name) VALUES (200, 'Bottom Position 1');
INSERT INTO bin_section (id, name) VALUES (201, 'Bottom Position 2');
INSERT INTO bin_section (id, name) VALUES (202, 'Bottom Position 3`');
INSERT INTO bin_section (id, name) VALUES (203, 'Bottom Position 4`');


-- Bin Group
INSERT INTO bin_grp (name, grp_bin_id, member_bin_id) VALUES ('Dryer Group - Bin 1', 200, 12);
INSERT INTO bin_grp (name, grp_bin_id, member_bin_id) VALUES ('Dryer Group - Bin 2', 200, 13);
INSERT INTO bin_grp (name, grp_bin_id, member_bin_id) VALUES ('Dryer Group - Bin 3', 200, 14);

-- Bin Section Group
INSERT INTO bin_section_grp (name, grp_bin_section_id, member_bin_section_id) VALUES ('Bottom Group - Bottom Position 1', 14, 200);
INSERT INTO bin_section_grp (name, grp_bin_section_id, member_bin_section_id) VALUES ('Bottom Group - Bottom Position 2', 14, 201);
INSERT INTO bin_section_grp (name, grp_bin_section_id, member_bin_section_id) VALUES ('Bottom Group - Bottom Position 3', 14, 202);
INSERT INTO bin_section_grp (name, grp_bin_section_id, member_bin_section_id) VALUES ('Bottom Group - Bottom Position 4', 14, 203);

-- Devices
INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (199, 10, 'Unit', 99, 1, true, 9, 9, 1980); -- Outdoor Outdoor


INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (200, 10, 'Unit', 100, 1, true, 12, 13, 1980); -- Bin 1 Top
INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (201, 10, 'Unit', 101, 1, true, 12, 14, 1980); -- Bin 1 Bottom

INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (202, 10, 'Unit', 102, 1, true, 13, 13, 1980); -- Bin 2 Top
--INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (203, 10, 'Unit', 102, 1, true, 13, 14, 1980); -- Bin 2 Bottom

INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (204, 10, 'Unit', 103, 1, true, 14, 13, 1980); -- Bin 3 Top
INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (205, 10, 'Unit', 104, 1, true, 14, 14, 1980); -- Bin 3 Bottom

INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (206, 10, 'Unit', 105, 1, true, 15, 13, 1980); -- Bin4 Top
INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (207, 10, 'Unit', 106, 1, true, 15, 14, 1980); -- Bin4 Bottom
INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (214, 10, 'Unit', 203, 1, true, 15, 200, 1980); -- Bin4 Bottom Pos 1

INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (208, 10, 'Unit', 110, 1, true, 16, 13, 1980); -- Bin 5 Top
INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (209, 10, 'Unit', 111, 1, true, 16, 14, 1980); -- Bin 5 Bottom

INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (212, 10, 'Unit', 201, 1, true, 16, 200, 1980); -- Bin 5 Bot Pos1
INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (213, 10, 'Unit', 202, 1, true, 16, 201, 1980); -- Bin 5 Bot Pos2 


INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (210, 10, 'Unit', 107, 1, true, 13, 200, 1980); -- Bin 2 Bottom Pos 1
INSERT INTO device (id, device_type_id, name, address, port, enabled_p, bin_id, bin_section_id, year) VALUES (211, 10, 'Unit', 108, 1, true, 13, 201, 1980); -- Bin 2 Bottom Pos 2

-- Sensors

INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (299, 199, 14); -- Outdoor Outdoor Pressure

INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (300, 200, 10); -- Bin1 Top Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (301, 200, 11); -- Bin1 Top RH


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (302, 201, 10); -- Bin1 Bottom Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (303, 201, 11); -- Bin1 Bottom RH


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (304, 202, 10); -- Bin2 Top Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (305, 202, 11); -- Bin2 Top RH


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (306, 204, 10); -- Bin3 Top Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (307, 204, 11); -- Bin3 Top RH


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (308, 205, 10); -- Bin3 Bottom Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (309, 205, 11); -- Bin3 Bottom RH


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (310, 206, 10); -- Bin4 Top Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (311, 206, 11); -- Bin4 Top RH


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (312, 207, 10); -- Bin4 Bottom Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (313, 207, 11); -- Bin4 Bottom RH


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (314, 208, 10); -- Bin5 Top Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (315, 208, 11); -- Bin5 Top RH
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (321, 208, 14); -- Bin5 Top Pressure

INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (316, 209, 10); -- Bin5 Bottom Temp
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (317, 209, 11); -- Bin5 Bottom RH
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (320, 209, 14); -- Bin5 Bottom Pressure


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (318, 210, 15); -- Bin 2 Bottom Pos 1 MultiT
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (319, 211, 15); -- Bin 2 Bottom Pos 2 MultiT

INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (322, 212, 15); -- Bin 5 Bottom Pos 1 MultiT
INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (323, 213, 15); -- Bin 5 Bottom Pos 2 MultiT


INSERT INTO sensor (id, device_id, sensor_type_id) VALUES (324, 214, 15); -- Bin 4 Bottom Pos 1 MultiT


--Sensor Mirror

INSERT INTO sensor_mirror (id, bin_id, bin_section_id, sensor_id) VALUES (200, 201, 14, 312); -- Mirror of sensor sht temp on bin 4 bottom mirror to Mirrored Bin Bottom
