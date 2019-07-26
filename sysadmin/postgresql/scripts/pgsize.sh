#!/bin/sh

psql -c 'select datname, pg_size_pretty(pg_database_size(datname)) from pg_database;';
psql -c 'select pg_size_pretty(sum(pg_database_size(datname))::bigint) as Total from pg_database;';
