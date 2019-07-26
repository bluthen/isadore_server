-- XXX: Add index for specific queries used.

CREATE TABLE privilege (
	id INTEGER NOT NULL,
	name VARCHAR(50) NOT NULL,
	CONSTRAINT privilege_pk PRIMARY KEY (id)
);

CREATE SEQUENCE account_seq START 100;
CREATE TABLE account (
	id INTEGER NOT NULL DEFAULT NEXTVAL('account_seq'),
	email VARCHAR(200) NOT NULL,
	name VARCHAR(300) NOT NULL,
	phone VARCHAR (12) DEFAULT NULL,
	password VARCHAR(100) NOT NULL,
	seed VARCHAR(100) NOT NULL,
	privilege_id INTEGER NOT NULL,
	enabled_p BOOLEAN NOT NULL DEFAULT TRUE,
	recovery_hash VARCHAR(40) DEFAULT NULL,
	recovery_datetime TIMESTAMPTZ DEFAULT NULL,
	configs JSON DEFAULT NULL,
	contact_news BOOLEAN DEFAULT true,
	CONSTRAINT account_pk PRIMARY KEY (id),
	CONSTRAINT account_fk_privilege FOREIGN KEY (privilege_id)
		REFERENCES privilege(id) ON DELETE CASCADE
);

CREATE SEQUENCE account_session_seq START 100;
CREATE TABLE account_session (
	id INTEGER NOT NULL DEFAULT NEXTVAL('account_session_seq'),
	account_id INTEGER NOT NULL,
	hash VARCHAR(40) DEFAULT NULL,
	datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT account_session_fk_account FOREIGN KEY (account_id)
		REFERENCES account(id) ON DELETE CASCADE
);


CREATE TABLE mid_info (
	id INTEGER NOT NULL DEFAULT 0,
	contact_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
	mid_ip VARCHAR(20) DEFAULT '',
	conf_version BIGINT DEFAULT 100,
	CONSTRAINT mid_info_pk PRIMARY KEY (id)
);

CREATE TABLE general_config (
	id INTEGER NOT NULL DEFAULT 0,
	interval INTEGER NOT NULL,
	enabled_p BOOLEAN NOT NULL,
	mid_pass VARCHAR(50) NOT NULL,
	alarm_clear_interval INTEGER DEFAULT 15, --minutes
	customer_name VARCHAR DEFAULT NULL,
	customer_short_name VARCHAR DEFAULT NULL,
	dump_scale_factor INTEGER DEFAULT 61,
	multiple_rolls BOOLEAN DEFAULT TRUE NOT NULL,
	trucks BOOLEAN DEFAULT TRUE NOT NULL,
	during_mc BOOLEAN DEFAULT TRUE NOT NULL,
	jfactor BOOLEAN DEFAULT TRUE NOT NULL,
	inletoutlet BOOLEAN DEFAULT TRUE NOT NULL,
	emchrs_per_point BOOLEAN DEFAULT FALSE NOT NULL,
	dothedew BOOLEAN DEFAULT FALSE NOT NULL,
	default_mc_maxtemp_lut_id INTEGER DEFAULT NULL,
	configs JSON DEFAULT NULL,
	base_url VARCHAR DEFAULT NULL,
	general_seed VARCHAR DEFAULT md5(random()::text),
	CONSTRAINT general_config_pk PRIMARY KEY (id)
);

CREATE SEQUENCE bin_seq START 100;
CREATE TABLE bin (
	id INTEGER DEFAULT NEXTVAL('bin_seq'),
	name VARCHAR(1024) NOT NULL,
	-- coordinates like pixels in image
	x INTEGER NOT NULL, -- 0=left
	y INTEGER NOT NULL, -- 0=up
	display_colspan INTEGER NOT NULL DEFAULT 1,
	extra_info JSON DEFAULT NULL,
	CONSTRAINT bin_pk PRIMARY KEY (id)
);

CREATE SEQUENCE bin_grp_seq START 100;
CREATE TABLE bin_grp (
	id INTEGER DEFAULT NEXTVAL('bin_grp_seq'),
	name VARCHAR(1024) NOT NULL,
	grp_bin_id INTEGER NOT NULL,
	member_bin_id INTEGER NOT NULL,
	CONSTRAINT grp_bin_pk PRIMARY KEY (id),
	CONSTRAINT grp_fk_bin FOREIGN KEY (grp_bin_id)
		REFERENCES bin(id) ON DELETE CASCADE,
	CONSTRAINT member_fk_bin FOREIGN KEY (member_bin_id)
		REFERENCES bin(id) ON DELETE CASCADE
);

