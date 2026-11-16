"""
GUI entry point module.
Launches the modern CustomTkinter interface.
"""

from src.ui.app import launch_gui, ModernApp

def start_gui(start_download_callback=None):
    """
    Launch the YouTube Studio Downloader modern graphical interface.
    """
    launch_gui()

if __name__ == "__main__":
    start_gui()
