import os
import sys
import threading
from datetime import datetime
from typing import Callable, List, Optional

class AppLogger:
    """Thread-safe logger with support for GUI callbacks, console, and file output."""
    def __init__(self, log_file: Optional[str] = None):
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[str, str], None]] = []  # (message, level)
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

        # Console output
        if level in ("ERROR", "WARNING"):
            print(formatted, file=sys.stderr)
        else:
            print(formatted)

        # File output if configured
        if self.log_file:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.log_file)), exist_ok=True)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(formatted + "\n")
            except Exception:
                pass

        # Trigger registered callbacks
        with self._lock:
            callbacks = list(self._callbacks)
        for cb in callbacks:
            try:
                cb(formatted, level)
            except Exception as e:
                print(f"Error in log callback: {e}", file=sys.stderr)

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

    # yt-dlp logger interface compatibility
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
        # Filter noisy debug messages if desired
        if not msg.startswith("[debug]"):
            self.logger.debug(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)


# Global logger instance
logger = AppLogger()

