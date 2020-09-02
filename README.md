# isadore_server
The server code for the Isadore Dryer Management System. Originally released with an open source license in 2019 by Dan Elliott and Russell Valentine. It is designed to monitor environmental conditions in corn seed dryers.

## Install

1. Setup a postgresql database. Setup schema using the files in ./server/sql
2. git clone git@github.com:bluthen/isadore_server.git
7. Until it is templated search for example.com in the code and switch it to what you want. `grep -r example.com *`
3. cd clients/www
4. ant deploy -Dsite=sitename
5. cd ../../server
6. ant deploy -Dsite=sitename
7. cp settings.cfg.example /www/sitename/webapps/isadore/settings.cfg
8. Edit settings.cfg with your auth info
9. Setup WSGI server to use app.wsgi


## Example to install on Ubuntu LTS

**Note** In these examples `$DBNAME` should be the name you choose. Maybe your dryer name, do not keep it as `$DBNAME`.


### Update and Install prereqs

```  
apt update && \
apt upgrade && \
apt install -y postgresql postgresql-contrib postgresql-plpython-10 apache2 libapache2-mod-wsgi python-matplotlib nginx python-pip postgresql-server-dev-10 ntpdate ntp sendmail git npm ant && \
pip2 install bottle==0.12.17 beaker==1.5.4 pytz http-parser==0.6.2 restkit==4.2.1 iso8601==0.1.10 psycopg2 twilio==6.29.4 croniter==0.3.12 && \
pip2 install git+https://github.com/bluthen/hygrometry.git
npm install -g coffeescript

```

### Setup database

Check out code
```
git clone git@github.com:bluthen/isadore_server.git && \
cd isadore_server && \
export GIT_LOC=`pwd`
```

```
su - postgres
createuser $DBNAME
createdb $DBNAME -O $DBNAME
psql -c "ALTER USER $DBNAME password 'somerandompassword';
```

Now we need to create the tables and everything

```
cd $GIT_LOC/server/sql
psql -U $DBNAME -f 0_json_methods_extra.sql
psql -U postgres -d $DBNAME -f 2_run_as_postgres_2.sql
psql -U $DBNAME -f 3_funcs.sql
psql -U $DBNAME -f 5_schema_index.sql
psql -U $DBNAME -f 6_schema_seed.sql
psql -U $DBNAME -f seed_customers/seed_generic.sql
psql -U $DBNAME -f seed_customers/init_readings.sql
```

### Deploy Server code
```
mkdir /www/$DBNAME
cd $GIT_LOC/server
ant deploy -Dsite=$DBNAME
cd ../clients/www
ant deploy -Dsite=$DBNAME
mkdir -p /www/$DBNAME/webapps/ROOT
mkdir -p /www/$DBNAME/logs
touch /www/$DBNAME/logs/time.log
touch /www/$DBNAME/logs/bottle.log
chown www-data /www/$DBNAME/logs/time.log
chown www-data /www/$DBNAME/logs/bottle.log
chown -R russ:www-data /www/$DBNAME/webapps/isadore
cp $GIT_LOC/server/settings.cfg.example /www/$DBNAME/webapps/isadore/settings.cfg
```

Make a file `/www/$DBNAME/webapps/ROOT/index.html` and have below be the contents:

```
<html>
<head>
<meta HTTP-EQUIV="REFRESH" content="0; url=./isadore/s/login.html">
</head>
<body>
</body>
</html>
```

### Passwords Configuration

Set DB midpass:
```
psql -U $DBNAME -c "update table general_config set mid_pass='someotherpassword';"
```
Modify `/www/$DBNAME/webapps/isadore/settings.cfg`
Make sure `midpass`, `dbuser`, `dbpass`, `dbhost` are correct.

If using twilio for alerts, make sure `account` and `token` are correct for your twilio account.


### Setup Apache as WSGI server

```
sh /usr/share/doc/apache2/examples/setup-instance $DBNAME
ln -s /etc/init.d/apache2 /etc/init.d/apache2-$DBNAME
systemctrl enable apache2-$DBNAME
mkdir /var/run/apache2-$DBNAME
```

Edit the file `/etc/apache2-$DBNAME/sites-enables/000-default.conf` It should contain:

```
<VirtualHost *:80>                                                                                          
        ServerAdmin webmaster@localhost
        DocumentRoot /www/$DBNAME/webapps/ROOT                                                
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined
        <Directory /www/$DBNAME/webapps/ROOT>
                Require all granted
        </Directory>
        WSGIDaemonProcess $DBNAME processes=2 threads=15 display-name=%{GROUP}
        WSGIProcessGroup $DBNAME    
        WSGIScriptAlias /isadore /www/$DBNAME/webapps/isadore/app.wsgi
        <Directory /www/$DBNAME/webapps/isadore>
                Require all granted
        </Directory>
</VirtualHost>
```

Startup apache:

```
/etc/init.d/apache2-$DBNAME start
```

You should then be able to log in with the default username and password, be sure to change it:
```
admin@example.com
_example_password
```


### Settings -> General Config

After logging in pasting the contents of `$GIT_LOC/server/src/general_config.example.json` into the Settings -> General Config, it may help get your Current Data views started. For further customization look into at the top comments in the file `$GIT_LOC/clients/www/src/coffee/handler/isadore_current_data_handler.coffee`


### Alarm Service

There is a alarm service to watch if it should sent email or text alerts. A way to start this one boot is using systemd.

Make a file in `/etc/systemd/system/$DBNAME_alarmwatcher.service`

with contents

```
[Unit]
Description=AlarmWatcher Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/www/$DBNAME/webapps/isadore
ExecStart=/usr/bin/python2 alarm_watcher.py start
ExecStop=/usr/bin/python2 alarm_watcher.py stop 
Type=forking
PIDFile=/www/$DBNAME/webapps/isadore/alarm_watcher.pid

[Install]
WantedBy=multi-user.target
 
```

Then Run:
```
systemctl enable $DBNAME_alarmwatcher
systemctl start $DBNAME_alarmwatcher
```


# Maintenance

1. Every year you need to clone the devices so they can be used for the coming year. This is in Settings -> Clone Devices.

Put in the previous year and the current year and click the clone devices but. This only needs to be done once per year. 

