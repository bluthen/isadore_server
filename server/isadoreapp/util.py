import psycopg2 as dbapi2
import psycopg2.extras as dbapi2extras
from flask import request, abort, Response, jsonify
import configparser
import hashlib
from datetime import datetime
from isadoreapp.localtz import LocalTimezone
import smtplib
import time
import random
from email.mime.text import MIMEText
import logging
import threading
import string
from twilio.rest import TwilioRestClient
import iso8601
import re
dbapi2.extras.register_uuid()


class Account:
    def __init__(self, account_id, email, name, phone, password, seed, privilege_id, recovery_hash, recovery_datetime,
                 session_hashes):
        self.id = account_id
        self.email = email
        self.name = name
        self.phone = phone
        self.password = password
        self.seed = seed
        self.privilege_id = privilege_id
        self.recovery_hash = recovery_hash
        self.recovery_datetime = recovery_datetime
        self.session_hashes = session_hashes

    def has_privilege(self, key):
        if key in Single().getPrivileges() and self.privilege_id >= Single().getPrivileges()[key]:
            return True
        else:
            return False

    def is_super_user(self):
        return self.has_privilege("Super User")

    def is_power_user(self):
        return self.has_privilege("Power User")

    def is_config_user(self):
        return self.has_privilege("Config User")

    def is_fill_user(self):
        return self.has_privilege("Fill User")


class Unit:
    def __init__(self, unit_id, address, port, location1_id, location2_id, temp_bias, hum_bias):
        self.unit_id = unit_id
        self.address = address
        self.port = port
        self.location1_id = location1_id
        self.location2_id = location2_id
        self.temp_bias = temp_bias
        self.hum_bias = hum_bias


def getDateFromParam(parameter):
    """
       Give you a datetime object from parameter, supports now keyword.
       :param parameter The parameter to turn into a datetime object.
       :param tz If true will give you a timezone object with system localtime as time zone.
    """
    # TODO: Handle timezones
    ltz = LocalTimezone()
    if not parameter:
        return None
    if parameter == "now":
        return datetime.now(ltz)
    try:
        d = iso8601.parse_date(parameter)
    except iso8601.iso8601.ParseError:
        return None
    return d


def datetimeToReadable(d, tz):
    """Returns datetime as string in format %H:%M %m/%d/%Y
    %d datetime object
    %returns string of object in readable format."""
    return d.astimezone(tz).strftime("%H:%M %m/%d/%Y")


def datetimeToReadableWithTZ(d, tz):
    """Returns datetime as string in format %H:%M %m/%d/%Y
    %d datetime object
    %returns string of object in readable format."""
    return d.astimezone(tz).strftime("%H:%M %m/%d/%Y %Z")


def timedeltaToHours(td):
    """Turns a timedelta into hours"""
    return float(td.days) * 24.0 + (float(td.seconds) / 3600.0)


def safeEval(evalString, x):
    # make a list of safe functions
    safe_list = ['math', 'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor',
                 'fmod', 'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh',
                 'sqrt', 'tan', 'tanh']
    # use the list to filter the local namespace
    safe_dict = dict([(k, locals().get(k, None)) for k in safe_list])
    # add any needed builtins back in.
    safe_dict['abs'] = abs
    safe_dict['x'] = x
    return eval(evalString, {"__builtins__": None}, safe_dict)


