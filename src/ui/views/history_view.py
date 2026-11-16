import os
import tkinter as tk
import customtkinter as ctk
from typing import List, Dict, Any

from src.utils.database import db
from src.utils.helpers import open_file_or_folder
from src.utils.config import config

class HistoryView(ctk.CTkFrame):
    """
    High-Performance SQLite Library & History View with Pagination.
    Displays 10 items per page with instant search, filters, and fast SQLite queries.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        self.total_count = 0
        self.search_term = ""
        self.type_filter = "all"

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # 1. Header Toolbar Card
        header_card = ctk.CTkFrame(self, corner_radius=10)
        header_card.pack(fill="x", padx=10, pady=(10, 6))

        h_top = ctk.CTkFrame(header_card, fg_color="transparent")
        h_top.pack(fill="x", padx=15, pady=(10, 6))

        ctk.CTkLabel(
            h_top,
            text="Downloads Library (SQLite Database)",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            h_top,
            text="Open Folder",
            width=100,
            height=28,
            cursor="hand2",
            command=self._open_downloads_folder
        ).pack(side="right")

        ctk.CTkButton(
            h_top,
            text="Clear All",
            width=80,
            height=28,
            cursor="hand2",
            fg_color="#C62828",
            hover_color="#B71C1C",
            command=self._clear_all
        ).pack(side="right", padx=(0, 6))

        ctk.CTkButton(
            h_top,
            text="Refresh",
            width=75,
            height=28,
            cursor="hand2",
            command=self.load_data
        ).pack(side="right", padx=(0, 6))

        # Search & Filter Row
        filter_row = ctk.CTkFrame(header_card, fg_color="transparent")
        filter_row.pack(fill="x", padx=15, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="Search downloads by title...",
            height=32,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        self.filter_segmented = ctk.CTkSegmentedButton(
            filter_row,
            values=["All Items", "Videos Only", "Audio Only"],
            command=self._on_filter_change,
            height=30
        )
        self.filter_segmented.set("All Items")
        self.filter_segmented.pack(side="right")

        # 2. Statistics Summary Strip
        self.stats_card = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray85", "gray20"))
        self.stats_card.pack(fill="x", padx=10, pady=(0, 6))

        self.stats_label = ctk.CTkLabel(
            self.stats_card,
            text="Total Downloads: 0  |  Videos: 0  |  Audio Tracks: 0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1E88E5"
        )
        self.stats_label.pack(padx=15, pady=6)

        # 3. Scrollable List Container (Displays 10 items)
        self.scroll_list = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # 4. Pagination Controls Bar (Bottom)
        self.pagination_card = ctk.CTkFrame(self, corner_radius=10)
        self.pagination_card.pack(fill="x", padx=10, pady=(0, 10))

        p_row = ctk.CTkFrame(self.pagination_card, fg_color="transparent")
        p_row.pack(padx=15, pady=8)

        self.first_btn = ctk.CTkButton(
            p_row,
            text="<< First",
            width=70,
            height=28,
            cursor="hand2",
            command=self._go_first_page
        )
        self.first_btn.pack(side="left", padx=3)

        self.prev_btn = ctk.CTkButton(
            p_row,
            text="< Prev",
            width=65,
            height=28,
            cursor="hand2",
            command=self._go_prev_page
        )
        self.prev_btn.pack(side="left", padx=3)

        self.page_info_label = ctk.CTkLabel(
            p_row,
            text="Page 1 of 1 (10 per page)",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=180
        )
        self.page_info_label.pack(side="left", padx=12)

        self.next_btn = ctk.CTkButton(
            p_row,
            text="Next >",
            width=65,
            height=28,
            cursor="hand2",
            command=self._go_next_page
        )
        self.next_btn.pack(side="left", padx=3)

        self.last_btn = ctk.CTkButton(
            p_row,
            text="Last >>",
            width=70,
            height=28,
            cursor="hand2",
            command=self._go_last_page
        )
        self.last_btn.pack(side="left", padx=3)

    def load_data(self):
        """Query SQLite database with pagination and render the 10 items."""
        # 1. Update stats
        stats = db.get_stats()
        self.stats_label.configure(
            text=f"Database Records: {stats['total']} Total  |  Videos: {stats['videos']}  |  Audio Tracks: {stats['audios']}"
        )

        # 2. Fetch paginated slice
        items, total_count, total_pages = db.get_paginated(
            page=self.current_page,
            page_size=self.page_size,
            search_query=self.search_term,
            type_filter=self.type_filter
        )
        self.total_count = total_count
        self.total_pages = total_pages

        # Clamp page index
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            items, total_count, total_pages = db.get_paginated(
                page=self.current_page,
                page_size=self.page_size,
                search_query=self.search_term,
                type_filter=self.type_filter
            )

        # 3. Update pagination label and button states
        self.page_info_label.configure(
            text=f"Page {self.current_page} of {self.total_pages} ({self.total_count} items)"
        )
        self.first_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < self.total_pages else "disabled")
        self.last_btn.configure(state="normal" if self.current_page < self.total_pages else "disabled")

        # 4. Render items
        for w in self.scroll_list.winfo_children():
            w.destroy()

        if not items:
            msg = "No matching downloads found in library." if self.search_term else "No downloads recorded yet.\nCompleted videos and songs will appear here."
            ctk.CTkLabel(
                self.scroll_list,
                text=msg,
                text_color="gray",
                font=ctk.CTkFont(size=13)
            ).pack(pady=40)
            return

        for entry in items:
            self._render_entry_card(entry)

    def _render_entry_card(self, entry: Dict[str, Any]):
        card = ctk.CTkFrame(self.scroll_list, corner_radius=6, fg_color=("gray90", "gray17"))
        card.pack(fill="x", padx=4, pady=3)

        info_col = ctk.CTkFrame(card, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        # Title
        title_text = entry.get("title", "Untitled Media")
        ctk.CTkLabel(
            info_col,
            text=title_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            wraplength=480,
            justify="left"
        ).pack(anchor="w")

        # Subtitle Metadata
        m_type = str(entry.get("media_type", "video")).upper()
        quality = entry.get("quality", "")
        size = entry.get("file_size", "")
        date = entry.get("date_created", "")

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

        # Actions Row
        btn_col = ctk.CTkFrame(card, fg_color="transparent")
        btn_col.pack(side="right", padx=10, pady=8)

        file_path = entry.get("file_path", "")

        if os.path.exists(file_path):
            ctk.CTkButton(
                btn_col,
                text="Play",
                width=55,
                height=26,
                cursor="hand2",
                command=lambda p=file_path: open_file_or_folder(p)
            ).pack(side="left", padx=2)

        folder_to_open = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
        ctk.CTkButton(
            btn_col,
            text="Locate",
            width=65,
            height=26,
            cursor="hand2",
            command=lambda p=folder_to_open: open_file_or_folder(p)
        ).pack(side="left", padx=2)

        entry_id = entry.get("id")
        ctk.CTkButton(
            btn_col,
            text="Delete",
            width=60,
            height=26,
            cursor="hand2",
            fg_color="gray40",
            hover_color="#C62828",
            command=lambda eid=entry_id: self._delete_entry(eid)
        ).pack(side="left", padx=2)

    def _on_search_change(self, event=None):
        self.search_term = self.search_entry.get().strip()
        self.current_page = 1
        self.load_data()

    def _on_filter_change(self, val):
        if val == "Videos Only":
            self.type_filter = "video"
        elif val == "Audio Only":
            self.type_filter = "audio"
        else:
            self.type_filter = "all"
        self.current_page = 1
        self.load_data()

    def _go_first_page(self):
        if self.current_page > 1:
            self.current_page = 1
            self.load_data()

    def _go_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def _go_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()

    def _go_last_page(self):
        if self.current_page < self.total_pages:
            self.current_page = self.total_pages
            self.load_data()

    def _delete_entry(self, entry_id: int):
        db.delete_record(entry_id)
        self.load_data()

    def _clear_all(self):
        db.clear_all()
        self.current_page = 1
        self.load_data()

    def _open_downloads_folder(self):
        folder = config.get("download_dir", os.path.abspath("downloads"))
        os.makedirs(folder, exist_ok=True)
        open_file_or_folder(folder)

    def refresh(self):
        """Called when tab is selected."""
        self.load_data()