CREATE SEQUENCE bin_section_seq START 100;
CREATE TABLE bin_section (
	id INTEGER DEFAULT NEXTVAL('bin_section_seq'),
	name VARCHAR(1024) NOT NULL,
	extra_info JSON DEFAULT NULL,
	CONSTRAINT bin_section_pk PRIMARY KEY (id)
);

CREATE SEQUENCE bin_section_grp_seq START 100;
CREATE TABLE bin_section_grp (
	id INTEGER DEFAULT NEXTVAL('bin_section_grp_seq'),
	name VARCHAR(1024) NOT NULL,
	grp_bin_section_id INTEGER NOT NULL,
	member_bin_section_id INTEGER NOT NULL,
	CONSTRAINT grp_bin_section_pk PRIMARY KEY (id),
	CONSTRAINT grp_fk_bin_section FOREIGN KEY (grp_bin_section_id)
		REFERENCES bin_section(id) ON DELETE CASCADE,
	CONSTRAINT member_fk_bin_section FOREIGN KEY (member_bin_section_id)
		REFERENCES bin_section(id) ON DELETE CASCADE
);



-- e.g. sensor unit, burner, VFD, etc
CREATE SEQUENCE device_type_seq START 100;
CREATE TABLE device_type (
	id INTEGER NOT NULL DEFAULT NEXTVAL('device_type_seq'),
	name VARCHAR(100) NOT NULL,
	CONSTRAINT device_type_pk PRIMARY KEY (id)
);

CREATE SEQUENCE device_seq START 100;
-- particular instance of a device_type
CREATE TABLE device (
	id INTEGER DEFAULT NEXTVAL('device_seq'),
	device_type_id INTEGER NOT NULL,
	name VARCHAR(1024) NOT NULL,
	mid_name VARCHAR(256) DEFAULT NULL,
	address INTEGER DEFAULT NULL,
	port INTEGER DEFAULT NULL,
	enabled_p BOOLEAN NOT NULL DEFAULT true,
	bin_id INTEGER NOT NULL,
	bin_section_id INTEGER NOT NULL,
	year INTEGER NOT NULL,
	info VARCHAR(5000) default NULL,
	CONSTRAINT device_pk PRIMARY KEY (id),
	CONSTRAINT device_address_port CHECK (address IS NULL and port IS NULL or address IS NOT NULL and port IS NOT NULL),
	CONSTRAINT device_fk_bin FOREIGN KEY (bin_id)
		REFERENCES bin(id) ON DELETE CASCADE,
	CONSTRAINT device_fk_bin_section FOREIGN KEY (bin_section_id)
		REFERENCES bin_section(id) ON DELETE CASCADE,
	CONSTRAINT device_fk_device_type FOREIGN KEY (device_type_id)
		REFERENCES device_type(id) ON DELETE CASCADE
);


CREATE SEQUENCE read_type_seq START 1000;
CREATE TABLE read_type (
	id INTEGER DEFAULT NEXTVAL('read_type_seq'),
	name VARCHAR NOT NULL,
	short_name VARCHAR NOT NULL,
	units VARCHAR DEFAULT NULL,
	value_type VARCHAR DEFAULT 'real',
	CONSTRAINT read_type_pk PRIMARY KEY (id)
);


CREATE SEQUENCE sensor_type_seq START 1000;
-- literally a sensor type (e.g. model of temp or anemometer or burner setting)
CREATE TABLE sensor_type (
	id INTEGER DEFAULT NEXTVAL('sensor_type_seq'),
	name VARCHAR NOT NULL, --example 'Temperature'
	default_convert_py VARCHAR DEFAULT NULL,
	read_type_id INTEGER NOT NULL,
	controllable BOOLEAN NOT NULL DEFAULT false,
	CONSTRAINT sensor_type_pk PRIMARY KEY (id),
	CONSTRAINT sensor_type_fk_read_type FOREIGN KEY (read_type_id)
		REFERENCES read_type(id) ON DELETE CASCADE
);

