CREATE OR REPLACE FUNCTION update_reading_data_latest_calc_wetbulb(_datetime TIMESTAMPTZ, _bin_id INTEGER,
    _bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION)
    RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    _wb double precision;
    _outside_record RECORD;
    _ts TIMESTAMPTZ;
    _myrow RECORD;
    _tc_record RECORD;
    _rh_record RECORD;
    _tc DOUBLE PRECISION;
BEGIN
    -- TODO: wetbulb, need temp, rh, and pressure. Pressure will be tricky, we should use best pressure we can find, or just outside pressure? Perhaps pressure with same bin/bin_section else outside? No tunnels. If we get outside pressure how do we know calculation wasn't done using bin pressure?
    -- For now just use outside pressure
    IF (_read_type_id = 14 AND _bin_id != 9 AND _bin_section_id != 9) OR (_read_type_id != 14 AND _read_type_id != 10 and _read_type_id != 11) THEN
        RETURN;
    END IF;
    SELECT datetime, value INTO _outside_record FROM reading_data_latest where datetime >= _datetime - interval '30min' AND bin_id = 9 and bin_section_id = 9 and read_type_id = 14;
    IF _outside_record.value IS NOT NULL THEN
        IF _bin_id = 9 and _bin_section_id = 9 THEN
            -- Get all bin and bin_sections that have temperature and humidity, and their temperature and humidity values with this reading.
            --TODO: Fix join
            FOR _myrow IN SELECT rdl1.bin_id, rdl1.bin_section_id, rdl1.datetime temp_datetime, rdl1.value temp_value, rdl2.datetime rh_datetime, rdl2.value rh_value FROM reading_data_latest rdl1, reading_data_latest rdl2 WHERE rdl1.bin_id = rdl2.bin_id and rdl1.bin_section_id = rdl2.bin_section_id AND rdl1.read_type_id = 10 and rdl2.read_type_id = 11 LOOP
                IF _myrow.temp_value IS NOT NULL and _myrow.rh_value IS NOT NULL THEN
                    _ts := _outside_record.datetime;
                    IF _ts >= _myrow.rh_datetime THEN
                        _ts := _myrow.rh_datetime;
                    END IF;
                    IF _ts >= _myrow.temp_datetime THEN
                        _ts := _myrow.temp_datetime;
                    END IF;
                    _wb := calc_wetbulb((_myrow.temp_value - 32.0) * 0.555556, _myrow.rh_value, _outside_record.value * 10.0);
                    WITH upsert AS (UPDATE reading_data_latest SET datetime = _ts, value = _wb WHERE bin_id = _myrow.bin_id AND bin_section_id = _myrow.bin_section_id and read_type_id = 131 RETURNING *)
                    INSERT INTO reading_data_latest (datetime, bin_id, bin_section_id, read_type_id, value) SELECT _ts, _myrow.bin_id, _myrow.bin_section_id, 131, _wb WHERE NOT EXISTS (SELECT * from upsert);
                END IF;
            END LOOP;
        ELSE
            SELECT datetime, value INTO _tc_record FROM reading_data_latest WHERE datetime >= _datetime - interval '30min' AND bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 10;
            SELECT datetime, value INTO _rh_record FROM reading_data_latest WHERE datetime >= _datetime - interval '30min' AND bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 11;
            IF _tc_record.value IS NOT NULL and _rh_record.value IS NOT NULL AND _rh_record.value > 0 THEN
                 _ts := _outside_record.datetime;
                 IF _ts >= _rh_record.datetime THEN
                 	_ts := _rh_record.datetime;
                 END IF;
                 IF _ts >= _tc_record.datetime THEN
                 	_ts := _tc_record.datetime;
                 END IF;
                _tc := (_tc_record.value - 32.0) * 0.555556;
                _wb := calc_wetbulb(_tc, _rh_record.value, _outside_record.value * 10.0);
                WITH upsert as (UPDATE reading_data_latest SET datetime = _ts, value = _wb WHERE bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 131 RETURNING *)
                    INSERT INTO reading_data_latest (datetime, bin_id, bin_section_id, read_type_id, value) SELECT _ts, _bin_id, _bin_section_id, 131, _wb WHERE NOT EXISTS (SELECT * from upsert);
            END IF;
        END IF;
    END IF;
