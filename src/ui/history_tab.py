"""
History Tab — View previous downloads
"""
import os
import subprocess
import customtkinter as ctk

from src.utils.history_manager import load_history, clear_history
from src.utils.i18n import _

class HistoryTab(ctk.CTkFrame):
    def __init__(self, parent, colors: dict):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.colors = colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=self.colors["bg_dark"], corner_radius=0)
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)
        
        self.bind("<Visibility>", lambda e: self._refresh_history())
        self._refresh_history()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=90)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        title = ctk.CTkLabel(header, text=_("nav_history"),
                             font=ctk.CTkFont("Segoe UI", 24, "bold"),
                             text_color=self.colors["text_primary"])
        title.grid(row=0, column=0, padx=36, pady=(24, 0), sticky="w")

        subtitle = ctk.CTkLabel(header, text=_("hist_subtitle"),
                                font=ctk.CTkFont("Segoe UI", 13),
                                text_color=self.colors["text_secondary"])
        subtitle.grid(row=1, column=0, padx=36, pady=(4, 16), sticky="w")
        
        clear_btn = ctk.CTkButton(header, text=_("btn_clear_hist"), width=120, height=40,
                                  corner_radius=10, fg_color=self.colors["error"],
                                  font=ctk.CTkFont("Segoe UI", 13, "bold"),
                                  command=self._on_clear)
        clear_btn.grid(row=0, column=1, rowspan=2, padx=36, sticky="e")

    def _refresh_history(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        history = load_history()
        
        if not history:
            lbl = ctk.CTkLabel(self.scroll, text=_("hist_empty"),
                               font=ctk.CTkFont("Segoe UI", 16),
                               text_color=self.colors["text_secondary"])
            lbl.grid(row=0, column=0, pady=50)
            return

        for i, item in enumerate(history):
            card = ctk.CTkFrame(self.scroll, fg_color=self.colors["card_bg"], corner_radius=16,
                                border_width=1, border_color=self.colors["border"])
            card.grid(row=i, column=0, padx=36, pady=(16 if i==0 else 8, 8), sticky="ew")
            card.grid_columnconfigure(1, weight=1)

            icon = "🎬" if item.get("mode") == "video" else "🎵"
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24)).grid(row=0, column=0, padx=20, pady=16)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="w", pady=12)

            ctk.CTkLabel(info_frame, text=item.get("title", "Unknown"), 
                         font=ctk.CTkFont("Segoe UI", 15, "bold"),
                         text_color=self.colors["text_primary"]).pack(anchor="w")
            
            ctk.CTkLabel(info_frame, text=item.get("date", ""), 
                         font=ctk.CTkFont("Segoe UI", 12),
                         text_color=self.colors["text_secondary"]).pack(anchor="w")

            btn = ctk.CTkButton(card, text=_("btn_open_folder"), width=120, height=36, corner_radius=8,
                                fg_color=self.colors["border"], hover_color=self.colors["accent"],
                                font=ctk.CTkFont("Segoe UI", 12),
                                command=lambda p=item.get("path"): self._open_path(p))
            btn.grid(row=0, column=2, padx=20)

    def _on_clear(self):
        clear_history()
        self._refresh_history()

    def _open_path(self, path: str):
        if not path: return
        
        # Open containing folder and select file if possible
        if os.name == 'nt':
            if os.path.exists(path):
                # If path is a specific file, open explorer with file selected
                if os.path.isfile(path):
                    subprocess.Popen(f'explorer /select,"{path}"')
                else:
                    os.startfile(path)
            else:
                # Fallback to dir if file not found
                dir_path = os.path.dirname(path)
                if os.path.exists(dir_path):
                    os.startfile(dir_path)