def getRowsFromTable(table, columns='*', extraWhere=None, extraArgs=(), checkEnabled=False, orderStatement="",
                     conn=None):
    """Gets arrays of dictionaries from table.
       :param table: The table to get rows from.
       :param columns: string of which columns to get (ex. "id, name, enable_p")
       :param extraWhere: Any extra where statements
       :param extraArgs: Params to stuff into the extra where string
       :param checkEnabled: If should check if enabled_p = TRUE on table"""

    if not extraWhere:
        extraWhere = "true"
    else:
        extraWhere = " ( " + extraWhere + ") "
    if checkEnabled:
        extraWhere = extraWhere + " AND enabled_p = %s"
        extraArgs += (True,)

    closeConn = False
    if not conn:
        conn = getConn()
        closeConn = True
    cur = conn.cursor(cursor_factory=dbapi2extras.DictCursor)  # DictCursor doesn't give real dictionaries
    # TODO: handle exceptions?
    sql = "SELECT " + columns + " FROM " + table + " WHERE " + extraWhere + " " + orderStatement
    cur.execute(sql, extraArgs)

    results = []
    for row in cur:
        resultRow = {}
        for key in row.keys():
            resultRow[key] = row[key]
        results.append(resultRow)
    cur.close()
    if closeConn:
        conn.close()
    return results


def getRowsFromTableBIG(table, columns='*', extraWhere=None, extraArgs=(), checkEnabled=False, orderStatement="",
                        conn=None):
    """
    Gets all arrays of arrays from table.
       :param table: The table to get rows from.
       :param columns: string of which columns to get (ex. "id, name, enable_p")
       :param extraWhere: Any extra where statements
       :param extraArgs: Params to stuff into the extra where string
       :param checkEnabled: If should check if enabled_p = TRUE on table
       :returns the rows as lists in a large list
       """

    if not extraWhere:
        extraWhere = "true"
    else:
        extraWhere = " ( " + extraWhere + ") "
    if checkEnabled:
        extraWhere = extraWhere + " AND enabled_p = %s"
        extraArgs += (True,)

    closeConn = False
    if not conn:
        conn = getConn()
        closeConn = True
    curname = "named_cursor_" + str(time.time()) + "_" + str(random.random())
    cur = conn.cursor(curname)  # Named server side cursor
    # TODO: handle exceptions?
    sql = "SELECT " + columns + " FROM " + table + " WHERE " + extraWhere + " " + orderStatement
    cur.execute(sql, extraArgs)

    results = []
    for row in cur:
        resultRow = []
        for value in row:
            resultRow.append(value)
        results.append(resultRow)
    cur.close()
    if closeConn:
        conn.close()
    return results


def getIdsFromTable(table, extraWhere=None, extraArgs=(), checkEnabled=False, conn=None):
    """Gets all id values from table.
       :param table: The table to get ids from.
       :param extraWhere: Any extra where statements
       :param extraArgs: Params to stuff into the extra where string
       :param checkEnabled: If should check if enabled_p = TRUE on table"""

    results = getRowsFromTable(table, columns='id', extraWhere=extraWhere, extraArgs=extraArgs,
                               checkEnabled=checkEnabled, conn=conn)
    return [row['id'] for row in results]


def getRowFromTableById(table, id, columns="*", checkEnabled=False, conn=None):
    """Fetches one row from table where table.id = id, returns a dictionary."""
    results = getRowsFromTable(table, columns=columns, extraWhere='id=%s', extraArgs=(id,), checkEnabled=checkEnabled,
                               conn=conn)
    if results:
        return results[0]
    else:
        return None


def deleteRowFromTableById(table, id, deleteIsDisable=False, cursor=None):
    """Delete a row from a given table by id.
    :param table: The table to delete from.
    :param id: The id of the entry to delete.
    :param deleteIsDisable: If True will set enabled_p column instead of remove from table."""
    sql = ""
    if deleteIsDisable:
        sql = "UPDATE " + table + " SET enabled_p=FALSE WHERE id=%s"
    else:
        sql = "DELETE FROM " + table + " WHERE id=%s"
    madeCursor = False
    if not cursor:
        madeCursor = True
        conn = getConn()
        cursor = conn.cursor()
    cursor.execute(sql, (id,))
    if madeCursor:
        conn.commit()
        cursor.close()
        conn.close()


