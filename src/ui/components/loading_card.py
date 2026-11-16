import customtkinter as ctk

class LoadingCard(ctk.CTkFrame):
    """
    Clean, lightweight loading card with an indeterminate animated progress bar.
    Displayed during heavy operations like URL analysis or playlist fetching.
    """

    def __init__(self, master, message="Analyzing media metadata... Please wait", **kwargs):
        super().__init__(master, corner_radius=10, fg_color=("gray85", "gray20"), **kwargs)

        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1E88E5"
        )
        self.message_label.pack(pady=(16, 8), padx=20)

        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=6,
            corner_radius=3,
            mode="indeterminate"
        )
        self.progress_bar.pack(fill="x", padx=30, pady=(0, 16))

    def start(self, message: str = "Analyzing media metadata... Please wait"):
        """Start the indeterminate loading animation."""
        self.message_label.configure(text=message)
        self.progress_bar.start()

    def stop(self):
        """Stop animation."""
        self.progress_bar.stop()

