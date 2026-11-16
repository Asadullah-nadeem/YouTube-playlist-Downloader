import re
from typing import Dict, Any, List, Optional

PLATFORMS_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "youtube",
        "name": "YouTube",
        "tag": "[YouTube]",
        "color": "#D32F2F",
        "pattern": r"(?:https?://)?(?:www\.|m\.|music\.)?(?:youtube\.com/(?:watch\?|playlist\?|shorts/|embed/|live/|v/)|youtu\.be/)",
        "media_types": ["Video (4K/1080p)", "Audio (MP3)", "Playlist", "Shorts"],
        "supports_subtitles": True,
        "supports_playlists": True,
        "default_type": "video",
        "description": "YouTube Videos, Shorts, Playlists & Music"
    },
    {
        "id": "instagram",
        "name": "Instagram",
        "tag": "[Instagram]",
        "color": "#C13584",
        "pattern": r"(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/(?:p|reel|reels|tv|stories)/",
        "media_types": ["Reels", "Posts", "Stories", "Audio"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Instagram Reels, Posts, and Videos"
    },
    {
        "id": "tiktok",
        "name": "TikTok",
        "tag": "[TikTok]",
        "color": "#00838F",
        "pattern": r"(?:https?://)?(?:www\.|vm\.|vt\.|m\.)?tiktok\.com/",
        "media_types": ["Videos (No Watermark)", "Audio"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "TikTok Short Videos & Sounds"
    },
    {
        "id": "facebook",
        "name": "Facebook",
        "tag": "[Facebook]",
        "color": "#1565C0",
        "pattern": r"(?:https?://)?(?:www\.|m\.|web\.)?(?:facebook\.com|fb\.watch|fb\.com)/",
        "media_types": ["Reels", "Watch Videos", "Feed Clips"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Facebook Reels, Watch & Feed Videos"
    },
    {
        "id": "twitter",
        "name": "Twitter / X",
        "tag": "[Twitter/X]",
        "color": "#37474F",
        "pattern": r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/.+/status/\d+",
        "media_types": ["Post Videos", "GIFs", "Audio"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Twitter / X Video Clips & Media Posts"
    },
    {
        "id": "reddit",
        "name": "Reddit",
        "tag": "[Reddit]",
        "color": "#E64A19",
        "pattern": r"(?:https?://)?(?:www\.|old\.|v\.)?(?:reddit\.com/r/.+/comments/|redd\.it/|v\.redd\.it/)",
        "media_types": ["Post Videos with Audio", "GIFs"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Reddit Video Posts (Merged Audio + Video)"
    },
    {
        "id": "pinterest",
        "name": "Pinterest",
        "tag": "[Pinterest]",
        "color": "#AD1457",
        "pattern": r"(?:https?://)?(?:www\.|[a-z]{2}\.)?(?:pinterest\.[a-z.]+/pin/|pin\.it/)",
        "media_types": ["Video Pins", "Stories"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Pinterest Video Pins & Idea Pins"
    },
    {
        "id": "twitch",
        "name": "Twitch",
        "tag": "[Twitch]",
        "color": "#6A1B9A",
        "pattern": r"(?:https?://)?(?:www\.|clips\.)?twitch\.tv/",
        "media_types": ["Clips", "VODs", "Highlights"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Twitch Clips, Broadcast VODs & Highlights"
    },
    {
        "id": "threads",
        "name": "Threads",
        "tag": "[Threads]",
        "color": "#263238",
        "pattern": r"(?:https?://)?(?:www\.)?threads\.net/@.+/post/",
        "media_types": ["Video Posts"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Threads by Instagram Video Posts"
    },
    {
        "id": "vimeo",
        "name": "Vimeo",
        "tag": "[Vimeo]",
        "color": "#0277BD",
        "pattern": r"(?:https?://)?(?:www\.|player\.)?vimeo\.com/",
        "media_types": ["HD Videos", "Audio"],
        "supports_subtitles": True,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Vimeo High-Definition Videos"
    },
    {
        "id": "dailymotion",
        "name": "Dailymotion",
        "tag": "[Dailymotion]",
        "color": "#0D47A1",
        "pattern": r"(?:https?://)?(?:www\.)?(?:dailymotion\.com/video/|dai\.ly/)",
        "media_types": ["Videos", "Audio"],
        "supports_subtitles": True,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Dailymotion Videos & Shows"
    },
    {
        "id": "soundcloud",
        "name": "SoundCloud",
        "tag": "[SoundCloud]",
        "color": "#E65100",
        "pattern": r"(?:https?://)?(?:www\.|m\.)?soundcloud\.com/",
        "media_types": ["Audio (Tracks)", "Playlists", "Albums"],
        "supports_subtitles": False,
        "supports_playlists": True,
        "default_type": "audio",
        "description": "SoundCloud Music Tracks & Playlists"
    },
    {
        "id": "bandcamp",
        "name": "Bandcamp",
        "tag": "[Bandcamp]",
        "color": "#00838F",
        "pattern": r"(?:https?://)?[a-zA-Z0-9-]+\.bandcamp\.com/(?:track|album)/",
        "media_types": ["Lossless Audio", "MP3 Tracks"],
        "supports_subtitles": False,
        "supports_playlists": True,
        "default_type": "audio",
        "description": "Bandcamp Artist Music & Albums"
    },
    {
        "id": "linkedin",
        "name": "LinkedIn",
        "tag": "[LinkedIn]",
        "color": "#004BA0",
        "pattern": r"(?:https?://)?(?:www\.)?linkedin\.com/(?:posts/|feed/update/|learning/)",
        "media_types": ["Professional Videos", "Learning Clips"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "LinkedIn Video Posts & Clips"
    },
    {
        "id": "kick",
        "name": "Kick",
        "tag": "[Kick]",
        "color": "#2E7D32",
        "pattern": r"(?:https?://)?(?:www\.)?kick\.com/",
        "media_types": ["Clips", "VODs", "Streams"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Kick Streaming Clips & Videos"
    },
    {
        "id": "rumble",
        "name": "Rumble",
        "tag": "[Rumble]",
        "color": "#558B2F",
        "pattern": r"(?:https?://)?(?:www\.)?rumble\.com/",
        "media_types": ["HD Videos", "Audio"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Rumble Video Platform"
    },
    {
        "id": "bilibili",
        "name": "Bilibili",
        "tag": "[Bilibili]",
        "color": "#00838F",
        "pattern": r"(?:https?://)?(?:www\.)?(?:bilibili\.com/video/|b23\.tv/)",
        "media_types": ["HD Videos", "Anime", "Audio"],
        "supports_subtitles": True,
        "supports_playlists": True,
        "default_type": "video",
        "description": "Bilibili Animation & Video Community"
    },
    {
        "id": "bluesky",
        "name": "Bluesky",
        "tag": "[Bluesky]",
        "color": "#0288D1",
        "pattern": r"(?:https?://)?(?:www\.)?bsky\.app/profile/.+/post/",
        "media_types": ["Video Posts"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Bluesky Social Video Posts"
    },
    {
        "id": "tumblr",
        "name": "Tumblr",
        "tag": "[Tumblr]",
        "color": "#263238",
        "pattern": r"(?:https?://)?(?:www\.)?(?:tumblr\.com|.+\.tumblr\.com)/post/",
        "media_types": ["Video Posts", "Audio"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Tumblr Video & Audio Posts"
    },
    {
        "id": "loom",
        "name": "Loom",
        "tag": "[Loom]",
        "color": "#4527A0",
        "pattern": r"(?:https?://)?(?:www\.)?loom\.com/share/",
        "media_types": ["Screen Recordings", "Presentations"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Loom Screen & Video Recordings"
    },
    {
        "id": "streamable",
        "name": "Streamable",
        "tag": "[Streamable]",
        "color": "#00838F",
        "pattern": r"(?:https?://)?(?:www\.)?streamable\.com/",
        "media_types": ["Short Clips", "Highlights"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Streamable Instant Video Hosting"
    },
    {
        "id": "mixcloud",
        "name": "Mixcloud",
        "tag": "[Mixcloud]",
        "color": "#4A148C",
        "pattern": r"(?:https?://)?(?:www\.)?mixcloud\.com/",
        "media_types": ["DJ Mixes", "Radio Shows", "Podcasts"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "audio",
        "description": "Mixcloud DJ Mixes & Radio Podcasts"
    },
    {
        "id": "ted",
        "name": "TED Talks",
        "tag": "[TED]",
        "color": "#C62828",
        "pattern": r"(?:https?://)?(?:www\.)?ted\.com/talks/",
        "media_types": ["Keynote Talks", "Subtitles in 40+ langs"],
        "supports_subtitles": True,
        "supports_playlists": False,
        "default_type": "video",
        "description": "TED Talks Presentations & Transcripts"
    },
    {
        "id": "vk",
        "name": "VKontakte",
        "tag": "[VK]",
        "color": "#283593",
        "pattern": r"(?:https?://)?(?:www\.|m\.)?vk\.com/(?:video|clip)",
        "media_types": ["Clips", "Videos", "Music"],
        "supports_subtitles": False,
        "supports_playlists": True,
        "default_type": "video",
        "description": "VK Video, Clips & Music"
    },
    {
        "id": "likee",
        "name": "Likee",
        "tag": "[Likee]",
        "color": "#AD1457",
        "pattern": r"(?:https?://)?(?:www\.|l\.)?likee\.(?:video|com)/",
        "media_types": ["Short Videos", "Sounds"],
        "supports_subtitles": False,
        "supports_playlists": False,
        "default_type": "video",
        "description": "Likee Short Videos"
    }
]

GENERIC_PLATFORM: Dict[str, Any] = {
    "id": "generic",
    "name": "Direct Media Link",
    "tag": "[Direct Link]",
    "color": "#1565C0",
    "media_types": ["Video", "Audio"],
    "supports_subtitles": False,
    "supports_playlists": False,
    "default_type": "video",
    "description": "Universal Media Stream"
}

class PlatformDetector:
    """Detects social media & video platforms from URLs with zero emojis."""

    @classmethod
    def detect(cls, url: str) -> Optional[Dict[str, Any]]:
        if not url or not isinstance(url, str):
            return None
        clean_url = url.strip()
        if not clean_url:
            return None

        for p in PLATFORMS_REGISTRY:
            if re.search(p["pattern"], clean_url, re.IGNORECASE):
                res = p.copy()
                if p["id"] == "instagram":
                    if "/reel" in clean_url:
                        res["name"] = "Instagram Reel"
                        res["tag"] = "[Instagram Reel]"
                    elif "/stories" in clean_url:
                        res["name"] = "Instagram Story"
                        res["tag"] = "[Instagram Story]"
                elif p["id"] == "youtube":
                    if "/shorts/" in clean_url:
                        res["name"] = "YouTube Short"
                        res["tag"] = "[YouTube Short]"
                    elif "playlist" in clean_url or "list=" in clean_url:
                        res["name"] = "YouTube Playlist"
                        res["tag"] = "[YouTube Playlist]"
                elif p["id"] == "facebook":
                    if "/reel" in clean_url or "fb.watch" in clean_url:
                        res["name"] = "Facebook Reel"
                        res["tag"] = "[Facebook Reel]"
                return res

        if clean_url.startswith("http://") or clean_url.startswith("https://"):
            return GENERIC_PLATFORM.copy()

        return None

    @classmethod
    def get_all_platforms(cls) -> List[Dict[str, Any]]:
        return list(PLATFORMS_REGISTRY)