def insertRow(table, parameters, cursor=None):
    """Insert new row into database.
    :param table: The table name
    :param parameters: dictionary of parameters, column_name: value.
    :returns: the new id from table_seq"""
    close = False
    if not cursor:
        close = True
        conn = getConn()
        cursor = conn.cursor()
    cursor.execute("SELECT NEXTVAL('" + table + "_seq')")
    id = cursor.fetchone()[0]
    sql = "INSERT INTO " + table + " (id, "
    values_sql = ") VALUES (%s, "
    for i, key in enumerate(parameters.keys()):
        sql += key
        values_sql += "%s"
        if i != (len(parameters) - 1):
            sql += ", "
            values_sql += ", "
    sql += values_sql + ")"
    values = [id]
    values.extend(parameters.values())
    cursor.execute(sql, tuple(values))
    if close:
        conn.commit()
        cursor.close()
        conn.close()
    return id


def updateRowById(table, id, parameters, cursor=None):
    """Update row in database.
    :param table: The table name
    :param id: The id of the row to update.
    :param parameters: dictionary of parameters, column_name: value."""
    close = False
    if not cursor:
        close = True
        conn = getConn()
        cursor = conn.cursor()
    sql = "UPDATE " + table + " SET "
    for i, key in enumerate(parameters.keys()):
        sql += key + "=%s"
        if i != (len(parameters) - 1):
            sql += ", "
    sql += " WHERE id=%s"
    values = list(parameters.values())
    values.append(id)
    cursor.execute(sql, tuple(values))
    if close:
        conn.commit()
        cursor.close()
        conn.close()


def getConfVersion():
    conn = getConn()
    cur = conn.cursor()
    cur.execute("SELECT conf_version, conf_datetime FROM cache_versions");
    row = cur.fetchone()
    v = [row[0], row[1]]
    cur.close()
    conn.close()
    return v


def getConn():
    """Returns a database connection, you are responsible for closing it."""
    conn = dbapi2.connect(database=Single().getDBName(), user=Single().getDBUser(), password=Single().getDBPassword(),
                          host=Single().getDBHost())
    return conn


def getAccount(email, password):
    """Returns an account object where account has email and password, or None if there is none."""
    account = getAccountByEmail(email)
    if account:
        # logging.debug("Pass:"+password+", hashes:"+str(account.session_hashes))
        if password in account.session_hashes:
            return account
        elif account.password == hashlib.sha1((account.seed + password).encode()).hexdigest():
            return account
        else:
            logging.debug("DEBUG: Failed login: account but no session or password: email=%s" % (email))
    else:
        logging.debug("DEBUG: Failed login: not account, email=%s", (email,))
    return None


def getAccountByEmail(email):
    """Returns an account object where with email, or None."""
    conn = getConn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, name, phone, password, seed, privilege_id, recovery_hash, recovery_datetime from account WHERE enabled_p=TRUE AND email=%s",
        (email,))
    row = cur.fetchone()
    if row:
        session_hashes = getRowsFromTableBIG(table="account_session", columns="hash",
                                             extraWhere="account_id=%s AND datetime > now() - interval '1month'",
                                             extraArgs=(row[0],), conn=conn)
        # logging.debug("session_hashes - "+str(session_hashes))
        if session_hashes:
            session_hashes = list(list(zip(*session_hashes))[0])
        else:
            session_hashes = []
        print(session_hashes)
        a = Account(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], session_hashes)
        cur.close()
        conn.close()
        return a
    else:
        cur.close()
        conn.close()
        return None


def sendEmail(toemail, fromemail, subject, message):
    msg = MIMEText(message)
    if not subject:
        msg['Subject'] = 'None'
    else:
        msg['Subject'] = subject
    msg['From'] = fromemail
    msg['To'] = toemail
    s = smtplib.SMTP('localhost')
    s.sendmail(fromemail, [toemail], msg.as_string())
    s.quit()


