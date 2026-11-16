import os
import re
import subprocess
import threading
from typing import Callable, Optional, Dict, Any

from src.utils.ffmpeg_checker import FFmpegChecker
from src.utils.logger import logger
from src.utils.helpers import format_seconds

class MediaConverter:
    """High-performance FFmpeg converter for pristine audio and video."""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = FFmpegChecker.get_ffmpeg_path(ffmpeg_path)
        self.ffprobe_path = FFmpegChecker.get_ffprobe_path(ffmpeg_path)
        self.current_process: Optional[subprocess.Popen] = None
        self._is_cancelled = False

    def cancel(self) -> None:
        """Cancel running conversion process."""
        self._is_cancelled = True
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=2)
            except Exception:
                try:
                    self.current_process.kill()
                except Exception:
                    pass
            logger.warning("Conversion process cancelled by user.")

    def get_media_duration(self, input_path: str) -> float:
        """Get the duration of a media file in seconds using ffprobe."""
        if not self.ffprobe_path or not os.path.exists(input_path):
            return 0.0
        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                return float(res.stdout.strip())
        except Exception:
            pass
        return 0.0

    def convert_media(
        self,
        input_file: str,
        output_file: str,
        output_format: str = "mp4",
        media_type: str = "video",
        audio_codec: str = "mp3",
        audio_bitrate: str = "320k",
        video_codec: str = "libx264",
        crf: int = 20,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        """
        Convert media with pristine quality and real-time progress parsing.
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg not found. Cannot convert.")
            return False

        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return False

        self._is_cancelled = False
        duration = self.get_media_duration(input_file)

        cmd = [self.ffmpeg_path, "-y"]

        # Trimming start
        if start_time and start_time.strip():
            cmd.extend(["-ss", start_time.strip()])

        cmd.extend(["-i", input_file])

        # Trimming end
        if end_time and end_time.strip():
            cmd.extend(["-to", end_time.strip()])

        # High-Fidelity Audio / Video encoding
        if media_type == "audio":
            cmd.append("-vn")
            clean_btr = audio_bitrate.replace("k", "") + "k" if "k" not in audio_bitrate else audio_bitrate
            if output_format.lower() == "mp3":
                # LAME high quality algorithmic flag -q:a 0 avoids audio distortion
                cmd.extend(["-c:a", "libmp3lame", "-q:a", "0", "-b:a", clean_btr])
            elif output_format.lower() in ("m4a", "aac"):
                cmd.extend(["-c:a", "aac", "-b:a", clean_btr])
            elif output_format.lower() == "flac":
                cmd.extend(["-c:a", "flac"])  # Lossless
            elif output_format.lower() == "wav":
                cmd.extend(["-c:a", "pcm_s16le"])  # Uncompressed PCM
            elif output_format.lower() == "opus":
                cmd.extend(["-c:a", "libopus", "-b:a", clean_btr])
            elif output_format.lower() == "ogg":
                cmd.extend(["-c:a", "libvorbis", "-q:a", "7"])
            else:
                cmd.extend(["-b:a", clean_btr])
        else:
            # Video conversion
            if video_codec == "copy":
                cmd.extend(["-c:v", "copy"])
            else:
                # CRF 18-22 delivers visually lossless quality without pixelation
                cmd.extend(["-c:v", video_codec, "-crf", str(crf), "-preset", "medium"])

            # High-fidelity audio track for video
            cmd.extend(["-c:a", "aac", "-b:a", "320k"])

        cmd.append(output_file)

        logger.info(f"Starting conversion: {os.path.basename(input_file)} -> {os.path.basename(output_file)}")

        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            time_pattern = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
            speed_pattern = re.compile(r"speed=\s*([\d\.]+)x")

            for line in self.current_process.stderr:  # type: ignore
                if self._is_cancelled:
                    break

                match_time = time_pattern.search(line)
                match_speed = speed_pattern.search(line)

                if match_time and progress_callback and duration > 0:
                    time_str = match_time.group(1)
                    parts = time_str.split(":")
                    cur_secs = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    percent = min(100.0, (cur_secs / duration) * 100.0)
                    speed = match_speed.group(1) + "x" if match_speed else "1.0x"

                    progress_callback({
                        "percent": percent,
                        "current_time": format_seconds(cur_secs),
                        "total_time": format_seconds(duration),
                        "speed": speed,
                        "status": "converting"
                    })

            self.current_process.wait()
            success = self.current_process.returncode == 0 and not self._is_cancelled

            if success:
                logger.success(f"Conversion completed successfully: {output_file}")
                if progress_callback:
                    progress_callback({"percent": 100.0, "status": "completed"})
            else:
                if not self._is_cancelled:
                    logger.error("Conversion failed. Check ffmpeg output.")
            return success

        except Exception as e:
            logger.error(f"Error during conversion: {e}")
            return False
        finally:
            self.current_process = None
