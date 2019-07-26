#!/bin/sh

PATH="/usr/local/bin:/usr/bin:/bin"
export PATH

TSMP=`/bin/date '+%Y-%m-%d'`

DBS=""

for db in $DBS
do
   `/usr/bin/pg_dump -Fc -b $db > /var/lib/postgresql/backups/$db-$TSMP.dmp`
#   `/usr/bin/psql -q -d $db -c "CLUSTER;"`
done

/usr/bin/vacuumdb -a -z
