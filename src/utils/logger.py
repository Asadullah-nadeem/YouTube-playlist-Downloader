import os
import sys
import threading
from datetime import datetime
from typing import Callable, List, Optional

class AppLogger:
    """Thread-safe logger with bounded memory and GUI callback support."""
    def __init__(self, log_file: Optional[str] = None):
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[str, str], None]] = []
        self.log_file = log_file

    def add_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add a callback function (msg: str, level: str) -> None for GUI updates."""
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str, str], None]) -> None:
        """Remove a previously added callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def _emit(self, message: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"

        if level in ("ERROR", "WARNING"):
            print(formatted, file=sys.stderr)
        else:
            print(formatted)

        if self.log_file:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.log_file)), exist_ok=True)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(formatted + "\n")
            except Exception:
                pass

        with self._lock:
            callbacks = list(self._callbacks)
        for cb in callbacks:
            try:
                cb(formatted, level)
            except Exception:
                pass

    def info(self, msg: str) -> None:
        self._emit(msg, "INFO")

    def success(self, msg: str) -> None:
        self._emit(msg, "SUCCESS")

    def warning(self, msg: str) -> None:
        self._emit(msg, "WARNING")

    def error(self, msg: str) -> None:
        self._emit(msg, "ERROR")

    def debug(self, msg: str) -> None:
        self._emit(msg, "DEBUG")

    def write(self, msg: str) -> None:
        msg = msg.strip()
        if msg:
            self.info(msg)

    def flush(self) -> None:
        pass


class YtDlpLoggerBridge:
    """Bridge for yt-dlp logger option to forward to AppLogger."""
    def __init__(self, logger: AppLogger):
        self.logger = logger

    def debug(self, msg: str) -> None:
        # Suppress verbose debug chatter to conserve system resources
        if not msg.startswith("[debug]") and not msg.startswith("[download] Destination:"):
            self.logger.debug(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

logger = AppLogger()
