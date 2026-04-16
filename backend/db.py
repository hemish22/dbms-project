import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


def get_connection():
    """Return a new MySQL connection. Caller is responsible for closing."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False
    )


def query(sql, params=None, dictionary=True, many=False):
    """
    Execute a SELECT and return all rows as dicts (default).
    Pass many=True for executemany.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=dictionary)
        if many:
            cur.executemany(sql, params or [])
        else:
            cur.execute(sql, params or ())
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def execute(sql, params=None):
    """
    Execute an INSERT / UPDATE / DELETE.
    Returns (lastrowid, rowcount).
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid, cur.rowcount
    finally:
        conn.close()
