import os
import threading
import tkinter as tk
import customtkinter as ctk
from typing import List, Dict, Any, Optional

from src.core.downloader import downloader
from src.core.playlist import PlaylistManager
from src.ui.components.progress_card import ProgressCard
from src.utils.config import config
from src.utils.logger import logger
from src.utils.helpers import is_valid_url, open_file_or_folder

class PlaylistView(ctk.CTkFrame):
    """View for inspecting YouTube playlists and selectively downloading items."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.playlist_data: Optional[Dict[str, Any]] = None
        self.item_check_vars: List[ctk.BooleanVar] = []
        self.item_widgets: List[ctk.CTkFrame] = []
        self.is_downloading = False

        self._build_ui()

    def _build_ui(self):
        # 1. URL & Fetch Bar
        input_card = ctk.CTkFrame(self, corner_radius=12)
        input_card.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            input_card,
            text="Playlist URL:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 4))

        row = ctk.CTkFrame(input_card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(0, 10))

        self.url_entry = ctk.CTkEntry(
            row,
            placeholder_text="Enter playlist link (e.g. https://www.youtube.com/playlist?list=...)",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.paste_btn = ctk.CTkButton(
            row,
            text="📋 Paste",
            width=80,
            height=38,
            command=self._paste_clipboard
        )
        self.paste_btn.pack(side="left", padx=(0, 8))

        self.fetch_btn = ctk.CTkButton(
            row,
            text="📥 Load Playlist",
            width=120,
            height=38,
            fg_color="#2B7A78",
            hover_color="#17252A",
            command=self._start_fetch
        )
        self.fetch_btn.pack(side="left")

        # 2. Playlist Header Info Banner
        self.header_card = ctk.CTkFrame(self, corner_radius=12)
        self.header_card.pack(fill="x", padx=10, pady=6)

        self.title_label = ctk.CTkLabel(
            self.header_card,
            text="No Playlist Loaded",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.title_label.pack(anchor="w", padx=15, pady=(8, 2))

        self.meta_label = ctk.CTkLabel(
            self.header_card,
            text="Channel: -- | Videos: 0",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        self.meta_label.pack(anchor="w", padx=15, pady=(0, 8))

        # 3. Selection & Filter Toolbar
        self.toolbar_card = ctk.CTkFrame(self, corner_radius=12)
        self.toolbar_card.pack(fill="x", padx=10, pady=6)

        tool_row = ctk.CTkFrame(self.toolbar_card, fg_color="transparent")
        tool_row.pack(fill="x", padx=12, pady=8)

        ctk.CTkButton(
            tool_row,
            text="Select All",
            width=85,
            height=28,
            command=self._select_all
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            tool_row,
            text="Deselect All",
            width=95,
            height=28,
            command=self._deselect_all
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            tool_row,
            text="Invert",
            width=70,
            height=28,
            command=self._invert_selection
        ).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(tool_row, text="Range (e.g. 1-5, 8):").pack(side="left", padx=(0, 4))
        self.range_entry = ctk.CTkEntry(tool_row, width=120, height=28)
        self.range_entry.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            tool_row,
            text="Apply Range",
            width=90,
            height=28,
            command=self._apply_range
        ).pack(side="left")

        # 4. Scrollable Video Checklist
        self.list_container = ctk.CTkScrollableFrame(self, height=220, corner_radius=12)
        self.list_container.pack(fill="both", expand=True, padx=10, pady=6)

        self.empty_label = ctk.CTkLabel(
            self.list_container,
            text="Load a playlist to view and select individual videos.",
            text_color="gray"
        )
        self.empty_label.pack(pady=40)

        # 5. Format & Download Bar
        bottom_card = ctk.CTkFrame(self, corner_radius=12)
        bottom_card.pack(fill="x", padx=10, pady=(6, 10))

        opt_row = ctk.CTkFrame(bottom_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=15, pady=8)

        self.p_type_var = ctk.StringVar(value="video")
        self.p_type_combo = ctk.CTkSegmentedButton(
            opt_row,
            values=["Video", "Audio"],
            command=self._on_playlist_type_changed
        )
        self.p_type_combo.set("Video")
        self.p_type_combo.pack(side="left", padx=(0, 15))

        self.p_res_label = ctk.CTkLabel(opt_row, text="Resolution:")
        self.p_res_label.pack(side="left", padx=(0, 4))
        self.p_res_combo = ctk.CTkComboBox(
            opt_row,
            values=["1080p", "720p", "480p", "360p", "Best"],
            width=100
        )
        self.p_res_combo.set("1080p")
        self.p_res_combo.pack(side="left", padx=(0, 15))

        self.p_format_label = ctk.CTkLabel(opt_row, text="Format:")
        self.p_format_label.pack(side="left", padx=(0, 4))
        self.p_format_combo = ctk.CTkComboBox(
            opt_row,
            values=["mp4", "mkv", "webm"],
            width=90
        )
        self.p_format_combo.set("mp4")
        self.p_format_combo.pack(side="left")

        btn_row = ctk.CTkFrame(bottom_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 10))

        self.download_selected_btn = ctk.CTkButton(
            btn_row,
            text="⚡ Download Selected Videos",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._start_download_selected
        )
        self.download_selected_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            btn_row,
            text="⏹ Cancel",
            height=38,
            width=90,
            fg_color="#D9534F",
            hover_color="#C9302C",
            state="disabled",
            command=self._cancel_download
        )
        self.stop_btn.pack(side="left", padx=(0, 10))

        self.folder_btn = ctk.CTkButton(
            btn_row,
            text="📂 Open Folder",
            height=38,
            width=110,
            command=self._open_folder
        )
        self.folder_btn.pack(side="left")

        # Progress Card
        self.progress_card = ProgressCard(self)
        self.progress_card.pack(fill="x", padx=10, pady=(0, 10))

    def _paste_clipboard(self):
        try:
            txt = self.clipboard_get()
            if txt:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, txt.strip())
                self._start_fetch()
        except Exception:
            pass

    def _on_playlist_type_changed(self, value):
        if value == "Audio":
            self.p_res_label.pack_forget()
            self.p_res_combo.pack_forget()
            self.p_format_combo.configure(values=["mp3", "m4a", "flac", "wav"])
            self.p_format_combo.set("mp3")
        else:
            self.p_res_label.pack(side="left", padx=(0, 4))
            self.p_res_combo.pack(side="left", padx=(0, 15))
            self.p_format_combo.configure(values=["mp4", "mkv", "webm"])
            self.p_format_combo.set("mp4")

    def _start_fetch(self):
        url = self.url_entry.get().strip()
        if not is_valid_url(url):
            logger.warning("Please enter a valid playlist link.")
            return

        self.fetch_btn.configure(state="disabled", text="Loading...")

        def worker():
            info = PlaylistManager.get_playlist_info(url)
            self.after(0, lambda: self._render_playlist(info))

        threading.Thread(target=worker, daemon=True).start()

    def _render_playlist(self, info: Optional[Dict[str, Any]]):
        self.fetch_btn.configure(state="normal", text="📥 Load Playlist")
        if not info:
            logger.error("Failed to load playlist data.")
            return

        self.playlist_data = info
        self.title_label.configure(text=f"Playlist: {info.get('title')}")
        self.meta_label.configure(text=f"Channel: {info.get('uploader')} | Total Videos: {info.get('count')}")

        # Clear existing list items
        for widget in self.list_container.winfo_children():
            widget.destroy()
        self.item_check_vars.clear()
        self.item_widgets.clear()

        videos = info.get('videos', [])
        for v in videos:
            row_frame = ctk.CTkFrame(self.list_container, fg_color=("gray90", "gray17"), corner_radius=6)
            row_frame.pack(fill="x", padx=4, pady=2)

            var = ctk.BooleanVar(value=True)
            self.item_check_vars.append(var)

            cb = ctk.CTkCheckBox(row_frame, text="", variable=var, width=24)
            cb.pack(side="left", padx=(8, 4), pady=6)

            idx_lbl = ctk.CTkLabel(row_frame, text=f"#{v['index']}", font=ctk.CTkFont(weight="bold"), width=35)
            idx_lbl.pack(side="left", padx=2)

            t_lbl = ctk.CTkLabel(row_frame, text=v['title'], anchor="w", wraplength=480, justify="left")
            t_lbl.pack(side="left", fill="x", expand=True, padx=6)

            dur_lbl = ctk.CTkLabel(row_frame, text=v['duration'], text_color="gray", width=60)
            dur_lbl.pack(side="right", padx=(4, 10))

            self.item_widgets.append(row_frame)

    def _select_all(self):
        for var in self.item_check_vars:
            var.set(True)

    def _deselect_all(self):
        for var in self.item_check_vars:
            var.set(False)

    def _invert_selection(self):
        for var in self.item_check_vars:
            var.set(not var.get())

    def _apply_range(self):
        if not self.playlist_data:
            return
        range_str = self.range_entry.get().strip()
        count = self.playlist_data.get('count', 0)
        selected_indices = PlaylistManager.parse_range_string(range_str, count)
        for idx, var in enumerate(self.item_check_vars, start=1):
            var.set(idx in selected_indices)

    def _start_download_selected(self):
        if not self.playlist_data:
            logger.warning("No playlist loaded.")
            return

        selected_indices = [idx for idx, var in enumerate(self.item_check_vars, start=1) if var.get()]
        if not selected_indices:
            logger.warning("No videos selected!")
            return

        range_query = ",".join(str(i) for i in selected_indices)
        url = self.url_entry.get().strip()
        media_type = "video" if self.p_type_combo.get() == "Video" else "audio"
        resolution = self.p_res_combo.get() if media_type == "video" else "best"
        target_format = self.p_format_combo.get()

        self.is_downloading = True
        self.download_selected_btn.configure(state="disabled", text="⏳ Downloading...")
        self.stop_btn.configure(state="normal")
        self.progress_card.reset()
        self.progress_card.set_status(f"Starting batch ({len(selected_indices)} videos)...")

        def worker():
            success = downloader.download(
                url=url,
                media_type=media_type,
                resolution=resolution,
                video_format=target_format if media_type == "video" else "mp4",
                audio_format=target_format if media_type == "audio" else "mp3",
                playlist_items=range_query,
                progress_callback=lambda d: self.after(0, lambda: self._on_progress(d))
            )
            self.after(0, lambda: self._on_complete(success))

        threading.Thread(target=worker, daemon=True).start()

    def _cancel_download(self):
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
            self.progress_card.set_status(data.get("message", "Processing video..."))

    def _on_complete(self, success: bool):
        self.is_downloading = False
        self.download_selected_btn.configure(state="normal", text="⚡ Download Selected Videos")
        self.stop_btn.configure(state="disabled")

        if success:
            self.progress_card.update_progress(100.0, status="Playlist Download Complete!")
            self.progress_card.set_status("Batch Finished! 🎉", color="#4CAF50")
        else:
            self.progress_card.set_status("Stopped or Error Occurred", color="#D9534F")

    def _open_folder(self):
        folder = config.get("download_dir", os.path.abspath("downloads"))
        os.makedirs(folder, exist_ok=True)
        open_file_or_folder(folder)

