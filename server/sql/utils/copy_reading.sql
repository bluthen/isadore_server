-- select * from reading where datetime > timestamp '2013-09-10 08:20' and datetime < timestamp '2013-09-10 08:30';
BEGIN;

DO $$
DECLARE 
	new_rid integer;
	s record;
BEGIN
	SELECT nextval('reading_seq') INTO new_rid;
	RAISE NOTICE 'New reading ID: %', new_rid;
	INSERT INTO READING (id) VALUES (new_rid);
	FOR s IN SELECT bin_id, bin_section_id, sensor_type_id, raw_data, value FROM reading_data WHERE reading_id = 6756 LOOP
		INSERT INTO reading_data (reading_id, bin_id, bin_section_id, sensor_type_id, raw_data, value) VALUES (new_rid, s.bin_id, s.bin_section_id, s.sensor_type_id, s.raw_data, s.value);
	END LOOP;
END $$;

commit;

END;

