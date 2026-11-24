"""Base SQLite repository with injected DatabaseManager."""

from typing import Optional
from src.core.database import DatabaseManager, db_manager


class BaseSQLiteRepository:
    """Base repository ensuring DIP via injectable DatabaseManager."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or db_manager
