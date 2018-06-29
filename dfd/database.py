import asyncio
import concurrent.futures as cf
import re
import sqlite3
from typing import Dict, Text


SQL_CREATE_TABLES = [
    '''
    CREATE TABLE filters (
        id INTEGER PRIMARY KEY,
        filter TEXT
    );
    ''',
    'PRAGMA user_version = 1;',
]

CURRENT_SCHEMA_VERSION = 1


class InvalidFilterError(Exception):

    def __init__(self, filter_):
        super().__init__()
        self._filter = filter_

    def __str__(self):
        return 'invalid filter: {0}'.format(self._filter)


class Filters(object):

    def __init__(self, dsn: Text) -> None:
        self._dsn = dsn
        self._loop = asyncio.get_event_loop()
        self._pool = cf.ProcessPoolExecutor()

    async def __aenter__(self) -> 'Filters':
        await self._bg(initialize)
        return self

    async def __aexit__(self, type_, value, traceback) -> bool:
        self._pool.shutdown()

    async def add(self, new_filter: Text) -> int:
        try:
            re.compile(new_filter)
        except Exception:
            raise InvalidFilterError(new_filter)
        return await self._bg(add, new_filter)

    async def get(self) -> Dict[int, Text]:
        return await self._bg(get)

    async def update(self, id_: int, new_filter: Text) -> bool:
        try:
            re.compile(new_filter)
        except Exception:
            raise InvalidFilterError(new_filter)
        return await self._bg(update, id_, new_filter)

    async def remove(self, id_: int) -> bool:
        return await self._bg(remove, id_)

    async def _bg(self, fn, *args):
        return await self._loop.run_in_executor(self._pool, fn, self._dsn,
                                                *args)


class Database(object):

    def __init__(self, dsn: Text) -> None:
        self._dsn = dsn

    def __enter__(self) -> sqlite3.Connection:
        self._db = sqlite3.connect(self._dsn)
        self._db.row_factory = sqlite3.Row
        return self._db

    def __exit__(self, type_, value, traceback) -> bool:
        self._db.close()


class ReadOnly(object):

    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def __enter__(self) -> sqlite3.Cursor:
        self._cursor = self._db.cursor()
        return self._cursor

    def __exit__(self, type_, value, traceback) -> bool:
        self._cursor.close()


class ReadWrite(object):

    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def __enter__(self) -> sqlite3.Cursor:
        self._cursor = self._db.cursor()
        return self._cursor

    def __exit__(self, type_, value, traceback) -> bool:
        if type_ is None:
            self._db.commit()
        else:
            self._db.rollback()
        self._cursor.close()


def initialize(dsn: Text):
    with Database(dsn) as db:
        try:
            # initialize table
            with ReadWrite(db) as query:
                for sql in SQL_CREATE_TABLES:
                    query.execute(sql)
        except sqlite3.OperationalError as e:
            pass

        # check the schema version
        with ReadOnly(db) as query:
            query.execute('PRAGMA user_version;')
            rv = query.fetchone()
        version = rv[0]

        if CURRENT_SCHEMA_VERSION > version:
            migrate(db, version)


def migrate(db: sqlite3.Connection, version: Text) -> None:
    raise NotImplementedError()


def add(dsn: Text, new_filter: Text) -> int:
    with Database(dsn) as db, \
         ReadWrite(db) as query:
        query.execute('INSERT INTO filters (filter) VALUES (?);', (new_filter,))
        id_ = query.lastrowid
    return id_


def get(dsn: Text) -> Dict[int, Text]:
    with Database(dsn) as db, \
         ReadOnly(db) as query:
        query.execute('SELECT id, filter FROM filters;')
        rv = query.fetchall()
    rv = dict(rv)
    return rv


def update(dsn: Text, id_: int, new_filter: Text) -> bool:
    with Database(dsn) as db, \
         ReadWrite(db) as query:
        query.execute('UPDATE filters SET filter=? WHERE id=?;', (new_filter, id_))
    return True


def remove(dsn: Text, id: int) -> bool:
    with Database(dsn) as db, \
         ReadWrite(db) as query:
        query.execute('DELETE FROM filters WHERE id=?;', (id_))
    return True
