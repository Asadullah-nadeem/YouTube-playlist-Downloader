import os
import threading
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from typing import Optional, Dict, Any

from src.core.downloader import downloader
from src.core.playlist import PlaylistManager
from src.ui.components.progress_card import ProgressCard
from src.ui.components.video_card import VideoPreviewCard
from src.utils.config import config
from src.utils.logger import logger
from src.utils.helpers import is_valid_url, open_file_or_folder

class DownloadView(ctk.CTkScrollableFrame):
    """Main view for single video / quick playlist downloading."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.analyzed_url = ""
        self.is_download_active = False

        self._build_ui()
        logger.add_callback(self._on_log_message)

    def _build_ui(self):
        # 1. URL Input Section
        self.url_frame = ctk.CTkFrame(self, corner_radius=12)
        self.url_frame.pack(fill="x", padx=10, pady=(10, 8))

        ctk.CTkLabel(
            self.url_frame,
            text="Media / Playlist URL:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 4))

        input_row = ctk.CTkFrame(self.url_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=15, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Paste YouTube video or playlist link (e.g. https://www.youtube.com/watch?v=...)",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.paste_btn = ctk.CTkButton(
            input_row,
            text="📋 Paste",
            width=85,
            height=38,
            command=self._paste_clipboard
        )
        self.paste_btn.pack(side="left", padx=(0, 8))

        self.analyze_btn = ctk.CTkButton(
            input_row,
            text="🔍 Analyze",
            width=95,
            height=38,
            fg_color="#2B7A78",
            hover_color="#17252A",
            command=self._start_analyze
        )
        self.analyze_btn.pack(side="left")

        # 2. Preview Card
        self.preview_card = VideoPreviewCard(self)
        self.preview_card.pack(fill="x", padx=10, pady=6)

        # 3. Format & Quality Options
        self.options_frame = ctk.CTkFrame(self, corner_radius=12)
        self.options_frame.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            self.options_frame,
            text="Download Configuration:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        # Media Type Selection (Video vs Audio)
        type_row = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        type_row.pack(fill="x", padx=15, pady=4)

        self.media_type_var = ctk.StringVar(value="video")
        self.type_segmented = ctk.CTkSegmentedButton(
            type_row,
            values=["Video", "Audio Only"],
            command=self._on_type_changed
        )
        self.type_segmented.set("Video")
        self.type_segmented.pack(side="left")

        # Dynamic Controls Container
        self.controls_container = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.controls_container.pack(fill="x", padx=15, pady=10)

        # Video Options Row
        self.video_options_frame = ctk.CTkFrame(self.controls_container, fg_color="transparent")
        self.video_options_frame.pack(fill="x")

        # Resolution dropdown
        res_col = ctk.CTkFrame(self.video_options_frame, fg_color="transparent")
        res_col.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(res_col, text="Resolution:").pack(anchor="w")
        self.res_combo = ctk.CTkComboBox(
            res_col,
            values=["Best", "2160p (4K)", "1440p (2K)", "1080p (Full HD)", "720p (HD)", "480p", "360p"],
            width=160
        )
        self.res_combo.set("1080p (Full HD)")
        self.res_combo.pack(anchor="w")

        # Video format container dropdown
        fmt_col = ctk.CTkFrame(self.video_options_frame, fg_color="transparent")
        fmt_col.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(fmt_col, text="Container:").pack(anchor="w")
        self.vfmt_combo = ctk.CTkComboBox(
            fmt_col,
            values=["mp4", "mkv", "webm"],
            width=110
        )
        self.vfmt_combo.set("mp4")
        self.vfmt_combo.pack(anchor="w")

        # Subtitles checkbox and language
        sub_col = ctk.CTkFrame(self.video_options_frame, fg_color="transparent")
        sub_col.pack(side="left")
        self.embed_sub_var = ctk.BooleanVar(value=False)
        self.sub_checkbox = ctk.CTkCheckBox(
            sub_col,
            text="Embed Subtitles",
            variable=self.embed_sub_var,
            command=self._toggle_sub_lang
        )
        self.sub_checkbox.pack(anchor="w", pady=(0, 2))

        self.sub_lang_combo = ctk.CTkComboBox(
            sub_col,
            values=["en", "es", "fr", "de", "hi", "ar", "ja", "zh", "all"],
            width=90,
            state="disabled"
        )
        self.sub_lang_combo.set("en")
        self.sub_lang_combo.pack(anchor="w")

        # Audio Options Row (hidden initially)
        self.audio_options_frame = ctk.CTkFrame(self.controls_container, fg_color="transparent")

        afmt_col = ctk.CTkFrame(self.audio_options_frame, fg_color="transparent")
        afmt_col.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(afmt_col, text="Audio Format:").pack(anchor="w")
        self.afmt_combo = ctk.CTkComboBox(
            afmt_col,
            values=["mp3", "m4a", "flac", "wav", "opus"],
            width=120
        )
        self.afmt_combo.set("mp3")
        self.afmt_combo.pack(anchor="w")

        abtr_col = ctk.CTkFrame(self.audio_options_frame, fg_color="transparent")
        abtr_col.pack(side="left")
        ctk.CTkLabel(abtr_col, text="Bitrate / Quality:").pack(anchor="w")
        self.abtr_combo = ctk.CTkComboBox(
            abtr_col,
            values=["320k (Best)", "256k", "192k (Standard)", "128k"],
            width=150
        )
        self.abtr_combo.set("320k (Best)")
        self.abtr_combo.pack(anchor="w")

        # Extra Checkboxes Row
        extras_row = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        extras_row.pack(fill="x", padx=15, pady=(0, 12))

        self.embed_thumb_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            extras_row,
            text="Embed Thumbnail & Metadata",
            variable=self.embed_thumb_var
        ).pack(side="left", padx=(0, 20))

        self.thread_label = ctk.CTkLabel(extras_row, text="Speed Boost (Fragments):")
        self.thread_label.pack(side="left", padx=(10, 6))

        self.threads_combo = ctk.CTkComboBox(
            extras_row,
            values=["4", "8 (Fast)", "16 (Ultra Fast)"],
            width=120
        )
        self.threads_combo.set("8 (Fast)")
        self.threads_combo.pack(side="left")

        # 4. Action Buttons Row
        actions_row = ctk.CTkFrame(self, fg_color="transparent")
        actions_row.pack(fill="x", padx=10, pady=8)

        self.download_btn = ctk.CTkButton(
            actions_row,
            text="🚀 Start Download",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_download
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            actions_row,
            text="⏹ Cancel",
            height=42,
            width=100,
            fg_color="#D9534F",
            hover_color="#C9302C",
            state="disabled",
            command=self._stop_download
        )
        self.stop_btn.pack(side="left", padx=(0, 10))

        self.folder_btn = ctk.CTkButton(
            actions_row,
            text="📂 Open Folder",
            height=42,
            width=120,
            command=self._open_downloads_folder
        )
        self.folder_btn.pack(side="left")

        # 5. Progress Card
        self.progress_card = ProgressCard(self)
        self.progress_card.pack(fill="x", padx=10, pady=6)

        # 6. Live Log Area
        self.log_frame = ctk.CTkFrame(self, corner_radius=12)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=(8, 12))

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            log_header,
            text="Live Activity Log:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            log_header,
            text="Clear Log",
            width=70,
            height=24,
            font=ctk.CTkFont(size=11),
            command=self._clear_log
        ).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            height=140,
            font=ctk.CTkFont(family="monospace", size=11),
            wrap="word"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _paste_clipboard(self):
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard_text.strip())
                self._start_analyze()
        except Exception:
            pass

    def _on_type_changed(self, value):
        if value == "Video":
            self.audio_options_frame.pack_forget()
            self.video_options_frame.pack(fill="x")
        else:
            self.video_options_frame.pack_forget()
            self.audio_options_frame.pack(fill="x")

    def _toggle_sub_lang(self):
        if self.embed_sub_var.get():
            self.sub_lang_combo.configure(state="normal")
        else:
            self.sub_lang_combo.configure(state="disabled")

    def _start_analyze(self):
        url = self.url_entry.get().strip()
        if not is_valid_url(url):
            logger.warning("Please enter a valid URL.")
            return

        self.analyze_btn.configure(state="disabled", text="Analyzing...")

        def run_analysis():
            info = PlaylistManager.get_playlist_info(url)
            self.after(0, lambda: self._apply_analysis_result(info, url))

        threading.Thread(target=run_analysis, daemon=True).start()

    def _apply_analysis_result(self, info: Optional[Dict[str, Any]], url: str):
        self.analyze_btn.configure(state="normal", text="🔍 Analyze")
        if not info:
            logger.error("Could not fetch media information.")
            return

        self.analyzed_url = url
        if info.get('is_playlist'):
            count = info.get('count', 0)
            self.preview_card.set_info(
                title=f"Playlist: {info.get('title')}",
                channel=f"{info.get('uploader')} ({count} videos)",
                duration=f"Total: {count} videos",
                thumbnail_url=info.get('thumbnail')
            )
            logger.info(f"Loaded Playlist '{info.get('title')}' with {count} items.")
        else:
            video = info.get('videos', [{}])[0]
            self.preview_card.set_info(
                title=video.get('title', 'Unknown'),
                channel=info.get('uploader', 'Unknown'),
                duration=video.get('duration', '--:--'),
                thumbnail_url=video.get('thumbnail')
            )
            logger.info(f"Loaded Video: '{video.get('title')}'")

    def _start_download(self):
        url = self.url_entry.get().strip()
        if not is_valid_url(url):
            logger.warning("Invalid URL entered.")
            return

        media_type = "video" if self.type_segmented.get() == "Video" else "audio"

        # Resolution clean
        res_raw = self.res_combo.get().split()[0]
        resolution = res_raw.lower()

        video_format = self.vfmt_combo.get()
        audio_format = self.afmt_combo.get()
        audio_bitrate = self.abtr_combo.get().split()[0]
        embed_sub = self.embed_sub_var.get()
        sub_lang = self.sub_lang_combo.get()
        embed_thumb = self.embed_thumb_var.get()
        threads = int(self.threads_combo.get().split()[0])

        self.is_download_active = True
        self.download_btn.configure(state="disabled", text="⏳ Downloading...")
        self.stop_btn.configure(state="normal")
        self.progress_card.reset()
        self.progress_card.set_status("Starting download...")

        def worker():
            success = downloader.download(
                url=url,
                media_type=media_type,
                resolution=resolution,
                video_format=video_format,
                audio_format=audio_format,
                audio_bitrate=audio_bitrate,
                embed_thumbnail=embed_thumb,
                embed_metadata=True,
                embed_subtitles=embed_sub,
                download_subtitles=embed_sub,
                subtitle_lang=sub_lang,
                concurrent_fragments=threads,
                progress_callback=lambda d: self.after(0, lambda: self._on_progress(d))
            )
            self.after(0, lambda: self._on_download_complete(success))

        threading.Thread(target=worker, daemon=True).start()

    def _stop_download(self):
        downloader.cancel()
        self.stop_btn.configure(state="disabled")
        self.progress_card.set_status("Cancelling...", color="#D9534F")

    def _on_progress(self, data: Dict[str, Any]):
        status = data.get("status")
        if status == "downloading":
            self.progress_card.update_progress(
                percent=data.get("percent", 0.0),
                status=f"Downloading {data.get('filename', '')}",
                speed=data.get("speed_str"),
                eta=data.get("eta_str"),
                transferred_str=data.get("downloaded_str"),
                total_str=data.get("total_str")
            )
        elif status == "processing":
            self.progress_card.set_status(data.get("message", "Processing media..."), color="#3B8ED0")

    def _on_download_complete(self, success: bool):
        self.is_download_active = False
        self.download_btn.configure(state="normal", text="🚀 Start Download")
        self.stop_btn.configure(state="disabled")

        if success:
            self.progress_card.update_progress(100.0, status="Download Completed Successfully!")
            self.progress_card.set_status("Completed! 🎉", color="#4CAF50")
        else:
            self.progress_card.set_status("Download Stopped or Failed", color="#D9534F")

    def _open_downloads_folder(self):
        folder = config.get("download_dir", os.path.abspath("downloads"))
        os.makedirs(folder, exist_ok=True)
        open_file_or_folder(folder)

    def _on_log_message(self, message: str, level: str):
        try:
            self.log_textbox.insert(tk.END, message + "\n")
            self.log_textbox.see(tk.END)
        except Exception:
            pass

    def _clear_log(self):
        self.log_textbox.delete("1.0", tk.END)

