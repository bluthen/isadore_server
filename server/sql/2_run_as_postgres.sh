#!/bin/sh

dir=`dirname $0`
if [ -z "$1" ]
then
	echo $0 dbname
	exit 1
else
	createlang plpython2u $1
	psql -d $1 -f $dir/2_run_as_postgres_2.sql
	echo 'Make sure /var/lib/postgresql/python contains wetbulb.py'
	echo "Add PYTHONPATH = '/var/lib/postgresql/python' to /etc/postgresql/VERSION/main/environment"
fi
