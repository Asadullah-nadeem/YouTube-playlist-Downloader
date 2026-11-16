"""
Legacy adapter for downloader.py.
Forwards calls to the modernized src.core.downloader engine.
"""

import os
from src.core.downloader import downloader, VideoDownloader, DownloadCancelledException
from src.utils.logger import CustomLogger if hasattr(__import__('logger', fromlist=['CustomLogger']), 'CustomLogger') else None

def download_media(playlist_url, output_folder, download_type, resolution, log_callback, stop_flag):
    """
    Backward-compatible download_media function.
    """
    res_str = f"{resolution}p" if resolution and str(resolution).isdigit() else (resolution or "1080p")
    downloader.stop_flag = stop_flag

    def progress_bridge(data):
        st = data.get("status")
        fn = data.get("filename", "")
        pct = data.get("percent", 0.0)
        speed = data.get("speed_str", "")
        if st == "downloading":
            log_callback(f"Status: {st} | {pct:.1f}% | Speed: {speed} | File: {fn}")
        elif st == "processing":
            log_callback(f"Status: {st} | Finalizing media...")

    return downloader.download(
        url=playlist_url,
        output_dir=output_folder,
        media_type=download_type or "video",
        resolution=res_str,
        progress_callback=progress_bridge
    )

__all__ = ["download_media", "downloader", "VideoDownloader"]