def txtSplit(msg, readableSplit=True):
    if len(msg) < 160:
        return [msg]
    if not readableSplit:
        if len(msg) > 1440:
            raise BadTxtBody('Split message greater than 1440 characters.')
        msgs = []
        for i in range(0, len(msg), 160):
            end = i + 160
            if end > len(msg):
                end = len(msg)
            msgs.append(msg[i:end])
        return msgs
    else:
        if len(msg) > 1395:  # No more than 10 messages split.
            raise BadTxtBody('Readable split message greater than 1395 characters.')
        msgs = []
        words = msg.split(' ')
        m = ""
        for word in words:
            if len(m) + len(word + " ") > 155:
                msgs.append(m)
                m = ""
            m += word + " "
        if m != "":
            msgs.append(m)
        if len(msgs) > 9:
            raise BadTxtBody('Readable split message is greater than 9 splits.')
        for i in range(0, len(msgs)):
            msgs[i] = "(%d/%d)" % (i + 1, len(msgs)) + msgs[i]
        return msgs


def sendTxt(toTxt, msg, readableSplit=True):
    client = TwilioRestClient(Single().getTwilioAccount(), Single().getTwilioToken())
    if str(toTxt)[0] != '+':
        toTxt = '+' + toTxt
    if len(toTxt) != 12:
        raise BadPhoneNumberError(toTxt)

    txts = txtSplit(msg, readableSplit)

    messages = []
    for txt in txts:
        message = client.sms.messages.create(to=toTxt, from_="+17852465982", body=txt)
        messages.append(message)
        if message.status == 'failed':
            raise FailedTxtError(message)
    return messages


def csvEscape(entry):
    mystr = entry.replace('\\', '\\\\')
    return mystr.replace('"', '\"')


def makeCSVLine(data):
    line = []
    for d in data:
        if isinstance(d, str):
            line.append('"' + csvEscape(d) + '"')
        elif d == None:
            line.append('')
        elif isinstance(d, float):
            line.append('%.3f' % d)
        elif isinstance(d, int):
            line.append(str(d))
    return ",".join(line)


def escapeSpecialLatexChars(oldStr):
    return string.replace(string.replace(string.replace(oldStr, "_", "\\_"), "&", "\\&"), "#", "\\#")


def getRequiredIntParam(name):
    value = request.values.get(name)
    if not value:
        abort(400, 'Missing %s' % name)
    try:
        value = int(value)
    except ValueError:
        abort(400, 'Invalid %s' % name)
    return value


def convertBinNumToID(binNum):
    IDs = getIdsFromTable("bin", extraWhere="name=\'Bin %s\'", extraArgs=(binNum,))
    # TODO: error handling including empty response
    return IDs[0]


def convertBinIDtoNum(binID):
    row = getRowFromTableById("bin", binID)
    # TODO: error handling including empty response
    m = re.search("Bin ([0-9]+)", row["name"])
    return int(m.group(1))


def getListOfBinNumbers():
    allRows = getRowsFromTable("bin")
    binNumbers = []
    for aR in allRows:
        m = re.search("Bin ([0-9]+)", aR["name"])
        if m:
            binNumbers += [int(m.group(1))]
    return list(set(binNumbers))  # remove duplicates and return


def computeAirHrs(fillRow):
    start_dt = fillRow["air_begin_datetime"] if fillRow["air_begin_datetime"] != None else fillRow["filled_datetime"]
    finish_dt = fillRow["air_end_datetime"] if fillRow["air_end_datetime"] != None else fillRow["emptied_datetime"]
    if start_dt and finish_dt:
        return timedeltaToHours(finish_dt - start_dt)
    else:
        return None


def getStartAirDT(fillRow):
    if not fillRow["air_begin_datetime"]:
        return fillRow["filled_datetime"]
    else:
        return fillRow["air_begin_datetime"]


def getStopAirDT(fillRow):
    if not fillRow["air_end_datetime"]:
        if fillRow["emptied_datetime"]:
            return fillRow["emptied_datetime"]
        else:
            return datetime.now()

    else:
        return fillRow["air_end_datetime"]


