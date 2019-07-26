INSERT INTO general_config (id, interval, enabled_p, mid_pass, customer_name, customer_short_name, multiple_rolls) values (1, 300, true, 'midpass_change_pwd', 'Generic Seed Farm', 'genfarm', FALSE); 

INSERT INTO bin_section (id, name) VALUES (9, 'Outdoor');
INSERT INTO bin_section (id, name) VALUES (10, 'Fan');
INSERT INTO bin_section (id, name) VALUES (11, 'Burner');
INSERT INTO bin_section (id, name) VALUES (12, 'VFD');
INSERT INTO bin_section (id, name) VALUES (13, 'Top');
INSERT INTO bin_section (id, name) VALUES (14, 'Bottom');

INSERT INTO bin (id, name, x, y) VALUES (9, 'Outdoor', -1, -1);
INSERT INTO bin (id, name, x, y) VALUES (10, 'Fan 1', 0, 0);
INSERT INTO bin (id, name, x, y) VALUES (11, 'Burner 1', 1, 0);
INSERT INTO bin (id, name, x, y) VALUES (12, 'Bin 1', 2, 0);
INSERT INTO bin (id, name, x, y) VALUES (13, 'Bin 2', 3, 0);
INSERT INTO bin (id, name, x, y) VALUES (14, 'Bin 3', 4, 0);
INSERT INTO bin (id, name, x, y) VALUES (15, 'Bin 4', 5, 0);
INSERT INTO bin (id, name, x, y) VALUES (16, 'Bin 5', 6, 0);
INSERT INTO bin (id, name, x, y) VALUES (17, 'Bin 6', 7, 0);
INSERT INTO bin (id, name, x, y) VALUES (18, 'Bin 7', 8, 0);

INSERT INTO bin (id, name, x, y) VALUES (19, 'Fan 2', 0, 1);
INSERT INTO bin (id, name, x, y) VALUES (20, 'Burner 2', 1, 1);
INSERT INTO bin (id, name, x, y) VALUES (21, 'Bin 8', 2, 1);
INSERT INTO bin (id, name, x, y) VALUES (22, 'Bin 9', 3, 1);
INSERT INTO bin (id, name, x, y) VALUES (23, 'Bin 10', 4, 1);
INSERT INTO bin (id, name, x, y) VALUES (24, 'Bin 11', 5, 1);
INSERT INTO bin (id, name, x, y) VALUES (25, 'Bin 12', 6, 1);
INSERT INTO bin (id, name, x, y) VALUES (26, 'Bin 13', 7, 1);
INSERT INTO bin (id, name, x, y) VALUES (27, 'Bin 14', 8, 1);