CREATE SEQUENCE sensor_seq START 100;
-- a particular instance of a sensor type (physical)
CREATE TABLE sensor (
	id INTEGER DEFAULT NEXTVAL('sensor_seq'),
	device_id INTEGER NOT NULL,
	sensor_type_id INTEGER NOT NULL,
	convert_py VARCHAR(1024) DEFAULT NULL, -- python math string
	bias REAL DEFAULT 0, -- number to bias the result after convert
	enabled_p BOOLEAN NOT NULL DEFAULT true,
	extra_info JSON DEFAULT NULL,
	CONSTRAINT sensor_pk PRIMARY KEY (id),
	CONSTRAINT sensor_fk_device FOREIGN KEY (device_id)
		REFERENCES device(id) ON DELETE CASCADE,
	CONSTRAINT sensor_fk_sensor_type FOREIGN KEY (sensor_type_id)
		REFERENCES sensor_type(id) ON DELETE CASCADE
);

CREATE SEQUENCE sensor_mirror_seq START 100;
CREATE TABLE sensor_mirror (
	id INTEGER DEFAULT NEXTVAL('sensor_mirror_seq'),
	bin_id INTEGER NOT NULL,
	bin_section_id INTEGER NOT NULL,
	sensor_id INTEGER NOT NULL,
	CONSTRAINT sensor_mirror_pk PRIMARY KEY (id),
	CONSTRAINT sensor_mirror_fk_sensor FOREIGN KEY (sensor_id)
		REFERENCES sensor(id) ON DELETE CASCADE,
	CONSTRAINT sensor_mirror_fk_bin FOREIGN KEY (bin_id)
		REFERENCES bin(id) ON DELETE CASCADE,
	CONSTRAINT sensor_mirror_fk_bin_sensor FOREIGN KEY (bin_section_id)
		REFERENCES bin_section(id) ON DELETE CASCADE
);

-- determines which sensor_type can be associated with a device_type
CREATE SEQUENCE device_type_to_sensor_type_seq START 100;
CREATE TABLE device_type_to_sensor_type (
	id INTEGER NOT NULL DEFAULT NEXTVAL('device_type_to_sensor_type_seq'),
	device_type_id INTEGER NOT NULL,
	sensor_type_id INTEGER NOT NULL,
	CONSTRAINT device_type_to_sensor_type_pk PRIMARY KEY (id),
	CONSTRAINT device_type_to_sensor_type_fk_device_type FOREIGN KEY (device_type_id)
		REFERENCES device_type(id) ON DELETE CASCADE,
	CONSTRAINT device_type_to_sensor_type_fk_sensor_type FOREIGN KEY (sensor_type_id)
		REFERENCES sensor_type(id) ON DELETE CASCADE
);

CREATE SEQUENCE sensor_data_seq START 1000;
CREATE TABLE sensor_data (
    id INTEGER NOT NULL DEFAULT NEXTVAL('sensor_data_seq'),
    sensor_id INTEGER NOT NULL,
    value DOUBLE PRECISION DEFAULT NULL,
    raw_data DOUBLE PRECISION DEFAULT NULL,
    datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    error_code INTEGER DEFAULT NULL,
    CONSTRAINT sensor_data_fk_sensor FOREIGN KEY (sensor_id)
        REFERENCES sensor(id) ON DELETE CASCADE
);

CREATE SEQUENCE sensor_data_latest_seq START 1000;
CREATE TABLE sensor_data_latest (
    id INTEGER NOT NULL DEFAULT NEXTVAL('sensor_data_latest_seq'),
    sensor_id INTEGER NOT NULL,
    value DOUBLE PRECISION DEFAULT NULL,
    raw_data DOUBLE PRECISION DEFAULT NULL,
    datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    error_code INTEGER DEFAULT NULL,
    CONSTRAINT sensor_data_latest_fk_sensor FOREIGN KEY (sensor_id)
        REFERENCES sensor(id) ON DELETE CASCADE
);

CREATE TABLE default_subsample (
	subsample INTEGER NOT NULL,
	UNIQUE(subsample)
);

