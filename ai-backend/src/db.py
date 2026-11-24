"""Backward-compatible database facade delegating to DatabaseManager."""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from src.core.database import (
    DatabaseManager,
    UnitOfWork,
    db_manager,
    dict_factory,
    resolve_default_db_path,
)

BASE_DIR = resolve_default_db_path().parent.parent
DB_PATH = resolve_default_db_path()


@contextmanager
def get_db_connection():
    with db_manager.connection() as conn:
        yield conn


def query_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    return db_manager.query_one(sql, params)


def query_all(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    return db_manager.query_all(sql, params)


def execute_commit(sql: str, params: tuple = ()) -> int:
    return db_manager.execute_commit(sql, params)


__all__ = [
    "BASE_DIR",
    "DB_PATH",
    "DatabaseManager",
    "UnitOfWork",
    "db_manager",
    "dict_factory",
    "get_db_connection",
    "query_one",
    "query_all",
    "execute_commit",
]
