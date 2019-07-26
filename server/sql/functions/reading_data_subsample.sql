-- convient function to compute a set of reading_data-subsamples from sensor_data table. 
-- @param start_id The start sensor_data.id 
-- @param end_id The end sensor_data.id, exclusive.
CREATE OR REPLACE FUNCTION update_reading_data_subsample_from_sensor_data(_start_id int, _end_id int)
	RETURNS TABLE(row_count bigint, time_taken INTERVAL) LANGUAGE plpgsql AS $$
DECLARE
	_before TIMESTAMPTZ;
	_after TIMESTAMPTZ;
	_count_r RECORD;
BEGIN
	_before := to_timestamp(timeofday(), 'Dy Mon DD HH24:MI:SS.MS YYYY');
	SELECT count(sensor_data_trig_func2(sd.*)) AS c INTO _count_r
		FROM sample_data sd WHERE id >= _start_id AND id < _end_id;
	_after := to_timestamp(timeofday(), 'Dy Mon DD HH24:MI:SS.MS YYYY');
	RETURN QUERY SELECT _count_r.c as row_count, _after - _before as time_taken;
END
$$;


--Absolute humidity and dew
CREATE OR REPLACE FUNCTION update_reading_data_subsample_calc_dew(_reading_subsample_id INTEGER, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _avg_value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_temp_value double precision;
	_hum_value double precision;
	_dew double precision;
	_abshum double precision;
BEGIN
	IF _read_type_id = 10 THEN
		_temp_value := _avg_value;
		SELECT reading_data_subsample.avg_value INTO _hum_value FROM reading_data_subsample where reading_subsample_id = _reading_subsample_id AND bin_id = _bin_id AND bin_section_id = _bin_section_id AND read_type_id = 11;
	ELSIF _read_type_id = 11 THEN
		_hum_value := _avg_value;
		SELECT reading_data_subsample.avg_value INTO _temp_value FROM reading_data_subsample where reading_subsample_id = _reading_subsample_id AND bin_id = _bin_id AND bin_section_id = _bin_section_id AND read_type_id = 10;
	END IF;
	IF _temp_value IS NOT NULL and _hum_value IS NOT NULL AND _hum_value > 0 THEN
		--Dew
		_dew := compute_dew(_temp_value, _hum_value);
		WITH upsert as (UPDATE reading_data_subsample SET avg_value = _dew, min = _dew, max = _dew, current_count = 1 WHERE reading_subsample_id = _reading_subsample_id AND bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 5 RETURNING *) 
			INSERT INTO reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id, avg_value, min, max, current_count) SELECT _reading_subsample_id, _bin_id, _bin_section_id, 5, _dew, _dew, _dew, 1 WHERE NOT EXISTS (SELECT * from upsert);
		--Absolute humidity
		_abshum := calc_absolute_humidity((_temp_value - 32.0) * 0.555556, _hum_value);
		WITH upsert as (UPDATE reading_data_subsample SET avg_value = _abshum, min = _abshum, max = _abshum, current_count = 1 WHERE reading_subsample_id = _reading_subsample_id AND bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 4 RETURNING *) 
			INSERT INTO reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id, avg_value, min, max, current_count) SELECT _reading_subsample_id, _bin_id, _bin_section_id, 4, _abshum, _abshum, _abshum, 1 WHERE NOT EXISTS (SELECT * from upsert);
	END IF;
END
$$;


CREATE OR REPLACE FUNCTION update_reading_data_subsample_calc_guage_pressure(_reading_subsample_id INTEGER, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _avg_value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_gp double precision;
	_outside double precision;
	_myrow RECORD;
BEGIN
	IF _read_type_id != 14 THEN
		RETURN;
	END IF;
	-- Get outside pressure
	SELECT reading_data_subsample.avg_value INTO _outside FROM reading_data_subsample where reading_subsample_id = _reading_subsample_id and bin_id = 9 and bin_section_id = 9 and read_type_id = 14;
	IF _outside IS NOT NULL THEN
		-- TODO: LOCK needed?
		IF _bin_id = 9 and _bin_section_id = 9 THEN
			-- Calc all guage pressure for pressures we have for this reading
			FOR _myrow IN SELECT * FROM reading_data_subsample where reading_subsample_id = _reading_subsample_id and read_type_id = 14 LOOP
				_gp := convert_kpa_to_inh2o(_myrow.avg_value - _outside);
				WITH upsert as (UPDATE reading_data_subsample SET avg_value = _gp, min = _gp, max = _gp, current_count = 1 WHERE reading_subsample_id = _reading_subsample_id AND bin_id = _myrow.bin_id AND bin_section_id = _myrow.bin_section_id and read_type_id = 7 RETURNING *) 
					INSERT INTO reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id, avg_value, min, max, current_count) SELECT _reading_subsample_id, _myrow.bin_id, _myrow.bin_section_id, 7, _gp, _gp, _gp, 1 WHERE NOT EXISTS (SELECT * from upsert);
			END LOOP;
		ELSE
			-- Calc just this one's guage pressure
			_gp := convert_kpa_to_inh2o(_avg_value - _outside);
			WITH upsert as (UPDATE reading_data_subsample SET avg_value = _gp, min = _gp, max = _gp, current_count = 1 WHERE reading_subsample_id = _reading_subsample_id AND bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 7 RETURNING *) 
				INSERT INTO reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id, avg_value, min, max, current_count) SELECT _reading_subsample_id, _bin_id, _bin_section_id, 7, _gp, _gp, _gp, 1 WHERE NOT EXISTS (SELECT * from upsert);
		END IF;
	END IF;
