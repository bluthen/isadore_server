%%%% BINS

add_bins_to_db :-
	findall([Ids,Names],
		odbc_query(tstConn,'SELECT id,name FROM bin',row(Ids,Names)),
		Bins)
	, add_bins_to_db(Bins).

add_bins_to_db([]).		%no more bins to process

add_bins_to_db([Bin|Bins]) :-
	add_bin_to_db(Bin)
	, add_bins_to_db(Bins).

add_bin_to_db([Bin_id,Bin_name]) :-
	asserta(bin_id(Bin_id , Bin_name) :- !).

%%%% BIN SECTIONS

add_bin_sections_to_db :-
	findall([Ids,Names],
		odbc_query(tstConn,'SELECT id,name FROM bin_section',row(Ids,Names)),
		Bin_secs)
	, add_bin_sections_to_db(Bin_secs).

add_bin_sections_to_db([]).	%no more bin sections to process

add_bin_sections_to_db([Bin_sec|Bin_secs]) :-
	add_bin_section_to_db(Bin_sec)
	, add_bin_sections_to_db(Bin_secs).

add_bin_section_to_db([Bin_sec_id,Bin_sec_name]) :-
	asserta(bin_section_id(Bin_sec_id , Bin_sec_name) :- !).

%%%% DEVICES

add_devices_to_db :-
	year(Year)
	, string_to_atom(Year_str)
	, string_concat('SELECT id,bin_id,bin_section_id FROM device WHERE year=',
			Year_str,
			Query_str)
	, findall([Id,Bin,Bin_section],
		  odbc_query(tstConn , Query_str , row(Id,Bin,Bin_section)),
		  Devcies)
	, add_devices_to_db(Devices).

add_devices_to_db([]).	%no more devices to process

add_devices_to_db([Device|Devices]) :-
	add_device_to_db(Device)
	, add_devices_to_db(Devices).

add_device_to_db([Device_id,Bin_id,Bin_sec_id]) :-
	bin_id(Bin_id , Bin_name)
	, bin_section_id(Bin_sec_id , Bin_sec_name)
	, asserta(device(Device_id, Bin_name, Bin_sec_name) :- !).

%%%% SENSORS
add_sensors_to_db :-
	findall([Id,Device_id,Sensor_type_id],
		odbc_query(tstConn,'SELECT id,device_id,sensor_type_id FROM device WHERE enabled_p = TRUE',row(Id,Device_id,Sensor_type_id)),
		Sensors)
	, add_devices_to_db(Sensors).

add_sensors_to_db([]).	%no more sensors to process

add_sensors_to_db([Sensor|Sensors]) :-
	add_sensor_to_db(Sensor)
	, add_sensors_to_db(Sensors).

add_sensor_to_db([Sensor_id,Device_id,Sensor_type_id]) :-
	device(Device_id, Bin_name, Bin_sec_name)
	, sensor_type_id(Sensor_type_id, Sensor_type_name)
	, asserta(sensor(Sensor_id, Bin_name, Bin_sec_name, Sensor_type_name) :- !).
