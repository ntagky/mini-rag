import uuid
import sqlite3
from typing import List
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.config.logger import get_logger
from app.config.configer import SQLITE_DIR

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
        """
        Initialize the SQLite database, creating the directory and database file if needed.

        Args:
            path (Path, optional): Directory path to store the database. Defaults to SQLITE_DIR.
            name (str, optional): Database filename. Defaults to "default".
        """
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self.db_path = SQLITE_DIR / name
        self._init_db(name)

    def _connect(self):
        """
        Create and return a connection to the SQLite database.

        Returns:
            sqlite3.Connection: Active SQLite connection.
        """
        return sqlite3.connect(self.db_path)

    def _init_db(self, db_name: str):
        """
        Initialize the ingested_files table if it does not exist.

        Args:
            db_name (str): Name of the database file.
        """
        logger.debug(
            f"[SQLiteDB] {'Loaded existing' if self.db_path.exists() else 'Created new'} db '{db_name}'"
        )
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ingested_files (
                    id VARCHAR(32) PRIMARY KEY,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    page_count INTEGER,
                    chunk_count INTEGER,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_control (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    status TEXT NOT NULL CHECK (status IN ('idle','running','completed','failed')),
                    started_at TEXT,
                    finished_at TEXT,
                    error_message TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

            conn.execute("""
                INSERT OR IGNORE INTO ingestion_control (
                    id,
                    status,
                    started_at,
                    finished_at,
                    error_message,
                    updated_at
                )
                VALUES (
                    1,
                    'idle',
                    NULL,
                    NULL,
                    NULL,
                    CURRENT_TIMESTAMP
                )
            """)

    def create_file(self, file: File):
        """
        Insert a new file record into the ingested_files table.

        Args:
            file (File): File metadata to store.
        """
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

    def read_ingestion_control(self):
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT status, started_at, finished_at, error_message, updated_at
                FROM ingestion_control
                WHERE id = 1;
            """)

            row = cursor.fetchone()
            return {
                "status": row[0],
                "is_running": row[0] == "running",
                "started_at": row[1],
                "finished_at": row[2],
                "error_message": row[3],
            }

    def update_ingestion_control(self, status: str, error: str | None = None):
        with self._connect() as conn:
            if status == "running":
                conn.execute("""
                    UPDATE ingestion_control
                    SET
                        status = 'running',
                        started_at = CURRENT_TIMESTAMP,
                        finished_at = NULL,
                        error_message = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """)
            elif status == "completed":
                conn.execute("""
                    UPDATE ingestion_control
                    SET
                        status = 'completed',
                        finished_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """)
            elif status == "failed":
                conn.execute(
                    """
                    UPDATE ingestion_control
                    SET
                        status = 'failed',
                        finished_at = CURRENT_TIMESTAMP,
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1;
                """,
                    error,
                )

    def file_exists_by_hash(self, hash: str) -> bool:
        """
        Check if a file with the given hash already exists in the database.

        Args:
            hash (str): SHA or unique hash of the file.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM ingested_files WHERE hash = ?", (hash,)
            )
            return cursor.fetchone() is not None

    def read_all_files(self) -> List[File]:
        """
        Retrieve all ingested file records ordered by ingestion time descending.

        Returns:
            List[File]: List of all ingested files.
        """
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
        """
        Delete all records from the ingested_files table, effectively clearing the database.
        """
        with self._connect() as conn:
            conn.execute("DELETE FROM ingested_files;")
            conn.execute("DELETE FROM ingestion_control;")
            conn.execute("""
                INSERT OR IGNORE INTO ingestion_control (
                    id,
                    status,
                    started_at,
                    finished_at,
                    error_message,
                    updated_at
                )
                VALUES (
                    1,
                    'idle',
                    NULL,
                    NULL,
                    NULL,
                    CURRENT_TIMESTAMP
                )
            """)
            logger.debug("Deleted all items from SQL db.")

    def exists(self) -> bool:
        """
        Check if the SQLite database file exists.

        Returns:
            bool: True if the database file exists, False otherwise.
        """
        return self.db_path.exists()