END
$$;


CREATE OR REPLACE FUNCTION update_reading_data_subsample_calc_wetbulb(_reading_subsample_id INTEGER, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _avg_value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_wb double precision;
	_outside double precision;
	_tc double precision;
	_rh double precision;
	_myrow RECORD;
BEGIN
	-- TODO: wetbulb, need temp, rh, and pressure. Pressure will be tricky, we should use best pressure we can find, or just outside pressure? Perhaps pressure with same bin/bin_section else outside? No tunnels. If we get outside pressure how do we know calculation wasn't done using bin pressure?
	-- For now just use outside pressure
	IF (_read_type_id = 14 AND _bin_id != 9 AND _bin_section_id != 9) OR (_read_type_id != 14 AND _read_type_id != 10 and _read_type_id != 11) THEN
		RETURN;
	END IF;
	SELECT avg_value INTO _outside FROM reading_data_subsample where reading_subsample_id = _reading_subsample_id and bin_id = 9 and bin_section_id = 9 and read_type_id = 14;
	IF _outside IS NOT NULL THEN
		-- TODO: LOCK needed?
		IF _bin_id = 9 and _bin_section_id = 9 THEN
			-- Get all bin and bin_sections that have temperature and humidity, and their temperature and humidity values with this reading.
			--TODO: Fix join
			FOR _myrow IN SELECT rds1.bin_id, rds1.bin_section_id, rds1.avg_value avg_temp, rds2.avg_value avg_rh FROM reading_data_subsample rds1, reading_data_subsample rds2 WHERE rds1.reading_subsample_id = _reading_subsample_id and rds2.reading_subsample_id = _reading_subsample_id AND rds1.bin_id = rds2.bin_id and rds1.bin_section_id = rds2.bin_section_id AND rds1.read_type_id = 10 and rds2.read_type_id = 11 LOOP
				IF _myrow.avg_temp IS NOT NULL and _myrow.avg_rh IS NOT NULL THEN
					_wb := calc_wetbulb((_myrow.avg_temp - 32.0) * 0.555556, _myrow.avg_rh, _outside * 10.0);
					WITH upsert as (UPDATE reading_data_subsample SET avg_value = _wb, min = _wb, max = _wb, current_count = 1 WHERE reading_subsample_id = _reading_subsample_id AND bin_id = _myrow.bin_id AND bin_section_id = _myrow.bin_section_id and read_type_id = 131 RETURNING *)
					INSERT INTO reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id, avg_value, min, max, current_count) SELECT _reading_subsample_id, _myrow.bin_id, _myrow.bin_section_id, 131, _wb, _wb, _wb, 1 WHERE NOT EXISTS (SELECT * from upsert);
				END IF;
			END LOOP;
		ELSE
			IF _read_type_id = 10 THEN
				_tc := (_avg_value - 32.0) * 0.555556;
				SELECT avg_value INTO _rh FROM reading_data_subsample WHERE reading_subsample_id = _reading_subsample_id AND bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 11;
			ELSE
				_rh := _avg_value;
				SELECT avg_value INTO _tc FROM reading_data_subsample WHERE reading_subsample_id = _reading_subsample_id AND bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 10;
				_tc := (_tc - 32.0) * 0.555556;
			END IF;
			IF _tc IS NOT NULL and _rh IS NOT NULL AND _rh > 0 THEN
				_wb := calc_wetbulb(_tc, _rh, _outside * 10.0);
				WITH upsert as (UPDATE reading_data_subsample SET avg_value = _wb, min = _wb, max = _wb, current_count = 1 WHERE reading_subsample_id = _reading_subsample_id AND bin_id = _bin_id AND bin_section_id = _bin_section_id and read_type_id = 131 RETURNING *)
					INSERT INTO reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id, avg_value, min, max, current_count) SELECT _reading_subsample_id, _bin_id, _bin_section_id, 131, _wb, _wb, _wb, 1 WHERE NOT EXISTS (SELECT * from upsert);
			END IF;
		END IF;
	END IF;
END
$$;


