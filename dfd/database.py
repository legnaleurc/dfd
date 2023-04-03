import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing, contextmanager
import re
import sqlite3
from typing import Self


SQL_CREATE_TABLES = [
    """
    CREATE TABLE filters (
        id INTEGER PRIMARY KEY,
        filter TEXT
    );
    """,
    "PRAGMA user_version = 1;",
]

CURRENT_SCHEMA_VERSION = 1


class InvalidFilterError(Exception):
    def __init__(self, filter_):
        super().__init__()
        self._filter = filter_

    def __str__(self):
        return "invalid filter: {0}".format(self._filter)


class Filters(object):
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool = ProcessPoolExecutor()

    async def __aenter__(self) -> Self:
        await self._bg(initialize)
        return self

    async def __aexit__(self, type_, value, traceback) -> bool:
        self._pool.shutdown()

    async def add(self, new_filter: str) -> int:
        try:
            re.compile(new_filter)
        except Exception:
            raise InvalidFilterError(new_filter)
        return await self._bg(add, new_filter)

    async def get(self) -> dict[int, str]:
        return await self._bg(get)

    async def update(self, id_: int, new_filter: str) -> bool:
        try:
            re.compile(new_filter)
        except Exception:
            raise InvalidFilterError(new_filter)
        return await self._bg(update, id_, new_filter)

    async def remove(self, id_: int) -> bool:
        return await self._bg(remove, id_)

    async def _bg(self, fn, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._pool, fn, self._dsn, *args)


@contextmanager
def database(dsn: str):
    with closing(sqlite3.connect(dsn)) as db:
        db.row_factory = sqlite3.Row
        yield db


@contextmanager
def read_only(dsn: str):
    with database(dsn) as db, closing(db.cursor()) as cursor:
        yield cursor


@contextmanager
def read_write(dsn: str):
    with database(dsn) as db, closing(db.cursor()) as cursor:
        try:
            yield cursor
            db.commit()
        except Exception:
            db.rollback()
            raise


def initialize(dsn: str):
    # initialize table
    try:
        with read_write(dsn) as query:
            for sql in SQL_CREATE_TABLES:
                query.execute(sql)
    except sqlite3.OperationalError as e:
        pass

    # check the schema version
    with read_only(dsn) as query:
        query.execute("PRAGMA user_version;")
        rv = query.fetchone()
    version = rv[0]

    if CURRENT_SCHEMA_VERSION > version:
        migrate(dsn, version)


def migrate(dsn: str, version: str) -> None:
    raise NotImplementedError()


def add(dsn: str, new_filter: str) -> int:
    with read_write(dsn) as query:
        query.execute("INSERT INTO filters (filter) VALUES (?);", (new_filter,))
        id_ = query.lastrowid
    return id_


def get(dsn: str) -> dict[int, str]:
    with read_only(dsn) as query:
        query.execute("SELECT id, filter FROM filters;")
        rv = query.fetchall()
    rv = dict(rv)
    return rv


def update(dsn: str, id_: int, new_filter: str) -> bool:
    with read_write(dsn) as query:
        query.execute("UPDATE filters SET filter=? WHERE id=?;", (new_filter, id_))
    return True


def remove(dsn: str, id_: int) -> bool:
    with read_write(dsn) as query:
        query.execute("DELETE FROM filters WHERE id=?;", (id_))
    return True
