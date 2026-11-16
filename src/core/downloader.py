import os
import threading
from typing import Callable, Optional, Dict, Any, List
import yt_dlp

from src.utils.logger import logger, YtDlpLoggerBridge
from src.utils.helpers import format_bytes, format_seconds, sanitize_filename
from src.utils.config import config
from src.utils.history import history_manager
from src.utils.ffmpeg_checker import FFmpegChecker

class DownloadCancelledException(Exception):
    """Raised when a download is halted by the user."""
    pass

class VideoDownloader:
    """High-performance YouTube video & playlist downloader engine."""

    def __init__(self):
        self.stop_flag = threading.Event()
        self.is_downloading = False
        self.current_title = ""
        self.current_filepath = ""

    def cancel(self):
        """Signal the running download to stop immediately."""
        self.stop_flag.set()
        logger.warning("Download cancellation requested.")

    def download(
        self,
        url: str,
        output_dir: Optional[str] = None,
        media_type: str = "video",            # 'video' or 'audio'
        resolution: str = "1080p",            # 'best', '2160p', '1440p', '1080p', '720p', '480p', '360p'
        video_format: str = "mp4",            # 'mp4', 'mkv', 'webm'
        audio_format: str = "mp3",            # 'mp3', 'm4a', 'flac', 'wav', 'opus'
        audio_bitrate: str = "320k",          # '320k', '256k', '192k', '128k'
        playlist_items: Optional[str] = None, # e.g. "1-5, 8"
        embed_thumbnail: bool = True,
        embed_metadata: bool = True,
        embed_subtitles: bool = False,
        download_subtitles: bool = False,
        subtitle_lang: str = "en",
        concurrent_fragments: int = 8,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        """
        Download media with optimal speed, progress updates, and format controls.
        """
        self.stop_flag.clear()
        self.is_downloading = True

        out_folder = output_dir or config.get("download_dir", os.path.abspath("downloads"))
        os.makedirs(out_folder, exist_ok=True)

        ffmpeg_path = FFmpegChecker.get_ffmpeg_path(config.get("custom_ffmpeg_path"))

        # Build output template
        outtmpl = os.path.join(out_folder, '%(title)s.%(ext)s')

        # Clean resolution string (e.g. '1080p' -> '1080')
        res_height = resolution.replace("p", "").strip().lower()

        # Build format selection string
        if media_type == "audio":
            format_spec = "bestaudio/best"
        else:
            if res_height == "best":
                format_spec = f"bestvideo[ext={video_format}]+bestaudio/bestvideo+bestaudio/best"
            else:
                format_spec = (
                    f"bestvideo[height<={res_height}][ext={video_format}]+bestaudio/"
                    f"bestvideo[height<={res_height}]+bestaudio/"
                    f"best[height<={res_height}]/best"
                )

        ydl_opts: Dict[str, Any] = {
            'format': format_spec,
            'outtmpl': outtmpl,
            'logger': YtDlpLoggerBridge(logger),
            'progress_hooks': [lambda d: self._progress_hook(d, progress_callback)],
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 5,
            'buffersize': 1024 * 1024,            # 1MB buffer
            'http_chunk_size': 10485760,          # 10MB chunk size
            'concurrent_fragment_downloads': max(1, concurrent_fragments),
            'js_runtimes': {'node': {}},
            'remote_components': ['ejs:github'],
            'ignoreerrors': True,                 # Continue downloading playlist even if one video fails
        }

        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        # Playlist item filter if specified
        if playlist_items and playlist_items.strip():
            ydl_opts['playlist_items'] = playlist_items.strip()

        # Postprocessors list
        postprocessors: List[Dict[str, Any]] = []

        # Audio extraction postprocessor
        if media_type == "audio":
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': audio_bitrate.replace("k", ""),
            })

        # Video container format
        if media_type == "video" and video_format:
            ydl_opts['merge_output_format'] = video_format

        # Subtitles configuration
        if download_subtitles or embed_subtitles:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            langs = [subtitle_lang] if subtitle_lang != "all" else ["all"]
            ydl_opts['subtitleslangs'] = langs

            if embed_subtitles and media_type == "video" and ffmpeg_path:
                postprocessors.append({
                    'key': 'FFmpegEmbedSubtitle',
                    'already_have_subtitle': False
                })

        # Metadata & thumbnail embedding
        if embed_metadata and ffmpeg_path:
            postprocessors.append({'key': 'FFmpegMetadata', 'add_chapters': True})

        if embed_thumbnail and ffmpeg_path:
            ydl_opts['writethumbnail'] = True
            postprocessors.append({'key': 'EmbedThumbnail'})

        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        logger.info(f"Initiating download ({media_type.upper()} | {resolution} | {concurrent_fragments} threads)")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    logger.warning("No media information retrieved.")
                    return False

                # Record in history
                if 'entries' in info:
                    # Playlist
                    for entry in info.get('entries', []):
                        if entry and entry.get('title'):
                            history_manager.add(
                                title=entry.get('title', 'Unknown'),
                                file_path=out_folder,
                                url=entry.get('webpage_url', url),
                                media_type=media_type,
                                quality=resolution if media_type == "video" else audio_bitrate
                            )
                else:
                    # Single video
                    title = info.get('title', 'Unknown')
                    filepath = ydl.prepare_filename(info)
                    if media_type == "audio":
                        base, _ = os.path.splitext(filepath)
                        filepath = f"{base}.{audio_format}"
                    history_manager.add(
                        title=title,
                        file_path=filepath,
                        url=url,
                        media_type=media_type,
                        quality=resolution if media_type == "video" else audio_bitrate,
                        file_size=format_bytes(info.get('filesize') or info.get('filesize_approx'))
                    )

            logger.success("Download process completed successfully!")
            if progress_callback:
                progress_callback({"status": "finished", "percent": 100.0})
            return True

        except DownloadCancelledException:
            logger.warning("Download aborted by user.")
            if progress_callback:
                progress_callback({"status": "cancelled", "percent": 0.0})
            return False
        except Exception as e:
            logger.error(f"Download encountered an error: {e}")
            if progress_callback:
                progress_callback({"status": "error", "error": str(e)})
            return False
        finally:
            self.is_downloading = False

    def _progress_hook(self, data: Dict[str, Any], callback: Optional[Callable[[Dict[str, Any]], None]]):
        """Process download progress and update callback."""
        if self.stop_flag.is_set():
            raise DownloadCancelledException("User requested download stop.")

        status = data.get('status')
        if not callback:
            return

        if status == 'downloading':
            total_bytes = data.get('total_bytes') or data.get('total_bytes_estimate') or 0
            downloaded_bytes = data.get('downloaded_bytes', 0)
            percent = (downloaded_bytes / total_bytes * 100.0) if total_bytes > 0 else 0.0

            speed = data.get('speed')
            eta = data.get('eta')
            filename = os.path.basename(data.get('filename', ''))

            callback({
                'status': 'downloading',
                'percent': percent,
                'filename': filename,
                'downloaded_bytes': downloaded_bytes,
                'total_bytes': total_bytes,
                'downloaded_str': format_bytes(downloaded_bytes),
                'total_str': format_bytes(total_bytes),
                'speed_str': f"{format_bytes(speed)}/s" if speed else "-- KB/s",
                'eta_str': format_seconds(eta) if eta is not None else "--:--",
                'fragment_index': data.get('fragment_index'),
                'fragment_count': data.get('fragment_count')
            })

        elif status == 'finished':
            callback({
                'status': 'processing',
                'filename': os.path.basename(data.get('filename', '')),
                'percent': 100.0,
                'message': 'Merging formats & processing audio/tags...'
            })

# Global instance for quick reuse
downloader = VideoDownloader()

