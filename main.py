#!/usr/bin/env python3
"""
YouTube Media Studio & Playlist Downloader Pro
Main application entry point.
"""

import sys
import os

# Ensure package root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.downloader import downloader, VideoDownloader
from src.utils.logger import logger

def start_download_callback(playlist_url, download_type, resolution, log_callback, stop_flag):
    """
    Backwards compatibility callback wrapper for legacy scripts.
    """
    res = f"{resolution}p" if resolution and str(resolution).isdigit() else (resolution or "1080p")
    output_folder = os.path.abspath("downloads")
    downloader.download(
        url=playlist_url,
        output_dir=output_folder,
        media_type=download_type or "video",
        resolution=res,
        progress_callback=lambda d: log_callback(f"Status: {d.get('status')} | {d.get('filename', '')}")
    )

def main():
    # If command line arguments provided (e.g. --help, --url, --convert, etc.), invoke CLI mode
    if len(sys.argv) > 1:
        from cli import main as cli_main
        cli_main()
    else:
        # Launch modern graphical user interface
        try:
            from src.ui.app import launch_gui
            launch_gui()
        except ImportError as e:
            print(f"Error launching GUI: {e}")
            print("Please make sure all dependencies are installed:")
            print("  pip install -r requirements.txt")
            sys.exit(1)

if __name__ == "__main__":
    main()
