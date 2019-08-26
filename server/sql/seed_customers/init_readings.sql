insert into reading_subsample (datetime, sample_period) select compute_sample_date(now() - interval '5 minutes', 5), 5;
insert into reading_subsample (datetime, sample_period) select compute_sample_date(now(), 5), 5;

insert into reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id, avg_value, min, max, current_count) values (100, 9, 9, 10, 70.0, 70.0, 70.0, 1);
insert into reading_data_subsample (reading_subsample_id, bin_id, bin_section_id, read_type_id, avg_value, min, max, current_count) values (101, 9, 9, 10, 70.0, 70.0, 70.0, 1);

insert into reading_data_latest (bin_id, bin_section_id, read_type_id, value) values (9, 9, 10, 70.0);
