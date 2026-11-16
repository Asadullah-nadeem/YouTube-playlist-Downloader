import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "library.db")
LEGACY_HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "history.json")

class DatabaseManager:
    """High-performance SQLite database manager for library, history, and pagination."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()
        self._migrate_legacy_json()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables and performance indexes."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    url TEXT,
                    media_type TEXT DEFAULT 'video',
                    quality TEXT,
                    file_size TEXT,
                    platform TEXT,
                    date_created TEXT,
                    timestamp REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads (timestamp DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_downloads_type ON downloads (media_type)")
            conn.commit()

    def _migrate_legacy_json(self):
        """Migrate any old history.json entries into SQLite."""
        if os.path.exists(LEGACY_HISTORY_FILE):
            try:
                with open(LEGACY_HISTORY_FILE, "r", encoding="utf-8") as f:
                    old_items = json.load(f)
                    if isinstance(old_items, list) and old_items:
                        with self._get_connection() as conn:
                            # Check if db already has items
                            count = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
                            if count == 0:
                                for item in old_items:
                                    conn.execute("""
                                        INSERT INTO downloads 
                                        (title, file_path, url, media_type, quality, file_size, platform, date_created, timestamp)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        item.get("title", "Untitled"),
                                        item.get("file_path", ""),
                                        item.get("url", ""),
                                        item.get("type", "video"),
                                        item.get("quality", ""),
                                        item.get("size", ""),
                                        "Universal",
                                        item.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                        datetime.now().timestamp()
                                    ))
                                conn.commit()
            except Exception:
                pass

    def add_download(
        self,
        title: str,
        file_path: str,
        url: str = "",
        media_type: str = "video",
        quality: str = "",
        file_size: str = "",
        platform: str = "Universal"
    ) -> int:
        """Insert a newly downloaded or converted item."""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        ts = now.timestamp()
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO downloads 
                (title, file_path, url, media_type, quality, file_size, platform, date_created, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, file_path, url, media_type, quality, file_size, platform, date_str, ts))
            conn.commit()
            return cursor.lastrowid or 0

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        search_query: str = "",
        type_filter: str = "all"
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        Fetch paginated records with search and type filter.
        Returns: (items, total_count, total_pages)
        """
        page = max(1, page)
        offset = (page - 1) * page_size

        where_clauses = []
        params: List[Any] = []

        if search_query and search_query.strip():
            where_clauses.append("title LIKE ?")
            params.append(f"%{search_query.strip()}%")

        if type_filter and type_filter.lower() != "all":
            if type_filter.lower() == "video":
                where_clauses.append("media_type NOT LIKE '%audio%'")
            elif type_filter.lower() == "audio":
                where_clauses.append("media_type LIKE '%audio%'")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        with self._get_connection() as conn:
            # Count total matching
            count_sql = f"SELECT COUNT(*) FROM downloads {where_sql}"
            total_items = conn.execute(count_sql, params).fetchone()[0]

            total_pages = max(1, (total_items + page_size - 1) // page_size) if total_items > 0 else 1

            # Fetch page items
            query_sql = f"""
                SELECT id, title, file_path, url, media_type, quality, file_size, platform, date_created
                FROM downloads 
                {where_sql}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            fetch_params = params + [page_size, offset]
            rows = conn.execute(query_sql, fetch_params).fetchall()

            items = [dict(row) for row in rows]
            return items, total_items, total_pages

    def get_stats(self) -> Dict[str, Any]:
        """Retrieve count of total, videos, and audios."""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
            audio = conn.execute("SELECT COUNT(*) FROM downloads WHERE media_type LIKE '%audio%'").fetchone()[0]
            video = total - audio
            return {
                "total": total,
                "videos": video,
                "audios": audio
            }

    def delete_record(self, record_id: int) -> bool:
        """Delete single download entry."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM downloads WHERE id = ?", (record_id,))
            conn.commit()
            return True

    def clear_all(self) -> bool:
        """Clear all download entries."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM downloads")
            conn.commit()
            return True

db = DatabaseManager()

