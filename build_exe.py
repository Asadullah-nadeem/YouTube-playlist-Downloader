#!/usr/bin/env python3
"""
Media Studio Pro - Executable Builder Script
Packages the application into a standalone Windows .exe using PyInstaller.
"""

import sys
import os
import subprocess
import shutil

def build():
    print("=" * 60)
    print("Media Studio Pro - Building Standalone Executable (.exe)")
    print("=" * 60)

    # 1. Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("[*] PyInstaller not detected. Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Locate CustomTkinter assets
    try:
        import customtkinter
        ctk_path = os.path.dirname(customtkinter.__file__)
        print(f"[*] CustomTkinter assets located at: {ctk_path}")
    except ImportError:
        print("[!] Error: CustomTkinter must be installed to package the app.")
        sys.exit(1)

    # Path separator for --add-data differs by OS (; on Windows, : on POSIX)
    sep = ";" if os.name == "nt" or sys.platform == "win32" else ":"
    ctk_data = f"{ctk_path}{sep}customtkinter"

    project_root = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(project_root, "main.py")

    # 3. Clean previous build artifacts
    for folder in ["build", "dist"]:
        p = os.path.join(project_root, folder)
        if os.path.exists(p):
            print(f"[*] Cleaning previous '{folder}' folder...")
            try:
                shutil.rmtree(p)
            except Exception:
                pass

    spec_file = os.path.join(project_root, "MediaStudioPro.spec")
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
        except Exception:
            pass

    # 4. Construct PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=MediaStudioPro",
        "--onefile",
        "--noconsole",
        f"--add-data={ctk_data}",
        f"--paths={project_root}",
        "--hidden-import=PIL",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=darkdetect",
        "--hidden-import=customtkinter",
        "--hidden-import=yt_dlp",
        "--hidden-import=requests",
        "--clean",
        main_script
    ]

    print("[*] Running PyInstaller build command...")
    print(" ".join(cmd))
    print()

    res = subprocess.run(cmd)

    if res.returncode == 0:
        exe_path = os.path.join(project_root, "dist", "MediaStudioPro.exe" if os.name == "nt" else "MediaStudioPro")
        print("=" * 60)
        print("[SUCCESS] Build finished successfully!")
        print(f"Executable file: {exe_path}")
        print("=" * 60)
        print("\nHow to use daily on Windows:")
        print("1. Copy 'MediaStudioPro.exe' from the 'dist' folder to your Desktop or Applications.")
        print("2. Ensure FFmpeg is on your Windows PATH or place 'ffmpeg.exe' in the same folder.")
        print("3. Double-click 'MediaStudioPro.exe' to run the app instantly without needing Python!")
    else:
        print("[ERROR] PyInstaller failed with exit code:", res.returncode)
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()

