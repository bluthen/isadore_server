-- jody factor
CREATE OR REPLACE FUNCTION jf(ut double precision, uh double precision, lt double precision, lh double precision) RETURNS double precision 
	LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
	return ut + uh - lt - lh;
END
$$;

--http://www.sensirion.com/en/pdf/product_information/Introduction_to_Relative_Humidity_E.pdf
--http://www.sensirion.com/en/pdf/product_information/AN-humidity-formulae.pdf
CREATE OR REPLACE FUNCTION compute_dew(double precision, double precision) 
	RETURNS double precision LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
	t DOUBLE PRECISION;
	h DOUBLE PRECISION;
	td DOUBLE PRECISION;
BEGIN
	t := ($1-32.0)*(5.0/9.0);
	if $2 < 0 then
		return null;
	end if;
	h := (log($2) - 2.0)/0.4343 + (17.62*t)/(243.12+t);
	td := (243.12*h/(17.62-h))*(9.0/5.0)+32.0;
	return td;
END
$$;

CREATE FUNCTION next_conf() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE cache_versions SET conf_version=NEXTVAL('conf_version'), conf_datetime=CURRENT_TIMESTAMP WHERE id=1;
  RETURN NULL; 
END
$$;

-- Returns '[arg,arg,arg]'
CREATE OR REPLACE FUNCTION json_repeat_array(arg anyelement) RETURNS varchar
	LANGUAGE sql IMMUTABLE AS $$
	SELECT '['||$1||','||$1||','||$1||']'
$$;

CREATE OR REPLACE FUNCTION array_avg(double precision[])
	RETURNS double precision LANGUAGE SQL IMMUTABLE AS $$
SELECT avg(v) FROM unnest($1) g(v)
$$;

--Ref: http://www.revsys.com/blog/2006/aug/04/automatically-updating-a-timestamp-column-in-postgresql/
CREATE OR REPLACE FUNCTION update_account_recovery_datetime()
RETURNS TRIGGER AS $$
BEGIN
	NEW.recovery_datetime = now();
	return NEW;
END;
$$ language 'plpgsql';

-- Computes the sample timestamp given a timestamp and sample period.
-- @param $1 The timestamp for a record.
-- @param $2 The sample period in minutes (1 to 1440).
CREATE OR REPLACE FUNCTION compute_sample_date(TIMESTAMPTZ, int) RETURNS TIMESTAMPTZ LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
	new_hours double precision;
	sample_period_hours double precision;
BEGIN
	sample_period_hours = $2/60.0;
	new_hours := ceil(
		trunc(
			(extract(hours from $1) + extract(minutes from $1)/60+extract(seconds from $1)/3600) / 
			(sample_period_hours/2.0))/2.0)*sample_period_hours;
	return date_trunc('day', $1)+new_hours*interval '1h';
END
$$;


CREATE OR REPLACE FUNCTION convert_kpa_to_inh2o(double precision)
	RETURNS double precision LANGUAGE SQL IMMUTABLE AS $$
	SELECT 4.0186*$1;
$$;


-- Source: http://archives.postgresql.org/pgsql-general/2009-02/msg01225.php
CREATE OR REPLACE function iso_timestamp(TIMESTAMPTZ)
   RETURNS VARCHAR AS $$
  SELECT substring(xmlelement(name x, $1)::VARCHAR FROM 4 FOR 25)
$$ LANGUAGE SQL IMMUTABLE;


-- Returns inlet data
-- (upper_temp >= lower_temp) ? upper_value : lower_value.
-- @param upper_temp The temp on top bin.
-- @param lower_temp The temp of top bin.
-- @param upper_value The top bin value.
-- @param lower_value The bottom bin value.
CREATE OR REPLACE FUNCTION inlet(upper_temp double precision, lower_temp 
	double precision, upper_value anyelement, lower_value anyelement)
	RETURNS anyelement LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    IF upper_temp IS NULL OR lower_temp IS NULL THEN
	    RETURN NULL;
	ELSE
    	IF upper_temp >= lower_temp THEN
	    	RETURN upper_value;
	    ELSE
		    RETURN lower_value;
	    END IF;
	END IF;
END
$$;

-- Returns outlet data
-- (upper_temp < lower_temp) ? upper_value : lower_value.
-- @param upper_temp The temp on top bin.
-- @param lower_temp The temp of top bin.
-- @param upper_value The top bin value.
-- @param lower_value The bottom bin value.
CREATE OR REPLACE FUNCTION outlet(upper_temp double precision, lower_temp 
	double precision, upper_value anyelement, lower_value anyelement)
	RETURNS anyelement LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    IF upper_temp IS NULL OR lower_temp IS NULL THEN
	    RETURN NULL;
	ELSE
    	IF upper_temp < lower_temp THEN
	    	RETURN upper_value;
    	ELSE
	    	RETURN lower_value;
    	END IF;
   	END IF;
END
$$;


