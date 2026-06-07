"""
my-dlp — Main entry point
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from src.ui.app import MyDLPApp


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = MyDLPApp()
    app.mainloop()


if __name__ == "__main__":
    main()
