# Media Studio Pro - Universal Downloader & Converter

A high-performance desktop suite, command-line interface, and web dashboard for downloading and converting media from **Instagram, TikTok, YouTube, Facebook, Twitter/X, Reddit, and 25+ platforms**.

Engineered with **CustomTkinter**, **yt-dlp**, and **FFmpeg** for **instant platform auto-detection on paste**, multi-fragment accelerated downloading, lossless video remuxing, high-bitrate audio extraction (320kbps), and exact playlist batch item counting.

---

## Key Capabilities

### 1. Instant Platform Auto-Detection on Paste
- Paste or type any link into the URL field. The application instantly detects whether it is an **Instagram Reel**, a **TikTok video**, a **Facebook Reel**, a **Twitter/X clip**, a **Reddit video**, or a **YouTube playlist**.
- Automatically applies optimal container settings (e.g. MP4 for Reels, MP3 for SoundCloud) without requiring manual adjustments.

### 2. High-Fidelity Audio & Video (No Distortion or Pixelation)
- **Video Quality**: Merges the highest quality DASH video stream with source audio losslessly via FFmpeg stream copy (`merge_output_format: mp4`), avoiding re-compression artifacts or pixelation.
- **Audio Quality**: Extracts high-fidelity audio up to **320 kbps MP3** (LAME algorithmic quality preset `-q:a 0`), **M4A / AAC**, or lossless **FLAC / WAV** without volume clipping or crackling.
- **Resolution Control**: Choose **Best Available**, **4K (2160p)**, **2K (1440p)**, **1080p Full HD**, **720p HD**, **480p**, or **360p**.

### 3. Exact Batch & Playlist Progress Counting
- When downloading playlists or batch items (even hundreds of videos), the application provides **dual progress tracking**:
  - **Overall Batch Progress**: Displays exact counters (e.g. `Item 14 of 150 Completed (9.3%)`).
  - **Active File Progress**: Displays live percentage, download speed (MB/s), countdown ETA, and transferred bytes.
  - **Library Statistics**: Displays cumulative totals of videos downloaded, audio tracks, and overall storage used.

### 4. Low System Resource Consumption
- Memory bounded: log console buffer is capped to prevent memory growth during massive playlists.
- Thread-safe, non-blocking asynchronous workers ensure smooth UI performance without freezing or high CPU usage.

### 5. Standard Windows & Linux Download Destination
- Defaults to your operating system's standard Downloads directory (`C:\Users\<Username>\Downloads` on Windows, `~/Downloads` on Linux/macOS).
- **First-Time Setup Prompt**: On first launch, a prominent banner asks you to verify or customize your download folder in Settings.
- Pre-flight write permission checks ensure no download fails due to missing or locked paths.

---

## Supported Social & Video Platforms (25+)

| Platform | Tag | Supported Formats |
|---|---|---|
| **Instagram** | [Instagram] | Reels, Posts, Stories, IGTV (High Quality MP4) |
| **TikTok** | [TikTok] | Videos without watermark, Original Audio |
| **YouTube** | [YouTube] | Videos (4K, 2K, 1080p, 720p), Shorts, Playlists, Music |
| **Facebook** | [Facebook] | Reels, Watch, Public Feed Clips |
| **Twitter / X** | [Twitter/X] | Video Clips, GIFs, Audio |
| **Reddit** | [Reddit] | Video Posts (Auto-merged audio + video DASH streams) |
| **Pinterest** | [Pinterest] | Video Pins, Idea Pins |
| **Twitch** | [Twitch] | Stream Clips, Broadcast VODs, Highlights |
| **Threads** | [Threads] | Video Posts |
| **Vimeo** | [Vimeo] | High-Definition Videos (1080p / 4K) |
| **SoundCloud** | [SoundCloud] | High-Quality Audio Tracks, Playlists, Albums |
| **Bandcamp** | [Bandcamp] | Lossless Audio (FLAC/WAV), MP3 Tracks |
| **Dailymotion** | [Dailymotion] | HD Videos & Shows |
| **LinkedIn** | [LinkedIn] | Professional Videos & Learning Clips |
| **Kick** | [Kick] | Live Stream Clips & VODs |
| **Rumble** | [Rumble] | HD Videos & Audio |
| **Bilibili** | [Bilibili] | HD Videos, Anime & Multi-part clips |
| **Bluesky** | [Bluesky] | Video Posts |
| **Tumblr** | [Tumblr] | Video & Audio Posts |
| **Loom** | [Loom] | Screen Recordings & Presentations |
| **Streamable** | [Streamable] | Fast Highlights & Short Clips |
| **Mixcloud** | [Mixcloud] | DJ Mixes, Radio Shows & Podcasts |
| **TED Talks** | [TED] | Keynote Talks & Subtitles in 40+ languages |
| **VKontakte** | [VK] | Videos, Clips & Music |
| **Likee** | [Likee] | Short Videos & Sounds |
| **Direct Media**| [Direct Link]| Direct MP4, M3U8, or web video streams |

