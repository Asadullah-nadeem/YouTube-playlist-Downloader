import customtkinter as ctk
from typing import Optional

class ProgressCard(ctk.CTkFrame):
    """
    Modern Dual Progress Card.
    Supports single file progress as well as multi-item batch/playlist tracking
    with exact counters (completed, pending, total items).
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)

        self.grid_columnconfigure(0, weight=1)

        # ----------------- BATCH / PLAYLIST SECTION -----------------
        self.batch_container = ctk.CTkFrame(self, fg_color="transparent")
        # Hidden by default until playlist or batch is active

        self.batch_header = ctk.CTkFrame(self.batch_container, fg_color="transparent")
        self.batch_header.pack(fill="x", padx=14, pady=(10, 2))

        self.batch_title_label = ctk.CTkLabel(
            self.batch_header,
            text="Playlist Batch Progress",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        self.batch_title_label.pack(side="left")

        self.batch_counter_label = ctk.CTkLabel(
            self.batch_header,
            text="0 / 0 Completed (0.0%)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1E88E5"
        )
        self.batch_counter_label.pack(side="right")

        self.batch_progress_bar = ctk.CTkProgressBar(self.batch_container, height=8, corner_radius=4)
        self.batch_progress_bar.pack(fill="x", padx=14, pady=(2, 6))
        self.batch_progress_bar.set(0)

        # ----------------- CURRENT FILE SECTION -----------------
        self.file_container = ctk.CTkFrame(self, fg_color="transparent")
        self.file_container.pack(fill="x", padx=14, pady=(10, 4))

        self.header_frame = ctk.CTkFrame(self.file_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 2))

        self.status_label = ctk.CTkLabel(
            self.header_frame,
            text="Ready",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        self.status_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(
            self.header_frame,
            text="0%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1E88E5"
        )
        self.percent_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self.file_container, height=10, corner_radius=5)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        # Stats Row (Speed, ETA, Size)
        self.stats_frame = ctk.CTkFrame(self.file_container, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(2, 10))

        self.speed_label = ctk.CTkLabel(
            self.stats_frame,
            text="Speed: -- MB/s",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.speed_label.pack(side="left", padx=(0, 16))

        self.eta_label = ctk.CTkLabel(
            self.stats_frame,
            text="ETA: --:--",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.eta_label.pack(side="left")

        self.size_label = ctk.CTkLabel(
            self.stats_frame,
            text="0 B / 0 B",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.size_label.pack(side="right")

    def show_batch_mode(self, show: bool = True):
        """Toggle visibility of the playlist batch progress bar."""
        if show:
            self.batch_container.pack(fill="x", before=self.file_container)
        else:
            self.batch_container.pack_forget()

    def update_batch_progress(self, current_index: int, total_items: int, title: str = ""):
        """Update the overall batch counter and progress bar."""
        if total_items > 0:
            self.show_batch_mode(True)
            completed = max(0, current_index - 1)
            pct = (completed / total_items) * 100.0
            self.batch_progress_bar.set(completed / total_items)
            self.batch_counter_label.configure(text=f"{completed} of {total_items} Completed ({pct:.1f}%)")
            if title:
                self.batch_title_label.configure(text=f"Batch Item [{current_index}/{total_items}]")
        else:
            self.show_batch_mode(False)

    def finish_batch(self, total_items: int, successful: int):
        """Mark the entire batch as finished."""
        self.batch_progress_bar.set(1.0)
        self.batch_counter_label.configure(
            text=f"All {successful}/{total_items} Completed",
            text_color="#43A047"
        )

    def update_file_progress(
        self,
        percent: float,
        status: str = "Downloading...",
        speed: Optional[str] = None,
        eta: Optional[str] = None,
        transferred_str: Optional[str] = None,
        total_str: Optional[str] = None
    ):
        """Update single file download progress."""
        clamped = max(0.0, min(100.0, percent))
        self.progress_bar.set(clamped / 100.0)
        self.percent_label.configure(text=f"{clamped:.1f}%")
        self.status_label.configure(text=status)

        if speed:
            self.speed_label.configure(text=f"Speed: {speed}")
        if eta:
            self.eta_label.configure(text=f"ETA: {eta}")
        if transferred_str and total_str:
            self.size_label.configure(text=f"{transferred_str} / {total_str}")
        elif transferred_str:
            self.size_label.configure(text=transferred_str)

    def set_status(self, status: str, text_color: Optional[str] = None):
        self.status_label.configure(text=status)
        if text_color:
            self.status_label.configure(text_color=text_color)

    def reset(self):
        """Reset all progress indicators to initial idle state."""
        self.progress_bar.set(0)
        self.batch_progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.status_label.configure(text="Ready", text_color=("gray10", "gray90"))
        self.speed_label.configure(text="Speed: -- MB/s")
        self.eta_label.configure(text="ETA: --:--")
        self.size_label.configure(text="0 B / 0 B")
        self.show_batch_mode(False)
