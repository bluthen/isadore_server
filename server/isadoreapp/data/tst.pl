%%%% TODO:
%%%% test db connection
%%%% dryer layout elements with same name?

%%%% LOAD MODULES
:- use_module(library(lists)).
:- use_module(library(odbc)).

%%%% DECLARE DYNAMIC PREDICATES
:- dynamic bin_id/2.
:- dynamic bin_section_id/2.
:- dynamic device/3.
:- dynamic sensor/4.
:- dynamic error_log/1.

%%%% ERROR LOGGING PREDICATE
error_log.

%%%% LOAD FILES
?- consult([db,dryer_layout]).

%%%% OPEN CONNECTION TO DB
%% TODO: move into each predicate that accesses the DB?
?- connect_to_db.

%%%% SET YEAR
year(2013).

%%%% SET SENSOR TYPE IDS
sensor_type_id(dp,5,computed).
sensor_type_id(jfactor,6,computed).
sensor_type_id(gpressure,7,computed).
sensor_type_id(temp,10,physical).
sensor_type_id(rh,11,physical).
sensor_type_id(wind_speed,12,physical).
sensor_type_id(wind_dir,13,pseudo).
sensor_type_id(kpa,14,physical).
sensor_type_id(pv,20,physical).
sensor_type_id(sp,21,physical).
sensor_type_id(temp_a,41,physical).
sensor_type_id(temp_b,42,physical).
sensor_type_id(rpm,50,physical).
sensor_type_id(amps,51,physical).
sensor_type_id(rpm_vfd_feedback,52,physical).
%%TODO: add these to schema_seed
sensor_type_id(avg_dp, 1005, pseudo).
sensor_type_id(avg_jfactor, 1006, pseudo).
sensor_type_id(avg_gpressure, 1007, pseudo).
sensor_type_id(avg_temp, 1010, pseudo).
sensor_type_id(avg_rh, 1011, pseudo).
sensor_type_id(avg_wind_speed, 1012 , pseudo).
sensor_type_id(avg_wind_dir, 1013 , pseudo).
sensor_type_id(avg_kpa, 1014 , pseudo).
sensor_type_id(avg_pv, 1020 , pseudo).
sensor_type_id(avg_sp, 1021 , pseudo).
sensor_type_id(avg_temp_a, 1041 , pseudo).
sensor_type_id(avg_temp_b, 1042 , pseudo).
sensor_type_id(avg_rpm, 1050 , pseudo).
sensor_type_id(avg_amps, 1051 , pseudo).
sensor_type_id(avg_rpm_vfd_feedback, 1052 , pseudo).

%%%% MAP PHYSICAL SENSORS TO AVGERAGING PSEUDO SENSORS
sensor_to_avg_pseudo_sensor(dp, avg_dp).
sensor_to_avg_pseudo_sensor(jfactor, avg_jfactor).
sensor_to_avg_pseudo_sensor(gpressure, avg_gpressure).
sensor_to_avg_pseudo_sensor(temp, avg_temp).
sensor_to_avg_pseudo_sensor(rh, avg_rh).
sensor_to_avg_pseudo_sensor(wind_speed, avg_wind_speed).
sensor_to_avg_pseudo_sensor(wind_dir, avg_wind_dir).
sensor_to_avg_pseudo_sensor(kpa, avg_kpa).
sensor_to_avg_pseudo_sensor(pv, avg_pv).
sensor_to_avg_pseudo_sensor(sp, avg_sp).
sensor_to_avg_pseudo_sensor(temp_a, avg_temp_a).
sensor_to_avg_pseudo_sensor(temp_b, avg_temp_b).
sensor_to_avg_pseudo_sensor(rpm, avg_rpm).
sensor_to_avg_pseudo_sensor(amps, avg_amps).
sensor_to_avg_pseudo_sensor(rpm_vfd_feedback, avg_rpm_vfd_feedback).

%%%% LOAD DRYER LAYOUT INTO PROLOG DB
?- add_bins_to_db.
?- add_bin_sections_to_db.
?- add_devices_to_db.
?- add_sensors_to_db.

%%%% PARSE MID DATA AND INSERT INTO PROLOG DB

%%%% CREATE NEW ROW IN READING TABLE

%%%% ENSURE ALL EXPECTED PHYSICAL SENSOR READINGS WERE RECEIVED

%%%% BUILD LIST OF PSEUDO SENSOR COMPUTATIONS, PERFORM COMPUTATIONS, AND INSERT INTO PROLOG DB

%%%% PUSH READINGS INTO DB

%%%% WRITE ERROR LOG TO LOG FILE