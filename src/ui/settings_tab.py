"""
Settings Tab — Application configuration and preferences (i18n & Modern UI)
"""
import os
import customtkinter as ctk
from tkinter import filedialog

from src.utils.config_manager import load_config, save_config
from src.utils.i18n import _

class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, colors: dict, refresh_callback=None):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.colors = colors
        self.refresh_callback = refresh_callback
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._config = load_config()
        self._build_header()
        self._build_body()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=90)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(header, text=_("set_title"),
                     font=ctk.CTkFont("Segoe UI", 24, "bold"),
                     text_color=self.colors["text_primary"]).grid(row=0, column=0, padx=36, pady=(24, 0), sticky="w")
        ctk.CTkLabel(header, text=_("set_subtitle"),
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=self.colors["text_secondary"]).grid(row=1, column=0, padx=36, pady=(4, 16), sticky="w")

    def _build_body(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=self.colors["bg_dark"], corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Download Settings ─────────────────────────────────────────
        dl_card = self._card(scroll, _("card_dl_set"))
        dl_card.grid(row=0, column=0, padx=36, pady=(32, 16), sticky="ew")
        dl_card.grid_columnconfigure(1, weight=1)

        # Download path
        self._setting_row(dl_card, 1, _("set_dl_path"))
        path_row = ctk.CTkFrame(dl_card, fg_color="transparent")
        path_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 16))
        path_row.grid_columnconfigure(0, weight=1)

        self.dl_path_var = ctk.StringVar(value=self._config.get("download_path", ""))
        self.dl_path_entry = ctk.CTkEntry(path_row, textvariable=self.dl_path_var,
                                           height=42, corner_radius=10,
                                           font=ctk.CTkFont("Segoe UI", 13),
                                           fg_color=self.colors["bg_dark"],
                                           border_color=self.colors["border"],
                                           text_color=self.colors["text_primary"])
        self.dl_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        ctk.CTkButton(path_row, text=_("btn_browse"), width=120, height=42, corner_radius=10,
                      fg_color=self.colors["border"], hover_color=self.colors["accent"],
                      font=ctk.CTkFont("Segoe UI", 13),
                      command=self._browse_dl_path).grid(row=0, column=1)

        # Video format
        self._setting_row(dl_card, 3, _("set_vid_fmt"))
        self.vid_fmt_var = ctk.StringVar(value=self._config.get("default_video_format", "mp4"))
        ctk.CTkOptionMenu(dl_card, variable=self.vid_fmt_var, values=["mp4", "mkv", "webm"],
                           height=40, corner_radius=10,
                           fg_color=self.colors["bg_dark"], button_color=self.colors["accent"],
                           font=ctk.CTkFont("Segoe UI", 13)
                           ).grid(row=4, column=0, sticky="w", padx=24, pady=(0, 16))

        # Audio format
        self._setting_row(dl_card, 5, _("set_aud_fmt"))
        self.aud_fmt_var = ctk.StringVar(value=self._config.get("default_audio_format", "mp3"))
        ctk.CTkOptionMenu(dl_card, variable=self.aud_fmt_var, values=["mp3", "m4a", "flac", "wav", "aac"],
                           height=40, corner_radius=10,
                           fg_color=self.colors["bg_dark"], button_color=self.colors["accent"],
                           font=ctk.CTkFont("Segoe UI", 13)
                           ).grid(row=6, column=0, sticky="w", padx=24, pady=(0, 16))

        # FFmpeg path
        self._setting_row(dl_card, 7, _("set_ffmpeg"))
        ffmpeg_row = ctk.CTkFrame(dl_card, fg_color="transparent")
        ffmpeg_row.grid(row=8, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 20))
        ffmpeg_row.grid_columnconfigure(0, weight=1)

        self.ffmpeg_var = ctk.StringVar(value=self._config.get("ffmpeg_path", ""))
        ctk.CTkEntry(ffmpeg_row, textvariable=self.ffmpeg_var,
                     placeholder_text=_("set_ffmpeg_ph"),
                     height=42, corner_radius=10,
                     font=ctk.CTkFont("Segoe UI", 13),
                     fg_color=self.colors["bg_dark"], border_color=self.colors["border"],
                     text_color=self.colors["text_primary"]).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ctk.CTkButton(ffmpeg_row, text="📁", width=46, height=42, corner_radius=10,
                      fg_color=self.colors["border"], hover_color=self.colors["accent"],
                      command=self._browse_ffmpeg).grid(row=0, column=1)

        # Options checkboxes
        self.embed_thumb_var = ctk.BooleanVar(value=self._config.get("embed_thumbnail", True))
        ctk.CTkCheckBox(dl_card, text=_("chk_thumb"),
                         variable=self.embed_thumb_var,
                         font=ctk.CTkFont("Segoe UI", 13),
                         text_color=self.colors["text_primary"],
                         fg_color=self.colors["accent"]
                         ).grid(row=9, column=0, sticky="w", padx=24, pady=(0, 12))

        self.embed_lyrics_var = ctk.BooleanVar(value=self._config.get("embed_lyrics", True))
        ctk.CTkCheckBox(dl_card, text=_("chk_meta"),
                         variable=self.embed_lyrics_var,
                         font=ctk.CTkFont("Segoe UI", 13),
                         text_color=self.colors["text_primary"],
                         fg_color=self.colors["accent"]
                         ).grid(row=10, column=0, sticky="w", padx=24, pady=(0, 24))

        # ── Spotify Settings ──────────────────────────────────────────
        sp_card = self._card(scroll, _("card_sp_set"))
        sp_card.grid(row=1, column=0, padx=36, pady=16, sticky="ew")
        sp_card.grid_columnconfigure((0, 1), weight=1)

        info_lbl = ctk.CTkLabel(sp_card, text=_("sp_info_lbl"),
                                 font=ctk.CTkFont("Segoe UI", 12),
                                 text_color=self.colors["text_secondary"])
        info_lbl.grid(row=1, column=0, columnspan=2, sticky="w", padx=24, pady=(8, 16))

        self._setting_row(sp_card, 2, "Client ID")
        self.sp_id_var = ctk.StringVar(value=self._config.get("spotify_client_id", ""))
        ctk.CTkEntry(sp_card, textvariable=self.sp_id_var,
                     placeholder_text="Spotify Client ID",
                     height=42, corner_radius=10,
                     font=ctk.CTkFont("Segoe UI", 13),
                     fg_color=self.colors["bg_dark"], border_color=self.colors["border"],
                     text_color=self.colors["text_primary"]
                     ).grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 16))

        self._setting_row(sp_card, 4, "Client Secret")
        self.sp_secret_var = ctk.StringVar(value=self._config.get("spotify_client_secret", ""))
        ctk.CTkEntry(sp_card, textvariable=self.sp_secret_var,
                     placeholder_text="Spotify Client Secret",
                     show="•", height=42, corner_radius=10,
                     font=ctk.CTkFont("Segoe UI", 13),
                     fg_color=self.colors["bg_dark"], border_color=self.colors["border"],
                     text_color=self.colors["text_primary"]
                     ).grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 24))

        # ── Lyrics Settings ───────────────────────────────────────────
        lyr_card = self._card(scroll, _("card_lyr_set"))
        lyr_card.grid(row=2, column=0, padx=36, pady=16, sticky="ew")

        self._setting_row(lyr_card, 1, _("set_lyr_prov"))
        self.lyrics_prov_var = ctk.StringVar(value=self._config.get("lyrics_provider", "lrclib"))
        ctk.CTkOptionMenu(lyr_card, variable=self.lyrics_prov_var,
                           values=["lrclib", "syncedlyrics"],
                           height=40, corner_radius=10,
                           fg_color=self.colors["bg_dark"], button_color=self.colors["accent"],
                           font=ctk.CTkFont("Segoe UI", 13)
                           ).grid(row=2, column=0, sticky="w", padx=24, pady=(0, 24))

        # ── Appearance & Language ─────────────────────────────────────
        app_card = self._card(scroll, _("card_app_set"))
        app_card.grid(row=3, column=0, padx=36, pady=16, sticky="ew")

        self._setting_row(app_card, 1, _("set_lang"))
        self.lang_var = ctk.StringVar(value="ar" if self._config.get("language", "ar") == "ar" else "en")
        
        def _set_lang_var(choice):
            if choice == _("lang_ar"): self.lang_var.set("ar")
            else: self.lang_var.set("en")

        curr_lang_text = _("lang_ar") if self.lang_var.get() == "ar" else _("lang_en")
        lang_menu = ctk.CTkOptionMenu(app_card, values=[_("lang_ar"), _("lang_en")],
                           height=40, corner_radius=10,
                           fg_color=self.colors["bg_dark"], button_color=self.colors["accent"],
                           font=ctk.CTkFont("Segoe UI", 13),
                           command=_set_lang_var)
        lang_menu.set(curr_lang_text)
        lang_menu.grid(row=2, column=0, sticky="w", padx=24, pady=(0, 16))

        self._setting_row(app_card, 3, _("set_theme"))
        self.appearance_var = ctk.StringVar(value=self._config.get("appearance_mode", "dark"))
        ctk.CTkSegmentedButton(app_card, variable=self.appearance_var,
                                values=["dark", "light", "system"],
                                font=ctk.CTkFont("Segoe UI", 13),
                                fg_color=self.colors["bg_dark"],
                                selected_color=self.colors["accent"],
                                ).grid(row=4, column=0, sticky="w", padx=24, pady=(0, 24))

        # ── Save button ───────────────────────────────────────────────
        save_row = ctk.CTkFrame(scroll, fg_color="transparent")
        save_row.grid(row=4, column=0, padx=36, pady=(16, 40), sticky="ew")

        self.save_btn = ctk.CTkButton(
            save_row, text=_("btn_save"), height=54, corner_radius=14,
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            command=self._save,
        )
        self.save_btn.pack(side="left")

        self.save_status = ctk.CTkLabel(save_row, text="",
                                         font=ctk.CTkFont("Segoe UI", 13),
                                         text_color=self.colors["text_secondary"])
        self.save_status.pack(side="left", padx=20)

    def _setting_row(self, parent, row: int, label: str):
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=self.colors["text_secondary"]
                     ).grid(row=row, column=0, sticky="w", padx=24, pady=(12, 6))

    def _browse_dl_path(self):
        path = filedialog.askdirectory(title=_("set_dl_path"))
        if path:
            self.dl_path_var.set(path)

    def _browse_ffmpeg(self):
        path = filedialog.askopenfilename(
            title="Choose ffmpeg.exe",
            filetypes=[("Executable", "*.exe"), ("All", "*.*")]
        )
        if path:
            self.ffmpeg_var.set(path)

    def _save(self):
        config = load_config()
        config["download_path"] = self.dl_path_var.get().strip()
        config["default_video_format"] = self.vid_fmt_var.get()
        config["default_audio_format"] = self.aud_fmt_var.get()
        config["ffmpeg_path"] = self.ffmpeg_var.get().strip()
        config["embed_thumbnail"] = self.embed_thumb_var.get()
        config["embed_lyrics"] = self.embed_lyrics_var.get()
        config["spotify_client_id"] = self.sp_id_var.get().strip()
        config["spotify_client_secret"] = self.sp_secret_var.get().strip()
        config["lyrics_provider"] = self.lyrics_prov_var.get()
        config["appearance_mode"] = self.appearance_var.get()
        config["language"] = self.lang_var.get()

        if save_config(config):
            self.save_status.configure(text=_("msg_saved"), text_color=self.colors["success"])
            if self.refresh_callback:
                self.refresh_callback()
        else:
            self.save_status.configure(text=_("msg_save_err"), text_color=self.colors["error"])

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card_bg"], corner_radius=16,
                              border_width=1, border_color=self.colors["border"])
        frame.grid_columnconfigure(0, weight=1)
        if title:
            ctk.CTkLabel(frame, text=title,
                          font=ctk.CTkFont("Segoe UI", 15, "bold"),
                          text_color=self.colors["accent"]).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 0))
        return frame