CREATE SEQUENCE reading_subsample_seq START 100;
CREATE TABLE reading_subsample (
	id INTEGER NOT NULL DEFAULT NEXTVAL('reading_subsample_seq'),
	datetime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
	sample_period INTEGER NOT NULL,
	CONSTRAINT reading_subsample_pk PRIMARY KEY (id),
	UNIQUE (datetime, sample_period)
);

CREATE SEQUENCE reading_data_subsample_seq START 100;
CREATE TABLE reading_data_subsample (
	id INTEGER NOT NULL DEFAULT NEXTVAL('reading_data_subsample_seq'),
	reading_subsample_id INTEGER NOT NULL, 
	bin_id INTEGER NOT NULL,
	bin_section_id INTEGER NOT NULL,
	read_type_id INTEGER NOT NULL,
	avg_value DOUBLE PRECISION NOT NULL,
	min DOUBLE PRECISION NOT NULL,
	max DOUBLE PRECISION NOT NULL,
	current_count INTEGER NOT NULL,
	CONSTRAINT reading_data_subsample_pk PRIMARY KEY (id),
	CONSTRAINT reading_data_subsample_fk_bin FOREIGN KEY (bin_id)
		REFERENCES bin(id) ON DELETE CASCADE,
	CONSTRAINT reading_data_subsample_fk_bin_section FOREIGN KEY (bin_section_id)
		REFERENCES bin_section(id) ON DELETE CASCADE,
	CONSTRAINT reading_data_subsample_fk_reading_subsample FOREIGN KEY (reading_subsample_id)
		REFERENCES reading_subsample(id) ON DELETE CASCADE,
	CONSTRAINT reading_data_subsample_fk_read_type FOREIGN KEY (read_type_id)
		REFERENCES read_type(id) ON DELETE CASCADE
);

CREATE SEQUENCE reading_data_latest_seq START 100;
CREATE TABLE reading_data_latest (
    id INTEGER NOT NULL DEFAULT NEXTVAL('reading_data_latest_seq'),
    datetime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    bin_id INTEGER NOT NULL,
    bin_section_id INTEGER NOT NULL,
    read_type_id INTEGER NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    CONSTRAINT reading_data_latest_pk PRIMARY KEY (id),
    CONSTRAINT reading_data_latest_fk_bin FOREIGN KEY (bin_id)
        REFERENCES bin(id) ON DELETE CASCADE,
    CONSTRAINT reading_data_latest_fk_bin_section FOREIGN KEY (bin_section_id)
        REFERENCES bin_section(id) ON DELETE CASCADE,
    CONSTRAINT reading_data_latest_fk_read_type FOREIGN KEY (read_type_id)
        REFERENCES read_type(id) ON DELETE CASCADE
);

CREATE SEQUENCE alarm_type_seq START 100;
CREATE TABLE alarm_type (
	id INTEGER NOT NULL DEFAULT NEXTVAL('alarm_type_seq'),
	name VARCHAR(100) NOT NULL,
	threshold_p BOOLEAN NOT NULL DEFAULT FALSE,	
	CONSTRAINT alarm_type_pk PRIMARY KEY (id)
);

CREATE SEQUENCE alarm_seq START 100;
CREATE TABLE alarm (
	id INTEGER NOT NULL DEFAULT NEXTVAL('alarm_seq'),
	alarm_type_id INTEGER NOT NULL,
	account_id INTEGER NOT NULL,
	-- sensor_type_id INTEGER NOT NULL,
	greater_than_p BOOLEAN DEFAULT NULL,
	value DOUBLE PRECISION DEFAULT NULL,
	CONSTRAINT alarm_pk PRIMARY KEY (id),
	CONSTRAINT alarm_fk_alarm_type FOREIGN KEY (alarm_type_id)
		REFERENCES alarm_type(id) ON DELETE CASCADE,
	CONSTRAINT alarm_fk_account FOREIGN KEY (account_id)
		REFERENCES account(id) ON DELETE CASCADE
);

-- sms, email, voicemail, etc
CREATE SEQUENCE alarm_contact_type_seq START 100;
CREATE TABLE alarm_contact_type (
	id INTEGER NOT NULL DEFAULT NEXTVAL('alarm_contact_type_seq'),
	name VARCHAR(50) NOT NULL,
	CONSTRAINT alarm_contact_type_pk PRIMARY KEY (id)
);

