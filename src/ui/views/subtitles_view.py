import os
import threading
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from typing import Dict, Any, List

from src.core.subtitles import SubtitleManager, POPULAR_LANGUAGES
from src.ui.components.progress_card import ProgressCard
from src.utils.config import config
from src.utils.logger import logger
from src.utils.helpers import is_valid_url, open_file_or_folder, verify_directory_writable

class SubtitlesView(ctk.CTkFrame):
    """View for extracting, browsing, and downloading subtitles in 100+ languages without emojis."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.available_subs: Dict[str, Any] = {"manual": [], "auto": []}
        self.is_downloading = False

        self._build_ui()

    def _build_ui(self):
        # 1. URL Bar
        url_card = ctk.CTkFrame(self, corner_radius=10)
        url_card.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            url_card,
            text="Video URL for Subtitle / Caption Extraction:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 4))

        row = ctk.CTkFrame(url_card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(0, 10))

        self.url_entry = ctk.CTkEntry(
            row,
            placeholder_text="Paste YouTube link to inspect subtitles and translations...",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Paste",
            width=80,
            height=38,
            command=self._paste_clipboard
        ).pack(side="left", padx=(0, 8))

        self.scan_btn = ctk.CTkButton(
            row,
            text="Scan Languages",
            width=130,
            height=38,
            fg_color="#00695C",
            hover_color="#004D40",
            command=self._scan_languages
        )
        self.scan_btn.pack(side="left")

        # 2. Subtitles Table / List
        self.list_card = ctk.CTkFrame(self, corner_radius=10)
        self.list_card.pack(fill="both", expand=True, padx=10, pady=6)

        header_row = ctk.CTkFrame(self.list_card, fg_color="transparent")
        header_row.pack(fill="x", padx=15, pady=(10, 6))

        self.sub_count_lbl = ctk.CTkLabel(
            header_row,
            text="Available Subtitle Tracks: (Scan a video link)",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.sub_count_lbl.pack(side="left")

        self.sub_scroll = ctk.CTkScrollableFrame(self.list_card, height=200)
        self.sub_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.empty_msg = ctk.CTkLabel(
            self.sub_scroll,
            text="Enter a video link and click 'Scan Languages' to find all available caption and translation tracks.",
            text_color="gray"
        )
        self.empty_msg.pack(pady=40)

        # 3. Download Options Bar
        opts_card = ctk.CTkFrame(self, corner_radius=10)
        opts_card.pack(fill="x", padx=10, pady=(6, 10))

        opt_row = ctk.CTkFrame(opts_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=15, pady=8)

        ctk.CTkLabel(opt_row, text="Select Language:").pack(side="left", padx=(0, 6))
        self.lang_combo = ctk.CTkComboBox(
            opt_row,
            values=[f"{code} - {name}" for code, name in POPULAR_LANGUAGES],
            width=200
        )
        self.lang_combo.set("en - English")
        self.lang_combo.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(opt_row, text="Format:").pack(side="left", padx=(0, 6))
        self.fmt_combo = ctk.CTkComboBox(opt_row, values=["srt", "vtt"], width=80)
        self.fmt_combo.set("srt")
        self.fmt_combo.pack(side="left", padx=(0, 15))

        self.auto_cb_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_row, text="Include Auto-Translated Captions", variable=self.auto_cb_var).pack(side="left")

        btn_row = ctk.CTkFrame(opts_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 10))

        self.download_btn = ctk.CTkButton(
            btn_row,
            text="Download Subtitle File (.srt / .vtt)",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._start_download_sub
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.folder_btn = ctk.CTkButton(
            btn_row,
            text="Open Folder",
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
                self._scan_languages()
        except Exception:
            pass

    def _scan_languages(self):
        url = self.url_entry.get().strip()
        if not is_valid_url(url):
            logger.warning("Please enter a valid video link.")
            return

        self.scan_btn.configure(state="disabled", text="Scanning...")

        def worker():
            subs = SubtitleManager.get_available_subtitles(url)
            self.after(0, lambda: self._render_subtitles(subs))

        threading.Thread(target=worker, daemon=True).start()

    def _render_subtitles(self, subs: Dict[str, Any]):
        self.scan_btn.configure(state="normal", text="Scan Languages")
        self.available_subs = subs

        manual = subs.get("manual", [])
        auto = subs.get("auto", [])
        total = len(manual) + len(auto)

        self.sub_count_lbl.configure(
            text=f"Available Tracks: {len(manual)} Official Subtitles, {len(auto)} Auto-Translations"
        )

        for w in self.sub_scroll.winfo_children():
            w.destroy()

        if total == 0:
            ctk.CTkLabel(self.sub_scroll, text="No subtitles found for this media.", text_color="gray").pack(pady=20)
            return

        if manual:
            ctk.CTkLabel(
                self.sub_scroll,
                text="-- Official Subtitle Tracks --",
                font=ctk.CTkFont(weight="bold"),
                text_color="#1E88E5"
            ).pack(anchor="w", padx=6, pady=4)

            for s in manual:
                row = ctk.CTkFrame(self.sub_scroll, fg_color=("gray90", "gray17"), height=30)
                row.pack(fill="x", padx=4, pady=2)
                ctk.CTkLabel(row, text=f"[{s['code']}]", width=60, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
                ctk.CTkLabel(row, text=s['name']).pack(side="left", padx=4)
                ctk.CTkLabel(row, text="Official", text_color="#43A047").pack(side="right", padx=10)

        if auto:
            ctk.CTkLabel(
                self.sub_scroll,
                text="-- Auto-Generated & Translated Tracks --",
                font=ctk.CTkFont(weight="bold"),
                text_color="#FB8C00"
            ).pack(anchor="w", padx=6, pady=(10, 4))

            for s in auto[:30]:
                row = ctk.CTkFrame(self.sub_scroll, fg_color=("gray90", "gray17"), height=30)
                row.pack(fill="x", padx=4, pady=2)
                ctk.CTkLabel(row, text=f"[{s['code']}]", width=60, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
                ctk.CTkLabel(row, text=s['name']).pack(side="left", padx=4)
                ctk.CTkLabel(row, text="Auto-Translated", text_color="gray").pack(side="right", padx=10)

            if len(auto) > 30:
                ctk.CTkLabel(
                    self.sub_scroll,
                    text=f"... and {len(auto) - 30} more languages available (select above to download)",
                    text_color="gray"
                ).pack(pady=4)

    def _start_download_sub(self):
        url = self.url_entry.get().strip()
        if not is_valid_url(url):
            logger.warning("Please enter a valid video link.")
            return

        out_dir = config.get("download_dir", os.path.abspath("downloads"))
        ok, err = verify_directory_writable(out_dir)
        if not ok:
            logger.error(f"Cannot write to output folder: {err}")
            self.progress_card.set_status(f"Error: {err}", text_color="#C62828")
            return

        lang_selection = self.lang_combo.get().split(" - ")[0].strip()
        fmt = self.fmt_combo.get()
        include_auto = self.auto_cb_var.get()

        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="Downloading Subtitles...")
        self.progress_card.reset()
        self.progress_card.set_status(f"Fetching subtitle [{lang_selection}]...")

        def worker():
            success = SubtitleManager.download_subtitles_only(
                url=url,
                output_dir=out_dir,
                language_code=lang_selection,
                sub_format=fmt,
                include_auto=include_auto
            )
            self.after(0, lambda: self._on_download_complete(success))

        threading.Thread(target=worker, daemon=True).start()

    def _on_download_complete(self, success: bool):
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="Download Subtitle File (.srt / .vtt)")
        if success:
            self.progress_card.update_file_progress(100.0, status="Subtitles downloaded successfully")
            self.progress_card.set_status("Completed Successfully", text_color="#43A047")
        else:
            self.progress_card.set_status("Failed to download subtitles", text_color="#C62828")

    def _open_folder(self):
        folder = config.get("download_dir", os.path.abspath("downloads"))
        open_file_or_folder(folder)
