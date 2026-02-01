import uuid
import sqlite3
from typing import List
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from ..config.logger import get_logger
from ..config.configer import SQLITE_DIR

logger = get_logger("mini-rag." + __name__)


class File(BaseModel):
    id: uuid.UUID
    filename: str
    path: str
    hash: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    ingested_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return self.model_dump()


class SqliteDb:
    def __init__(self, path: Path = SQLITE_DIR, name: str = "default"):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self.db_path = SQLITE_DIR / name
        self._init_db(name)

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self, db_name: str):
        logger.debug(
            f"[SQLiteDB] {'Loaded existing' if self.db_path.exists() else 'Created new'} db '{db_name}'"
        )
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ingested_files (
                    id VARCHAR(32) PRIMARY KEY,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL,
                    hash TEXT NOT NULL UNIQUE,
                    page_count INTEGER,
                    chunk_count INTEGER,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def create_file(self, file: File):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ingested_files (
                    id, filename, path, hash,
                    page_count, chunk_count
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    str(file.id),
                    file.filename,
                    file.path,
                    file.hash,
                    file.page_count,
                    file.chunk_count,
                ),
            )

    def file_exists_by_hash(self, hash: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM ingested_files WHERE hash = ?", (hash,)
            )
            return cursor.fetchone() is not None

    def read_all_files(self) -> List[File]:
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT
                    id,
                    filename,
                    path,
                    hash,
                    page_count,
                    chunk_count,
                    ingested_at
                FROM ingested_files
                ORDER BY ingested_at DESC
            """)

            rows = cursor.fetchall()

        return [
            File(
                id=uuid.UUID(row[0]),
                filename=row[1],
                path=row[2],
                hash=row[3],
                page_count=row[4],
                chunk_count=row[5],
                ingested_at=row[6],
            )
            for row in rows
        ]

    def reset(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM ingested_files;")
            logger.debug("Deleted all items from SQL db.")
