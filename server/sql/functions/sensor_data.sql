CREATE OR REPLACE function iso_timestamp(TIMESTAMPTZ)
	RETURNS VARCHAR AS $$
	SELECT substring(xmlelement(name x, $1)::VARCHAR FROM 4 FOR 25)
	 $$ LANGUAGE SQL IMMUTABLE;



\i reading_data_subsample.sql
\i reading_data_latest_funcs.sql

CREATE OR REPLACE FUNCTION sensor_data_trig_func2(_sd sensor_data) RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_myrow record;
	_myrow2 record;
BEGIN
	IF _sd.error_code IS NULL THEN
		-- Get read_type, bin, bin_section
		SELECT device.bin_id, device.bin_section_id, sensor_type.read_type_id as read_type_id INTO _myrow FROM sensor, device, sensor_type WHERE sensor.id = _sd.sensor_id and device.id = sensor.device_id and sensor_type.id = sensor.sensor_type_id;
		PERFORM update_reading_data_subsample(_sd.datetime, _myrow.bin_id, _myrow.bin_section_id, _myrow.read_type_id, _sd.value);
		PERFORM update_reading_data_latest(_sd.datetime, _myrow.bin_id, _myrow.bin_section_id, _myrow.read_type_id, _sd.value);
		-- sensor_mirror
		SELECT bin_id, bin_section_id INTO _myrow2 FROM sensor_mirror WHERE sensor_id = _sd.sensor_id;
		IF _myrow2 IS NOT NULL THEN
			PERFORM update_reading_data_subsample(_sd.datetime, _myrow2.bin_id, _myrow2.bin_section_id, _myrow.read_type_id, _sd.value);
			PERFORM update_reading_data_latest(_sd.datetime, _myrow2.bin_id, _myrow2.bin_section_id, _myrow.read_type_id, _sd.value);
		END IF;
	END IF;
	RETURN;
END
$$;

-- The trigger function to update the subsample tables and call dew jf sensor 
-- type functions.
CREATE OR REPLACE FUNCTION sensor_data_trig_func() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
	PERFORM sensor_data_trig_func2(NEW);
	RETURN NEW;
END;
$$;


CREATE TRIGGER sensor_data_trig AFTER INSERT ON sensor_data
	FOR EACH ROW
		EXECUTE PROCEDURE sensor_data_trig_func();


-- Sensor data latest trigs

CREATE OR REPLACE FUNCTION sensor_data_latest_trig_func2(_sd sensor_data) RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    _ourrow RECORD;
BEGIN
    SELECT id, datetime INTO _ourrow FROM sensor_data_latest WHERE sensor_id = _sd.sensor_id;
    IF _ourrow IS NULL THEN
        INSERT INTO sensor_data_latest (sensor_id, value, raw_data, datetime, error_code) VALUES (_sd.sensor_id, _sd.value, _sd.raw_data, _sd.datetime, _sd.error_code);
    ELSE
        IF _ourrow.datetime < _sd.datetime THEN
            UPDATE sensor_data_latest SET value=_sd.value, raw_data=_sd.raw_data, datetime=_sd.datetime, error_code=_sd.error_code WHERE id = _ourrow.id;
        END IF;
    END IF;
    RETURN;
END
$$;

-- The trigger function to update the subsample tables and call dew jf sensor·
-- type functions.
CREATE OR REPLACE FUNCTION sensor_data_latest_trig_func() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM sensor_data_latest_trig_func2(NEW);
    RETURN NEW;
END;
$$;



CREATE TRIGGER sensor_data_latest_trig AFTER INSERT ON sensor_data
    FOR EACH ROW
        EXECUTE PROCEDURE sensor_data_latest_trig_func();



CREATE OR REPLACE FUNCTION err_out_latest_sensor_data() RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    _row RECORD;
BEGIN
    DELETE from sensor_data_latest;
    FOR _row in select s.id as sensor_id from sensor s, device d where s.device_id = d.id and d.year = extract(year from now()) and d.enabled_p = true and s.enabled_p = true LOOP
	    INSERT into sensor_data_latest (sensor_id, error_code) values (_row.sensor_id, -2);
	END LOOP;
END
$$;

