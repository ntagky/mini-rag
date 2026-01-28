import uuid
import sqlite3
from typing import List
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class IngestedFile(BaseModel):
    id: uuid.UUID
    filename: str
    path: str
    hash: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    ingested_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return self.model_dump()


class IngestionDB:
    def __init__(self, path: str = ".sqlite_db", name: str = "default"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(path + "/" + name)
        self._init_db(name)

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self, db_name: str):
        print(f"[SQLiteDB] {'Loaded existing' if self.db_path.exists() else 'Created new'} db '{db_name}'")
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

    @staticmethod
    def _table_exists(conn, table_name: str) -> bool:
        cursor = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None

    def create_file(self, file: IngestedFile):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO ingested_files (
                    id, filename, path, hash,
                    page_count, chunk_count
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(file.id),
                file.filename,
                file.path,
                file.hash,
                file.page_count,
                file.chunk_count
            ))

    def file_exists_by_hash(self, hash: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM ingested_files WHERE hash = ?",
                (hash,)
            )
            return cursor.fetchone() is not None

    def read_all_files(self) -> List[IngestedFile]:
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
            IngestedFile(
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
