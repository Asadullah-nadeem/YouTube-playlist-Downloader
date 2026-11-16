import json
import os
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "download_dir": os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "downloads")),
    "max_concurrent_fragments": 8,
    "preferred_resolution": "1080p",
    "preferred_video_format": "mp4",
    "preferred_audio_format": "mp3",
    "preferred_audio_bitrate": "320k",
    "embed_thumbnail": True,
    "embed_metadata": True,
    "embed_subtitles": False,
    "download_subtitles": False,
    "subtitles_language": "en",
    "auto_create_playlist_folder": True,
    "theme": "dark",
    "color_theme": "blue",
    "custom_ffmpeg_path": "",
    "js_runtime": "node",
    "keep_video_after_conversion": True
}

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

class ConfigManager:
    """Manages application settings persisted in a JSON file."""
    def __init__(self, filepath: str = CONFIG_FILE):
        self.filepath = filepath
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load settings from config file or initialize with defaults."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config.update(data)
            except Exception as e:
                print(f"Error loading config, using defaults: {e}")
        else:
            self.save()
        return self._config

    def save(self) -> bool:
        """Save settings to config file."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        self._config[key] = value
        self.save()

    def get_all(self) -> Dict[str, Any]:
        """Return a copy of all configuration options."""
        return self._config.copy()

    def reset_to_defaults(self) -> None:
        """Reset all configuration values to defaults."""
        self._config = DEFAULT_CONFIG.copy()
        self.save()

# Global config instance
config = ConfigManager()

