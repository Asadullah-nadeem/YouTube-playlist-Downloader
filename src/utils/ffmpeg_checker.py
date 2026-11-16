import os
import shutil
import subprocess
from typing import Dict, Optional, Tuple

class FFmpegChecker:
    """Detects, inspects, and validates FFmpeg and FFprobe installations."""

    @staticmethod
    def get_ffmpeg_path(custom_path: Optional[str] = None) -> Optional[str]:
        """Find the ffmpeg executable from custom path, PATH, or common locations."""
        if custom_path and os.path.exists(custom_path):
            if os.path.isdir(custom_path):
                binary = os.path.join(custom_path, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
                if os.path.isfile(binary) and os.access(binary, os.X_OK):
                    return binary
            elif os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
                return custom_path

        # Check standard PATH
        found = shutil.which("ffmpeg")
        if found:
            return found

        # Common fallback locations
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, ".local", "bin", "ffmpeg"),
            "/usr/local/bin/ffmpeg",
            "/usr/bin/ffmpeg",
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"
        ]
        for path in candidates:
            if os.path.isfile(path) and (os.name == "nt" or os.access(path, os.X_OK)):
                return path

        return None

    @staticmethod
    def get_ffprobe_path(custom_path: Optional[str] = None) -> Optional[str]:
        """Find the ffprobe executable."""
        if custom_path and os.path.exists(custom_path):
            if os.path.isdir(custom_path):
                binary = os.path.join(custom_path, "ffprobe.exe" if os.name == "nt" else "ffprobe")
                if os.path.isfile(binary) and os.access(binary, os.X_OK):
                    return binary
            elif os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
                return custom_path

        found = shutil.which("ffprobe")
        if found:
            return found

        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, ".local", "bin", "ffprobe"),
            "/usr/local/bin/ffprobe",
            "/usr/bin/ffprobe",
            "C:\\ffmpeg\\bin\\ffprobe.exe",
            "C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe"
        ]
        for path in candidates:
            if os.path.isfile(path) and (os.name == "nt" or os.access(path, os.X_OK)):
                return path

        return None

    @classmethod
    def check_ffmpeg(cls, custom_path: Optional[str] = None) -> Tuple[bool, str]:
        """Check if FFmpeg is installed and get its version string."""
        path = cls.get_ffmpeg_path(custom_path)
        if not path:
            return False, "FFmpeg was not found. Please install FFmpeg or set its path in Settings."
        try:
            res = subprocess.run([path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if res.returncode == 0:
                first_line = res.stdout.splitlines()[0] if res.stdout else "FFmpeg present"
                return True, f"Found: {first_line} ({path})"
            return False, f"FFmpeg returned error code {res.returncode}"
        except Exception as e:
            return False, f"Failed to execute FFmpeg: {e}"

    @classmethod
    def get_codecs_info(cls, custom_path: Optional[str] = None) -> Dict[str, bool]:
        """Check availability of common encoders."""
        path = cls.get_ffmpeg_path(custom_path)
        codecs = {
            "libmp3lame": False,
            "libx264": False,
            "libx265": False,
            "libopus": False,
            "aac": False
        }
        if not path:
            return codecs
        try:
            res = subprocess.run([path, "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            out = res.stdout.lower()
            for codec in codecs.keys():
                codecs[codec] = codec in out
        except Exception:
            pass
        return codecs

