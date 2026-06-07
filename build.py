import PyInstaller.__main__
import customtkinter
import os

# Get path to customtkinter to include its themes and fonts
customtkinter_path = os.path.dirname(customtkinter.__file__)

print("Building my-dlp...")
PyInstaller.__main__.run([
    'main.py',
    '--name=my-dlp',
    '--noconfirm',
    '--onedir',
    '--windowed',
    '--icon=assets/icon.ico',
    f'--add-data={customtkinter_path};customtkinter/',
    '--add-data=assets;assets',
    '--hidden-import=PIL._tkinter_finder',
])
print("Build complete! You can find the executable in the 'dist/my-dlp' folder.")
