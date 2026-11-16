import io
import requests
import customtkinter as ctk
from PIL import Image
from typing import Optional

class VideoPreviewCard(ctk.CTkFrame):
    """Card widget that displays a video's thumbnail, title, channel, and duration without emojis."""

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)

        self.thumbnail_label = ctk.CTkLabel(
            self,
            text="[No Media Loaded]\nEnter URL and click Analyze",
            width=170,
            height=96,
            fg_color=("gray85", "gray20"),
            corner_radius=6,
            font=ctk.CTkFont(size=11)
        )
        self.thumbnail_label.pack(side="left", padx=12, pady=12)

        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(side="left", fill="both", expand=True, padx=(4, 12), pady=12)

        self.title_label = ctk.CTkLabel(
            self.info_frame,
            text="Media Title will appear here",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            wraplength=440,
            justify="left"
        )
        self.title_label.pack(anchor="w", pady=(0, 4))

        self.meta_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.meta_frame.pack(anchor="w", fill="x")

        self.channel_label = ctk.CTkLabel(
            self.meta_frame,
            text="Channel / Creator: --",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        self.channel_label.pack(side="left", padx=(0, 16))

        self.duration_label = ctk.CTkLabel(
            self.meta_frame,
            text="Duration: --:--",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1E88E5"
        )
        self.duration_label.pack(side="left")

    def set_info(self, title: str, channel: str, duration: str, thumbnail_url: Optional[str] = None):
        self.title_label.configure(text=title)
        self.channel_label.configure(text=f"Channel / Creator: {channel}")
        self.duration_label.configure(text=f"Duration: {duration}")

        if thumbnail_url:
            self._load_thumbnail(thumbnail_url)
        else:
            self.thumbnail_label.configure(text="[Media Ready]", image=None)

    def _load_thumbnail(self, url: str):
        try:
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                img_data = resp.content
                image = Image.open(io.BytesIO(img_data))
                ctk_img = ctk.CTkImage(light_image=image, dark_image=image, size=(160, 90))
                self.thumbnail_label.configure(image=ctk_img, text="")
                return
        except Exception:
            pass
        self.thumbnail_label.configure(text="[Preview Image]", image=None)

    def reset(self):
        self.title_label.configure(text="Media Title will appear here")
        self.channel_label.configure(text="Channel / Creator: --")
        self.duration_label.configure(text="Duration: --:--")
        self.thumbnail_label.configure(text="[No Media Loaded]\nEnter URL and click Analyze", image=None)
