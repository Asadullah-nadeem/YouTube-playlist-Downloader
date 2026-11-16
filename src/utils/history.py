import json
import os
from datetime import datetime
from typing import Any, Dict, List

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "history.json")

class HistoryManager:
    """Tracks downloaded items and maintains persistent history."""
    def __init__(self, filepath: str = HISTORY_FILE):
        self.filepath = filepath
        self._history: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> List[Dict[str, Any]]:
        """Load history from file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")
                self._history = []
        return self._history

    def save(self) -> bool:
        """Persist history to JSON file."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving history: {e}")
            return False

    def add(self, title: str, file_path: str, url: str = "", media_type: str = "video",
            quality: str = "", file_size: str = "") -> None:
        """Add an item to the history record."""
        entry = {
            "id": len(self._history) + 1,
            "title": title,
            "file_path": file_path,
            "url": url,
            "type": media_type,
            "quality": quality,
            "size": file_size,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Prepend to keep latest first
        self._history.insert(0, entry)
        # Cap at 500 items
        if len(self._history) > 500:
            self._history = self._history[:500]
        self.save()

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def delete(self, entry_id: int) -> bool:
        """Delete an entry by ID."""
        initial_len = len(self._history)
        self._history = [item for item in self._history if item.get("id") != entry_id]
        if len(self._history) != initial_len:
            self.save()
            return True
        return False

    def clear(self) -> None:
        """Clear all history."""
        self._history = []
        self.save()

history_manager = HistoryManager()

