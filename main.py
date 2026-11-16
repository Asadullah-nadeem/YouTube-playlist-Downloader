#!/usr/bin/env python3
"""
Media Studio Pro - Universal Downloader & Converter
Primary Application Entry Point.
"""

import sys
import os

# Add project root to python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def start_download_callback(playlist_url, download_type, resolution, log_callback, stop_flag):
    """Callback adapter for backwards compatibility."""
    from src.core.downloader import downloader
    res = f"{resolution}p" if resolution and str(resolution).isdigit() else (resolution or "1080p")
    downloader.download(
        url=playlist_url,
        media_type=download_type or "video",
        resolution=res,
        progress_callback=lambda d: log_callback(f"Status: {d.get('status')} | {d.get('filename', '')}")
    )

def main():
    args = sys.argv[1:]

    # Web Dashboard Mode
    if "--server" in args:
        from src.server import app
        from werkzeug.serving import run_simple
        print("Starting Media Studio Web Dashboard at http://127.0.0.1:5000 ...")
        run_simple("127.0.0.1", 5000, app.wsgi_app, use_reloader=False)
        return

    # CLI Command Line Mode
    if len(args) > 0:
        from src.cli import main as cli_main
        cli_main()
        return

    # Default: Modern Graphical Desktop Interface
    try:
        from src.ui.app import launch_gui
        launch_gui()
    except ImportError as e:
        print(f"Error launching GUI: {e}")
        print("Please ensure required dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
