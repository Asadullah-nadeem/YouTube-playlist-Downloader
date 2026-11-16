import os
import threading
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from typing import Dict, Any

from src.core.converter import MediaConverter
from src.ui.components.progress_card import ProgressCard
from src.utils.config import config
from src.utils.logger import logger
from src.utils.helpers import format_bytes, format_seconds, open_file_or_folder, verify_directory_writable

class ConverterView(ctk.CTkScrollableFrame):
    """View for converting media files, extracting audio, compressing, and trimming without emojis."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.converter = MediaConverter(config.get("custom_ffmpeg_path"))
        self.selected_file = ""
        self.is_converting = False

        self._build_ui()

    def _build_ui(self):
        # 1. File Selection Section
        file_card = ctk.CTkFrame(self, corner_radius=10)
        file_card.pack(fill="x", padx=10, pady=(10, 8))

        ctk.CTkLabel(
            file_card,
            text="Source Media File:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 4))

        row = ctk.CTkFrame(file_card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(0, 10))

        self.file_entry = ctk.CTkEntry(
            row,
            placeholder_text="Select a video or audio file to convert...",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            row,
            text="Browse...",
            width=90,
            height=38,
            command=self._browse_file
        )
        self.browse_btn.pack(side="left")

        # File Meta Info Row
        self.meta_frame = ctk.CTkFrame(file_card, fg_color="transparent")
        self.meta_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.file_info_lbl = ctk.CTkLabel(
            self.meta_frame,
            text="File Size: -- | Duration: --:--",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.file_info_lbl.pack(side="left")

        # 2. Conversion Mode & Options
        options_card = ctk.CTkFrame(self, corner_radius=10)
        options_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            options_card,
            text="Conversion Settings:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        type_row = ctk.CTkFrame(options_card, fg_color="transparent")
        type_row.pack(fill="x", padx=15, pady=4)

        self.mode_var = ctk.StringVar(value="convert_video")
        self.mode_segmented = ctk.CTkSegmentedButton(
            type_row,
            values=["Convert Video", "Extract Audio", "Compress Video", "Trim Clip"],
            command=self._on_mode_changed
        )
        self.mode_segmented.set("Convert Video")
        self.mode_segmented.pack(side="left")

        self.dyn_options_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        self.dyn_options_frame.pack(fill="x", padx=15, pady=10)

        # Target Format
        fmt_row = ctk.CTkFrame(self.dyn_options_frame, fg_color="transparent")
        fmt_row.pack(fill="x", pady=4)

        self.format_label = ctk.CTkLabel(fmt_row, text="Target Format:")
        self.format_label.pack(side="left", padx=(0, 10))

        self.format_combo = ctk.CTkComboBox(
            fmt_row,
            values=["mp4", "mkv", "webm", "avi", "mov"],
            width=110
        )
        self.format_combo.set("mp4")
        self.format_combo.pack(side="left", padx=(0, 20))

        # Bitrate / Codec
        self.codec_label = ctk.CTkLabel(fmt_row, text="Video Codec:")
        self.codec_label.pack(side="left", padx=(0, 10))

        self.codec_combo = ctk.CTkComboBox(
            fmt_row,
            values=["libx264 (H.264)", "libx265 (HEVC)", "copy (Direct Remux)"],
            width=160
        )
        self.codec_combo.set("libx264 (H.264)")
        self.codec_combo.pack(side="left", padx=(0, 20))

        self.audio_bitrate_label = ctk.CTkLabel(fmt_row, text="Audio Bitrate:")
        self.audio_bitrate_combo = ctk.CTkComboBox(
            fmt_row,
            values=["320k (Maximum Quality)", "256k", "192k", "128k"],
            width=170
        )
        self.audio_bitrate_combo.set("320k (Maximum Quality)")

        # Trimming Row
        self.trim_frame = ctk.CTkFrame(self.dyn_options_frame, fg_color="transparent")

        ctk.CTkLabel(self.trim_frame, text="Start Time (HH:MM:SS):").pack(side="left", padx=(0, 6))
        self.start_time_entry = ctk.CTkEntry(self.trim_frame, width=100)
        self.start_time_entry.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(self.trim_frame, text="End Time (HH:MM:SS):").pack(side="left", padx=(0, 6))
        self.end_time_entry = ctk.CTkEntry(self.trim_frame, width=100)
        self.end_time_entry.pack(side="left")

        # Compression Preset Row
        self.compress_frame = ctk.CTkFrame(self.dyn_options_frame, fg_color="transparent")

        ctk.CTkLabel(self.compress_frame, text="Compression Preset:").pack(side="left", padx=(0, 10))
        self.compress_preset_combo = ctk.CTkComboBox(
            self.compress_frame,
            values=["Balanced (CRF 23)", "High Compression (CRF 28)", "Smallest File (CRF 32)"],
            width=210
        )
        self.compress_preset_combo.set("Balanced (CRF 23)")
        self.compress_preset_combo.pack(side="left")

        # Output folder row
        out_row = ctk.CTkFrame(options_card, fg_color="transparent")
        out_row.pack(fill="x", padx=15, pady=(4, 12))

        ctk.CTkLabel(out_row, text="Output Directory:").pack(side="left", padx=(0, 8))
        self.out_dir_entry = ctk.CTkEntry(out_row)
        self.out_dir_entry.insert(0, config.get("download_dir", os.path.abspath("downloads")))
        self.out_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            out_row,
            text="Change...",
            width=85,
            command=self._browse_out_dir
        ).pack(side="left")

        # 3. Actions Row
        actions_row = ctk.CTkFrame(self, fg_color="transparent")
        actions_row.pack(fill="x", padx=10, pady=8)

        self.convert_btn = ctk.CTkButton(
            actions_row,
            text="Start Conversion",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_conversion
        )
        self.convert_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            actions_row,
            text="Cancel",
            height=40,
            width=90,
            fg_color="#C62828",
            hover_color="#B71C1C",
            state="disabled",
            command=self._cancel_conversion
        )
        self.cancel_btn.pack(side="left", padx=(0, 10))

        self.folder_btn = ctk.CTkButton(
            actions_row,
            text="Open Folder",
            height=40,
            width=110,
            command=self._open_output
        )
        self.folder_btn.pack(side="left")

        # 4. Progress Card
        self.progress_card = ProgressCard(self)
        self.progress_card.pack(fill="x", padx=10, pady=8)

    def _browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Media File",
            filetypes=[
                ("Media Files", "*.mp4 *.mkv *.webm *.mov *.avi *.mp3 *.m4a *.wav *.flac *.opus *.ogg"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.selected_file = filename
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)

            size_str = format_bytes(os.path.getsize(filename))
            duration_secs = self.converter.get_media_duration(filename)
            dur_str = format_seconds(duration_secs)
            self.file_info_lbl.configure(text=f"File Size: {size_str} | Duration: {dur_str}")

    def _browse_out_dir(self):
        directory = filedialog.askdirectory(title="Select Output Folder")
        if directory:
            self.out_dir_entry.delete(0, tk.END)
            self.out_dir_entry.insert(0, directory)

    def _on_mode_changed(self, mode):
        self.trim_frame.pack_forget()
        self.compress_frame.pack_forget()
        self.audio_bitrate_label.pack_forget()
        self.audio_bitrate_combo.pack_forget()

        if mode == "Convert Video":
            self.format_label.configure(text="Target Format:")
            self.format_combo.configure(values=["mp4", "mkv", "webm", "avi", "mov"])
            self.format_combo.set("mp4")
            self.codec_label.pack(side="left", padx=(0, 10))
            self.codec_combo.pack(side="left", padx=(0, 20))
        elif mode == "Extract Audio":
            self.format_label.configure(text="Audio Format:")
            self.format_combo.configure(values=["mp3", "m4a", "flac (Lossless)", "wav (Lossless)", "opus", "ogg"])
            self.format_combo.set("mp3")
            self.codec_label.pack_forget()
            self.codec_combo.pack_forget()
            self.audio_bitrate_label.pack(side="left", padx=(0, 10))
            self.audio_bitrate_combo.pack(side="left")
        elif mode == "Compress Video":
            self.format_label.configure(text="Target Format:")
            self.format_combo.configure(values=["mp4", "mkv", "webm"])
            self.format_combo.set("mp4")
            self.codec_label.pack_forget()
            self.codec_combo.pack_forget()
            self.compress_frame.pack(fill="x", pady=4)
        elif mode == "Trim Clip":
            self.format_label.configure(text="Target Format:")
            self.format_combo.configure(values=["mp4", "mkv", "mp3", "wav"])
            self.format_combo.set("mp4")
            self.codec_label.pack_forget()
            self.codec_combo.pack_forget()
            self.trim_frame.pack(fill="x", pady=4)

    def _start_conversion(self):
        input_file = self.file_entry.get().strip()
        if not input_file or not os.path.exists(input_file):
            logger.warning("Please choose a valid existing source media file.")
            return

        out_dir = self.out_dir_entry.get().strip()
        ok, err = verify_directory_writable(out_dir)
        if not ok:
            logger.error(f"Cannot write to output folder: {err}")
            self.progress_card.set_status(f"Error: {err}", text_color="#C62828")
            return

        mode = self.mode_segmented.get()
        target_ext = self.format_combo.get().split()[0].lower()

        base_name = os.path.splitext(os.path.basename(input_file))[0]
        suffix = "_converted"
        if mode == "Extract Audio":
            suffix = "_audio"
        elif mode == "Compress Video":
            suffix = "_compressed"
        elif mode == "Trim Clip":
            suffix = "_trimmed"

        output_file = os.path.join(out_dir, f"{base_name}{suffix}.{target_ext}")

        media_type = "audio" if (mode == "Extract Audio" or target_ext in ("mp3", "m4a", "flac", "wav", "opus", "ogg")) else "video"
        codec_raw = self.codec_combo.get().split()[0]
        audio_bitrate = self.audio_bitrate_combo.get().split()[0]

        crf = 23
        if mode == "Compress Video":
            preset_str = self.compress_preset_combo.get()
            if "28" in preset_str:
                crf = 28
            elif "32" in preset_str:
                crf = 32

        start_time = self.start_time_entry.get().strip() if mode == "Trim Clip" else None
        end_time = self.end_time_entry.get().strip() if mode == "Trim Clip" else None

        self.is_converting = True
        self.convert_btn.configure(state="disabled", text="Processing...")
        self.cancel_btn.configure(state="normal")
        self.progress_card.reset()
        self.progress_card.set_status(f"Converting {os.path.basename(input_file)}...")

        def worker():
            success = self.converter.convert_media(
                input_file=input_file,
                output_file=output_file,
                output_format=target_ext,
                media_type=media_type,
                audio_codec="libmp3lame" if target_ext == "mp3" else "aac",
                audio_bitrate=audio_bitrate,
                video_codec=codec_raw,
                crf=crf,
                start_time=start_time,
                end_time=end_time,
                progress_callback=lambda d: self.after(0, lambda: self._on_progress(d))
            )
            self.after(0, lambda: self._on_complete(success, output_file))

        threading.Thread(target=worker, daemon=True).start()

    def _cancel_conversion(self):
        self.converter.cancel()
        self.cancel_btn.configure(state="disabled")
        self.progress_card.set_status("Cancelled by user.", text_color="#C62828")

    def _on_progress(self, data: Dict[str, Any]):
        percent = data.get("percent", 0.0)
        speed = data.get("speed")
        cur_t = data.get("current_time")
        tot_t = data.get("total_time")
        self.progress_card.update_file_progress(
            percent=percent,
            status=f"Converting: {cur_t} / {tot_t}" if cur_t else "Processing...",
            speed=speed
        )

    def _on_complete(self, success: bool, output_file: str):
        self.is_converting = False
        self.convert_btn.configure(state="normal", text="Start Conversion")
        self.cancel_btn.configure(state="disabled")

        if success:
            self.progress_card.update_file_progress(100.0, status="Conversion Completed Successfully")
            self.progress_card.set_status("Completed Successfully", text_color="#43A047")
        else:
            self.progress_card.set_status("Conversion Failed", text_color="#C62828")

    def _open_output(self):
        folder = self.out_dir_entry.get().strip() or os.path.abspath("downloads")
        open_file_or_folder(folder)
