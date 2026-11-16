import yt_dlp
from typing import Dict, List, Any, Optional
from src.utils.logger import logger
from src.utils.helpers import format_seconds

class PlaylistManager:
    """Handles playlist metadata inspection, item parsing, and range filtering."""

    @staticmethod
    def get_playlist_info(playlist_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract playlist metadata and all video entries without downloading files.
        """
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'js_runtimes': {'node': {}},
            'remote_components': ['ejs:github'],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                if not info:
                    return None

                # Handle single video URL passed accidentally
                if 'entries' not in info:
                    return {
                        'is_playlist': False,
                        'title': info.get('title', 'Single Video'),
                        'uploader': info.get('uploader', 'Unknown Channel'),
                        'thumbnail': info.get('thumbnail', ''),
                        'count': 1,
                        'videos': [{
                            'index': 1,
                            'id': info.get('id', ''),
                            'title': info.get('title', 'Unknown Title'),
                            'url': info.get('webpage_url', playlist_url),
                            'duration': format_seconds(info.get('duration')),
                            'thumbnail': info.get('thumbnail', '')
                        }]
                    }

                entries = list(info.get('entries', []))
                parsed_videos = []
                for idx, entry in enumerate(entries, start=1):
                    if not entry:
                        continue
                    video_id = entry.get('id', '')
                    title = entry.get('title', f"Video {idx}")
                    duration = entry.get('duration')
                    url = entry.get('url') or f"https://www.youtube.com/watch?v={video_id}"
                    thumbnail = entry.get('thumbnail') or (
                        entry.get('thumbnails', [{}])[-1].get('url', '') if entry.get('thumbnails') else ''
                    )

                    parsed_videos.append({
                        'index': idx,
                        'id': video_id,
                        'title': title,
                        'url': url,
                        'duration': format_seconds(duration) if duration else "--:--",
                        'thumbnail': thumbnail
                    })

                return {
                    'is_playlist': True,
                    'title': info.get('title', 'Untitled Playlist'),
                    'uploader': info.get('uploader') or info.get('channel', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'count': len(parsed_videos),
                    'videos': parsed_videos
                }

        except Exception as e:
            logger.error(f"Failed to inspect playlist: {e}")
            return None

    @staticmethod
    def parse_range_string(range_str: str, max_count: int) -> List[int]:
        """
        Parses user ranges like "1-5, 8, 12-15" into a 1-based index list.
        """
        if not range_str or not range_str.strip():
            return list(range(1, max_count + 1))

        indices = set()
        parts = [p.strip() for p in range_str.split(",") if p.strip()]

        for part in parts:
            if "-" in part:
                try:
                    start_str, end_str = part.split("-", 1)
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    for i in range(max(1, start), min(max_count, end) + 1):
                        indices.add(i)
                except ValueError:
                    continue
            else:
                try:
                    val = int(part)
                    if 1 <= val <= max_count:
                        indices.add(val)
                except ValueError:
                    continue

        return sorted(list(indices))

