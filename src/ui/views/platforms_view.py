import customtkinter as ctk
from src.core.platform_detector import PLATFORMS_REGISTRY, GENERIC_PLATFORM

class PlatformsView(ctk.CTkScrollableFrame):
    """View presenting all 25+ supported social media and video platforms without emojis."""

    def __init__(self, master, on_platform_select=None, **kwargs):
        super().__init__(master, **kwargs)

        self.on_platform_select = on_platform_select
        self._build_ui()

    def _build_ui(self):
        # Header Card
        header_card = ctk.CTkFrame(self, corner_radius=10)
        header_card.pack(fill="x", padx=10, pady=(10, 8))

        ctk.CTkLabel(
            header_card,
            text="Supported Social & Video Platforms (25+ Sites)",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            header_card,
            text="Paste any video, reel, post, or audio link into the Downloader. The engine recognizes the platform and applies optimal quality settings automatically.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=760,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 12))

        # Search / Filter Bar
        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=(0, 8))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Filter platforms (e.g. instagram, tiktok, music, reels)...",
            height=36
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._filter_platforms)

        # Platforms Grid Container
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=4)
        self.grid_frame.grid_columnconfigure((0, 1), weight=1)

        self.cards = []
        self._render_cards(PLATFORMS_REGISTRY)

    def _render_cards(self, platforms):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.cards.clear()

        row_idx = 0
        col_idx = 0

        for p in platforms:
            card = ctk.CTkFrame(self.grid_frame, corner_radius=8, fg_color=("gray90", "gray17"))
            card.grid(row=row_idx, column=col_idx, padx=6, pady=6, sticky="nsew")

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=12, pady=10)

            top_line = ctk.CTkFrame(content, fg_color="transparent")
            top_line.pack(fill="x")

            name_lbl = ctk.CTkLabel(
                top_line,
                text=p["name"],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            name_lbl.pack(side="left")

            badge = ctk.CTkLabel(
                top_line,
                text="Supported",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white",
                fg_color=p.get("color", "#1565C0"),
                corner_radius=4,
                padx=8,
                pady=2
            )
            badge.pack(side="right")

            desc_lbl = ctk.CTkLabel(
                content,
                text=p.get("description", ""),
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
                justify="left"
            )
            desc_lbl.pack(anchor="w", pady=(4, 6))

            tags_str = " | ".join(p.get("media_types", []))
            tags_lbl = ctk.CTkLabel(
                content,
                text=f"Formats: {tags_str}",
                font=ctk.CTkFont(size=11),
                text_color=("#0D47A1", "#64B5F6"),
                anchor="w"
            )
            tags_lbl.pack(anchor="w")

            col_idx += 1
            if col_idx > 1:
                col_idx = 0
                row_idx += 1

    def _filter_platforms(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self._render_cards(PLATFORMS_REGISTRY)
            return

        filtered = [
            p for p in PLATFORMS_REGISTRY
            if query in p["name"].lower()
            or query in p["description"].lower()
            or any(query in m.lower() for m in p["media_types"])
        ]
        self._render_cards(filtered)
