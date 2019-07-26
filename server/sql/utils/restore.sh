#!/bin/sh
user=$1
dmpfile=$2

if [ -z "$1" -o -z "$2" ]
then
	echo "$0 [user-db] [dmpfile]"
	exit 1
fi

psql -c "alter user $user with superuser;"
pg_restore -d $user -U $user -O $dmpfile
psql -c "alter user $user with nosuperuser;"
