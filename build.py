"""
Build my-dlp into a standalone Windows / Linux executable using PyInstaller.

Output goes to dist/my-dlp/ (onedir mode — required because the Inno Setup
installer packages the whole folder and because VLC / ytmusicapi ship
native bits).

After this script finishes, run:

    iscc setup.iss

to wrap dist/my-dlp/ into a Windows installer.
"""
import os
import PyInstaller.__main__
import customtkinter

# Get path to customtkinter to include its themes and fonts
customtkinter_path = os.path.dirname(customtkinter.__file__)

# Ship the VERSION file at the bundle root so updater._running_version()
# can find it inside the frozen exe.
here = os.path.dirname(os.path.abspath(__file__))
version_path = os.path.join(here, "VERSION")
add_data = [
    f"{customtkinter_path};customtkinter/",
    "assets;assets",
]
if os.path.exists(version_path):
    add_data.append(f"{version_path};.")

print("Building my-dlp...")
args = [
    "main.py",
    "--name=my-dlp",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--icon=assets/icon.ico",
    *sum((["--add-data", d] for d in add_data), []),
    # PIL backend for tkinter image interop
    "--hidden-import=PIL._tkinter_finder",
    # The following libs ship data files, native modules, or do runtime
    # imports that PyInstaller's static analyzer misses. --collect-all
    # bundles the whole package so the frozen exe doesn't crash on launch.
    "--collect-all=customtkinter",
    "--collect-all=yt_dlp",
    "--collect-all=ytmusicapi",
    "--collect-all=spotipy",
    "--collect-all=syncedlyrics",
    "--collect-all=thefuzz",
    "--collect-all=python_Levenshtein",
    "--collect-all=mutagen",
    "--collect-all=pystray",
    "--collect-all=PIL",
    # Drag-and-drop: collect tkinterdnd2 if installed (graceful no-op otherwise)
    "--collect-all=tkinterdnd2",
    # Suppress the console window on Windows (we already pass --windowed)
    "--noconsole",
]

PyInstaller.__main__.run(args)
print("Build complete! You can find the executable in the 'dist/my-dlp' folder.")