-- Alarm to account&contact type association
CREATE SEQUENCE alarm_contact_seq START 100;
CREATE TABLE alarm_contact (
	id INTEGER NOT NULL DEFAULT NEXTVAL('alarm_contact_seq'),
	alarm_id INTEGER NOT NULL,
	alarm_contact_type_id INTEGER NOT NULL,
	CONSTRAINT alarm_contact_pk PRIMARY KEY (id),
	CONSTRAINT alarm_contact_fk_alarm FOREIGN KEY (alarm_id)
		REFERENCES alarm(id) ON DELETE CASCADE,
	CONSTRAINT alarm_contact_fk_alarm_contact_type FOREIGN KEY (alarm_contact_type_id)
		REFERENCES alarm_contact_type(id) ON DELETE CASCADE
);

CREATE SEQUENCE alarm_event_seq START 100;
CREATE TABLE alarm_event (
	id INTEGER NOT NULL DEFAULT NEXTVAL('alarm_event_seq'),
	alarm_id INTEGER NOT NULL,
	extra_info VARCHAR DEFAULT NULL,
	begin_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
	end_datetime TIMESTAMPTZ DEFAULT NULL,
	CONSTRAINT alarm_event_pk PRIMARY KEY (id),
	CONSTRAINT alarm_event_fk_alarm FOREIGN KEY (alarm_id)
		REFERENCES alarm(id) ON DELETE CASCADE
);

CREATE SEQUENCE alarm_history_seq START 100;
CREATE TABLE alarm_history (
    id INTEGER NOT NULL DEFAULT NEXTVAL('alarm_history_seq'),
    key VARCHAR NOT NULL,
    info JSON DEFAULT NULL,
    CONSTRAINT alarm_history_pk PRIMARY KEY (id)
);


CREATE SEQUENCE alarm_global_event_seq START 100;
CREATE TABLE alarm_global_event (
	id INTEGER NOT NULL DEFAULT NEXTVAL('alarm_global_event_seq'),
	alarm_type_id INTEGER NOT NULL,
	begin_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
	end_datetime TIMESTAMPTZ DEFAULT NULL,
	CONSTRAINT alarm_global_event_pk PRIMARY KEY (id),
	CONSTRAINT alarm_global_fk_alarm_type FOREIGN KEY (alarm_type_id)
		REFERENCES alarm_type(id) ON DELETE CASCADE
);

CREATE SEQUENCE subscription_seq START 100;
CREATE TABLE subscription (
	id INTEGER NOT NULL DEFAULT NEXTVAL('subscription_seq'),
	last_datetime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
	subscriber_id UUID NOT NULL,
	subscribed JSON NOT NULL DEFAULT '{"subscriptions": []}'::json,
	CONSTRAINT subscription_pk PRIMARY KEY (id),
	unique(subscriber_id)
);

CREATE SEQUENCE subscription_event_seq START 100;
CREATE TABLE subscription_event (
	id INTEGER NOT NULL DEFAULT NEXTVAL('subscription_event_seq'),
	subscriber_id UUID NOT NULL,
	event JSON NOT NULL,
	CONSTRAINT subscript_event_pk PRIMARY KEY(id),
	CONSTRAINT subscription_event_fk_subscription_subscriber_id FOREIGN KEY (subscriber_id) REFERENCES subscription(subscriber_id) ON DELETE CASCADE
);

CREATE SEQUENCE fill_config_seq START 100;
CREATE TABLE fill_config (
	id INTEGER NOT NULL DEFAULT NEXTVAL('fill_config_seq'),
	year INTEGER NOT NULL,
	config JSON NOT NULL,
	CONSTRAINT fill_config_pk PRIMARY KEY (id),
	UNIQUE(year)
);

CREATE SEQUENCE fill_type_seq START 100;
CREATE TABLE fill_type (
    id INTEGER DEFAULT NEXTVAL('fill_type_seq'),
    name VARCHAR(50) NOT NULL,
    short_name VARCHAR(50) NOT NULL,
    CONSTRAINT fill_type_pk PRIMARY KEY (id)
);

