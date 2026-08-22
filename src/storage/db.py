"""SQLite database connection and schema management."""

import sqlite3
from pathlib import Path
from typing import Optional
from ..core.config import DB_PATH, DATA_DIR
from ..core.logger import logger


class DatabaseManager:
    """Manages SQLite connection and migrations."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._shared_conn: Optional[sqlite3.Connection] = None
        if str(self.db_path) == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        conn = self.get_connection()
        # Settings table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )

        # Quota history table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quota_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                percentage REAL NOT NULL,
                remaining_fraction REAL NOT NULL,
                reset_at TEXT,
                group_name TEXT
            );
            """
        )

        # Index for fast time-series queries
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_history_timestamp_model 
            ON quota_history(timestamp, model_id);
            """
        )
        conn.commit()
        if self._shared_conn is None:
            conn.close()
