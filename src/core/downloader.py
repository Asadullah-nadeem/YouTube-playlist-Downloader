import os
import threading
from typing import Callable, Optional, Dict, Any, List
import yt_dlp

from src.utils.logger import logger, YtDlpLoggerBridge
from src.utils.helpers import format_bytes, format_seconds, sanitize_filename, verify_directory_writable
from src.utils.config import config
from src.utils.history import history_manager
from src.utils.ffmpeg_checker import FFmpegChecker
from src.core.platform_detector import PlatformDetector

class DownloadCancelledException(Exception):
    """Raised when a download is halted by the user."""
    pass

class VideoDownloader:
    """
    Universal high-performance media downloader supporting 25+ social platforms.
    Engineered with lossless remuxing, high-bitrate audio, and playlist progress counters.
    """

    def __init__(self):
        self.stop_flag = threading.Event()
        self.is_downloading = False
        self.current_title = ""
        self.current_filepath = ""

        # Batch / Playlist tracking
        self.current_playlist_index = 0
        self.total_playlist_count = 0
        self.completed_items_count = 0
        self.failed_items_count = 0
        self.is_playlist_active = False

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
        Download media with optimal speed, progress updates, and pristine audio/video quality.
        """
        self.stop_flag.clear()
        self.is_downloading = True
        self.current_playlist_index = 0
        self.total_playlist_count = 0
        self.completed_items_count = 0
        self.failed_items_count = 0
        self.is_playlist_active = False

        out_folder = output_dir or config.get("download_dir", os.path.abspath("downloads"))
        ok, err = verify_directory_writable(out_folder)
        if not ok:
            logger.error(f"Cannot write to output folder: {err}")
            if progress_callback:
                progress_callback({"status": "error", "error": f"Invalid download path: {err}"})
            self.is_downloading = False
            return False

        ffmpeg_path = FFmpegChecker.get_ffmpeg_path(config.get("custom_ffmpeg_path"))

        # Detect platform for targeted optimization
        platform = PlatformDetector.detect(url)
        platform_name = platform["name"] if platform else "Universal Media"
        platform_id = platform["id"] if platform else "generic"

        # Build output template
        outtmpl = os.path.join(out_folder, '%(title)s.%(ext)s')

        # Clean resolution string (e.g. '1080p' -> '1080')
        res_height = resolution.replace("p", "").strip().lower()

        # Build format selection string to guarantee NO pixelation / crackling
        if media_type == "audio":
            # Select highest quality audio stream directly from source
            format_spec = "bestaudio[acodec!=none]/bestaudio/best"
        else:
            if res_height == "best":
                format_spec = f"bestvideo+bestaudio/best"
            else:
                # Priority: best resolution video + best audio stream with fallback
                format_spec = (
                    f"bestvideo[height<={res_height}]+bestaudio/"
                    f"best[height<={res_height}]/"
                    f"bestvideo+bestaudio/best"
                )

        ydl_opts: Dict[str, Any] = {
            'format': format_spec,
            'outtmpl': outtmpl,
            'logger': YtDlpLoggerBridge(logger),
            'progress_hooks': [lambda d: self._progress_hook(d, progress_callback)],
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 5,
            'buffersize': 1024 * 1024,
            'http_chunk_size': 10485760,
            'concurrent_fragment_downloads': max(1, min(16, concurrent_fragments)),
            'ignoreerrors': True,
        }

        # Format sort prioritizes resolution and audio quality without compression artifacts
        if media_type == "video" and res_height != "best":
            ydl_opts['format_sort'] = [f"res:{res_height}", "fps", "br", "size"]

        # Enable JS runtimes for YouTube challenge solving
        if platform_id == "youtube":
            ydl_opts['js_runtimes'] = {'node': {}}
            ydl_opts['remote_components'] = ['ejs:github']

        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        # Playlist item filter if specified
        if playlist_items and playlist_items.strip():
            ydl_opts['playlist_items'] = playlist_items.strip()

        # Postprocessors list
        postprocessors: List[Dict[str, Any]] = []

        # Audio extraction postprocessor with pristine parameters (320kbps high fidelity)
        if media_type == "audio":
            clean_btr = audio_bitrate.replace("k", "").strip() or "320"
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': clean_btr,
                'nopostoverwrites': False,
            })

        # Video container format merge (lossless remuxing)
        if media_type == "video" and video_format:
            ydl_opts['merge_output_format'] = video_format

        # Subtitles configuration
        if (download_subtitles or embed_subtitles) and platform.get("supports_subtitles", True):
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

        logger.info(f"Starting {platform_name} download ({media_type.upper()} | {resolution} | {concurrent_fragments} conn)")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    logger.warning(f"Could not retrieve media info from {platform_name}.")
                    return False

                # Record in history
                if 'entries' in info:
                    entries = [e for e in info.get('entries', []) if e]
                    total_count = len(entries)
                    for idx, entry in enumerate(entries, start=1):
                        if entry and entry.get('title'):
                            history_manager.add(
                                title=entry.get('title', 'Unknown'),
                                file_path=out_folder,
                                url=entry.get('webpage_url', url),
                                media_type=media_type,
                                quality=resolution if media_type == "video" else audio_bitrate
                            )
                else:
                    title = info.get('title', f"{platform_name} Media")
                    filepath = ydl.prepare_filename(info)
                    if media_type == "audio":
                        base, _ = os.path.splitext(filepath)
                        filepath = f"{base}.{audio_format}"
                    history_manager.add(
                        title=title,
                        file_path=filepath,
                        url=url,
                        media_type=f"{platform_name} {media_type}",
                        quality=resolution if media_type == "video" else audio_bitrate,
                        file_size=format_bytes(info.get('filesize') or info.get('filesize_approx'))
                    )

            logger.success(f"{platform_name} download completed successfully.")
            if progress_callback:
                progress_callback({
                    "status": "finished",
                    "percent": 100.0,
                    "playlist_index": self.current_playlist_index,
                    "playlist_total": self.total_playlist_count,
                    "completed_count": self.completed_items_count
                })
            return True

        except DownloadCancelledException:
            logger.warning("Download aborted by user.")
            if progress_callback:
                progress_callback({"status": "cancelled", "percent": 0.0})
            return False
        except Exception as e:
            logger.error(f"Download encountered an error on {platform_name}: {e}")
            if progress_callback:
                progress_callback({"status": "error", "error": str(e)})
            return False
        finally:
            self.is_downloading = False

    def _progress_hook(self, data: Dict[str, Any], callback: Optional[Callable[[Dict[str, Any]], None]]):
        """Process download progress and update callback with exact playlist counters."""
        if self.stop_flag.is_set():
            raise DownloadCancelledException("User requested download stop.")

        status = data.get('status')
        info_dict = data.get('info_dict', {}) or {}

        # Extract playlist counters if available
        pl_index = info_dict.get('playlist_index') or info_dict.get('playlist_autonumber')
        pl_count = info_dict.get('n_entries') or info_dict.get('playlist_count')

        if pl_index:
            self.current_playlist_index = int(pl_index)
            self.is_playlist_active = True
        if pl_count:
            self.total_playlist_count = int(pl_count)

        if not callback:
            return

        if status == 'downloading':
            total_bytes = data.get('total_bytes') or data.get('total_bytes_estimate') or 0
            downloaded_bytes = data.get('downloaded_bytes', 0)
            percent = (downloaded_bytes / total_bytes * 100.0) if total_bytes > 0 else 0.0

            speed = data.get('speed')
            eta = data.get('eta')
            filename = os.path.basename(data.get('filename', ''))
            cur_title = info_dict.get('title') or filename

            callback({
                'status': 'downloading',
                'percent': percent,
                'filename': filename,
                'title': cur_title,
                'downloaded_bytes': downloaded_bytes,
                'total_bytes': total_bytes,
                'downloaded_str': format_bytes(downloaded_bytes),
                'total_str': format_bytes(total_bytes),
                'speed_str': f"{format_bytes(speed)}/s" if speed else "-- KB/s",
                'eta_str': format_seconds(eta) if eta is not None else "--:--",
                'playlist_index': self.current_playlist_index,
                'playlist_total': self.total_playlist_count,
                'completed_count': self.completed_items_count
            })

        elif status == 'finished':
            self.completed_items_count += 1
            filename = os.path.basename(data.get('filename', ''))
            cur_title = info_dict.get('title') or filename
            callback({
                'status': 'processing',
                'filename': filename,
                'title': cur_title,
                'percent': 100.0,
                'message': 'Merging media streams losslessly...',
                'playlist_index': self.current_playlist_index,
                'playlist_total': self.total_playlist_count,
                'completed_count': self.completed_items_count
            })

downloader = VideoDownloader()
