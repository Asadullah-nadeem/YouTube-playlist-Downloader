# 🎬 YouTube Studio Pro & Playlist Downloader

A modern, high-performance Python desktop suite, CLI, and web application for downloading, converting, and managing YouTube videos, playlists, audio tracks, and multilingual subtitles.

Built with **CustomTkinter**, **yt-dlp**, and **FFmpeg**, engineered for maximum download speeds, modern UI/UX, and modular architecture.

---

## 🌟 Key Features

### 🚀 Ultra-Fast Download Engine
- **Multi-Fragment Acceleration**: Download multiple video and audio stream chunks simultaneously (4, 8, or 16 parallel fragment connections) for 3x–10x faster speeds.
- **Full Resolution Support**: Download in **Best**, **4K (2160p)**, **2K (1440p)**, **1080p Full HD**, **720p HD**, **480p**, and **360p** at 60fps / HDR.
- **Smart JavaScript Challenge Solver**: Uses the system JavaScript runtime (`node` / `bun`) with automated challenge solver distribution to avoid YouTube speed throttling and format limitations.
- **Embedded Artwork & Metadata**: Embed video thumbnails, chapter markers, artist tags, and album info directly into files.

### 🎨 Modern UI & UX (CustomTkinter)
- **Dark / Light Mode**: Beautiful dark and light appearance modes with rounded cards and visual status badges.
- **Live Video Preview**: Instantly inspect video thumbnail, duration badge, title, and channel information before downloading.
- **Dynamic Progress HUD**: Real-time progress bar with live download speed (MB/s), estimated time remaining (ETA), and transferred size.
- **Live Activity Console**: Collapsible, color-coded logging console with clear status messages.

### 📋 Advanced Playlist Manager
- **Playlist Inspection**: View full playlist info, total video count, and channel name before downloading.
- **Selective Item Checkboxes**: Select or deselect individual videos from an interactive checklist.
- **Range Filtering**: Download specific slices (e.g. `1-10, 15, 20-25`) without downloading the entire playlist.
- **Batch Processing**: Progress indicator showing current video index and remaining items.

### 🔄 Media Converter & Audio Tools
- **Video Conversion**: Convert local videos between **MP4**, **MKV**, **WebM**, **MOV**, and **AVI** with customizable codecs (**H.264**, **H.265 / HEVC**, or fast stream copy).
- **Audio Extraction**: Extract crystal-clear audio from any video into **MP3** (up to 320 kbps), **M4A / AAC**, **FLAC (lossless)**, **WAV**, or **OPUS**.
- **Video Compressor**: Reduce video file size using CRF compression presets (Balanced, High Compression, or Smallest File).
- **Video & Audio Trimmer**: Trim clips precisely by specifying start (`HH:MM:SS`) and end timestamps.

### 🌐 Subtitles & Translations
- **100+ Languages**: Browse and extract both official human captions and auto-translated closed captions.
- **Multiple Formats**: Export standalone `.srt` or `.vtt` files, or embed subtitles directly into video containers.

### 🕒 Library & Download History
- Persistent history of completed downloads.
- **1-Click Play**: Launch downloaded media in your system's default media player.
- **1-Click Locate**: Open the containing folder in your file manager with the file selected.

### ⚡ Dual Interface: Desktop GUI, Headless CLI & Web Server
- **Desktop GUI**: Native CustomTkinter desktop interface (`./run.sh` or `python main.py`).
- **Command Line (CLI)**: Full CLI interface with flags for terminal and headless server automation (`python cli.py`).
- **Web Dashboard**: Modern Tailwind CSS + SocketIO web app with live streaming progress (`python server.py`).

---

## 📁 Project Architecture

The codebase is organized cleanly into modular packages:

```
YouTube-playlist-Downloader/
├── src/
│   ├── core/
│   │   ├── downloader.py       # Core yt-dlp engine (multi-fragment speedup, progress hooks, cancellation)
│   │   ├── converter.py        # FFmpeg converter (audio extraction, compression, trimming)
│   │   ├── playlist.py         # Playlist inspector, metadata extraction & range parser
│   │   └── subtitles.py        # Subtitle scanner, translation downloader & format converter
│   ├── ui/
│   │   ├── app.py              # Main CustomTkinter application window & navigation sidebar
│   │   ├── components/
│   │   │   ├── progress_card.py # Animated progress card (speed, ETA, size HUD)
│   │   │   └── video_card.py   # Thumbnail preview card with channel and duration
│   │   └── views/
│   │       ├── download_view.py   # Primary quick downloader view
│   │       ├── playlist_view.py   # Selective playlist manager view
│   │       ├── converter_view.py  # Media converter, audio extractor & trimmer
│   │       ├── subtitles_view.py  # Subtitles & translation studio
│   │       ├── history_view.py    # Downloads history & library manager
│   │       └── settings_view.py   # Persistent configuration & FFmpeg verification
│   └── utils/
│       ├── config.py           # Persistent settings store (config.json)
│       ├── history.py          # Persistent download history store (history.json)
│       ├── logger.py           # Thread-safe logging with GUI callbacks
│       ├── ffmpeg_checker.py   # Auto-detection & validation of FFmpeg / FFprobe
│       └── helpers.py          # Format helpers (bytes, time, filenames, platform opener)
├── main.py                     # Primary GUI application entry point
├── cli.py                      # Complete command-line interface
├── server.py                   # Web dashboard & REST/SocketIO server
├── run.sh                      # Quick one-click launcher
├── setup.sh                    # Automated setup & environment check script
├── requirements.txt            # Python dependencies
└── downloads/                  # Output directory (gitignored)
```

---

## 🛠️ Prerequisites & Installation

### Requirements
- **Python 3.10+** (tested up to Python 3.14)
- **FFmpeg** (required for audio extraction, video remuxing, and subtitle embedding)
- **Node.js** (recommended for YouTube JavaScript challenge solving without throttling)

### Automated Setup (Recommended)
Run the setup script, which automatically prepares the virtual environment, verifies dependencies, and checks FFmpeg:

```bash
./setup.sh
```

### Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Asadullah-nadeem/YouTube-playlist-Downloader.git
   cd YouTube-playlist-Downloader
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Linux / macOS
   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify FFmpeg:**
   - **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install ffmpeg`
   - **macOS:** `brew install ffmpeg`
   - **Windows:** Download from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) and add `bin` to your System `PATH`, or set the custom path in the app Settings.

---

## 🚀 How to Run

### 1. Modern Desktop GUI
```bash
./run.sh
# or
python3 main.py
```

### 2. Command Line Interface (CLI)
You can use `cli.py` or pass CLI flags directly to `main.py`:

```bash
# Verify FFmpeg installation
python3 cli.py --check-ffmpeg

# Inspect a video or playlist without downloading
python3 cli.py --info "https://www.youtube.com/playlist?list=PL..."

# Download a video in 1080p MP4 with 8 parallel connections
python3 cli.py --url "https://www.youtube.com/watch?v=..." -r 1080p

# Download audio only as 320kbps MP3
python3 cli.py --url "https://www.youtube.com/watch?v=..." -t audio -b 320k --aformat mp3

# Download specific videos from a playlist (videos 1 through 5, and video 8)
python3 cli.py --url "https://www.youtube.com/playlist?list=PL..." -p "1-5, 8"

# Download video with embedded subtitles in English
python3 cli.py --url "https://www.youtube.com/watch?v=..." --embed-subs --sub-lang en

# Convert a local video to MP4 or extract audio to MP3
python3 cli.py --convert "input.mkv" --to-format mp3 -b 320k
```

### 3. Web Dashboard
```bash
./venv/bin/python3 server.py
```
Then open your browser at `http://127.0.0.1:5000`.

---

## ⚙️ Configuration & Customization

Settings can be changed visually through the **Settings** tab in the desktop application or in `config.json`:

| Setting Key | Default | Description |
|---|---|---|
| `download_dir` | `./downloads` | Destination folder for completed files |
| `max_concurrent_fragments` | `8` | Number of simultaneous fragment connections for accelerated downloading |
| `preferred_resolution` | `1080p` | Default video resolution target |
| `preferred_video_format` | `mp4` | Preferred video container (`mp4`, `mkv`, `webm`) |
| `preferred_audio_format` | `mp3` | Preferred audio format (`mp3`, `m4a`, `flac`, `wav`, `opus`) |
| `preferred_audio_bitrate` | `320k` | Audio bitrate for extraction |
| `theme` | `dark` | UI appearance mode (`dark`, `light`, `system`) |
| `custom_ffmpeg_path` | `""` | Optional explicit path to custom FFmpeg binary |

---

## ❓ Troubleshooting

- **Speed is slow or videos get throttled:**
  Make sure Node.js is installed (`node -v`). The downloader automatically uses Node to solve YouTube JavaScript challenges, unlocking unthrottled bandwidth and full 4K/60fps streams.
- **Audio extraction fails:**
  Verify FFmpeg is installed by running `./venv/bin/python3 cli.py --check-ffmpeg` or checking the Settings tab.
- **Tkinter display error on headless Linux:**
  If you are running in a headless SSH session without a GUI display, use the CLI mode (`python3 cli.py ...`) or run the Web Dashboard (`python3 server.py`).
