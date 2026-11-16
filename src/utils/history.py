"""
History management adapter backed by SQLite database.
"""

from src.utils.database import db

class HistoryManager:
    """Adapter forwarding history operations to SQLite database."""

    def add(self, title: str, file_path: str, url: str = "", media_type: str = "video",
            quality: str = "", file_size: str = "") -> None:
        db.add_download(
            title=title,
            file_path=file_path,
            url=url,
            media_type=media_type,
            quality=quality,
            file_size=file_size
        )

    def get_all(self):
        items, _, _ = db.get_paginated(page=1, page_size=1000)
        return items

    def get_stats(self):
        return db.get_stats()

    def delete(self, entry_id: int):
        return db.delete_record(entry_id)

    def clear(self):
        return db.clear_all()

history_manager = HistoryManager()
