"""SQLite database management"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

class Database:
    """SQLite database for metadata"""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def connection(self):
        """Context manager for connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema"""
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE NOT NULL,
                    message TEXT,
                    tag TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parent_id INTEGER,
                    is_autosave BOOLEAN DEFAULT 0,
                    trigger_type TEXT,
                    files_count INTEGER,
                    total_size INTEGER,
                    compressed_size INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES snapshots(id)
                );

                CREATE TABLE IF NOT EXISTS snapshot_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    size INTEGER,
                    mode INTEGER,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id),
                    UNIQUE(snapshot_id, file_path)
                );

                CREATE TABLE IF NOT EXISTS file_contents (
                    hash TEXT PRIMARY KEY,
                    content BLOB NOT NULL,
                    original_size INTEGER,
                    compressed_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS autosave_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_check TIMESTAMP,
                    last_save TIMESTAMP,
                    last_snapshot_id INTEGER,
                    files_tracked INTEGER,
                    FOREIGN KEY (last_snapshot_id) REFERENCES snapshots(id)
                );

                CREATE INDEX IF NOT EXISTS idx_snapshots_created ON snapshots(created_at);
                CREATE INDEX IF NOT EXISTS idx_snapshots_tag ON snapshots(tag);
                CREATE INDEX IF NOT EXISTS idx_snapshot_files_hash ON snapshot_files(file_hash);
                CREATE INDEX IF NOT EXISTS idx_file_contents_hash ON file_contents(hash);
            """)

    # Snapshot CRUD
    def create_snapshot(
        self,
        hash: str,
        message: Optional[str] = None,
        tag: Optional[str] = None,
        is_autosave: bool = False,
        trigger_type: str = 'manual',
        parent_id: Optional[int] = None,
        files_count: int = 0,
        total_size: int = 0,
        compressed_size: int = 0
    ) -> int:
        """Create new snapshot record"""
        with self.connection() as conn:
            cursor = conn.execute("""
                INSERT INTO snapshots
                (hash, message, tag, is_autosave, trigger_type, parent_id,
                 files_count, total_size, compressed_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (hash, message, tag, is_autosave, trigger_type, parent_id,
                  files_count, total_size, compressed_size))
            return cursor.lastrowid

    def get_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """Get snapshot by ID"""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snapshots WHERE id = ?",
                (snapshot_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_snapshot_by_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """Get snapshot by tag"""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snapshots WHERE tag = ?",
                (tag,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_snapshots(
        self,
        limit: Optional[int] = None,
        include_autosave: bool = True
    ) -> List[Dict[str, Any]]:
        """List snapshots"""
        with self.connection() as conn:
            query = "SELECT * FROM snapshots"
            if not include_autosave:
                query += " WHERE is_autosave = 0"
            query += " ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"

            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get most recent snapshot"""
        snapshots = self.list_snapshots(limit=1)
        return snapshots[0] if snapshots else None

    def delete_snapshot(self, snapshot_id: int) -> None:
        """Delete snapshot and its files"""
        with self.connection() as conn:
            conn.execute("DELETE FROM snapshot_files WHERE snapshot_id = ?", (snapshot_id,))
            conn.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))

    # Snapshot files
    def add_file_to_snapshot(
        self,
        snapshot_id: int,
        file_path: str,
        file_hash: str,
        size: int,
        mode: int
    ) -> None:
        """Add file to snapshot"""
        with self.connection() as conn:
            conn.execute("""
                INSERT INTO snapshot_files (snapshot_id, file_path, file_hash, size, mode)
                VALUES (?, ?, ?, ?, ?)
            """, (snapshot_id, file_path, file_hash, size, mode))

    def get_snapshot_files(self, snapshot_id: int) -> List[Dict[str, Any]]:
        """Get all files in snapshot"""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM snapshot_files WHERE snapshot_id = ?
            """, (snapshot_id,))
            return [dict(row) for row in cursor.fetchall()]

    # File contents (with deduplication)
    def store_content(
        self,
        content_hash: str,
        content: bytes,
        original_size: int,
        compressed_size: int
    ) -> None:
        """Store file content (deduplicated)"""
        with self.connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO file_contents
                (hash, content, original_size, compressed_size)
                VALUES (?, ?, ?, ?)
            """, (content_hash, content, original_size, compressed_size))

    def get_content(self, content_hash: str) -> Optional[bytes]:
        """Get file content by hash"""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT content FROM file_contents WHERE hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()
            return row['content'] if row else None

    def content_exists(self, content_hash: str) -> bool:
        """Check if content exists"""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM file_contents WHERE hash = ? LIMIT 1",
                (content_hash,)
            )
            return cursor.fetchone() is not None

    # Autosave state
    def update_autosave_state(
        self,
        last_check: Optional[datetime] = None,
        last_save: Optional[datetime] = None,
        last_snapshot_id: Optional[int] = None,
        files_tracked: Optional[int] = None
    ) -> None:
        """Update autosave state"""
        with self.connection() as conn:
            # Ensure row exists
            conn.execute("""
                INSERT OR IGNORE INTO autosave_state (id) VALUES (1)
            """)

            updates = []
            params = []

            if last_check:
                updates.append("last_check = ?")
                params.append(last_check)
            if last_save:
                updates.append("last_save = ?")
                params.append(last_save)
            if last_snapshot_id:
                updates.append("last_snapshot_id = ?")
                params.append(last_snapshot_id)
            if files_tracked is not None:
                updates.append("files_tracked = ?")
                params.append(files_tracked)

            if updates:
                params.append(1)
                conn.execute(
                    f"UPDATE autosave_state SET {', '.join(updates)} WHERE id = ?",
                    params
                )

    def get_autosave_state(self) -> Optional[Dict[str, Any]]:
        """Get autosave state"""
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM autosave_state WHERE id = 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    # Cleanup
    def cleanup_old_autosaves(self, max_keep: int = 50) -> int:
        """Delete old autosaves beyond retention limit"""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT id FROM snapshots
                WHERE is_autosave = 1
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
            """, (max_keep,))

            old_ids = [row['id'] for row in cursor.fetchall()]

            for snapshot_id in old_ids:
                self.delete_snapshot(snapshot_id)

            return len(old_ids)
