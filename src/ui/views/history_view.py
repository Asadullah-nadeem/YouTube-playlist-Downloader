import os
import customtkinter as ctk
from typing import List, Dict, Any

from src.utils.history import history_manager
from src.utils.helpers import open_file_or_folder
from src.utils.config import config

class HistoryView(ctk.CTkFrame):
    """View to view completed downloads, open files, or manage history records."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header Bar
        header_card = ctk.CTkFrame(self, corner_radius=12)
        header_card.pack(fill="x", padx=10, pady=(10, 6))

        h_row = ctk.CTkFrame(header_card, fg_color="transparent")
        h_row.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            h_row,
            text="Downloads Library & History",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            h_row,
            text="🔄 Refresh",
            width=80,
            height=28,
            command=self.refresh
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            h_row,
            text="🗑 Clear All",
            width=90,
            height=28,
            fg_color="#D9534F",
            hover_color="#C9302C",
            command=self._clear_all
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            h_row,
            text="📂 Open Folder",
            width=110,
            height=28,
            command=self._open_downloads_folder
        ).pack(side="right")

        # Scrollable List
        self.scroll_list = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh(self):
        """Reload and render history items."""
        for w in self.scroll_list.winfo_children():
            w.destroy()

        entries = history_manager.get_all()
        if not entries:
            ctk.CTkLabel(
                self.scroll_list,
                text="No downloads recorded yet.\nCompleted videos and songs will appear here.",
                text_color="gray",
                font=ctk.CTkFont(size=13)
            ).pack(pady=40)
            return

        for entry in entries:
            self._create_entry_card(entry)

    def _create_entry_card(self, entry: Dict[str, Any]):
        card = ctk.CTkFrame(self.scroll_list, corner_radius=8, fg_color=("gray90", "gray17"))
        card.pack(fill="x", padx=4, pady=4)

        info_col = ctk.CTkFrame(card, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        # Title
        title_text = entry.get("title", "Unknown Title")
        ctk.CTkLabel(
            info_col,
            text=title_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            wraplength=480,
            justify="left"
        ).pack(anchor="w")

        # Metadata subtitle
        m_type = entry.get("type", "video").upper()
        quality = entry.get("quality", "")
        size = entry.get("size", "")
        date = entry.get("date", "")

        meta_parts = [f"Format: {m_type}"]
        if quality:
            meta_parts.append(f"Quality: {quality}")
        if size:
            meta_parts.append(f"Size: {size}")
        if date:
            meta_parts.append(f"Date: {date}")

        ctk.CTkLabel(
            info_col,
            text=" | ".join(meta_parts),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        # Actions
        btn_col = ctk.CTkFrame(card, fg_color="transparent")
        btn_col.pack(side="right", padx=10, pady=8)

        file_path = entry.get("file_path", "")

        if os.path.exists(file_path):
            ctk.CTkButton(
                btn_col,
                text="▶ Play",
                width=65,
                height=28,
                command=lambda p=file_path: open_file_or_folder(p)
            ).pack(side="left", padx=2)

        folder_to_open = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
        ctk.CTkButton(
            btn_col,
            text="📂 Locate",
            width=70,
            height=28,
            command=lambda p=folder_to_open: open_file_or_folder(p)
        ).pack(side="left", padx=2)

        entry_id = entry.get("id")
        ctk.CTkButton(
            btn_col,
            text="✕",
            width=30,
            height=28,
            fg_color="gray40",
            hover_color="#D9534F",
            command=lambda eid=entry_id: self._delete_entry(eid)
        ).pack(side="left", padx=2)

    def _delete_entry(self, entry_id: int):
        history_manager.delete(entry_id)
        self.refresh()

    def _clear_all(self):
        history_manager.clear()
        self.refresh()

    def _open_downloads_folder(self):
        folder = config.get("download_dir", os.path.abspath("downloads"))
        open_file_or_folder(folder)

