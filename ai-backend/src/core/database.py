"""SQLite Database Manager & Unit of Work (Repository foundation, WAL mode, atomic tx)."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def resolve_default_db_path() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    env_path = os.environ.get("AI_CHAN_DB_PATH")
    if env_path:
        return Path(env_path)
    primary = base_dir / "database" / "app.db"
    if primary.exists():
        return primary
    alt = base_dir / "app.db"
    if alt.exists():
        return alt
    return primary


class UnitOfWork:
    """Transactional context for atomic multi-statement SQLite operations."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def query_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(sql, tuple(params))
        return cursor.fetchone()

    def query_all(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        cursor = self._conn.cursor()
        cursor.execute(sql, tuple(params))
        return cursor.rowcount


class DatabaseManager:
    """Manages SQLite connections with WAL mode, busy_timeout, and atomic transactions.

    Respects dynamic `src.db.DB_PATH` overrides used by test fixtures (`conftest.py`)
    when `db_path` is not explicitly pinned.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._pinned_path = db_path

    @property
    def db_path(self) -> Path:
        if self._pinned_path is not None:
            return self._pinned_path
        import src.db as db_module

        return Path(db_module.DB_PATH)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        try:
            if str(self.db_path) != ":memory:":
                conn.execute("PRAGMA journal_mode = WAL;")
        except sqlite3.OperationalError:
            pass
        conn.row_factory = dict_factory
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[UnitOfWork]:
        """Executes multiple SQL operations atomically (commit on success, rollback on error)."""
        with self.connection() as conn:
            uow = UnitOfWork(conn)
            try:
                yield uow
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def query_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            return cursor.fetchone()

    def query_all(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()

    def execute_commit(self, sql: str, params: Sequence[Any] = ()) -> int:
        with self.transaction() as uow:
            return uow.execute(sql, params)


db_manager = DatabaseManager()
