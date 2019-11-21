import sqlite3
from time import time
import datetime

DAY = 86400
time_format = "%d/%m/%Y"

def db_init(db, type):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    if type == 'log':
        cur.execute(
            "CREATE TABLE IF NOT EXISTS APIUSAGE (id integer primary key autoincrement, api text, log_time real);")
    if type == 'user':
        cur.execute("CREATE TABLE IF NOT EXISTS users (id integer primary key autoincrement,"
                    "username text unique, password text, firstName text, lastName text, age real, gender text, role text not null);")
        cur.execute('SELECT id from users where id = 1;')
        check = cur.fetchone()
        if not check:
            cur.execute('INSERT INTO users (username, password, firstName, lastName, age, gender, role)'
                        'VALUES (?,?,?,?,?,?,?)',
                        ('admin', 'admin', 'Ray', 'Lee', 32, 'Male', 'Admin'))
    conn.commit()
    conn.close()


def register(db, reg_info):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO users (username, password, firstName, lastName, age, gender, role)'
                    ' VALUES (?,?,?,?,?,?,?);',
                    (reg_info['username'], reg_info['password'], reg_info['firstName'], reg_info['lastName'],
                     reg_info['age'],reg_info['gender'],reg_info['role']))
    except sqlite3.IntegrityError:
        print("username has already been taken")
        conn.close()
        return False
    conn.commit()
    conn.close()
    return True


def login(db, login_info):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    result = None
    try:
        cur.execute('select id from users where username=? and password=?', (login_info[0], login_info[1]))
        result = cur.fetchone()
    except sqlite3.OperationalError:
        print('no such users table exits')
    conn.close()
    return result


def getuser(db, uid=None, username=None):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    result = None
    if uid:
        try:
            cur.execute('select id, firstName, lastName, age, gender, role from users where id=?', (uid,))
            result = cur.fetchone()
        except sqlite3.OperationalError:
            print('no such users table exits')
    else:
        try:
            cur.execute('select id, firstName, lastName, age, gender, role from users where username=?', (username,))
            result = cur.fetchone()
        except sqlite3.OperationalError:
            print('no such users table exits')
    conn.close()
    return result


def log_usage(db, api_type, current_time):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO APIUSAGE (api, log_time) VALUES (?,?);', (api_type, current_time,))
    except sqlite3.IntegrityError:
        print("Fail to log")
    conn.commit()
    conn.close()


# return last 24hours usage for a specific api
# type could be '24' for last 24 hours, '7d' for last 7 days, 's' for total usage, default type is 24
def get_api_usage(db, api_type, type='24'):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        days = [i for i in range(0, 7)]
        if type == '24':
            cur.execute('select count(*) from APIUSAGE where api=? and ?-log_time< ?', (api_type, time(), DAY,))
        if type == '7d':
            exec = "SELECT STRFTIME('%d/%m',log_time,'unixepoch', 'localtime') as creat, COUNT(*) "
            exec2 = "from APIUSAGE where api=? and strftime('%d/%m/%Y',log_time,'unixepoch', 'localtime') in (?,?,?,?,?,?,?) GROUP by creat"
            curtime = time()
            for i in range(0,7):
                ept = datetime.datetime.fromtimestamp(curtime - DAY * i)
                days[i] = ept.strftime(time_format)
            cur.execute(exec+exec2,(api_type,days[0],days[1],days[2],days[3],days[4], days[5], days[6]))
        result = None
        if type == 't':
            cur.execute('select count(*) from APIUSAGE where api=?', (api_type,))
        if type == 't' or type == '24':
            temp = cur.fetchone()
            result = dict()
            result = temp[0]
        else:
            day_usage = dict(cur.fetchall())
            dic = dict()
            result = []
            for day in days:
                temp1 = day.split('/')
                temp = temp1[0]+'/'+temp1[1]
                dic[temp] = day_usage.get(temp, 0)
            for k,v in dic.items():
                result.append(v)
            result.reverse()
        conn.close()
        return result
    except sqlite3.IntegrityError:
        print('no such log table')
        conn.close()
        return 0
