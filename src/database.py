"""
Abstraction layer to a database.
"""
import sqlite3


class Database:
    """
    Implements the database interface using SQLite.
    """

    def __init__(self, path):
        self._conn = sqlite3.connect(path)

    def execute(self, query, data=None):
        if data is None:
            data = ()
        cur = self._conn.execute(query, data)
        cur.close()

    def update(self, query, data=None):
        cur = self._conn.executemany(query, data)
        self._conn.commit()
        cur.close()

    def insert(self, query, data):
        cur = self._conn.executemany(query, data)
        self._conn.commit()
        cur.close()

    def insertone(self, query, data=None):
        if data is None:
            data = ()
        cur = self._conn.execute(query, data)
        ident = cur.lastrowid
        self._conn.commit()
        cur.close()
        return ident

    def fetchone(self, query, params):
        cur = self._conn.execute(query, params)
        row = cur.fetchone()
        cur.close()
        return row

    def fetchall(self, query, params):
        cur = self._conn.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def close(self):
        self._conn.close()