CREATE OR REPLACE FUNCTION update_reading_data_subsample_calculations(_reading_subsample_id INTEGER, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _avg_value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
BEGIN
	-- TODO: Maybe we can pre-fetch data that is needed for multiple calculations. Dew and wetbulb share common needed data for example.
	IF _read_type_id = 10 or _read_type_id = 11 THEN -- temp or humidity
		-- Dew
		PERFORM update_reading_data_subsample_calc_dew(_reading_subsample_id, _bin_id, _bin_section_id, _read_type_id, _avg_value);
	END IF;
	IF _read_type_id = 14 THEN -- pressure
		-- TODO: guage pressure
		PERFORM update_reading_data_subsample_calc_guage_pressure(_reading_subsample_id, _bin_id, _bin_section_id, _read_type_id, _avg_value);
	END IF;
	IF _read_type_id = 14 OR _read_type_id = 10 or _read_type_id = 11 THEN --temp, humidity, or pressure
		PERFORM update_reading_data_subsample_calc_wetbulb(_reading_subsample_id, _bin_id, _bin_section_id, _read_type_id, _avg_value);
	END IF;
END
$$;


CREATE OR REPLACE FUNCTION update_reading_data_subsample_groups(_datetime TIMESTAMPTZ, _bin_id INTEGER, 
	_bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION, _period INTEGER)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_myrow RECORD;
BEGIN
	FOR _myrow IN SELECT grp_bin_id FROM bin_grp WHERE member_bin_id = _bin_id LOOP
		PERFORM update_reading_data_subsample(_datetime, _myrow.grp_bin_id, _bin_section_id, _read_type_id, _value, _period);
	END LOOP;

	FOR _myrow IN SELECT grp_bin_section_id FROM bin_section_grp WHERE member_bin_section_id = _bin_section_id LOOP
		PERFORM update_reading_data_subsample(_datetime, _bin_id, _myrow.grp_bin_section_id, _read_type_id, _value, _period);
	END LOOP;
END
$$;



-- Update reading_data_subsample for a sample period, adds reading_subsample if needed.
-- @param newrow The reading_data row that needs to be processed.
-- @param period The sample period in minutes.
-- @param record_date The timestamp associated with newrow.
CREATE OR REPLACE FUNCTION update_reading_data_subsample(_datetime TIMESTAMPTZ, _bin_id INTEGER, 
	_bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION, _period INTEGER)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_old_rds reading_data_subsample%ROWTYPE;
	_rs_row reading_subsample%ROWTYPE;
	_rds_avg_value double precision;
	_rds_min double precision;
	_rds_max double precision;
	_rds_count integer;
	_sample_date TIMESTAMPTZ;
BEGIN
	IF _value IS NULL THEN
		RETURN;
	END IF;
	_sample_date := compute_sample_date(_datetime, _period);

	SELECT * INTO _rs_row FROM reading_subsample WHERE
		datetime = _sample_date AND sample_period=_period;
	IF _rs_row.id IS NULL THEN
		INSERT INTO reading_subsample (datetime, sample_period) VALUES
			(_sample_date, _period);
		SELECT * INTO _rs_row FROM reading_subsample WHERE
			datetime = _sample_date AND sample_period = _period;
	END IF;
	SELECT * INTO _old_rds FROM reading_data_subsample WHERE
		reading_subsample_id = _rs_row.id AND bin_id = _bin_id AND
		bin_section_id = _bin_section_id AND
		read_type_id = _read_type_id;


	--TODO: Change to upsert
	--TODO: Lock?
	IF _old_rds.id IS NOT NULL THEN
		_rds_avg_value := _old_rds.avg_value;
		_rds_min := _old_rds.min;
		_rds_max := _old_rds.max;
		_rds_count := _old_rds.current_count;

		_rds_avg_value := (_rds_avg_value*_rds_count + _value)/(_rds_count+1);
		_rds_count := _rds_count+1;
		IF _value < _rds_min THEN
			_rds_min := _value;
		END IF;
		IF _value > _rds_max THEN
			_rds_max := _value;
		END IF;
		UPDATE reading_data_subsample SET avg_value = _rds_avg_value,
			min = _rds_min, max = _rds_max, current_count = _rds_count WHERE
			id = _old_rds.id;
	ELSE
		INSERT INTO reading_data_subsample (reading_subsample_id, bin_id, 
			bin_section_id, read_type_id, avg_value, min, max, current_count)
			VALUES (_rs_row.id, _bin_id, _bin_section_id,
			_read_type_id, _value, _value, _value,
			1);
		_rds_avg_value := _value;
	END IF;
	-- Calcuations
	PERFORM update_reading_data_subsample_calculations(_rs_row.id, _bin_id, _bin_section_id, _read_type_id, _rds_avg_value);
	-- Group Crawl
	PERFORM update_reading_data_subsample_groups(_sample_date, _bin_id, _bin_section_id, _read_type_id, _rds_avg_value, _period);
END
$$;

-- For an inserted row into reading_data for each subsample put in subsample data.
-- @param newrow The reading_data row that needs to be processed.
CREATE OR REPLACE FUNCTION update_reading_data_subsample(_datetime TIMESTAMPTZ, _bin_id INTEGER,
	_bin_section_id INTEGER, _read_type_id INTEGER, _value DOUBLE PRECISION)
	RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
	_s record;
BEGIN
	FOR _s IN SELECT subsample FROM default_subsample LOOP
		PERFORM update_reading_data_subsample(_datetime, _bin_id, _bin_section_id, _read_type_id, _value, _s.subsample);
	END LOOP;
END
$$;


