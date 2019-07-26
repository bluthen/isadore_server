#!/usr/local/bin/python2.7

import sys, os, time, atexit
from signal import SIGTERM 
import util
import datetime
import logging
import traceback
from localtz import LocalTimezone
#import alerts
from alarms import EMC


#Daemon class is from http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#by Sander Marechal
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
        #os.chdir("/") 
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


ALARM_TYPE_MID_DOWN = 10
ALARM_TYPE_SENSOR_TEMP = 14
ALARM_TYPE_MC_TEMP = 15
SENSOR_TYPE_TEMP = 10
ALARM_CONTACT_TYPE_EMAIL = 100
ALARM_CONTACT_TYPE_SMS = 101


class Alarm:
    def __init__(self, alarm_type_id):
        self.alarm_type_id = alarm_type_id
        self.alarmed = False

    def process(self):
        self.now = util.getDateFromParam("now")


class GlobalAlarm(Alarm):
    def __init__(self, alarm_type_id, conn):
        Alarm.__init__(alarm_type_id)
        self.msg = "Alarm message not set, contact admin."
        self.shortMsg = "Alarm message not set, contact admin."
        self.subject = "Isadore Alarm"
        self.conn = conn

    def openNewGlobalEvent(self):
        cursor = self.conn.cursor()
        util.insertRow("alarm_global_event", {"alarm_type_id": self.alarm_type_id, "begin_datetime": self.now}, cursor)
        self.conn.commit()
        cursor.close()
        
    def closeGlobalEvent(self, globalEventId):
        util.updateRowById("alarm_global_event", globalEventId, {"end_datetime": self.now})
        self.conn.commit();

    def preexistingGlobalAlert(self):
        """%returns False if no current event of this type, else returns id of event."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM alarm_global_event WHERE alarm_type_id=%s AND (begin_datetime < %s AND end_datetime IS NULL)", (self.alarm_type_id, self.now));
        row = cursor.fetchone()
        if(not row):
            cursor.close()
            return False
        cursor.close()
        return row[0]
    
    def sendAlarmNotices(self):
        sql = "SELECT DISTINCT account.email FROM account, alarm WHERE account.id=alarm.account_id AND alarm.alarm_type_id = %s AND alarm.id IN (SELECT alarm_id from alarm_contact WHERE alarm_contact_type_id = %s)"
        cursor = self.conn.cursor()
        cursor.execute(sql, (self.ALARM_TYPE_MID_DOWN, self.ALARM_CONTACT_TYPE_EMAIL))
        emails = []
        for row in cursor:
            emails.append(row[0])
        sql = "SELECT DISTINCT account.phone FROM account, alarm WHERE account.id=alarm.account_id AND alarm.alarm_type_id = %s AND alarm.id IN (SELECT alarm_id from alarm_contact WHERE alarm_contact_type_id = %s)"
        cursor.execute(sql, (self.ALARM_TYPE_MID_DOWN, self.ALARM_CONTACT_TYPE_SMS))
        sms = []
        for row in cursor:
            sms.append(row[0])
        if(emails):
            for email in emails:
                logging.debug("sendEmail to " + email + ": " + (self.msg % util.datetimeToReadable(self.now)))
                util.sendEmail(email, "info@exotericanalytics.com", self.subject, self.msg)
        if(sms):
            #alerts.send_SMS(sms, msg)
            logging.debug("sendSMS to " + str(sms) + ": " + self.shortMsg)
        cursor.close()


class MIDMIAAlarm(GlobalAlarm):
    """To use:
