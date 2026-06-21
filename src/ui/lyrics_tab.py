"""
Lyrics Tab — Karaoke style synchronized lyrics viewer
"""
import os
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog

from src.core import lyrics_fetcher, lrc_parser, audio_player
from src.utils.i18n import _

class LyricsTab(ctk.CTkFrame):
    def __init__(self, parent, colors: dict):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.colors = colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.player = audio_player.AudioPlayer()
        self.current_lyrics = []
        self._sync_loop_id = None
        self._last_active_idx = -1

        self._build_header()
        self._build_body()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=90)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(header, text=_("lyr_title"),
                     font=ctk.CTkFont("Segoe UI", 24, "bold"),
                     text_color=self.colors["text_primary"]).grid(row=0, column=0, padx=36, pady=(24, 0), sticky="w")
        ctk.CTkLabel(header, text=_("lyr_subtitle"),
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=self.colors["text_secondary"]).grid(row=1, column=0, padx=36, pady=(4, 16), sticky="w")

    def _build_body(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=36, pady=24)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Player Controls
        controls = self._card(main_frame, _("card_player"))
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        controls.grid_columnconfigure(1, weight=1)

        btn_choose = ctk.CTkButton(controls, text=_("btn_choose_audio"), width=160, height=48,
                                   corner_radius=12,
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   fg_color=self.colors["accent"],
                                   hover_color=self.colors["accent_hover"],
                                   command=self._on_choose_file)
        btn_choose.grid(row=1, column=0, padx=24, pady=20)

        self.lbl_file = ctk.CTkLabel(controls, text=_("lyr_no_file"),
                                     font=ctk.CTkFont("Segoe UI", 14),
                                     text_color=self.colors["text_secondary"], anchor="w")
        self.lbl_file.grid(row=1, column=1, sticky="ew", padx=(0, 16))

        self.btn_play = ctk.CTkButton(controls, text=_("btn_play"), width=48, height=48,
                                      corner_radius=24,
                                      font=ctk.CTkFont(size=20),
                                      fg_color=self.colors["border"],
                                      hover_color=self.colors["accent"],
                                      state="disabled",
                                      command=self._on_play_pause)
        self.btn_play.grid(row=1, column=2, padx=24)

        # Lyrics Display
        lyrics_frame = self._card(main_frame, _("card_lyrics"))
        lyrics_frame.grid(row=1, column=0, sticky="nsew")
        lyrics_frame.grid_rowconfigure(1, weight=1)
        lyrics_frame.grid_columnconfigure(0, weight=1)

        self.lyrics_canvas = tk.Canvas(lyrics_frame,
                                       bg=self.colors["card_bg"],
                                       highlightthickness=0, bd=0)
        self.lyrics_scroll = ctk.CTkScrollableFrame(lyrics_frame,
                                                    fg_color="transparent",
                                                    corner_radius=0)
        self.lyrics_scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        self.lyrics_scroll.grid_columnconfigure(0, weight=1)

        self.lyrics_labels = []

        self.lbl_status = ctk.CTkLabel(self.lyrics_scroll, text=_("lyr_wait"),
                                       font=ctk.CTkFont("Segoe UI", 16),
                                       text_color=self.colors["text_secondary"])
        self.lbl_status.grid(row=0, column=0, pady=40)

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card_bg"], corner_radius=16,
                              border_width=1, border_color=self.colors["border"])
        frame.grid_columnconfigure(0, weight=1)
        if title:
            ctk.CTkLabel(frame, text=title,
                          font=ctk.CTkFont("Segoe UI", 15, "bold"),
                          text_color=self.colors["accent"]).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 0))
        return frame

    def _on_choose_file(self):
        path = filedialog.askopenfilename(
            title="Choose Audio File",
            filetypes=[("Audio Files", "*.mp3 *.m4a *.flac *.wav *.ogg"), ("All Files", "*.*")]
        )
        if not path:
            return

        self.lbl_file.configure(text=os.path.basename(path), text_color=self.colors["text_primary"])
        self.player.load(path)
        self.btn_play.configure(state="normal", text=_("btn_play"))

        # Try to find lyrics
        self._clear_lyrics()
        self.lbl_status.configure(text=_("lyr_searching"), text_color=self.colors["accent2"])
        self.lbl_status.grid(row=0, column=0, pady=40)

        threading.Thread(target=self._fetch_lyrics, args=(path,), daemon=True).start()

    def _fetch_lyrics(self, path: str):
        # We need artist/title. If not available in tags, fallback to filename.
        # For simplicity, let's use filename minus extension.
        base = os.path.basename(path)
        name, _ = os.path.splitext(base)

        lrc_text = lyrics_fetcher.get_lyrics(name, "")
        # Detect any LRC timestamp pattern like [mm:ss.xx], not just [00:xx]
        if lrc_text and lrc_parser.has_lrc_timestamps(lrc_text):
            lines, _meta = lrc_parser.parse_lrc(lrc_text)
            self.after(0, lambda: self._on_lyrics_found(lines))
        else:
            self.after(0, lambda: self._on_lyrics_not_found())

    def _on_lyrics_found(self, lines: list):
        self.current_lyrics = lines
        self.lbl_status.grid_forget()

        for i, line in enumerate(lines):
            lbl = ctk.CTkLabel(self.lyrics_scroll, text=line["text"],
                               font=ctk.CTkFont("Segoe UI", 18, "bold"),
                               text_color=self.colors["text_secondary"],
                               wraplength=700)
            lbl.grid(row=i, column=0, pady=8)
            self.lyrics_labels.append(lbl)

        self._last_active_idx = -1

    def _on_lyrics_not_found(self):
        self.lbl_status.configure(text=_("lyr_not_found"), text_color=self.colors["error"])

    def _clear_lyrics(self):
        self.current_lyrics = []
        for lbl in self.lyrics_labels:
            lbl.destroy()
        self.lyrics_labels.clear()
        if self._sync_loop_id:
            self.after_cancel(self._sync_loop_id)
            self._sync_loop_id = None

    def _on_play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.btn_play.configure(text=_("btn_play"))
            if self._sync_loop_id:
                self.after_cancel(self._sync_loop_id)
                self._sync_loop_id = None
        else:
            self.player.play()
            self.btn_play.configure(text=_("btn_pause"))
            self._sync_loop()

    def _sync_loop(self):
        if not self.player.is_playing() or not self.current_lyrics:
            return

        ms = self.player.get_time()
        active_idx = lrc_parser.get_current_line_index(self.current_lyrics, ms)

        if active_idx != self._last_active_idx and active_idx != -1:
            # Revert old active
            if 0 <= self._last_active_idx < len(self.lyrics_labels):
                self.lyrics_labels[self._last_active_idx].configure(
                    text_color=self.colors["text_secondary"],
                    font=ctk.CTkFont("Segoe UI", 18, "bold")
                )

            # Set new active
            if 0 <= active_idx < len(self.lyrics_labels):
                self.lyrics_labels[active_idx].configure(
                    text_color=self.colors["accent"],
                    font=ctk.CTkFont("Segoe UI", 22, "bold")
                )

            self._last_active_idx = active_idx

        self._sync_loop_id = self.after(100, self._sync_loop)
