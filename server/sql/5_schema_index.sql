CREATE INDEX account_idx_email_password ON account(email, password);
CREATE INDEX account_idx_enabled ON account(enabled_p);
CREATE INDEX account_session_idx_hd on account_session(hash, datetime);
-- Unique emails for enabled accounts.
CREATE UNIQUE INDEX account_uidx_email_enabled ON account(email) WHERE enabled_p;

CREATE INDEX device_type_to_sensor_type_idx_device_id ON device_type_to_sensor_type(device_type_id);

CREATE INDEX device_idx_bin_id ON device(bin_id);
CREATE INDEX device_idx_bin_section_id ON device(bin_section_id);

CREATE INDEX sensor_idx_device_id ON sensor(device_id);

CREATE INDEX sensor_mirror_idx_sensor_id ON sensor_mirror(sensor_id);
CREATE INDEX sensor_mirror_idx_sbbs ON sensor_mirror(sensor_id, bin_id, bin_section_id);

CREATE INDEX reading_subsample_idx_datetime ON reading_subsample (datetime);
CREATE INDEX reading_subsample_idx_date_sample ON reading_subsample (datetime, sample_period);
CREATE INDEX reading_data_subsample_idx_reading_subsample_id ON reading_data_subsample(reading_subsample_id);
CREATE INDEX reading_data_subsample_idx_read_type_id ON reading_data_subsample(read_type_id);
CREATE INDEX reading_data_subsample_idx_rsid_binid_bsid_rtid ON reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id);
CREATE INDEX reading_data_latest_idx_bbsrt ON reading_data_latest(bin_id, bin_section_id, read_type_id);

CREATE INDEX subscription_idx_subscriber_id ON subscription(subscriber_id);
CREATE INDEX subscription_event_idx_subscriber_id ON subscription_event(subscriber_id);

CREATE INDEX fill_idx_air_begin_datetime ON fill(air_begin_datetime);
CREATE INDEX fill_idx_air_end_datetime ON fill(air_end_datetime);
CREATE INDEX fill_idx_filled_datetime ON fill(filled_datetime);
CREATE INDEX fill_idx_emptied_datetime ON fill(emptied_datetime);
CREATE INDEX fill_idx_fill_number ON fill(fill_number);
CREATE INDEX fill_idx_bin_id ON fill(bin_id);
CREATE INDEX fill_idx_field_code ON fill(field_code);
CREATE INDEX fill_idx_hybrid_code ON fill(hybrid_code);
CREATE INDEX fill_idx_storage_bin_number ON fill(storage_bin_number);
CREATE INDEX fill_idx_storage_bin_code ON fill(storage_bin_code);
CREATE INDEX fill_during_mc_idx_fill_id ON fill_during_mc(fill_id);
CREATE INDEX fill_during_mc_idx_datetime ON fill_during_mc(datetime);
CREATE INDEX fill_sheller_window_idx_fill ON fill_sheller_window(fill_id);

CREATE INDEX alarm_idx_account_id ON alarm(account_id);
CREATE INDEX contact_idx_alarm_id ON alarm_contact(alarm_id);
CREATE INDEX contact_idx_type ON alarm_contact(alarm_contact_type_id);
CREATE INDEX control_idx_sensor_id ON control(sensor_id);
CREATE INDEX control_idx_posted_datetime on control(posted_datetime);

CREATE INDEX air_deduct_idx_begin_datetime on air_deduct(begin_datetime);
CREATE INDEX air_deduct_idx_end_datetime on air_deduct(end_datetime);


CREATE INDEX mc_maxtemp_lut_value_idx_lutid_mc ON mc_maxtemp_lut_value (mc_maxtemp_lut_id, mc);

CREATE INDEX sensor_data_idx_sensor ON sensor_data (sensor_id);
CREATE INDEX sensor_data_idx_datetime ON sensor_data (datetime);

CREATE INDEX sensor_data_latest_idx_sensor ON sensor_data_latest(sensor_id);
CREATE INDEX sensor_data_latest_idx_datetime ON sensor_data_latest(datetime);


CREATE INDEX alarm_history_key_idx ON alarm_history(key);

CREATE INDEX last_mc_prediction_idx_bin_id ON last_mc_prediction(bin_id);
