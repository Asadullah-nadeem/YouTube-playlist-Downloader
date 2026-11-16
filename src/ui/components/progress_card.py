import customtkinter as ctk
from typing import Optional

class ProgressCard(ctk.CTkFrame):
    """Modern progress card displaying progress bar, percent, speed, ETA, and transfer sizes."""

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)

        self.grid_columnconfigure(0, weight=1)

        # Header: status label and percent
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=15, pady=(12, 4))

        self.status_label = ctk.CTkLabel(
            self.header_frame,
            text="Ready",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.status_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(
            self.header_frame,
            text="0%",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0"
        )
        self.percent_label.pack(side="right")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, height=12, corner_radius=6)
        self.progress_bar.pack(fill="x", padx=15, pady=6)
        self.progress_bar.set(0)

        # Sub-stats: Speed, ETA, Size transferred
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=15, pady=(2, 12))

        self.speed_label = ctk.CTkLabel(
            self.stats_frame,
            text="Speed: -- MB/s",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.speed_label.pack(side="left", padx=(0, 15))

        self.eta_label = ctk.CTkLabel(
            self.stats_frame,
            text="ETA: --:--",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.eta_label.pack(side="left")

        self.size_label = ctk.CTkLabel(
            self.stats_frame,
            text="0 B / 0 B",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.size_label.pack(side="right")

    def update_progress(
        self,
        percent: float,
        status: str = "Downloading...",
        speed: Optional[str] = None,
        eta: Optional[str] = None,
        transferred_str: Optional[str] = None,
        total_str: Optional[str] = None
    ):
        """Update the visual progress indicators."""
        clamped_percent = max(0.0, min(100.0, percent))
        self.progress_bar.set(clamped_percent / 100.0)
        self.percent_label.configure(text=f"{clamped_percent:.1f}%")
        self.status_label.configure(text=status)

        if speed:
            self.speed_label.configure(text=f"Speed: {speed}")
        if eta:
            self.eta_label.configure(text=f"ETA: {eta}")
        if transferred_str and total_str:
            self.size_label.configure(text=f"{transferred_str} / {total_str}")
        elif transferred_str:
            self.size_label.configure(text=transferred_str)

    def set_status(self, status: str, color: Optional[str] = None):
        """Update just the status badge text and color."""
        self.status_label.configure(text=status)
        if color:
            self.status_label.configure(text_color=color)

    def reset(self):
        """Reset progress card to initial state."""
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.status_label.configure(text="Ready", text_color=("gray10", "gray90"))
        self.speed_label.configure(text="Speed: -- MB/s")
        self.eta_label.configure(text="ETA: --:--")
        self.size_label.configure(text="0 B / 0 B")

