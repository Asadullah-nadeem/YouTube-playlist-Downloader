import os
import yt_dlp
from typing import Dict, List, Any, Optional
from src.utils.logger import logger
from src.utils.ffmpeg_checker import FFmpegChecker

# Common subtitle languages for quick selection
POPULAR_LANGUAGES = [
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("hi", "Hindi"),
    ("ar", "Arabic"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("zh-Hans", "Chinese (Simplified)"),
    ("it", "Italian"),
    ("tr", "Turkish"),
    ("id", "Indonesian"),
    ("vi", "Vietnamese"),
    ("all", "All Available Languages")
]

class SubtitleManager:
    """Manages subtitle extraction, language listing, and caption downloading."""

    @staticmethod
    def get_available_subtitles(url: str) -> Dict[str, Any]:
        """
        Fetch available manual and automatic captions for a given video URL.
        Returns a dict with 'manual': [...], 'auto': [...]
        """
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'js_runtimes': {'node': {}},
            'remote_components': ['ejs:github'],
        }
        manual_subs = []
        auto_subs = []

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return {"manual": [], "auto": []}

                subtitles = info.get('subtitles', {})
                for lang_code, formats in subtitles.items():
                    name = formats[0].get('name', lang_code) if formats else lang_code
                    manual_subs.append({"code": lang_code, "name": name})

                auto_captions = info.get('automatic_captions', {})
                for lang_code, formats in auto_captions.items():
                    name = formats[0].get('name', lang_code) if formats else lang_code
                    auto_subs.append({"code": lang_code, "name": name})

        except Exception as e:
            logger.error(f"Failed to fetch subtitles: {e}")

        return {"manual": manual_subs, "auto": auto_subs}

    @staticmethod
    def download_subtitles_only(
        url: str,
        output_dir: str,
        language_code: str = "en",
        sub_format: str = "srt",
        include_auto: bool = True
    ) -> bool:
        """Download subtitle files (.srt or .vtt) for a video without downloading the video."""
        ffmpeg_path = FFmpegChecker.get_ffmpeg_path()
        langs = [language_code] if language_code != "all" else ["all"]

        ydl_opts: Dict[str, Any] = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': include_auto,
            'subtitleslangs': langs,
            'subtitlesformat': sub_format,
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegSubtitlesConvertor',
                'format': sub_format,
            }] if ffmpeg_path else [],
            'js_runtimes': {'node': {}},
            'remote_components': ['ejs:github'],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.success(f"Subtitles downloaded to: {output_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to download subtitles: {e}")
            return False

