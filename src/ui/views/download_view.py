import os
import threading
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from typing import Optional, Dict, Any

from src.core.downloader import downloader
from src.core.playlist import PlaylistManager
from src.core.platform_detector import PlatformDetector
from src.ui.components.progress_card import ProgressCard
from src.ui.components.video_card import VideoPreviewCard
from src.ui.components.loading_card import LoadingCard
from src.utils.config import config
from src.utils.logger import logger
from src.utils.helpers import is_valid_url, open_file_or_folder, verify_directory_writable

class DownloadView(ctk.CTkScrollableFrame):
    """
    Main Downloader View.
    Features instant platform detection, clean replace-on-paste, loading screen overlay,
    responsive small-screen layout, and zero emojis.
    """

    def __init__(self, master, on_navigate_settings=None, **kwargs):
        super().__init__(master, **kwargs)

        self.on_navigate_settings = on_navigate_settings
        self.analyzed_url = ""
        self.is_download_active = False
        self.detected_platform: Optional[Dict[str, Any]] = None

        self._build_ui()
        logger.add_callback(self._on_log_message)

    def _build_ui(self):
        # 0. First-Time Setup Notice Banner
        self.setup_banner = ctk.CTkFrame(self, corner_radius=10, fg_color=("#E3F2FD", "#102A43"))
        if not config.get("first_run_completed", False):
            self.setup_banner.pack(fill="x", padx=10, pady=(10, 4))
            self._build_setup_banner_content()

        # 1. URL Input & Platform Detection Section
        self.url_frame = ctk.CTkFrame(self, corner_radius=10)
        self.url_frame.pack(fill="x", padx=10, pady=(6, 8))

        header_line = ctk.CTkFrame(self.url_frame, fg_color="transparent")
        header_line.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            header_line,
            text="Media Link (Instagram, TikTok, YouTube, Facebook, Twitter/X, Reddit, etc.):",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left")

        input_row = ctk.CTkFrame(self.url_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=15, pady=(4, 6))

        self.url_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Paste any video, reel, post, or playlist link here...",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.url_entry.bind("<KeyRelease>", self._on_url_input_change)
        self.url_entry.bind("<Control-v>", self._on_keyboard_paste)
        self.url_entry.bind("<Control-V>", self._on_keyboard_paste)

        self.clear_btn = ctk.CTkButton(
            input_row,
            text="Clear",
            width=60,
            height=38,
            cursor="hand2",
            fg_color="gray40",
            hover_color="gray50",
            command=self._clear_url
        )
        self.clear_btn.pack(side="left", padx=(0, 6))

        self.paste_btn = ctk.CTkButton(
            input_row,
            text="Paste",
            width=75,
            height=38,
            cursor="hand2",
            command=self._paste_clipboard
        )
        self.paste_btn.pack(side="left", padx=(0, 6))

        self.analyze_btn = ctk.CTkButton(
            input_row,
            text="Analyze",
            width=85,
            height=38,
            cursor="hand2",
            fg_color="#00695C",
            hover_color="#004D40",
            command=self._start_analyze
        )
        self.analyze_btn.pack(side="left")

        # Live Platform Auto-Detection Pill
        self.platform_banner = ctk.CTkFrame(self.url_frame, fg_color="transparent")
        self.platform_banner.pack(fill="x", padx=15, pady=(0, 10))

        self.platform_badge = ctk.CTkLabel(
            self.platform_banner,
            text="Platform Auto-Detect: Ready for 25+ platforms (YouTube, Instagram, TikTok, Facebook, Twitter, Reddit...)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
            anchor="w"
        )
        self.platform_badge.pack(side="left")

        # 2. Loading State Card (Shown while analyzing)
        self.loading_card = LoadingCard(self)
        # Hidden by default

        # 3. Preview Card
        self.preview_card = VideoPreviewCard(self)
        self.preview_card.pack(fill="x", padx=10, pady=6)

        # 4. Format & Quality Options
        self.options_frame = ctk.CTkFrame(self, corner_radius=10)
        self.options_frame.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            self.options_frame,
            text="Download Configuration:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

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

        res_col = ctk.CTkFrame(self.video_options_frame, fg_color="transparent")
        res_col.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(res_col, text="Resolution:").pack(anchor="w")
        self.res_combo = ctk.CTkComboBox(
            res_col,
            values=["Best Available (Max Quality)", "2160p (4K)", "1440p (2K)", "1080p (Full HD)", "720p (HD)", "480p", "360p"],
            width=200
        )
        self.res_combo.set("1080p (Full HD)")
        self.res_combo.pack(anchor="w")

        fmt_col = ctk.CTkFrame(self.video_options_frame, fg_color="transparent")
        fmt_col.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(fmt_col, text="Container:").pack(anchor="w")
        self.vfmt_combo = ctk.CTkComboBox(
            fmt_col,
            values=["mp4", "mkv", "webm"],
            width=95
        )
        self.vfmt_combo.set("mp4")
        self.vfmt_combo.pack(anchor="w")

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
        afmt_col.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(afmt_col, text="Audio Format:").pack(anchor="w")
        self.afmt_combo = ctk.CTkComboBox(
            afmt_col,
            values=["mp3", "m4a", "flac (Lossless)", "wav (Lossless)", "opus"],
            width=150
        )
        self.afmt_combo.set("mp3")
        self.afmt_combo.pack(anchor="w")

        abtr_col = ctk.CTkFrame(self.audio_options_frame, fg_color="transparent")
        abtr_col.pack(side="left")
        ctk.CTkLabel(abtr_col, text="Bitrate Quality:").pack(anchor="w")
        self.abtr_combo = ctk.CTkComboBox(
            abtr_col,
            values=["320k (Maximum Quality)", "256k", "192k (Standard)", "128k"],
            width=180
        )
        self.abtr_combo.set("320k (Maximum Quality)")
        self.abtr_combo.pack(anchor="w")

        # Extra Options Row
        extras_row = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        extras_row.pack(fill="x", padx=15, pady=(0, 12))

        self.embed_thumb_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            extras_row,
            text="Embed Thumbnail & Metadata Tags",
            variable=self.embed_thumb_var
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(extras_row, text="Connections (Threads):").pack(side="left", padx=(6, 4))
        self.threads_combo = ctk.CTkComboBox(
            extras_row,
            values=["4 (Standard)", "8 (High Speed)", "16 (Turbo)"],
            width=150
        )
        self.threads_combo.set("8 (High Speed)")
        self.threads_combo.pack(side="left")

        # 5. Action Buttons Row (Clickable feedback with cursor hand2)
        actions_row = ctk.CTkFrame(self, fg_color="transparent")
        actions_row.pack(fill="x", padx=10, pady=8)

        self.download_btn = ctk.CTkButton(
            actions_row,
            text="Start Download",
            height=40,
            cursor="hand2",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_download
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            actions_row,
            text="Cancel",
            height=40,
            width=90,
            cursor="hand2",
            fg_color="#C62828",
            hover_color="#B71C1C",
            state="disabled",
            command=self._stop_download
        )
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.folder_btn = ctk.CTkButton(
            actions_row,
            text="Open Folder",
            height=40,
            width=110,
            cursor="hand2",
            command=self._open_downloads_folder
        )
        self.folder_btn.pack(side="left")

        # 6. Progress Card
        self.progress_card = ProgressCard(self)
        self.progress_card.pack(fill="x", padx=10, pady=6)

        # 7. Live Activity Log Area
        self.log_frame = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=(8, 12))

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            log_header,
            text="Activity Log:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            log_header,
            text="Clear Log",
            width=70,
            height=24,
            cursor="hand2",
            font=ctk.CTkFont(size=11),
            command=self._clear_log
        ).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            height=130,
            font=ctk.CTkFont(family="monospace", size=11),
            wrap="word"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _build_setup_banner_content(self):
        dest = config.get("download_dir", "")
        for w in self.setup_banner.winfo_children():
            w.destroy()

        content = ctk.CTkFrame(self.setup_banner, fg_color="transparent")
        content.pack(fill="x", padx=14, pady=10)

        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(
            top,
            text="Notice: First-Time Setup Required",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#0D47A1", "#64B5F6")
        ).pack(side="left")

        ctk.CTkLabel(
            content,
            text=f"Please verify your download folder. Default location: {dest}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(2, 6))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(anchor="w")

        ctk.CTkButton(
            btn_row,
            text="Configure in Settings",
            height=28,
            width=160,
            cursor="hand2",
            command=self._go_to_settings
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Confirm Default Path",
            height=28,
            width=150,
            cursor="hand2",
            fg_color="gray40",
            hover_color="gray50",
            command=self._dismiss_setup_banner
        ).pack(side="left")

    def _go_to_settings(self):
        if self.on_navigate_settings:
            self.on_navigate_settings()

    def _dismiss_setup_banner(self):
        config.set("first_run_completed", True)
        self.setup_banner.pack_forget()

    def _clear_url(self):
        self.url_entry.delete(0, tk.END)
        self.platform_badge.configure(
            text="Platform Auto-Detect: Ready for 25+ platforms (YouTube, Instagram, TikTok, Facebook, Twitter, Reddit...)",
            text_color="gray",
            fg_color="transparent"
        )
        self.detected_platform = None
        self.preview_card.reset()

    def _on_keyboard_paste(self, event=None):
        try:
            txt = self.clipboard_get()
            if txt:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, txt.strip())
                self._on_url_input_change()
                self._start_analyze()
                return "break"
        except Exception:
            pass

    def _paste_clipboard(self):
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard_text.strip())
                self._on_url_input_change()
                self._start_analyze()
        except Exception:
            pass

    def _on_url_input_change(self, event=None):
        url = self.url_entry.get().strip()
        if not url:
            self.platform_badge.configure(
                text="Platform Auto-Detect: Ready for 25+ platforms (YouTube, Instagram, TikTok, Facebook, Twitter, Reddit...)",
                text_color="gray",
                fg_color="transparent"
            )
            self.detected_platform = None
            return

        platform = PlatformDetector.detect(url)
        if platform:
            self.detected_platform = platform
            p_name = platform["name"]
            p_tag = platform.get("tag", f"[{p_name}]")
            p_color = platform.get("color", "#1565C0")
            desc = platform.get("description", "")

            self.platform_badge.configure(
                text=f"  Detected: {p_tag}  --  {desc}  ",
                text_color="white",
                fg_color=p_color,
                corner_radius=6
            )

            if platform.get("default_type") == "audio" and self.type_segmented.get() != "Audio Only":
                self.type_segmented.set("Audio Only")
                self._on_type_changed("Audio Only")
        else:
            self.platform_badge.configure(
                text="  Detected: [Direct Web Media Link]  ",
                text_color="white",
                fg_color="#37474F",
                corner_radius=6
            )

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

        self._on_url_input_change()
        self.analyze_btn.configure(state="disabled", text="Loading...")

        # Show Loading Screen
        self.preview_card.pack_forget()
        self.loading_card.pack(fill="x", padx=10, pady=6, after=self.url_frame)
        self.loading_card.start("Analyzing media from source... Please wait")

        def run_analysis():
            info = PlaylistManager.get_playlist_info(url)
            self.after(0, lambda: self._apply_analysis_result(info, url))

        threading.Thread(target=run_analysis, daemon=True).start()

    def _apply_analysis_result(self, info: Optional[Dict[str, Any]], url: str):
        # Stop and hide loading screen
        self.loading_card.stop()
        self.loading_card.pack_forget()
        self.preview_card.pack(fill="x", padx=10, pady=6, after=self.url_frame)

        self.analyze_btn.configure(state="normal", text="Analyze")
        if not info:
            logger.error("Could not fetch media information.")
            return

        self.analyzed_url = url
        p_name = self.detected_platform["name"] if self.detected_platform else "Media"

        if info.get('is_playlist'):
            count = info.get('count', 0)
            self.preview_card.set_info(
                title=f"Playlist: {info.get('title')}",
                channel=f"{info.get('uploader')} ({count} items)",
                duration=f"Total: {count} items",
                thumbnail_url=info.get('thumbnail')
            )
            logger.info(f"Loaded Playlist '{info.get('title')}' with {count} items.")
        else:
            video = info.get('videos', [{}])[0]
            self.preview_card.set_info(
                title=f"[{p_name}] {video.get('title', 'Media Clip')}",
                channel=info.get('uploader', 'Unknown'),
                duration=video.get('duration', '--:--'),
                thumbnail_url=video.get('thumbnail')
            )
            logger.info(f"Loaded {p_name}: '{video.get('title')}'")

    def _start_download(self):
        url = self.url_entry.get().strip()
        if not is_valid_url(url):
            logger.warning("Invalid URL entered.")
            return

        out_folder = config.get("download_dir", os.path.abspath("downloads"))
        ok, err = verify_directory_writable(out_folder)
        if not ok:
            logger.error(f"Cannot write to output folder: {err}")
            self.progress_card.set_status(f"Error: {err}", text_color="#C62828")
            return

        media_type = "video" if self.type_segmented.get() == "Video" else "audio"

        res_raw = self.res_combo.get().split()[0].lower()
        resolution = "best" if "best" in res_raw else res_raw

        video_format = self.vfmt_combo.get()
        audio_format = self.afmt_combo.get().split()[0].lower()
        audio_bitrate = self.abtr_combo.get().split()[0]
        embed_sub = self.embed_sub_var.get()
        sub_lang = self.sub_lang_combo.get()
        embed_thumb = self.embed_thumb_var.get()
        threads = int(self.threads_combo.get().split()[0])

        self.is_download_active = True
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.stop_btn.configure(state="normal")
        self.progress_card.reset()
        self.progress_card.set_status("Initializing download engine...")

        def worker():
            success = downloader.download(
                url=url,
                output_dir=out_folder,
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
        self.progress_card.set_status("Cancelling...", text_color="#C62828")

    def _on_progress(self, data: Dict[str, Any]):
        status = data.get("status")

        pl_index = data.get("playlist_index", 0)
        pl_total = data.get("playlist_total", 0)
        if pl_total > 0:
            self.progress_card.update_batch_progress(pl_index, pl_total, data.get("title", ""))

        if status == "downloading":
            item_tag = f"[{pl_index}/{pl_total}] " if pl_total > 0 else ""
            self.progress_card.update_file_progress(
                percent=data.get("percent", 0.0),
                status=f"Downloading {item_tag}{data.get('filename', '')}",
                speed=data.get("speed_str"),
                eta=data.get("eta_str"),
                transferred_str=data.get("downloaded_str"),
                total_str=data.get("total_str")
            )
        elif status == "processing":
            self.progress_card.set_status(data.get("message", "Processing media..."), text_color="#1E88E5")

    def _on_download_complete(self, success: bool):
        self.is_download_active = False
        self.download_btn.configure(state="normal", text="Start Download")
        self.stop_btn.configure(state="disabled")

        if success:
            self.progress_card.update_file_progress(100.0, status="Download Completed Successfully")
            self.progress_card.set_status("Completed Successfully", text_color="#43A047")
        else:
            self.progress_card.set_status("Download Stopped or Failed", text_color="#C62828")

    def _open_downloads_folder(self):
        folder = config.get("download_dir", os.path.abspath("downloads"))
        os.makedirs(folder, exist_ok=True)
        open_file_or_folder(folder)

    def _on_log_message(self, message: str, level: str):
        try:
            self.log_textbox.insert(tk.END, message + "\n")
            lines = int(self.log_textbox.index('end-1c').split('.')[0])
            if lines > 300:
                self.log_textbox.delete("1.0", "50.0")
            self.log_textbox.see(tk.END)
        except Exception:
            pass

    def _clear_log(self):
        self.log_textbox.delete("1.0", tk.END)
