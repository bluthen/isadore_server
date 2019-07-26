insert into account (email, password, seed, name, phone,  privilege_id) VALUES ('testsuperuser@exotericanalytics.com', encode(digest('candy23j:+lI%:38', 'sha1'), 'hex'), 'candy23', 'Test Super User','15555555555', 2000);

insert into account (email, password, seed, name, phone,  privilege_id) VALUES ('testpoweruser@exotericanalytics.com', encode(digest('fanbdo3H_FKB{#r', 'sha1'), 'hex'), 'fanbdo', 'Test Power User','15555555555', 1000);

insert into account (email, password, seed, name, phone,  privilege_id) VALUES ('testconfiguser@exotericanalytics.com', encode(digest('34adjk6=9%KVn6', 'sha1'), 'hex'), '34adj', 'Test Config User','15555555555', 500);

insert into account (email, password, seed, name, phone,  privilege_id) VALUES ('testfilluser@exotericanalytics.com', encode(digest('bartwWL1CgCZW.', 'sha1'), 'hex'), 'bart', 'Test Fill User','15555555555', 250);

insert into account (email, password, seed, name, phone,  privilege_id) VALUES ('testuser@exotericanalytics.com', encode(digest('hokie439J2)Tl8', 'sha1'), 'hex'), 'hokie', 'Test User','15555555555', 100);

INSERT INTO general_config (id, interval, enabled_p, mid_pass, customer_name, customer_short_name, multiple_rolls) values (1, 300, true, 'v7-J}8$bh', 'Dans Basement Farm', 'Basic', TRUE); -- yes, this is a horrible password

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
INSERT INTO bin (id, name, x, y) VALUES (26, 'Burner 2', 16, 0);
INSERT INTO bin (id, name, x, y) VALUES (27, 'Fan 2', 17, 0);

INSERT INTO bin (id, name, x, y) VALUES (28, 'Fan 3', 0, 1);
INSERT INTO bin (id, name, x, y) VALUES (29, 'Burner 3', 1, 1);
INSERT INTO bin (id, name, x, y) VALUES (30, 'Bin 15', 2, 1);
INSERT INTO bin (id, name, x, y) VALUES (31, 'Bin 16', 3, 1);

INSERT INTO customer (id,name) VALUES (1,'internal');
INSERT INTO customer (id,name) VALUES (2,'customer 1');
INSERT INTO customer (id,name) VALUES (3,'customer 2');

INSERT INTO operator (id,name) VALUES (1,'internal');
INSERT INTO operator (id,name) VALUES (2,'operator 1');
INSERT INTO operator (id,name) VALUES (3,'operator 2');

INSERT INTO product (id,name) VALUES (1,'GEC');
INSERT INTO product (id,name) VALUES (2,'commercial corn');
INSERT INTO product (id,name) VALUES (3,'soybeans');
INSERT INTO product (id,name) VALUES (4,'cobbs');
INSERT INTO product (id,name) VALUES (5,'that other stuff');

INSERT INTO storage (id,name,description) VALUES (1,'RB1','Round bin 1');
INSERT INTO storage (id,name,description) VALUES (2,'RB2','Round bin 1');
INSERT INTO storage (id,name,description) VALUES (3,'RB3','Round bin 1');
INSERT INTO storage (id,name,description) VALUES (4,'RB4','Round bin 1');
INSERT INTO storage (id,name,description) VALUES (5,'RB5','Round bin 1');
INSERT INTO storage (id,name,description) VALUES (6,'RB6','Round bin 1');
INSERT INTO storage (id,name,description) VALUES (7,'RB7','Round bin 1');
INSERT INTO storage (id,name,description) VALUES (8,'RB8','Round bin 1');
INSERT INTO storage (id,name,description) VALUES (9,'BS1','Bulk storage 1');
INSERT INTO storage (id,name,description) VALUES (10,'BS2','Bulk storage 2');
INSERT INTO storage (id,name,description) VALUES (11,'BS3','Bulk storage 3');
INSERT INTO storage (id,name,description) VALUES (12,'cobbs','Cobb storage');

INSERT INTO field (id,name,landlord,operator,product,year) VALUES (1,'field 1',1,1,1,2012);
INSERT INTO field (id,name,landlord,operator,product,year) VALUES (2,'field 2',1,1,1,2012);
INSERT INTO field (id,name,landlord,operator,product,year) VALUES (3,'field 3',1,1,1,2012);
INSERT INTO field (id,name,landlord,operator,product,year) VALUES (4,'field 4',2,1,2,2012);
INSERT INTO field (id,name,landlord,operator,product,year) VALUES (5,'field 5',3,2,3,2012);
INSERT INTO field (id,name,landlord,operator,product,year) VALUES (6,'field 6',2,3,1,2012);
INSERT INTO field (id,name,landlord,operator,product,year) VALUES (7,'field 7',2,3,2,2012);
