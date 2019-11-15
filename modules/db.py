import sqlite3
from time import time
DAY = 86400


def log_usage(api_type, current_time):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS APIUSAGE (id integer primary key autoincrement, api text, time real);")
    try:
        cur.execute('INSERT INTO APIUSAGE (api, time) VALUES (?,?)',(api_type, current_time))
    except sqlite3.IntegrityError:
        print("Fail to insert")
    conn.commit()
    conn.close()


# return last 24hours usage
def get_api_usage_24(api_type):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    try:
        cur.execute('select count(*) from APIUSAGE where api=? and ?-time< ?',(api_type, time(), DAY))
        result = cur.fetchone()
        conn.close()
        return result
    except sqlite3.OperationalError:
        print('no such table')
        conn.close()
        return 0