END
$$;

CREATE OR REPLACE FUNCTION update_reading_data_latest_calc_guage_pressure(_datetime TIMESTAMPTZ, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_gp double precision;
	_outside_record RECORD;
	_myrow RECORD;
    _ts TIMESTAMPTZ;
BEGIN
	IF _read_type_id != 14 THEN
		RETURN;
	END IF;
	-- Get outside pressure
	SELECT datetime, value INTO _outside_record FROM reading_data_latest WHERE datetime >= _datetime - interval '30min' AND bin_id = 9 and bin_section_id = 9 and read_type_id = 14;
	IF _outside_record.value IS NOT NULL THEN
		IF _bin_id = 9 and _bin_section_id = 9 THEN
			-- Calc all guage pressure for pressures we have for this reading
			FOR _myrow IN SELECT * FROM reading_data_latest where read_type_id = 14 LOOP
                IF _outside_record.datetime <= _myrow.datetime THEN 
                	_ts := _outside_record.datetime;
                ELSE
                    _ts := _myrow.datetime;
                END IF;
				_gp := convert_kpa_to_inh2o(_myrow.value - _outside_record.value);
				WITH upsert as (UPDATE reading_data_latest SET datetime = _ts, value = _gp WHERE bin_id = _myrow.bin_id AND bin_section_id = _myrow.bin_section_id and read_type_id = 7 RETURNING *)
					INSERT INTO reading_data_latest (datetime, bin_id, bin_section_id, read_type_id, value) SELECT _ts, _myrow.bin_id, _myrow.bin_section_id, 7, _gp WHERE NOT EXISTS (SELECT * from upsert);
			END LOOP;
		ELSE
			-- Calc just this one's guage pressure
            IF _outside_record.datetime <= _datetime THEN 
            	_ts := _outside_record.datetime;
            ELSE
                _ts := _datetime;
            END IF;
			_gp := convert_kpa_to_inh2o(_value - _outside_record.value);
			WITH upsert as (UPDATE reading_data_latest SET datetime = _ts, value = _gp WHERE bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 7 RETURNING *)
				INSERT INTO reading_data_latest (datetime, bin_id, bin_section_id, read_type_id, value) SELECT _ts, _bin_id, _bin_section_id, 7, _gp WHERE NOT EXISTS (SELECT * from upsert);
		END IF;
	END IF;
END
$$;

--Absolute humidity and dew
CREATE OR REPLACE FUNCTION update_reading_data_latest_calc_dew(_datetime TIMESTAMPTZ, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_temp_record RECORD;
	_hum_record RECORD;
	_dew double precision;
	_abshum double precision;
	_ts TIMESTAMPTZ;
BEGIN
	SELECT datetime, value INTO _hum_record FROM reading_data_latest where datetime >= _datetime - interval '30min' AND bin_id = _bin_id AND bin_section_id = _bin_section_id AND read_type_id = 11;
	SELECT datetime, value INTO _temp_record FROM reading_data_latest where datetime >= _datetime - interval '30min' AND bin_id = _bin_id AND bin_section_id = _bin_section_id AND read_type_id = 10;
	IF _temp_record.value IS NOT NULL and _hum_record.value IS NOT NULL AND _hum_record.value > 0 THEN
		IF _temp_record.datetime <= _hum_record.datetime THEN
			_ts := _temp_record.datetime;
		ELSE
			_ts := _hum_record.datetime;
		END IF; 
		--Dew
		_dew := compute_dew(_temp_record.value, _hum_record.value);
		WITH upsert as (UPDATE reading_data_latest SET datetime = _ts, value = _dew WHERE bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 5 RETURNING *)
			INSERT INTO reading_data_latest (datetime, bin_id, bin_section_id, read_type_id, value) SELECT _ts, _bin_id, _bin_section_id, 5, _dew WHERE NOT EXISTS (SELECT * from upsert);
		--Absolute humidity
		_abshum := calc_absolute_humidity((_temp_record.value - 32.0) * 0.555556, _hum_record.value);
		WITH upsert as (UPDATE reading_data_latest SET datetime = _ts, value = _abshum WHERE bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 4 RETURNING *)
			INSERT INTO reading_data_latest (datetime, bin_id, bin_section_id, read_type_id, value) SELECT _ts, _bin_id, _bin_section_id, 4, _abshum WHERE NOT EXISTS (SELECT * from upsert);
	END IF;
END
$$;

CREATE OR REPLACE FUNCTION update_reading_data_latest_calculations(_datetime TIMESTAMPTZ, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
BEGIN
	IF _read_type_id = 10 or _read_type_id = 11 THEN -- temp or humidity
		-- Dew
		PERFORM update_reading_data_latest_calc_dew(_datetime, _bin_id, _bin_section_id, _read_type_id, _value);
	END IF;
	IF _read_type_id = 14 THEN -- pressure
		-- TODO: guage pressure
		PERFORM update_reading_data_latest_calc_guage_pressure(_datetime, _bin_id, _bin_section_id, _read_type_id, _value);
	END IF;
	IF _read_type_id = 14 OR _read_type_id = 10 or _read_type_id = 11 THEN --temp, humidity, or pressure
		PERFORM update_reading_data_latest_calc_wetbulb(_datetime, _bin_id, _bin_section_id, _read_type_id, _value);
	END IF;
END
$$;

CREATE OR REPLACE FUNCTION update_reading_data_latest_groups(_datetime TIMESTAMPTZ, _bin_id INTEGER,
    _bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION)
    RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    _myrow RECORD;
    _myrow2 RECORD;
BEGIN
    FOR _myrow IN SELECT DISTINCT grp_bin_id FROM bin_grp WHERE member_bin_id = _bin_id LOOP
    	SELECT min(rdl.datetime) as datetime, avg(rdl.value) as value INTO _myrow2 FROM reading_data_latest rdl, bin_grp bg WHERE rdl.datetime >= _datetime - interval '30min' AND rdl.bin_section_id = _bin_section_id AND rdl.bin_id = bg.member_bin_id AND bg.grp_bin_id = _myrow.grp_bin_id AND rdl.read_type_id = _read_type_id;
        PERFORM update_reading_data_latest(_myrow2.datetime, _myrow.grp_bin_id, _bin_section_id, _read_type_id, _myrow2.value);
    END LOOP;

	FOR _myrow IN SELECT DISTINCT grp_bin_section_id FROM bin_section_grp WHERE member_bin_section_id = _bin_section_id LOOP
		SELECT min(rdl.datetime) AS datetime, avg(rdl.value) AS value INTO _myrow2 FROM reading_data_latest rdl, bin_section_grp WHERE rdl.datetime >= _datetime - interval '30min' AND rdl.bin_id = _bin_id and rdl.bin_section_id = bin_section_grp.member_bin_section_id AND rdl.read_type_id = _read_type_id;
        PERFORM update_reading_data_latest(_myrow2.datetime, _bin_id, _myrow.grp_bin_section_id, _read_type_id, _myrow2.value);
	END LOOP;
END
$$;

CREATE OR REPLACE FUNCTION update_reading_data_latest(_datetime TIMESTAMPTZ, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_old_rdl reading_data_latest%ROWTYPE;
BEGIN
	IF _value IS NULL THEN
		RETURN;
	END IF;

	SELECT * INTO _old_rdl FROM reading_data_latest WHERE
		bin_id = _bin_id AND
		bin_section_id = _bin_section_id AND
		read_type_id = _read_type_id;
	IF _old_rdl.id IS NOT NULL THEN
		UPDATE reading_data_latest SET datetime = _datetime, value = _value WHERE id = _old_rdl.id;
	ELSE
		INSERT INTO reading_data_latest (datetime, bin_id,
			bin_section_id, read_type_id, value)
			VALUES (_datetime, _bin_id, _bin_section_id,
			_read_type_id, _value);
	END IF;
	-- Calcuations
	PERFORM update_reading_data_latest_calculations(_datetime, _bin_id, _bin_section_id, _read_type_id, _value);
	-- Group Crawl
	PERFORM update_reading_data_latest_groups(_datetime, _bin_id, _bin_section_id, _read_type_id, _value);
END
$$;