CREATE SEQUENCE fill_seq START 100;
CREATE TABLE fill (
	id INTEGER NOT NULL DEFAULT NEXTVAL('fill_seq'),
	fill_number INTEGER NOT NULL,
	fill_type_id INTEGER NOT NULL DEFAULT 1,
	filled_datetime TIMESTAMPTZ DEFAULT NULL,
	emptied_datetime TIMESTAMPTZ DEFAULT NULL,
	air_begin_datetime TIMESTAMPTZ DEFAULT NULL, --air
	air_end_datetime TIMESTAMPTZ DEFAULT NULL, --air
	roll_datetime TIMESTAMPTZ[] DEFAULT NULL, --air
	rotation_number INTEGER DEFAULT NULL,
	bin_id INTEGER DEFAULT NULL, 
	hybrid_code VARCHAR(1024) DEFAULT NULL,
	field_code VARCHAR(1024) DEFAULT NULL,	   --remove
	storage_bin_number INTEGER DEFAULT NULL,   --remove
	storage_bin_code VARCHAR(50) DEFAULT NULL, --remove
	pre_mc REAL[] DEFAULT NULL, --remove
	post_mc REAL[] DEFAULT NULL, --replace will fill_shelling_mc table
	dump_count INTEGER DEFAULT NULL, --number of times dump scale dumps
	dump_scale_factor INTEGER DEFAULT NULL, --Bu per dump
	bushels REAL DEFAULT NULL, --remove
	truck VARCHAR(1024) DEFAULT NULL, --remove
	depth DOUBLE PRECISION DEFAULT NULL,
	lot_number VARCHAR(100) DEFAULT NULL,
	extras JSON DEFAULT NULL,
	CONSTRAINT fill_pk PRIMARY KEY (id),
	CONSTRAINT fill_fk_fill_type FOREIGN KEY (fill_type_id)
		REFERENCES fill_type(id) ON DELETE CASCADE,
	CONSTRAINT fill_fk_bin FOREIGN KEY (bin_id)
		REFERENCES bin(id) ON DELETE CASCADE,
	CONSTRAINT filled_datetime_key_check CHECK (filled_datetime IS NOT NULL OR air_begin_datetime IS NOT NULL)
);

CREATE SEQUENCE fill_during_mc_seq START 100;
CREATE TABLE fill_during_mc (
    id INTEGER NOT NULL DEFAULT NEXTVAL('fill_during_mc_seq'),
    fill_id INTEGER NOT NULL,
    mc REAL NOT NULL,
    datetime TIMESTAMPTZ NOT NULL,
    CONSTRAINT fill_during_mc_pk PRIMARY KEY(id),
    CONSTRAINT fill_during_mc_fk_fill FOREIGN KEY (fill_id)
        REFERENCES fill(id) ON DELETE CASCADE
); 

CREATE SEQUENCE fill_shelling_mc_seq START 100;
CREATE TABLE fill_shelling_mc (
    id INTEGER NOT NULL DEFAULT NEXTVAL('fill_shelling_mc_seq'),
    fill_id INTEGER NOT NULL,
    mc REAL NOT NULL,
    CONSTRAINT fill_shelling_mc_pk PRIMARY KEY(id),
    CONSTRAINT fill_shelling_mc_fk_fill FOREIGN KEY (fill_id)
        REFERENCES fill(id) ON DELETE CASCADE
); 

CREATE SEQUENCE fill_sheller_window_seq START 100;
CREATE TABLE fill_sheller_window (
    id INTEGER NOT NULL DEFAULT NEXTVAL('fill_sheller_window_seq'),
    fill_id INTEGER NOT NULL,
    bin_id INTEGER NOT NULL,
    bin_section_id INTEGER NOT NULL,
    begin_datetime TIMESTAMPTZ DEFAULT NULL,
    end_datetime TIMESTAMPTZ DEFAULT NULL,
    CONSTRAINT fill_sheller_window_pk PRIMARY KEY (id),
    CONSTRAINT fill_sheller_window_fk_fill FOREIGN KEY (fill_id)
        REFERENCES fill(id) ON DELETE CASCADE,
    CONSTRAINT fill_sheller_window_fk_bin FOREIGN KEY (bin_id)
        REFERENCES bin(id) ON DELETE CASCADE,
    CONSTRAINT fill_sheller_window_fk_bin_section FOREIGN KEY (bin_section_id)
        REFERENCES bin_section(id) ON DELETE CASCADE
);

