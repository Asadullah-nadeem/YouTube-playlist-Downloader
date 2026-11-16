import os
import customtkinter as ctk

from src.utils.config import config
from src.utils.logger import logger
from src.ui.views.download_view import DownloadView
from src.ui.views.playlist_view import PlaylistView
from src.ui.views.converter_view import ConverterView
from src.ui.views.subtitles_view import SubtitlesView
from src.ui.views.history_view import HistoryView
from src.ui.views.settings_view import SettingsView

class ModernApp(ctk.CTk):
    """Main application window with modern responsive sidebar navigation."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("YouTube Media Studio & Playlist Downloader Pro")
        self.geometry("1100x760")
        self.minsize(920, 640)

        # Apply user theme
        saved_theme = config.get("theme", "dark")
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme(config.get("color_theme", "blue"))

        # Configure Grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.current_view_name = "download"

        self._build_sidebar()
        self._build_content_area()
        self._select_tab("download")

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Logo / App Title
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        title_lbl = ctk.CTkLabel(
            logo_frame,
            text="🎬 YT Studio Pro",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            logo_frame,
            text="High-Speed Media Suite",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        sub_lbl.pack(anchor="w")

        # Navigation Buttons
        self.nav_buttons = {}

        nav_items = [
            ("download", "📥 Downloader", 1),
            ("playlist", "📋 Playlist Manager", 2),
            ("converter", "🔄 Converter & Tools", 3),
            ("subtitles", "🌐 Subtitles & Audio", 4),
            ("history", "🕒 Library & History", 5),
            ("settings", "⚙️ Settings", 6),
        ]

        for key, label, row_idx in nav_items:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray25"),
                command=lambda k=key: self._select_tab(k)
            )
            btn.grid(row=row_idx, column=0, padx=15, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Bottom Info Area
        bottom_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        bottom_frame.grid(row=9, column=0, padx=15, pady=15, sticky="ew")

        ctk.CTkLabel(
            bottom_frame,
            text="Appearance Mode:",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 2))

        self.theme_option = ctk.CTkOptionMenu(
            bottom_frame,
            values=["Dark", "Light", "System"],
            command=self._on_quick_theme_change,
            height=28
        )
        self.theme_option.set(config.get("theme", "dark").capitalize())
        self.theme_option.pack(fill="x")

    def _build_content_area(self):
        # Views Container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Instantiate View Frames
        self.views = {
            "download": DownloadView(self.content_frame),
            "playlist": PlaylistView(self.content_frame),
            "converter": ConverterView(self.content_frame),
            "subtitles": SubtitlesView(self.content_frame),
            "history": HistoryView(self.content_frame),
            "settings": SettingsView(self.content_frame, on_theme_change=self._sync_theme_dropdown),
        }

    def _select_tab(self, key: str):
        self.current_view_name = key

        # Highlight selected button in sidebar
        for name, btn in self.nav_buttons.items():
            if name == key:
                btn.configure(fg_color=("#3B8ED0", "#1F6AA5"), text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        # Switch visible view
        for name, view in self.views.items():
            if name == key:
                view.grid(row=0, column=0, sticky="nsew")
                if hasattr(view, "refresh"):
                    view.refresh()
            else:
                view.grid_forget()

    def _on_quick_theme_change(self, mode_str: str):
        mode = mode_str.lower()
        ctk.set_appearance_mode(mode)
        config.set("theme", mode)

    def _sync_theme_dropdown(self, mode: str):
        self.theme_option.set(mode.capitalize())

def launch_gui():
    """Launch the modern application."""
    app = ModernApp()
    app.mainloop()

if __name__ == "__main__":
    launch_gui()