def computeUpAirHrs(fillRow):
    """
    Computes number of up air hours.  Assumes always starts in up-air.
    """
    startAir_dt = getStartAirDT(fillRow)
    if not startAir_dt:
        raise UtilComputationError("No start air or even filled datetime available for fill.")
    end_dt = fillRow["roll_datetime"] or getStopAirDT

    return timedeltaToHours(end_dt - startAir_dt)


def computeDownAirHrs(fillRow):
    """
    Computes number of down air hours.  Assumes always starts in up-air.
    """
    roll_dt = fillRow["roll_datetime"][0]
    if not roll_dt:
        roll_dt = getStopAirDT(fillRow)
    # raise UtilComputationError("No reverse air time, so it is assumed not in down-air yet.")
    stopAir_dt = getStopAirDT(fillRow)
    return timedeltaToHours(stopAir_dt - roll_dt)


class UtilComputationError(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class BadPhoneNumberError(Exception):
    def __init__(self, number):
        Exception.__init__(self)
        self.msg = "Invalid phone number format %s (+XXXXXXXX)" + (str(number),)

    def __str__(self):
        return self.msg


class BadTxtBody(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class FailedTxtError(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.msg = "Failed to send txt: to=%s, body=%s" % (message.to, message.body)

    def __str__(self):
        return self.msg


class Single:
    """A singleton to cache stuff."""

    class __impl:
        def __init__(self):
            self.privileges = None
            self.dbuser = None
            self.dbpass = None
            self.dbname = None
            self.dbhost = None
            self.MIDpass = None
            self.sessionSecretKey = None
            self.runningPort = None
            self.twilioAccount = None
            self.twilioToken = None
            self.lock = threading.RLock()
            self.configLoc = "settings.cfg"

        def getPrivileges(self):
            """Returns a dictionary with privilege names ('Super User') as keys."""
            self.lock.acquire()
            if self.privileges == None:
                self.privileges = {}
                conn = getConn()
                cur = conn.cursor()
                cur.execute("SELECT name, id FROM privilege ORDER BY id");
                for record in cur:
                    self.privileges[record[0]] = record[1]
                cur.close()
                conn.close()
            self.lock.release()
            return self.privileges

        def loadSettings(self):
            self.lock.acquire()
            config = configparser.ConfigParser()
            config.read(self.configLoc)
            self.dbname = config.get('database', 'dbname')
            self.dbuser = config.get('database', 'dbuser')
            self.dbpass = config.get('database', 'dbpass')
            self.dbhost = config.get('database', 'dbhost')
            self.sessionSecretKey = config.get('flask', 'session_secret_key')
            self.runningPort = int(config.get('flask', 'running_port'))
            self.MIDpass = config.get('MID', 'MIDpass')
            self.twilioAccount = config.get('twilio', 'account')
            self.twilioToken = config.get('twilio', 'token')
            self.lock.release()

        def getDBName(self):
            if not self.dbname:
                self.loadSettings()
            return self.dbname

        def getDBUser(self):
            if not self.dbuser:
                self.loadSettings()
            return self.dbuser

        def getDBPassword(self):
            if not self.dbpass:
                self.loadSettings()
            return self.dbpass

        def getDBHost(self):
            if not self.dbhost:
                self.loadSettings()
            return self.dbhost

        def getMIDPassword(self):
            if not self.MIDpass:
                self.loadSettings()
            return self.MIDpass

        def getTwilioAccount(self):
            if not self.twilioAccount:
                self.loadSettings()
            return self.twilioAccount

        def getTwilioToken(self):
            if not self.twilioToken:
                self.loadSettings()
            return self.twilioToken

        def getSessionSecretKey(self):
            if not self.sessionSecretKey:
                self.loadSettings()
            return self.sessionSecretKey

        def getRunningPort(self):
            if not self.runningPort:
                self.loadSettings()
            return self.runningPort

    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Single.__instance is None:
            # Create and remember instance
            Single.__instance = Single.__impl()

        # Store instance reference as the only member in the handle
        self.__dict__['_Single__instance'] = Single.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