CREATE SEQUENCE air_deduct_seq START 100;
CREATE TABLE air_deduct (
    id INTEGER NOT NULL DEFAULT NEXTVAL('air_deduct_seq'),
	begin_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
	end_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT air_decuct_pk PRIMARY KEY (id)
);

CREATE SEQUENCE control_seq START 100;
CREATE TABLE control (
	id INTEGER NOT NULL DEFAULT NEXTVAL('control_seq'),
	sensor_id INTEGER NOT NULL,
	sensor_type_id INTEGER NOT NULL, -- Redundent, but for history maybe?
	value DOUBLE PRECISION NOT NULL,
	posted_datetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
	fetched_datetime TIMESTAMPTZ DEFAULT NULL, -- Time it was downloaded by MID.
	fetched_note VARCHAR DEFAULT NULL,
	CONSTRAINT control_pk PRIMARY KEY (id),
	CONSTRAINT control_fk_sensor FOREIGN KEY (sensor_id)
		REFERENCES sensor(id),
	CONSTRAINT control_fk_sensor_type_id FOREIGN KEY (sensor_type_id)
		REFERENCES sensor_type(id) ON DELETE CASCADE
);

CREATE SEQUENCE permission_seq START 100;
CREATE TABLE permission (
       id INTEGER NOT NULL DEFAULT NEXTVAL('permission_seq'),
       url VARCHAR NOT NULL,
       method_name VARCHAR NOT NULL,
       param VARCHAR DEFAULT NULL,
       privilege_id INTEGER NOT NULL,
       CONSTRAINT permission_pk PRIMARY KEY (id),
       CONSTRAINT permission_fk_privilege FOREIGN KEY (privilege_id)
    		  REFERENCES privilege(id) ON DELETE CASCADE
);

CREATE SEQUENCE config_log_seq START 100;
-- logs all changes to configurations and alarms
CREATE TABLE config_log (
       id INTEGER NOT NULL DEFAULT NEXTVAL('config_log_seq'),
       account_id INTEGER NOT NULL,
       datetime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
       description VARCHAR NOT NULL,
       CONSTRAINT config_log_pk PRIMARY KEY (id),
       CONSTRAINT config_log_fk_account FOREIGN KEY (account_id)
    		  REFERENCES account(id) ON DELETE CASCADE
);

-- Cache related
CREATE SEQUENCE conf_version START 100;
CREATE TABLE cache_versions (
	id INTEGER NOT NULL DEFAULT 0,
	conf_version BIGINT NOT NULL,
	conf_datetime TIMESTAMPTZ NOT NULL
);

CREATE SEQUENCE mc_maxtemp_lut_seq START 100;
CREATE TABLE mc_maxtemp_lut (
	id INTEGER NOT NULL DEFAULT NEXTVAL('mc_maxtemp_lut'),
	name VARCHAR NOT NULL,
	hours_per_mc REAL NOT NULL,
	CONSTRAINT mc_maxtemp_lut_pk PRIMARY KEY (id)
);

CREATE SEQUENCE mc_maxtemp_lut_value_seq START 100;
CREATE TABLE mc_maxtemp_lut_value (
	id INTEGER NOT NULL DEFAULT NEXTVAL('mc_maxtemp_lut_value_seq'),
	mc_maxtemp_lut_id INTEGER NOT NULL,
	mc double precision NOT NULL,
	maxtemp double precision NOT NULL,
	CONSTRAINT mc_maxtemp_lut_value_pk PRIMARY KEY (id),
	CONSTRAINT mc_maxtemp_lut_value_fk_mc_maxtemp_lut FOREIGN KEY (mc_maxtemp_lut_id)
		REFERENCES mc_maxtemp_lut(id) ON DELETE CASCADE
);

CREATE SEQUENCE last_mc_prediction_seq START 100;
CREATE TABLE last_mc_prediction (
	id INTEGER NOT NULL DEFAULT NEXTVAL('last_mc_prediction_seq'),
	bin_id INTEGER NOT NULL,
	value DOUBLE PRECISION NOT NULL,
	CONSTRAINT last_mc_prediction_pk PRIMARY KEY (id),
	CONSTRAINT last_mc_prediction_fk_bin FOREIGN KEY (bin_id)
	        REFERENCES bin(id) ON DELETE CASCADE
);

