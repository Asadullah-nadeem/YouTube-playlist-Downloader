import os
import re
import sys
import subprocess
from typing import Optional, Tuple

def format_bytes(bytes_count: Optional[float]) -> str:
    """Format bytes into a human-readable string (KB, MB, GB)."""
    if bytes_count is None or bytes_count <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(bytes_count)
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"

def format_seconds(seconds: Optional[float]) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds is None or seconds < 0:
        return "--:--"
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Sanitize filename to prevent invalid filesystem characters."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    sanitized = sanitized.strip().strip(".")
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized or "untitled"

def is_valid_url(url: str) -> bool:
    """Check if the string is a valid HTTP/HTTPS URL."""
    if not url or not isinstance(url, str):
        return False
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url.strip()) is not None

def is_playlist_url(url: str) -> bool:
    """Check if a URL points to a playlist."""
    if not url:
        return False
    url_lower = url.lower()
    return "list=" in url_lower or "/playlist" in url_lower

def verify_directory_writable(directory_path: str) -> Tuple[bool, str]:
    """Verify that the target directory exists (or can be created) and has write permissions."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        if not os.path.exists(directory_path):
            return False, f"Directory does not exist: {directory_path}"
        if not os.access(directory_path, os.W_OK):
            return False, f"No write permissions for directory: {directory_path}"
        return True, "Path valid and writable"
    except Exception as e:
        return False, f"Invalid directory path: {e}"

def open_file_or_folder(path: str) -> bool:
    """Open a file or directory in the native file manager or default application."""
    if not os.path.exists(path):
        return False
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
        return True
    except Exception:
        return False
