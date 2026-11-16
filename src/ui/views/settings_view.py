import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

from src.utils.config import config
from src.utils.ffmpeg_checker import FFmpegChecker
from src.utils.logger import logger
from src.utils.helpers import verify_directory_writable

class SettingsView(ctk.CTkScrollableFrame):
    """View to adjust application preferences, download destination, and performance without emojis."""

    def __init__(self, master, on_theme_change=None, **kwargs):
        super().__init__(master, **kwargs)

        self.on_theme_change = on_theme_change
        self._build_ui()
        self.load_values()

    def _build_ui(self):
        # 1. Storage & Downloads Section
        store_card = ctk.CTkFrame(self, corner_radius=10)
        store_card.pack(fill="x", padx=10, pady=(10, 8))

        ctk.CTkLabel(
            store_card,
            text="Storage & Download Destination",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        dir_row = ctk.CTkFrame(store_card, fg_color="transparent")
        dir_row.pack(fill="x", padx=15, pady=(0, 4))

        ctk.CTkLabel(dir_row, text="Target Directory Path (Standard Windows/Linux Downloads folder):").pack(anchor="w", pady=(0, 4))

        input_row = ctk.CTkFrame(dir_row, fg_color="transparent")
        input_row.pack(fill="x")

        self.dir_entry = ctk.CTkEntry(input_row, height=36)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            input_row,
            text="Browse...",
            width=90,
            height=36,
            command=self._browse_download_dir
        ).pack(side="left")

        self.path_status_lbl = ctk.CTkLabel(
            store_card,
            text="",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.path_status_lbl.pack(anchor="w", padx=15, pady=(2, 10))

        # 2. Performance & Speed Optimization
        perf_card = ctk.CTkFrame(self, corner_radius=10)
        perf_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            perf_card,
            text="Performance & Speed Optimization",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        thread_row = ctk.CTkFrame(perf_card, fg_color="transparent")
        thread_row.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            thread_row,
            text="Concurrent Connections (Fragment Threads):"
        ).pack(anchor="w", pady=(0, 4))

        self.threads_combo = ctk.CTkComboBox(
            thread_row,
            values=["2 (Low Resource)", "4 (Standard)", "8 (High Speed)", "16 (Turbo)"],
            width=220
        )
        self.threads_combo.pack(anchor="w")

        # 3. Defaults Preferences
        defaults_card = ctk.CTkFrame(self, corner_radius=10)
        defaults_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            defaults_card,
            text="Quality & Format Preferences",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        grid = ctk.CTkFrame(defaults_card, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=(0, 12))

        c1 = ctk.CTkFrame(grid, fg_color="transparent")
        c1.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(c1, text="Preferred Resolution:").pack(anchor="w")
        self.default_res_combo = ctk.CTkComboBox(
            c1,
            values=["Best", "2160p", "1440p", "1080p", "720p", "480p"],
            width=120
        )
        self.default_res_combo.pack(anchor="w")

        c2 = ctk.CTkFrame(grid, fg_color="transparent")
        c2.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(c2, text="Default Video Container:").pack(anchor="w")
        self.default_vfmt_combo = ctk.CTkComboBox(
            c2,
            values=["mp4", "mkv", "webm"],
            width=100
        )
        self.default_vfmt_combo.pack(anchor="w")

        c3 = ctk.CTkFrame(grid, fg_color="transparent")
        c3.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(c3, text="Default Audio Format:").pack(anchor="w")
        self.default_afmt_combo = ctk.CTkComboBox(
            c3,
            values=["mp3", "m4a", "flac", "wav", "opus"],
            width=100
        )
        self.default_afmt_combo.pack(anchor="w")

        c4 = ctk.CTkFrame(grid, fg_color="transparent")
        c4.pack(side="left")
        ctk.CTkLabel(c4, text="Audio Bitrate:").pack(anchor="w")
        self.default_abtr_combo = ctk.CTkComboBox(
            c4,
            values=["320k", "256k", "192k", "128k"],
            width=100
        )
        self.default_abtr_combo.pack(anchor="w")

        # 4. FFmpeg Engine Status
        ffmpeg_card = ctk.CTkFrame(self, corner_radius=10)
        ffmpeg_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            ffmpeg_card,
            text="FFmpeg Engine Status",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        ff_row = ctk.CTkFrame(ffmpeg_card, fg_color="transparent")
        ff_row.pack(fill="x", padx=15, pady=(0, 6))

        self.ffmpeg_status_label = ctk.CTkLabel(
            ff_row,
            text="Checking FFmpeg status...",
            anchor="w",
            wraplength=600,
            justify="left"
        )
        self.ffmpeg_status_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            ff_row,
            text="Verify Engine",
            width=110,
            command=self._check_ffmpeg_status
        ).pack(side="right")

        custom_ff_row = ctk.CTkFrame(ffmpeg_card, fg_color="transparent")
        custom_ff_row.pack(fill="x", padx=15, pady=(4, 12))

        ctk.CTkLabel(custom_ff_row, text="Custom FFmpeg Binary Path (optional):").pack(anchor="w", pady=(0, 4))
        self.custom_ff_entry = ctk.CTkEntry(custom_ff_row, placeholder_text="Leave blank to use system FFmpeg")
        self.custom_ff_entry.pack(fill="x")

        # 5. Appearance & UI Theme
        ui_card = ctk.CTkFrame(self, corner_radius=10)
        ui_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            ui_card,
            text="Appearance Mode",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        ui_row = ctk.CTkFrame(ui_card, fg_color="transparent")
        ui_row.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(ui_row, text="Color Theme:").pack(side="left", padx=(0, 8))
        self.theme_segmented = ctk.CTkSegmentedButton(
            ui_row,
            values=["Dark", "Light", "System"],
            command=self._on_theme_select
        )
        self.theme_segmented.pack(side="left")

        # 6. Save & Reset Action Bar
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=(10, 20))

        self.save_btn = ctk.CTkButton(
            actions,
            text="Save Settings",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.save_values
        )
        self.save_btn.pack(side="left", padx=(0, 10))

        self.reset_btn = ctk.CTkButton(
            actions,
            text="Reset to Defaults",
            height=38,
            fg_color="gray40",
            hover_color="#C62828",
            command=self.reset_defaults
        )
        self.reset_btn.pack(side="left")

    def load_values(self):
        dest = config.get("download_dir", os.path.abspath("downloads"))
        self.dir_entry.delete(0, tk.END)
        self.dir_entry.insert(0, dest)
        self._validate_path_display(dest)

        threads = config.get("max_concurrent_fragments", 8)
        self.threads_combo.set(f"{threads} (High Speed)" if threads == 8 else f"{threads}")

        self.default_res_combo.set(config.get("preferred_resolution", "1080p"))
        self.default_vfmt_combo.set(config.get("preferred_video_format", "mp4"))
        self.default_afmt_combo.set(config.get("preferred_audio_format", "mp3"))
        self.default_abtr_combo.set(config.get("preferred_audio_bitrate", "320k"))

        self.custom_ff_entry.delete(0, tk.END)
        self.custom_ff_entry.insert(0, config.get("custom_ffmpeg_path", ""))

        theme = config.get("theme", "dark").capitalize()
        self.theme_segmented.set(theme)

        self._check_ffmpeg_status()

    def _validate_path_display(self, path: str):
        ok, msg = verify_directory_writable(path)
        if ok:
            self.path_status_lbl.configure(text=f"[Status: Valid and writable]", text_color="#43A047")
        else:
            self.path_status_lbl.configure(text=f"[Status: {msg}]", text_color="#C62828")

    def save_values(self):
        download_dir = self.dir_entry.get().strip() or os.path.abspath("downloads")
        ok, msg = verify_directory_writable(download_dir)
        if not ok:
            logger.error(f"Cannot save settings: {msg}")
            self._validate_path_display(download_dir)
            return

        config.set("download_dir", download_dir)
        config.set("first_run_completed", True)

        threads_str = self.threads_combo.get().split()[0]
        config.set("max_concurrent_fragments", int(threads_str))

        config.set("preferred_resolution", self.default_res_combo.get())
        config.set("preferred_video_format", self.default_vfmt_combo.get())
        config.set("preferred_audio_format", self.default_afmt_combo.get())
        config.set("preferred_audio_bitrate", self.default_abtr_combo.get())

        custom_ff = self.custom_ff_entry.get().strip()
        config.set("custom_ffmpeg_path", custom_ff)

        theme = self.theme_segmented.get().lower()
        config.set("theme", theme)

        self._validate_path_display(download_dir)
        logger.success("Settings updated and saved successfully.")
        self.save_btn.configure(text="Settings Saved")
        self.after(1500, lambda: self.save_btn.configure(text="Save Settings"))

    def reset_defaults(self):
        config.reset_to_defaults()
        self.load_values()
        logger.info("Settings reset to defaults.")

    def _browse_download_dir(self):
        folder = filedialog.askdirectory(title="Select Downloads Directory")
        if folder:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, folder)
            self._validate_path_display(folder)

    def _on_theme_select(self, theme_name):
        mode = theme_name.lower()
        ctk.set_appearance_mode(mode)
        config.set("theme", mode)
        if self.on_theme_change:
            self.on_theme_change(mode)

    def _check_ffmpeg_status(self):
        custom_path = self.custom_ff_entry.get().strip() or None
        is_ok, msg = FFmpegChecker.check_ffmpeg(custom_path)
        if is_ok:
            self.ffmpeg_status_label.configure(
                text=f"[OK] {msg}",
                text_color="#43A047"
            )
        else:
            self.ffmpeg_status_label.configure(
                text=f"[FAIL] {msg}",
                text_color="#C62828"
            )
