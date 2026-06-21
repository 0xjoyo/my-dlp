"""
Build my-dlp into a standalone Windows executable using PyInstaller.
Output goes to dist/my-dlp/ (onedir mode — required because Inno Setup
packages the whole folder and because VLC/ytmusicapi ship native bits).
"""
import PyInstaller.__main__
import customtkinter
import os

# Get path to customtkinter to include its themes and fonts
customtkinter_path = os.path.dirname(customtkinter.__file__)

print("Building my-dlp...")
args = [
    "main.py",
    "--name=my-dlp",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--icon=assets/icon.ico",
    f"--add-data={customtkinter_path};customtkinter/",
    "--add-data=assets;assets",
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
    "--collect-all=PIL",
    # Avoid bundling tkinter (it lives in the Python install / frozen bundle
    # already) but make sure the bundled Tcl/Tk finds its data files.
    "--noconsole",
]

PyInstaller.__main__.run(args)
print("Build complete! You can find the executable in the 'dist/my-dlp' folder.")