--recovery_account
CREATE TRIGGER account_recovery_hash_datetime_trig BEFORE UPDATE ON account FOR EACH ROW EXECUTE PROCEDURE update_account_recovery_datetime();
--general_config
CREATE TRIGGER general_config_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON general_config EXECUTE PROCEDURE next_conf(); 
--bin
CREATE TRIGGER bin_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON bin EXECUTE PROCEDURE next_conf(); 
--bin_section
CREATE TRIGGER bin_section_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON bin_section EXECUTE PROCEDURE next_conf(); 
--device_type
CREATE TRIGGER device_type_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON device_type EXECUTE PROCEDURE next_conf(); 
--device
CREATE TRIGGER device_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON device EXECUTE PROCEDURE next_conf(); 
--sensor_type
CREATE TRIGGER sensor_type_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON sensor_type EXECUTE PROCEDURE next_conf(); 
--sensor
CREATE TRIGGER sensor_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON sensor EXECUTE PROCEDURE next_conf(); 
CREATE TRIGGER sensor_mirror_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON sensor_mirror EXECUTE PROCEDURE next_conf(); 
--read_type
CREATE TRIGGER read_type_confv_trig AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON read_type EXECUTE PROCEDURE next_conf(); 

-- Part maxtemp


CREATE OR REPLACE FUNCTION compute_interval_dried(startt TIMESTAMPTZ, 
	endt TIMESTAMPTZ) RETURNS interval LANGUAGE plpgsql STABLE AS $$
DECLARE
	dtime interval;
	lastTime TIMESTAMPTZ;
	deducts boolean;
	d RECORD;
BEGIN
	lastTime := startt;
	dtime := '0'::interval;
	FOR d IN SELECT begin_datetime, end_datetime FROM air_deduct WHERE 
		((begin_datetime >= startt AND begin_datetime <= endt) OR 
		(begin_datetime <= startt AND end_datetime IS NULL) OR 
		(begin_datetime <= startt AND end_datetime >= startt)) ORDER BY 
		begin_datetime LOOP
		deducts := true;
		if d.begin_datetime <= lastTime THEN
			IF d.end_datetime IS NULL OR d.end_datetime >= endt THEN
				RETURN dtime;
			ELSIF d.end_datetime < lastTime THEN
				CONTINUE;
			ELSE
				lastTime := d.end_datetime;
			END IF;
		ELSIF d.begin_datetime > lastTime THEN
			IF d.begin_datetime < endt THEN
				dtime := dtime + (d.begin_datetime - lastTime);
				if d.end_datetime IS NOT NULL AND d.end_datetime < endt THEN
					lastTIME := d.end_datetime;
				ELSE
					RETURN dtime;
				END IF;
			END IF;
		END IF;
	END LOOP;
	RETURN dtime + (endt - lastTime);
END
$$;

CREATE OR REPLACE FUNCTION interval_to_hours(ourinterval INTERVAL)
	RETURNS DOUBLE PRECISION LANGUAGE SQL IMMUTABLE AS $$
	SELECT EXTRACT(EPOCH FROM $1)/3600.0;
$$;

CREATE OR REPLACE FUNCTION hours_to_expected_mc(mc double precision, hours_dried double precision)
	RETURNS double precision LANGUAGE SQL STABLE AS $$
	-- TODO: Get this from bill, or overall config.
	SELECT $1 - $2/4.5;
$$;


CREATE OR REPLACE FUNCTION mc_to_maxtemp(lut_id INTEGER, ourmc double precision) 
	RETURNS DOUBLE PRECISION LANGUAGE plpgsql STABLE AS $$
DECLARE
	retval double precision;
BEGIN
	SELECT maxtemp INTO retval FROM mc_maxtemp_lut_value WHERE mc_maxtemp_lut_id = lut_id AND mc <= ourmc ORDER BY mc DESC LIMIT 1;
	IF retval IS NULL THEN
		SELECT maxtemp INTO retval FROM mc_maxtemp_lut_value WHERE mc_maxtemp_lut_id = lut_id AND mc > ourmc ORDER BY mc LIMIT 1;
	END IF;
	RETURN retval;
END
$$;

-- preMC, startDatetime, deductions, datetimes, 0
-- This needs to be a lot faster.
CREATE OR REPLACE FUNCTION compute_maxtemp(dt TIMESTAMPTZ) RETURNS double precision 
	LANGUAGE plpgsql STABLE AS $$
DECLARE
	myfill fill%ROWTYPE;
	premc double precision;
	hours_dried double precision;
	mc double precision;
BEGIN
	SELECT f.* INTO myfill FROM fill f WHERE
		(f.air_begin_datetime <= dt AND f.air_end_datetime > dt) OR
		(f.air_begin_datetime <= dt AND f.air_end_datetime IS NULL);
	
	-- Should use durings MCs to get better max temp.
	SELECT sum(un)/count(un) INTO premc FROM unnest(myfill.pre_mc) un;
	hours_dried := interval_to_hours(compute_interval_dried(myfill.air_begin_datetime, dt));
	mc := hours_to_expected_mc(premc, hours_dried);
	RETURN mc_to_maxtemp(50, mc);
END
$$;

CREATE OR REPLACE FUNCTION bin_fill_airon(int) RETURNS BOOLEAN
AS $$
	SELECT EXISTS (SELECT TRUE FROM fill WHERE fill_type_id = 1 and bin_id = $1 AND
        ( ((air_begin_datetime < NOW() AND air_end_datetime IS NULL) OR
		        (air_begin_datetime < NOW() AND air_end_datetime > NOW())) ))
$$ LANGUAGE SQL
VOLATILE;