---

## Clean Project Architecture

The root directory contains only the essential entry points; all logic is cleanly organized in `src/`:

```
YouTube-playlist-Downloader/
├── main.py                     # Primary Application Entry Point (Desktop GUI, CLI, Web)
├── build_exe.py                # Standalone Windows .EXE builder
├── build_exe.bat               # 1-Click Windows batch script to create .EXE
├── requirements.txt            # Dependency list
├── run.sh                      # Linux launcher script
├── setup.sh                    # Linux automated setup script
├── README.md                   # Complete documentation
└── src/                        # Modular package structure
    ├── core/
    │   ├── downloader.py       # High-fidelity download engine (no distortion, playlist counters)
    │   ├── converter.py        # FFmpeg media converter & audio extractor
    │   ├── playlist.py         # Playlist inspector & item selector
    │   ├── subtitles.py        # Subtitle scanner & multi-language handler
    │   └── platform_detector.py# 25+ platform detector (zero emojis)
    ├── ui/
    │   ├── app.py              # Main CustomTkinter UI (clean executive styling)
    │   ├── components/
    │   │   ├── progress_card.py# Dual progress card (Batch counters + File HUD)
    │   │   └── video_card.py   # Preview card with thumbnail & stats
    │   └── views/
    │       ├── download_view.py# Downloader with First-Time Setup notice & auto-detection
    │       ├── playlist_view.py# Playlist manager with exact item counters
    │       ├── converter_view.py# Media converter & audio extractor
    │       ├── subtitles_view.py# Subtitles & translation studio
    │       ├── platforms_view.py# Supported platforms catalog
    │       ├── history_view.py # Downloads library with audio/video summary stats
    │       └── settings_view.py# Destination folder selector & FFmpeg verification
    └── utils/
        ├── config.py           # Persistent settings (Windows Downloads default, first-run flag)
        ├── history.py          # Persistent download history
        ├── logger.py           # Thread-safe logging with line buffer limits
        ├── ffmpeg_checker.py   # FFmpeg & ffprobe verification
        └── helpers.py          # System paths, bytes/time formatters, cross-platform opener
```

---

## How to Build Standalone Windows Executable (.EXE)

You can package this entire application into a standalone `.exe` so you can use it every day without opening a terminal or needing Python installed on other machines:

### Method A: 1-Click Batch Build (Windows)
Double-click `build_exe.bat`. It will:
1. Verify Python and pip.
2. Install PyInstaller and dependencies.
3. Automatically bundle CustomTkinter data and themes.
4. Output `MediaStudioPro.exe` into the `dist/` folder.

### Method B: Manual Command (Windows / Linux)
```bash
pip install pyinstaller -r requirements.txt
python build_exe.py
```

### Making the .EXE Completely Portable with FFmpeg:
To run the `.exe` on any Windows PC without installing FFmpeg separately:
1. Download the static release of FFmpeg (`ffmpeg.exe` and `ffprobe.exe`) from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/).
2. Place `ffmpeg.exe` and `ffprobe.exe` in the same directory as `MediaStudioPro.exe`.
3. The application will automatically detect the local `ffmpeg.exe`!

---

## Daily Usage Instructions

### 1. Daily Desktop GUI
```bash
./run.sh
# or
python3 main.py
```
1. On first launch, check the notification banner at the top or open **Settings** to verify where downloaded files are saved.
2. Copy a link from Instagram, TikTok, YouTube, Facebook, Twitter/X, or Reddit.
3. Click **Paste** in the app. The platform will be auto-detected immediately.
4. Click **Start Download**. Real-time download speed, ETA, and progress will display.

### 2. Command Line (CLI) Usage
```bash
# List all 25+ platforms
python3 main.py --platforms

# Download an Instagram Reel
python3 main.py --url "https://www.instagram.com/reel/C8qL..."

# Download a TikTok video
python3 main.py --url "https://www.tiktok.com/@user/video/..."

# Download a YouTube video in 1080p
python3 main.py --url "https://www.youtube.com/watch?v=..." -r 1080p

# Download high-quality 320kbps MP3 audio from any link
python3 main.py --url "https://soundcloud.com/..." -t audio -b 320k

# Download a selective range from a playlist (e.g. items 1 to 10, and item 15)
python3 main.py --url "https://www.youtube.com/playlist?list=..." -p "1-10, 15"

# Convert a local video or extract audio
python3 main.py --convert "my_video.mkv" --to-format mp3 -b 320k
```

### 3. Web Dashboard
```bash
python3 main.py --server
```
Access the responsive web interface at `http://127.0.0.1:5000`.
