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
