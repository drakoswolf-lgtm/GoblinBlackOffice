"""SQLite connection and schema initialization helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.ledgergut.storage.schema import SCHEMA_STATEMENTS


class LedgergutDatabase:
    """Owns a SQLite connection for Ledgergut storage."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    def initialize(self) -> None:
        with self.connection:
            for statement in SCHEMA_STATEMENTS:
                self.connection.execute(statement)

    def close(self) -> None:
        self.connection.close()
