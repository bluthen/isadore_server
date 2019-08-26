#!/usr/local/bin/python2.7
#   Copyright 2010-2019 Dan Elliott, Russell Valentine
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import sys
import os
import time
import atexit
from signal import SIGTERM
import util
import datetime
import pytz
import logging
import json
import traceback
from localtz import LocalTimezone
import psycopg2
import psycopg2.extras
psycopg2.extras.register_default_json(loads=lambda x: x)

# import alerts


# Daemon class is from http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
# by Sander Marechal
class Daemon:
    """
    A generic daemon class.
    
    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        # os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

            # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process    
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """


class AlarmWatcher(Daemon):
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        Daemon.__init__(self, pidfile, stdin, stdout, stderr)
        self.ALARM_TYPE_MID_DOWN = 10
        self.ALARM_TYPE_SENSOR_TEMP = 14
        self.READ_TYPE_TEMP = 10
        self.ALARM_CONTACT_TYPE_EMAIL = 100
        self.ALARM_CONTACT_TYPE_SMS = 101
        self.tz = pytz.timezone('America/Chicago')

    def hasGlobalAlert(self, alarm_type_id, cur):
        """%returns False if no current even of this type, else returns id of event."""
        now = util.getDateFromParam("now")
        cur.execute("""SELECT id FROM alarm_global_event WHERE alarm_type_id=%s AND
            (begin_datetime < %s AND end_datetime IS NULL)""", (alarm_type_id, now))
        row = cur.fetchone()
        if not row:
            return False
        return row[0]

    def sendAlarmNotice(self, short_name, alarm_id, alarm_type_id, event_time, conn, msg):
        cur = conn.cursor()
        sql = """SELECT account.email FROM account, alarm WHERE account.id=alarm.account_id AND account.enabled_p and
            alarm.id = %s AND alarm.id IN (SELECT alarm_id FROM alarm_contact WHERE alarm_contact_type_id = %s)"""
        cur.execute(sql, (alarm_id, self.ALARM_CONTACT_TYPE_EMAIL))
        row = cur.fetchone()
        email = None
        if row:
            email = row[0]

        sql = """SELECT account.phone FROM account, alarm WHERE account.id=alarm.account_id AND account.enabled_p and
            alarm.id = %s AND alarm.id IN (SELECT alarm_id FROM alarm_contact WHERE alarm_contact_type_id = %s)"""
        cur.execute(sql, (alarm_id, self.ALARM_CONTACT_TYPE_SMS))
        row = cur.fetchone()
        sms = None
        if row:
            sms = row[0]

        if alarm_type_id == self.ALARM_TYPE_SENSOR_TEMP:
            amsg = short_name + ": At least one bin triggered alarm " + msg + " starting on " + \
                util.datetimeToReadableWithTZ(event_time, self.tz)
            if email:
                try:
                    logging.debug("sendEmail to " + email + ": " + amsg)
                    util.sendEmail(email, "info@exotericanalytics.com", "Isadore Alarm: Temperature Condition", amsg)
                except:
                    logging.error(traceback.format_exc())
            if sms:
                try:
                    # Send SMS
                    logging.debug("sendSMS to " + sms + ": " + amsg)
                    util.sendTxt(sms, amsg)
                except:
                    logging.error(traceback.format_exc())

    def sendGlobalNotices(self, short_name, alarm_type_id, event_time, conn):
        cur = conn.cursor()
        sql = """SELECT DISTINCT account.email FROM account, alarm WHERE account.id=alarm.account_id AND
            account.enabled_p AND alarm.alarm_type_id = %s AND alarm.id IN (SELECT alarm_id from alarm_contact WHERE
            alarm_contact_type_id = %s)"""
        cur.execute(sql, (self.ALARM_TYPE_MID_DOWN, self.ALARM_CONTACT_TYPE_EMAIL))
        emails = []
        for row in cur:
            emails.append(row[0])
        sql = """SELECT DISTINCT account.phone FROM account, alarm WHERE account.id=alarm.account_id AND
            account.enabled_p AND alarm.alarm_type_id = %s AND alarm.id IN (SELECT alarm_id from alarm_contact WHERE
            alarm_contact_type_id = %s)"""
        cur.execute(sql, (self.ALARM_TYPE_MID_DOWN, self.ALARM_CONTACT_TYPE_SMS))
        sms = []
        for row in cur:
            sms.append(row[0])
        if alarm_type_id == self.ALARM_TYPE_MID_DOWN:
            msg = short_name + "'s MID has not communicated in a while, detected on " + \
                util.datetimeToReadableWithTZ(event_time, self.tz)
            if emails:
                for email in emails:
                    try:
                        logging.debug("sendEmail to " + email + ": " + msg)
                        util.sendEmail(email, "info@exotericanalytics.com", "Isadore Alarm: MID Down", msg)
                    except:
                        logging.error(traceback.format_exc())
            if sms:
                logging.debug("sendSMS to " + str(sms) + ": " + msg)
                for s in sms:
                    try:
                        # alerts.send_SMS(sms, msg)
                        logging.debug("sendSMS to " + str(s) + ": " + msg)
                        util.sendTxt(s, msg)
                    except:
                        logging.error(traceback.format_exc())

        cur.close()

    def run(self):
        logging.basicConfig(filename='./alarm_watcher.log', level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s')
        # Set last_read = last reading time
        # set last_contact_time = long time ago
        last_read = datetime.datetime(year=1970, month=1, day=1, tzinfo=LocalTimezone())
        contact_last_read = None
        while True:
            try:
                # Get current datetime
                now = util.getDateFromParam("now")
                # Get general config interval
                conn = util.getConn()
                general_config = util.getRowFromTableById("general_config", 1, conn=conn)
                gc_configs = {}
                if "configs" in general_config and general_config["configs"]:
                    gc_configs = json.loads(general_config["configs"])
                # Set working_last_time  to last reading
                cur = conn.cursor()

                # Check for MID down
                cur.execute("""SELECT id, datetime from reading_subsample WHERE sample_period = 5
                    ORDER BY datetime desc limit 2""")
                row = cur.fetchone()
                readDeltaAlt = now - row[1]
                row = cur.fetchone()
                working_last_read = row[1]
                working_last_read_id = row[0]

                readDelta = now - working_last_read
                midGlobalEvent = self.hasGlobalAlert(self.ALARM_TYPE_MID_DOWN, cur)
                logging.debug("readDelta: " + str(readDelta))
                if readDeltaAlt > datetime.timedelta(seconds=(20*60.0)):
                    if not midGlobalEvent:
                        util.insertRow("alarm_global_event",
                                       {"alarm_type_id": self.ALARM_TYPE_MID_DOWN, "begin_datetime": now}, cur)
                        conn.commit()
                        self.sendGlobalNotices(general_config["customer_short_name"], self.ALARM_TYPE_MID_DOWN, now,
                                               conn)
                elif midGlobalEvent:
                    # MID is back up.
                    util.updateRowById("alarm_global_event", midGlobalEvent, {"end_datetime": now})
                    conn.commit()
                    # TODO: Contact that it is back up?

                if working_last_read > last_read:
                    # If any new errors
                    # post alarms row
                    # if last contact time is greater than contact_time_interval then
                    # for everyone who needs to be contacted
                    # contact them about error
                    # set last contact time for type
                    tempRows = util.getRowsFromTable("alarm", extraWhere=" alarm_type_id = %s ",
                                                     extraArgs=(self.ALARM_TYPE_SENSOR_TEMP,), conn=conn)
                    for row in tempRows:
                        sql = "SELECT id FROM alarm_event WHERE alarm_id=%s AND end_datetime IS NULL"
                        cur.execute(sql, (row["id"],))
                        erow = cur.fetchone()
                        ae_id = None
                        if erow:
                            ae_id = erow[0]

                        if row["greater_than_p"]:
                            gtlt = ">"
                        else:
                            gtlt = "<"
                        aironsql = ""
                        if "alarms" in gc_configs and "aironly" in gc_configs["alarms"] and gc_configs["alarms"]["aironly"]:
                            aironsql = " AND bin_fill_airon(b.id) IS TRUE "

                        if "alarms" in gc_configs and "bottom_only" in gc_configs["alarms"] and gc_configs["alarms"]["bottom_only"]:
                            sql = """select rd.bin_id, rd.avg_value as hottest from
reading_data_subsample rd, bin b WHERE
  rd.reading_subsample_id = %s AND
  rd.read_type_id = 10 and
  rd.bin_id = b.id and
  b.name like 'Bin %%' and
  rd.bin_section_id = 14 """ + aironsql + """ AND
  rd.avg_value """+gtlt+""" %s"""
                            cur.execute(sql, (working_last_read_id, row["value"]))
                            rows = cur.fetchall()
                            countRow = [len(rows)]
                        else:
                            sql = """select rd.bin_id, greatest(rd.avg_value, rd2.avg_value) as hottest from
reading_data_subsample rd, reading_data_subsample rd2, bin b WHERE
  rd.reading_subsample_id = %s AND
  rd.read_type_id = 10 and
  rd.bin_id = b.id and
  b.name like 'Bin %%' and
  (rd.bin_section_id = 13) """ + aironsql + """ AND
  rd2.reading_subsample_id = %s and
  rd2.read_type_id = %s and
  rd2.bin_id = b.id and
  rd2.bin_section_id = 14 and greatest(rd.avg_value, rd2.avg_value) """+gtlt+""" %s"""
                            cur.execute(sql, (working_last_read_id, working_last_read_id, self.READ_TYPE_TEMP, row["value"]))
                            rows = cur.fetchall()
                            countRow = [len(rows)]
                        if countRow[0] > 0 and not ae_id:
                            sql = "INSERT INTO alarm_event (alarm_id, begin_datetime) VALUES (%s, %s)"
                            cur.execute(sql, (row["id"], now))
                            conn.commit()
                            self.sendAlarmNotice(general_config["customer_short_name"], row["id"],
                                                 self.ALARM_TYPE_SENSOR_TEMP, now, conn, gtlt + " %.2f" % row["value"])
                            # TODO: contact
                        elif countRow[0] == 0 and ae_id:
                            sql = "UPDATE alarm_event SET end_datetime = %s WHERE id = %s"
                            cur.execute(sql, (now, ae_id))
                            conn.commit()
                last_read = working_last_read
                cur.close()
                conn.close()
                time.sleep(180)
            except:
                logging.error(traceback.format_exc())
                time.sleep(180)


if __name__ == "__main__":
    daemon = AlarmWatcher('alarm_watcher.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)


# Local Variables:
# indent-tabs-mode: f
# python-indent: 4
# tab-width: 4
# End:
