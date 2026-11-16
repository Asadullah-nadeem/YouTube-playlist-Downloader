#!/usr/bin/env python3
import argparse
import sys
import os

from src.core.downloader import downloader
from src.core.converter import MediaConverter
from src.core.playlist import PlaylistManager
from src.core.subtitles import SubtitleManager
from src.core.platform_detector import PlatformDetector
from src.utils.logger import logger
from src.utils.config import config
from src.utils.ffmpeg_checker import FFmpegChecker

def main():
    parser = argparse.ArgumentParser(
        description="Media Studio Pro CLI - Download from YouTube, Instagram, TikTok & 25+ Platforms",
        formatter_class=argparse.RawTextHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", type=str, help="Media link from Instagram, TikTok, YouTube, Facebook, Twitter, Reddit, etc.")
    group.add_argument("-i", "--info", type=str, help="Inspect video or playlist metadata without downloading")
    group.add_argument("--convert", type=str, help="Path of local media file to convert")
    group.add_argument("--check-ffmpeg", action="store_true", help="Check and verify FFmpeg installation")
    group.add_argument("--platforms", action="store_true", help="List all 25+ supported social media and video platforms")

    # Download options
    parser.add_argument("-t", "--type", choices=["video", "audio"], default="video", help="Media download type (default: video)")
    parser.add_argument("-r", "--resolution", type=str, default="1080p", help="Resolution: best, 2160p, 1440p, 1080p, 720p, 480p (default: 1080p)")
    parser.add_argument("--vformat", choices=["mp4", "mkv", "webm"], default="mp4", help="Video container format (default: mp4)")
    parser.add_argument("--aformat", choices=["mp3", "m4a", "flac", "wav", "opus"], default="mp3", help="Audio format (default: mp3)")
    parser.add_argument("-b", "--bitrate", choices=["320k", "256k", "192k", "128k"], default="320k", help="Audio bitrate (default: 320k)")
    parser.add_argument("-o", "--output", type=str, help="Output destination folder")
    parser.add_argument("-p", "--playlist-items", type=str, help="Playlist video range (e.g. '1-5, 8, 12-15')")
    parser.add_argument("--embed-subs", action="store_true", help="Download and embed subtitles into video")
    parser.add_argument("--sub-lang", type=str, default="en", help="Subtitle language code (e.g. en, es, hi, all)")
    parser.add_argument("--threads", type=int, default=8, help="Concurrent fragment download connections (default: 8)")

    # Conversion options
    parser.add_argument("--to-format", type=str, default="mp4", help="Target format for conversion (default: mp4 or mp3)")
    parser.add_argument("--codec", type=str, default="libx264", help="Video codec (libx264, libx265, copy)")
    parser.add_argument("--crf", type=int, default=20, help="Compression quality CRF (18-28)")

    args = parser.parse_args()

    if args.platforms:
        print("\n==========================================================")
        print("Supported Platforms (25+ Social & Video Platforms)")
        print("==========================================================")
        for idx, p in enumerate(PlatformDetector.get_all_platforms(), start=1):
            types = ", ".join(p.get("media_types", []))
            tag = p.get("tag", f"[{p['name']}]")
            print(f"{idx:2d}. {tag:<18} | {p['description']}")
            print(f"    Supported: {types}\n")
        sys.exit(0)

    if args.check_ffmpeg:
        ok, msg = FFmpegChecker.check_ffmpeg()
        print(f"[{'OK' if ok else 'FAIL'}] {msg}")
        sys.exit(0 if ok else 1)

    if args.info:
        platform = PlatformDetector.detect(args.info)
        p_name = platform['name'] if platform else "Media"
        print(f"\n--- Inspecting {p_name}: {args.info} ---")
        info = PlaylistManager.get_playlist_info(args.info)
        if not info:
            print("Failed to retrieve media information.")
            sys.exit(1)
        if info.get('is_playlist'):
            print(f"Playlist Title : {info.get('title')}")
            print(f"Channel        : {info.get('uploader')}")
            print(f"Total Videos   : {info.get('count')}")
            print("\nFirst 10 Videos:")
            for v in info.get('videos', [])[:10]:
                print(f"  #{v['index']:2d} | {v['title'][:60]:<60} | {v['duration']}")
            if info.get('count', 0) > 10:
                print(f"  ... and {info['count'] - 10} more videos.")
        else:
            v = info.get('videos', [{}])[0]
            print(f"Title    : {v.get('title')}")
            print(f"Creator  : {info.get('uploader')}")
            print(f"Duration : {v.get('duration')}")
        sys.exit(0)

    if args.convert:
        if not os.path.exists(args.convert):
            print(f"Error: file not found: {args.convert}")
            sys.exit(1)
        converter = MediaConverter()
        out_folder = args.output or config.get("download_dir", os.path.abspath("downloads"))
        os.makedirs(out_folder, exist_ok=True)
        base = os.path.splitext(os.path.basename(args.convert))[0]
        out_file = os.path.join(out_folder, f"{base}_converted.{args.to_format}")

        is_audio = args.to_format in ("mp3", "m4a", "flac", "wav", "opus", "ogg")
        print(f"Converting '{args.convert}' -> '{out_file}'...")
        success = converter.convert_media(
            input_file=args.convert,
            output_file=out_file,
            output_format=args.to_format,
            media_type="audio" if is_audio else "video",
            audio_bitrate=args.bitrate,
            video_codec=args.codec,
            crf=args.crf,
            progress_callback=lambda d: print(f"\rProgress: {d.get('percent', 0.0):.1f}% | Time: {d.get('current_time')} | Speed: {d.get('speed')}", end="", flush=True)
        )
        print()
        if success:
            print("Conversion completed successfully.")
            sys.exit(0)
        else:
            print("Conversion failed.")
            sys.exit(1)

    if args.url:
        platform = PlatformDetector.detect(args.url)
        p_name = platform['name'] if platform else "Universal Platform"
        out_folder = args.output or config.get("download_dir", os.path.abspath("downloads"))

        print(f"\n--- Starting {p_name} Download ---")
        print(f"Platform    : {p_name}")
        print(f"URL         : {args.url}")
        print(f"Type        : {args.type.upper()}")
        print(f"Resolution  : {args.resolution}")
        print(f"Output Dir  : {out_folder}")
        print(f"Connections : {args.threads} parallel fragments\n")

        success = downloader.download(
            url=args.url,
            output_dir=out_folder,
            media_type=args.type,
            resolution=args.resolution,
            video_format=args.vformat,
            audio_format=args.aformat,
            audio_bitrate=args.bitrate,
            playlist_items=args.playlist_items,
            embed_thumbnail=True,
            embed_metadata=True,
            embed_subtitles=args.embed_subs,
            subtitle_lang=args.sub_lang,
            concurrent_fragments=args.threads,
            progress_callback=lambda d: _cli_progress(d)
        )
        print()
        if success:
            print(f"\n{p_name} download finished successfully.")
            sys.exit(0)
        else:
            print(f"\n{p_name} download failed or was cancelled.")
            sys.exit(1)

def _cli_progress(data):
    if data.get('status') == 'downloading':
        pct = data.get('percent', 0.0)
        speed = data.get('speed_str', '--')
        eta = data.get('eta_str', '--:--')
        downloaded = data.get('downloaded_str', '--')
        total = data.get('total_str', '--')
        pl_idx = data.get('playlist_index', 0)
        pl_tot = data.get('playlist_total', 0)
        item_str = f"[{pl_idx}/{pl_tot}] " if pl_tot > 0 else ""
        sys.stdout.write(f"\r{item_str}[{pct:5.1f}%] {downloaded}/{total} | Speed: {speed} | ETA: {eta}  ")
        sys.stdout.flush()
    elif data.get('status') == 'processing':
        sys.stdout.write(f"\nProcessing / Merging: {data.get('filename')}...\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
