from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reading_state (
                book_id TEXT PRIMARY KEY,
                chapter_idx INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS character_aliases (
                alias TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                alias_type TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS character_cards (
                canonical_name TEXT PRIMARY KEY,
                first_chapter_idx INTEGER NOT NULL,
                summary TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def list_tables(self) -> list[str]:
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]
