from datetime import datetime
import time
import random
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
import psycopg2
from psycopg2.errors import SerializationFailure

def parse_cmdline():
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("dsn")

    parser.add_argument("-v", "--verbose", action="store_true", help="print debug info")

    opt = parser.parse_args()
    return opt

def get_conn():
    opt = parse_cmdline()
    logging.basicConfig(level=logging.DEBUG if opt.verbose else logging.INFO)
    conn = psycopg2.connect(opt.dsn)
    cur = conn.cursor()
    return conn, cur


def check_user(username_id):
    t = (username_id, )
    conn, cur = get_conn()
    cur.execute("SELECT COUNT(*) FROM users WHERE username = %s", t)
    users = cur.fetchall()
    if(users[0][0] == 0):
        return False
    else:
        return True
    
def add_user(username_id):
    conn, cur = get_conn()
    t = (username_id, 0, )
    cur.execute("INSERT INTO users(username, points) VALUES(%s, %s)", t)
    conn.commit()
    
def add_points_user(username_id, points):
    conn, cur = get_conn()
    t = (points, username_id, )
    cur.execute("UPDATE users SET points = points + %s WHERE username = %s", t)
    conn.commit()


def remove_points(username_id, points):
    conn, cur = get_conn()
    t = (points, username_id, )
    t2 = (username_id, )
    cur.execute("UPDATE users SET points = points - %s WHERE username = %s", t)
    cur.execute("UPDATE users SET points = 0 WHERE username = %s AND points < 0", t2)
    conn.commit()


def add_points(username_id, points):
    t = (username_id,)
    if(check_user(username_id) == False and username_id.isdigit()):
        add_user(username_id)
        add_points_user(username_id,points)
    elif(username_id.isdigit()):
        add_points_user(username_id,points)
       

def add_leaderboard(username, message_id, count):
    conn, cur = get_conn()
    now=datetime.now()
    timestamp=datetime.timestamp(now)
    timestamp = int(str(timestamp).replace('.', ''))
    t = (str(message_id), str(username), timestamp, 1, count, )
    cur.execute("INSERT INTO board_tables(message_id, username, created_time, page_number, last_usernumber) VALUES(%s,%s,%s,%s,%s)", t)
    conn.commit()
    
def check_leaderboard(message_id, user_id):
    conn, cur = get_conn()
    t = (str(user_id), str(message_id), )
    cur.execute("SELECT COUNT(*) FROM board_tables WHERE username = %s AND message_id = %s",t)
    data = cur.fetchall()
    if(data[0][0] == 0):
        return False
    else:
        return True
    
    
def get_user_point(username_id):
    conn, cur = get_conn()
    t = (username_id, )
    cur.execute("SELECT * FROM users WHERE username = %s", t)
    data = cur.fetchall()
    if not data:
        return 0
    else:
        return data[0][2]
    
def get_leaderboard_page(message_id, user_id):
    conn, cur = get_conn()
    t = (str(user_id), str(message_id), )
    cur.execute("SELECT * FROM board_tables WHERE username = %s AND message_id = %s",t)
    data = cur.fetchall()
    return data[0][4], data[0][5]
    
def update_leaderboard(page, last_user, message_id):
    conn, cur = get_conn()
    t = (page, last_user, str(message_id))
    cur.execute("UPDATE board_tables SET page_number = %s , last_usernumber = %s WHERE message_id = %s", t)
    conn.commit()
    
def get_users(page = 1):
    page_offset = (page - 1) * 10
    conn, cur = get_conn()
    cur.execute("SELECT * FROM users ORDER BY points DESC OFFSET %s ROWS FETCH NEXT 10 ROWS ONLY", (page_offset,))
    rows = cur.fetchall()
    return rows
    
    
def insert_points_requests(message_id, users, points, approved, created_by):
    conn, cur = get_conn()
    t = (message_id, users, points, approved, created_by, )
    cur.execute("INSERT INTO points_requests(message_id, users, points, approved, created_by)  VALUES(%s, %s, %s, %s, %s)", t)
    conn.commit()
    
    
def check_requests(message_id):
    conn, cur = get_conn()
    t = (message_id, )
    cur.execute("SELECT * FROM points_requests WHERE message_id = %s AND approved = 0 LIMIT 1", t)
    data = cur.fetchall()
    if(not data):
        return None
    else:
        return True
        
        
def get_users_requests(message_id):
    conn, cur = get_conn()
    t = (message_id, )
    cur.execute("SELECT * FROM points_requests WHERE message_id = %s LIMIT 1", t)
    data = cur.fetchall()
    if(not data):
        return None
    else:
        return data[0][2], data[0][3]
        
def update_requests(message_id, app):
    conn, cur = get_conn()
    t = (app, message_id, )
    cur.execute("UPDATE points_requests SET approved = %s WHERE message_id = %s", t)
    conn.commit()
    
    
async def reset_database():
    conn, cur = get_conn()
    cur.execute("DELETE FROM users WHERE 'a' = 'a'")
    conn.commit()