alarm = MIDMIAAlarm(conn, general_config)
alarm.process()
"""
    def __init__(self, conn, general_config):
        GlobalAlarm.__init__(self, ALARM_TYPE_MID_DOWN, conn)
        self.general_config = general_config
        self.msg = self.general_config["customer_short_name"] + "'s MID has not communicated in a while, detected on %s"
        self.shortMsg = self.msg
        self.subject = "Isadore Alarm: MID Down"
        self.reading_id = 0
        
    def process(self):
        self.process()
        self.alarmed = self.alarmCondition()
        preexist = self.preexistingGlobalAlert()
        if(self.alarmed and not preexist):
            self.openNewGlobalEvent()
            self.sendAlarmNotices()
        elif(not self.alarmed and preexist):
            self.closeOldEvent(preexist)
            #self.sendResolvedNotices()

    def alarmCondition(self):
        #Check for MID down
        now = util.getDateFromParam("now")
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, datetime from reading ORDER BY datetime desc limit 1")
        row = cursor.fetchone()
        self.reading_id = row[0]
        lastReadDatetime = row[1]
        readDelta = now - lastReadDatetime
        if(readDelta > datetime.timedelta(seconds=2.5 * self.general_config["interval"])):
            cursor.close()
            return True
        cursor.close()


class UserAlarm(Alarm):
    def __init__(self, alarm_type_id, conn):
        Alarm.__init__(alarm_type_id)
        self.msg = "Alarm message not set, contact admin: %s"
        self.shortMsg = self.msg
        self.subject = "Isadore Alarm"
        self.conn = conn

    def closeOldEvent(self, event_id):
        cursor = self.conn.cursor()
        sql = "UPDATE alarm_event SET end_datetime = %s WHERE id = %s"
        cursor.execute(sql, (self.now, event_id))
        self.conn.commit()
        cursor.close()
        
    def openNewEvent(self, alarm_id):
        cur = self.conn.cursor()
        sql = "INSERT INTO alarm_event (alarm_id, extra_info, begin_datetime) VALUES (%s, %s, %s)"
        cur.execute(sql, (alarm_id, self.alarmed, self.now))
        self.conn.commit()
        cur.close()

    def preexistingAlert(self, id):
        cursor = self.conn.cursor()
        sql = "SELECT id, extra_info FROM alarm_event WHERE alarm_id=%s AND end_datetime IS NULL"
        cursor.execute(sql, (id,))
        erow = cursor.fetchone()
        if(erow):
            return (erow[0], erow[1])
        return (None, None)

    def sendAlarmNotice(self, alarm_id, alarmMSG):
        cur = self.conn.cursor()
        sql = "SELECT account.email FROM account, alarm WHERE account.id=alarm.account_id and alarm.id = %s AND alarm.id IN (SELECT alarm_id FROM alarm_contact WHERE alarm_contact_type_id = %s)"
        cur.execute(sql, (alarm_id, self.ALARM_CONTACT_TYPE_EMAIL))
        row = cur.fetchone()
        email = None
        if(row):
            email = row[0]
            
        sql = "SELECT account.phone FROM account, alarm WHERE account.id=alarm.account_id and alarm.id = %s AND alarm.id IN (SELECT alarm_id FROM alarm_contact WHERE alarm_contact_type_id = %s)"
        cur.execute(sql, (alarm_id, self.ALARM_CONTACT_TYPE_SMS))
        row = cur.fetchone()
        sms = None
        if(row):
            sms = row[0]

        if(email):
            amsg = self.msg % (alarmMSG, util.datetimeToReadable(self.now))
            logging.debug("sendEmail to " + email + ": " + amsg)
            util.sendEmail(email, "info@exotericanalytics.com", self.subject, amsg)
        if(sms):
            amsg = self.shortMsg % (alarmMSG, util.datetimeToReadable(self.now))
            #Send SMS
            logging.debug("sendSMS to " + sms + ": " + amsg)
            pass


class BinTemperatureAlarm(UserAlarm):
    def __init__(self, conn, general_config, reading_id):
        UserAlarm.__init__(self, ALARM_TYPE_SENSOR_TEMP, conn)
        self.reading_id = reading_id
        short_name = self.general_config["customer_short_name"]
        self.subject = "Isadore Alarm: Temperature Condition"
        self.msg = short_name + ": Bin with temperature alarm triggered (%s) on %s"
        self.shortMsg = self.msg

    def process(self):
        self.process()
        
        self.alarmed = self.alarmCondition()
        for a in self.alarmed:
            new_bins, alarm_id = a
            event_id, pre_bins = self.preexistingAlert(alarm_id)
            if(pre_bins):
                pre_bins = [int(x) for x in pre_bins.split(",")]
            if(new_bins and not event_id):
                self.openNewEvent(alarm_id)
                self.sendAlarmNotices(alarm_id, ", ".join(new_bins))
            elif(new_bins and event_id and pre_bins != new_bins):
                self.closeOldEvent(event_id)
                self.openNewEvent(alarm_id)
                #Perhaps only if new bins added, not removed.
                new_bins_set = set(new_bins)
                pre_bins_set = set(pre_bins)
                if(pre_bins_set.difference(new_bins_set)):
                    self.sendAlarmNotices(alarm_id, ", ".join(new_bins))
            elif(not new_bins and event_id):
                self.closeOldEvent(event_id)
                #self.sendResolvedNotices()

    def alarmCondition(self):
        cursor = self.conn.cursor()
        conditions = []
        alarms = util.getRowsFromTable("alarm", extraWhere=" alarm_type_id = %s ", extraArgs=(self.alarm_type_id,), conn=self.conn)
        for alarm in alarms:
            if(alarm["greater_than_p"]):
                gtlt = ">"
            else:
                gtlt = "<"
            #sql = "SELECT count(id) FROM reading_data rd WHERE rd.reading_id = %s AND rd.sensor_type_id = %s and bin_id IN (SELECT id FROM bin WHERE name like 'Bin %%') AND value " + gtlt + " %s"
            sql = "SELECT DISTINCT ON (bin.name) bin.name FROM reading_data rd, bin WHERE rd.reading_id = %s AND rd.sensor_type_id = %s and rd.bin_id=bin.id AND bin.name like 'Bin %%' AND rd.value " + gtlt + " %s ORDER BY bin.name"
            cursor.execute(sql, (self.reading_id, self.SENSOR_TYPE_TEMP, alarm["value"]))
            bins = cursor.fetchall()
            if(bins):
                binNums = []
                for bin in bins:
                    binNums.append(int(bin[0].split(" ")[1]))
                conditions.append([binNums, alarm["id"]])
            conditions.append([None, alarm["id"]])
        return conditions

class EMCTemperatureAlarm(UserAlarm):
    def __init__(self, conn, general_config, reading_id, reading_datetime):
        UserAlarm.__init__(self, ALARM_TYPE_MC_TEMP, conn)
        self.reading_id = reading_id
        self.reading_datetime = reading_datetime
        short_name = self.general_config["customer_short_name"]
        self.subject = "Isadore Alarm: Temperature MC Condition"
        self.msg = short_name + ": Bin with mc temperature alarm triggered (%s) on %s"
        self.shortMsg = self.msg

    def process(self):
        self.process(self)
        
        self.alarmed = self.alarmCondition()
        for a in self.alarmed:
            new_bins, alarm_id = a
            event_id, pre_bins = self.preexistingAlert(alarm_id)
            if(pre_bins):
                pre_bins = [int(x) for x in pre_bins.split(",")]
            if(new_bins and not event_id):
                self.openNewEvent(alarm_id)
                self.sendAlarmNotices(alarm_id, ", ".join(new_bins))
            elif(new_bins and event_id and pre_bins != new_bins):
                self.closeOldEvent(event_id)
                self.openNewEvent(alarm_id)
                #Perhaps only if new bins added, not removed.
                new_bins_set = set(new_bins)
                pre_bins_set = set(pre_bins)
                if(pre_bins_set.difference(new_bins_set)):
                    self.sendAlarmNotices(alarm_id, ", ".join(new_bins))
            elif(not new_bins and event_id):
                self.closeOldEvent(event_id)
                #self.sendResolvedNotices()

    def alarmCondition(self):
        cursor = self.conn.cursor()
        conditions = []
        alarms = util.getRowsFromTable("alarm", extraWhere=" alarm_type_id = %s ", extraArgs=(self.alarm_type_id,), conn=self.conn)
        for alarm in alarms:
            #sql = "SELECT count(id) FROM reading_data rd WHERE rd.reading_id = %s AND rd.sensor_type_id = %s and bin_id IN (SELECT id FROM bin WHERE name like 'Bin %%') AND value " + gtlt + " %s"
            sql = "SELECT bin.name, fill.id, fill.air_begin_datetime, array_avg(fill.pre_mc), rd.value \
FROM fill, bin, reading_data rd \
WHERE rd.reading_id = %s AND \
rd.sensor_type_id = %s AND \
rd.bin_id=bin.id AND \
bin.name like 'Bin %%' AND \
fill.bin_id=rd.bin_id \
AND ((fill.air_begin_time >= %s AND fill.air_end_time IS NULL) OR (fill.air_begin_time >= %s AND fill.air_end_time <= %s)) \
ORDER BY bin.name";
            cursor.execute(sql, (self.reading_id, self.SENSOR_TYPE_TEMP, self.reading_datetime, self.reading_datetime))
            bins = cursor.fetchall()
            if(bins):
                binNums = []
                for bin in bins:
                    cursor.execute("SELECT begin_datetime, end_datetime FROM air_deduct WHERE (begin_datetime >= %s AND end_datetime IS NULL) OR (begin_datetime >= %s AND end_datetime <= %s)", (bin[2], bin[2], bin[2]))
                    deductions = cursor.fetchall()
                    mcTemp = EMC.computeMaxTemps(bin[3], bin[2], deductions, self.reading_datetime, self.general_config["emchrs_per_point"])
                    if(bin[4] > mcTemp + alarm["value"]):
                        binNums.append(int(bin[0].split(" ")[1]))
                conditions.append([binNums, alarm["id"]])
            conditions.append([None, alarm["id"]])
        return conditions



class AlarmWatcher(Daemon):
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        Daemon.__init__(self, pidfile, stdin, stdout, stderr)

    def run(self):
        logging.basicConfig(filename='./alarm_watcher.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
        #Set last_read = last reading time
        #set last_contact_time = long time ago
        while True:
            try:
                conn = util.getConn()
                general_config = util.getRowFromTableById("general_config", 1, conn=conn)
                midMIAAlarm = MIDMIAAlarm(conn, general_config)
                midMIAAlarm.process()
                if (not midMIAAlarm.alarmed):
                    binTempAlarms = BinTemperatureAlarm(conn, general_config, midMIAAlarm.reading_id)
                    binTempAlarms.process()
                    if(self.general_config["emchrs_per_point"]):
                        pass
                    
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
