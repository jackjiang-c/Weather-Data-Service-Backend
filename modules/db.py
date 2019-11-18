import sqlite3
from time import time

DAY = 86400


def db_init(db, type):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    if type == 'log':
        cur.execute(
            "CREATE TABLE IF NOT EXISTS APIUSAGE (id integer primary key autoincrement, api text, log_time real);")
    if type == 'user':
        cur.execute("CREATE TABLE IF NOT EXISTS users (id integer primary key autoincrement,"
                    "username text unique, password text, firstName text, lastName text, age real, role text not null);")
        cur.execute('SELECT id from users where id = 1;')
        check = cur.fetchone()
        if not check:
            cur.execute('INSERT INTO users (username, password, firstName, lastName, age, role)'
                        'VALUES (?,?,?,?,?,?)',
                        ('admin', 'admin', 'Ray', 'Lee', 32, 'Admin'))
    conn.commit()
    conn.close()


def register(db, reg_info):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO users (username, password, firstName, lastName, age, role)'
                    ' VALUES (?,?,?,?,?,?);',
                    (reg_info['username'], reg_info['password'], reg_info['firstName'], reg_info['lastName'],
                     reg_info['age'], reg_info['role']))
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
            cur.execute('select id, firstName, lastName, age, role from users where id=?', (uid,))
            result = cur.fetchone()
        except sqlite3.OperationalError:
            print('no such users table exits')
    else:
        try:
            cur.execute('select id, firstName, lastName, age, role from users where username=?', (username,))
            result = cur.fetchone()
        except sqlite3.OperationalError:
            print('no such users table exits')
    conn.close()
    return result


def log_usage(db, api_type, current_time):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO APIUSAGE (api, log_time) VALUES (?,?);', (api_type, current_time))
    except sqlite3.IntegrityError:
        print("Fail to log")
    conn.commit()
    conn.close()


# return last 24hours usage for a specific api
def get_api_usage_24(db, api_type):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        cur.execute('select count(*) from APIUSAGE where api=? and ?-time< ?', (api_type, time(), DAY))
        result = cur.fetchone()
        conn.close()
        return result
    except sqlite3.OperationalError:
        print('no such table')
        conn.close()
        return 0
