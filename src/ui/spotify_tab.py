"""
Spotify Tab — Search tracks & playlists, view results, and download via yt-dlp
"""
import threading
import tkinter as tk
import customtkinter as ctk

from src.core import spotify_search, downloader
from src.utils.config_manager import load_config
from src.utils.i18n import _

class SpotifyTab(ctk.CTkFrame):
    def __init__(self, parent, colors: dict):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.colors = colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=90)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(header, text=_("sp_title"),
                     font=ctk.CTkFont("Segoe UI", 24, "bold"),
                     text_color=self.colors["text_primary"]).grid(row=0, column=0, padx=36, pady=(24, 0), sticky="w")
        ctk.CTkLabel(header, text=_("sp_subtitle"),
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=self.colors["text_secondary"]).grid(row=1, column=0, padx=36, pady=(4, 16), sticky="w")

    def _build_body(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=self.colors["bg_dark"], corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Search Card
        search_card = self._card(scroll, _("sp_card_search"))
        search_card.grid(row=0, column=0, padx=36, pady=(32, 16), sticky="ew")
        search_card.grid_columnconfigure(0, weight=1)

        search_row = ctk.CTkFrame(search_card, fg_color="transparent")
        search_row.grid(row=1, column=0, sticky="ew", padx=24, pady=(8, 16))
        search_row.grid_columnconfigure(0, weight=1)

        self.query_entry = ctk.CTkEntry(
            search_row,
            placeholder_text=_("sp_placeholder"),
            height=48, corner_radius=12,
            font=ctk.CTkFont("Segoe UI", 14),
            fg_color=self.colors["bg_dark"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        self.query_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.query_entry.bind("<Return>", lambda e: self._on_search())

        self.search_btn = ctk.CTkButton(
            search_row, text=_("btn_search"), width=120, height=48,
            corner_radius=12,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            command=self._on_search
        )
        self.search_btn.grid(row=0, column=1)

        self.status_lbl = ctk.CTkLabel(search_card, text="",
                                        font=ctk.CTkFont("Segoe UI", 13),
                                        text_color=self.colors["text_secondary"])
        self.status_lbl.grid(row=2, column=0, sticky="w", padx=24, pady=(0, 16))

        # Results Card
        self.results_card = self._card(scroll, _("sp_card_results"))
        self.results_card.grid(row=1, column=0, padx=36, pady=16, sticky="ew")
        self.results_card.grid_columnconfigure(0, weight=1)
        
        self.results_frame = ctk.CTkFrame(self.results_card, fg_color="transparent")
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.results_frame.grid_columnconfigure(0, weight=1)

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card_bg"], corner_radius=16,
                              border_width=1, border_color=self.colors["border"])
        frame.grid_columnconfigure(0, weight=1)
        if title:
            ctk.CTkLabel(frame, text=title,
                          font=ctk.CTkFont("Segoe UI", 15, "bold"),
                          text_color=self.colors["accent"]).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 8))
        return frame

    def _on_search(self):
        query = self.query_entry.get().strip()
        if not query:
            return

        config = load_config()
        if not config.get("spotify_client_id") or not config.get("spotify_client_secret"):
            self.status_lbl.configure(text=_("msg_sp_no_keys"), text_color=self.colors["warning"])
            return

        self.search_btn.configure(state="disabled")
        self.status_lbl.configure(text=_("msg_sp_searching"), text_color=self.colors["text_secondary"])

        # Clear old results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        def do_search():
            try:
                res = spotify_search.search_spotify(query)
                self.after(0, lambda: self._on_search_done(res))
            except Exception as e:
                self.after(0, lambda: self._on_search_error(str(e)))

        threading.Thread(target=do_search, daemon=True).start()

    def _on_search_done(self, results: list):
        self.search_btn.configure(state="normal")
        if not results:
            self.status_lbl.configure(text=_("msg_sp_no_results"), text_color=self.colors["error"])
            return

        self.status_lbl.configure(text="")
        
        for i, item in enumerate(results):
            row = ctk.CTkFrame(self.results_frame, fg_color=self.colors["bg_dark"], corner_radius=10)
            row.grid(row=i, column=0, sticky="ew", pady=6)
            row.grid_columnconfigure(1, weight=1)

            # Icon
            icon = "🎵" if item["type"] == "track" else "📋"
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=22)).grid(row=0, column=0, padx=16, pady=12)

            # Info
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="w")
            
            title = f"{item['title']} - {item['artist']}" if item["type"] == "track" else item['title']
            ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont("Segoe UI", 14, "bold"),
                         text_color=self.colors["text_primary"]).pack(anchor="w")
            
            meta = f"Spotify URL" if item["type"] == "track" else _("lbl_tracks_count", count=item['count'])
            ctk.CTkLabel(info_frame, text=meta, font=ctk.CTkFont("Segoe UI", 12),
                         text_color=self.colors["text_secondary"]).pack(anchor="w")

            # Action button
            action_text = _("btn_dl_track") if item["type"] == "track" else _("btn_dl_playlist")
            btn = ctk.CTkButton(row, text=action_text, width=120, height=36, corner_radius=8,
                                fg_color=self.colors["border"], hover_color=self.colors["accent"],
                                font=ctk.CTkFont("Segoe UI", 12),
                                command=lambda u=item["url"]: self._download_spotify_url(u))
            btn.grid(row=0, column=2, padx=16)

    def _on_search_error(self, err: str):
        self.search_btn.configure(state="normal")
        self.status_lbl.configure(text=f"❌ {err}", text_color=self.colors["error"])

    def _download_spotify_url(self, url: str):
        # We will dispatch this back to the main downloader via a callback in a full app, 
        # or handle it directly. For now, we'll just download it to default dir.
        config = load_config()
        out_dir = config.get("download_path")
        
        self.status_lbl.configure(text=f"⏳ {url} ...", text_color=self.colors["accent2"])
        
        task = downloader.DownloadTask(
            url=url,
            mode="audio",
            quality="192kbps",
            output_dir=out_dir,
            progress_callback=lambda d: None,
            done_callback=lambda: self.status_lbl.configure(text="✅ " + _("msg_dl_done"), text_color=self.colors["success"]),
            error_callback=lambda e: self.status_lbl.configure(text=f"❌ {e[:50]}", text_color=self.colors["error"]),
        )
        downloader.download(task)
