"""
Downloader Tab — Main download UI with video info, quality selector, progress
"""
import os
import io
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import requests

from src.core import downloader, info_fetcher
from src.utils.config_manager import load_config
from src.utils.helpers import is_valid_url, is_playlist_url, get_platform_name
from src.utils.i18n import _

class DownloaderTab(ctk.CTkFrame):
    def __init__(self, parent, colors: dict):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.colors = colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._info = None
        self._thumb_image = None
        self._download_task = None
        self._current_mode = "video"

        self._build_header()
        self._build_body()

    # ─── Header ──────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=90)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        title = ctk.CTkLabel(header, text=_("dl_title"),
                              font=ctk.CTkFont("Segoe UI", 24, "bold"),
                              text_color=self.colors["text_primary"])
        title.grid(row=0, column=0, padx=36, pady=(24, 0), sticky="w")

        subtitle = ctk.CTkLabel(header, text=_("dl_subtitle"),
                                 font=ctk.CTkFont("Segoe UI", 13),
                                 text_color=self.colors["text_secondary"])
        subtitle.grid(row=1, column=0, padx=36, pady=(4, 16), sticky="w")

    # ─── Body ─────────────────────────────────────────────────────────
    def _build_body(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=self.colors["bg_dark"], corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        # URL input card
        url_card = self._card(scroll, _("card_url"))
        url_card.grid(row=0, column=0, padx=36, pady=(32, 16), sticky="ew")
        url_card.grid_columnconfigure(0, weight=1)

        url_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_row.grid(row=1, column=0, sticky="ew", padx=0, pady=(8, 0))
        url_row.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text=_("url_placeholder"),
            height=50, corner_radius=12,
            font=ctk.CTkFont("Segoe UI", 14),
            fg_color=self.colors["bg_dark"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.url_entry.bind("<Return>", lambda e: self._on_fetch())

        paste_btn = ctk.CTkButton(url_row, text=_("btn_paste"), width=90, height=50,
                                   corner_radius=12,
                                   fg_color=self.colors["border"],
                                   hover_color=self.colors["accent"],
                                   font=ctk.CTkFont("Segoe UI", 14),
                                   command=self._paste_url)
        paste_btn.grid(row=0, column=1)

        fetch_btn = ctk.CTkButton(url_row, text=_("btn_fetch"), width=160, height=50,
                                   corner_radius=12,
                                   fg_color=self.colors["accent"],
                                   hover_color=self.colors["accent_hover"],
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   command=self._on_fetch)
        fetch_btn.grid(row=0, column=2, padx=(12, 0))

        self.fetch_status = ctk.CTkLabel(url_card, text="",
                                          font=ctk.CTkFont("Segoe UI", 12),
                                          text_color=self.colors["text_secondary"])
        self.fetch_status.grid(row=2, column=0, sticky="w", pady=(8, 0))

        # Info card (hidden until URL fetched)
        self.info_card = self._card(scroll, "")
        self.info_card.grid(row=1, column=0, padx=36, pady=16, sticky="ew")
        self.info_card.grid_columnconfigure(1, weight=1)
        self.info_card.grid_remove()

        # Thumbnail
        self.thumb_label = ctk.CTkLabel(self.info_card, text="", width=180, height=100)
        self.thumb_label.grid(row=0, column=0, rowspan=4, padx=(0, 24), pady=12, sticky="nw")

        self.vid_title = ctk.CTkLabel(self.info_card, text="", wraplength=500,
                                       font=ctk.CTkFont("Segoe UI", 16, "bold"),
                                       text_color=self.colors["text_primary"], anchor="w", justify="left")
        self.vid_title.grid(row=0, column=1, sticky="ew", pady=(12, 4))

        self.vid_uploader = ctk.CTkLabel(self.info_card, text="",
                                          font=ctk.CTkFont("Segoe UI", 13),
                                          text_color=self.colors["accent2"], anchor="w")
        self.vid_uploader.grid(row=1, column=1, sticky="ew")

        self.vid_meta = ctk.CTkLabel(self.info_card, text="",
                                      font=ctk.CTkFont("Segoe UI", 12),
                                      text_color=self.colors["text_secondary"], anchor="w")
        self.vid_meta.grid(row=2, column=1, sticky="ew")

        self.playlist_badge = ctk.CTkLabel(self.info_card, text="",
                                            font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                            text_color=self.colors["warning"])
        self.playlist_badge.grid(row=3, column=1, sticky="ew", pady=(6, 12))

        # Options card
        opt_card = self._card(scroll, _("card_options"))
        opt_card.grid(row=2, column=0, padx=36, pady=16, sticky="ew")
        opt_card.grid_columnconfigure((0, 1, 2), weight=1)

        # Mode selector
        mode_label = ctk.CTkLabel(opt_card, text=_("lbl_type"),
                                   font=ctk.CTkFont("Segoe UI", 13),
                                   text_color=self.colors["text_secondary"])
        mode_label.grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(16, 6))

        mode_frame = ctk.CTkFrame(opt_card, fg_color="transparent")
        mode_frame.grid(row=2, column=0, sticky="ew", padx=(0, 20))

        self.mode_var = ctk.StringVar(value="video")
        for txt, val in [(_("opt_video"), "video"), (_("opt_audio"), "audio")]:
            rb = ctk.CTkRadioButton(mode_frame, text=txt, variable=self.mode_var, value=val,
                                     font=ctk.CTkFont("Segoe UI", 14),
                                     text_color=self.colors["text_primary"],
                                     fg_color=self.colors["accent"],
                                     command=self._on_mode_change)
            rb.pack(side="left", padx=(0, 20))

        # Quality selector
        quality_label = ctk.CTkLabel(opt_card, text=_("lbl_quality"),
                                      font=ctk.CTkFont("Segoe UI", 13),
                                      text_color=self.colors["text_secondary"])
        quality_label.grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(16, 6))

        self.quality_var = ctk.StringVar(value="1080p")
        self.quality_menu = ctk.CTkOptionMenu(
            opt_card, variable=self.quality_var,
            values=["4K", "1080p", "720p", "480p", "360p"],
            height=42, corner_radius=10,
            fg_color=self.colors["bg_dark"],
            button_color=self.colors["accent"],
            font=ctk.CTkFont("Segoe UI", 14),
        )
        self.quality_menu.grid(row=2, column=1, sticky="ew", padx=(0, 20))

        # Output folder
        folder_label = ctk.CTkLabel(opt_card, text=_("lbl_folder"),
                                     font=ctk.CTkFont("Segoe UI", 13),
                                     text_color=self.colors["text_secondary"])
        folder_label.grid(row=1, column=2, sticky="w", pady=(16, 6))

        folder_row = ctk.CTkFrame(opt_card, fg_color="transparent")
        folder_row.grid(row=2, column=2, sticky="ew")
        folder_row.grid_columnconfigure(0, weight=1)

        config = load_config()
        self.folder_var = ctk.StringVar(value=config.get("download_path", os.path.expanduser("~/Downloads")))
        self.folder_entry = ctk.CTkEntry(folder_row, textvariable=self.folder_var,
                                          height=42, corner_radius=10,
                                          font=ctk.CTkFont("Segoe UI", 12),
                                          fg_color=self.colors["bg_dark"],
                                          border_color=self.colors["border"],
                                          text_color=self.colors["text_primary"])
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        browse_btn = ctk.CTkButton(folder_row, text="📁", width=42, height=42, corner_radius=10,
                                    fg_color=self.colors["border"],
                                    hover_color=self.colors["accent"],
                                    command=self._browse_folder)
        browse_btn.grid(row=0, column=1)

        # Progress card
        prog_card = self._card(scroll, _("card_progress"))
        prog_card.grid(row=3, column=0, padx=36, pady=16, sticky="ew")
        prog_card.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(prog_card, height=16, corner_radius=8,
                                                fg_color=self.colors["bg_dark"],
                                                progress_color=self.colors["accent"])
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(16, 8))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(prog_card, text=_("prog_ready"),
                                            font=ctk.CTkFont("Segoe UI", 13),
                                            text_color=self.colors["text_secondary"])
        self.progress_label.grid(row=2, column=0, sticky="w", pady=(0, 12))

        # Download button
        self.dl_btn = ctk.CTkButton(
            scroll, text=_("btn_download"), height=60,
            corner_radius=16,
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            command=self._on_download,
        )
        self.dl_btn.grid(row=4, column=0, padx=36, pady=(12, 40), sticky="ew")

    # ─── Helpers ──────────────────────────────────────────────────────
    def _card(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card_bg"], corner_radius=16,
                              border_width=1, border_color=self.colors["border"])
        frame.grid_columnconfigure(0, weight=1)
        if title:
            lbl = ctk.CTkLabel(frame, text=title,
                                font=ctk.CTkFont("Segoe UI", 15, "bold"),
                                text_color=self.colors["accent"])
            lbl.grid(row=0, column=0, sticky="w", padx=24, pady=(20, 0))
        return frame

    def _paste_url(self):
        try:
            text = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text.strip())
            self._on_fetch()
        except Exception:
            pass

    def _browse_folder(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title=_("lbl_folder"))
        if path:
            self.folder_var.set(path)

    def _on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "audio":
            self.quality_menu.configure(values=["320kbps", "192kbps", "128kbps"])
            self.quality_var.set("192kbps")
        else:
            self.quality_menu.configure(values=["4K", "1080p", "720p", "480p", "360p"])
            self.quality_var.set("1080p")

    def _on_fetch(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        if not is_valid_url(url):
            self.fetch_status.configure(text=_("err_invalid_url"), text_color=self.colors["error"])
            return
        self.fetch_status.configure(text=_("msg_fetching"), text_color=self.colors["text_secondary"])
        self.info_card.grid_remove()

        platform = get_platform_name(url)
        self.fetch_status.configure(text=_("msg_fetching_plat", platform=platform))

        info_fetcher.fetch_info(
            url,
            callback=lambda info: self.after(0, lambda: self._on_info_ready(info)),
            error_callback=lambda e: self.after(0, lambda: self._on_fetch_error(e)),
        )

    def _on_info_ready(self, info: dict):
        self._info = info
        self.fetch_status.configure(text=_("msg_fetch_done"), text_color=self.colors["success"])
        self.info_card.grid()

        if info["type"] == "playlist":
            self.vid_title.configure(text=f"📋 {info['title']}")
            self.vid_uploader.configure(text=info.get("uploader", ""))
            self.vid_meta.configure(text="")
            self.playlist_badge.configure(
                text=_("lbl_playlist_badge", count=info['count'])
            )
        else:
            self.vid_title.configure(text=info["title"])
            self.vid_uploader.configure(text=f"📺 {info['uploader']}")
            self.vid_meta.configure(
                text=f"⏱ {info['duration']}   👁 {info['view_count']} " + _("lbl_views")
            )
            self.playlist_badge.configure(text="")

            # Update quality options
            fmts = info.get("formats", {})
            if fmts:
                mode = self.mode_var.get()
                if mode == "video" and fmts.get("video"):
                    self.quality_menu.configure(values=fmts["video"])
                    self.quality_var.set(fmts["video"][0])
                elif fmts.get("audio"):
                    self.quality_menu.configure(values=fmts["audio"])
                    self.quality_var.set(fmts["audio"][0])

        # Load thumbnail
        thumb_url = info.get("thumbnail", "")
        if thumb_url:
            threading.Thread(target=self._load_thumb, args=(thumb_url,), daemon=True).start()

    def _load_thumb(self, url: str):
        data = info_fetcher.fetch_thumbnail_bytes(url)
        if data:
            try:
                img = Image.open(io.BytesIO(data)).resize((180, 100), Image.LANCZOS)
                ctk_img = ctk.CTkImage(img, size=(180, 100))
                self.after(0, lambda: self.thumb_label.configure(image=ctk_img, text=""))
                self._thumb_image = ctk_img
            except Exception:
                pass

    def _on_fetch_error(self, error: str):
        self.fetch_status.configure(
            text=f"❌ {error[:80]}",
            text_color=self.colors["error"]
        )

    def _on_download(self):
        url = self.url_entry.get().strip()
        if not url:
            self.progress_label.configure(text=_("err_no_url"), text_color=self.colors["error"])
            return

        out_dir = self.folder_var.get()
        if not os.path.isdir(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except Exception:
                self.progress_label.configure(text=_("err_invalid_folder"), text_color=self.colors["error"])
                return

        self.progress_bar.set(0)
        self.progress_label.configure(text=_("msg_downloading"), text_color=self.colors["text_secondary"])
        self.dl_btn.configure(state="disabled", text=_("msg_downloading"))

        task = downloader.DownloadTask(
            url=url,
            mode=self.mode_var.get(),
            quality=self.quality_var.get(),
            output_dir=out_dir,
            progress_callback=lambda d: self.after(0, lambda: self._on_progress(d)),
            done_callback=lambda: self.after(0, self._on_done),
            error_callback=lambda e: self.after(0, lambda: self._on_error(e)),
        )
        self._download_task = task
        downloader.download(task)

    def _on_progress(self, data: dict):
        status = data.get("status", "")
        percent = data.get("percent", 0)
        speed = data.get("speed", "—")
        eta = data.get("eta", "—")

        self.progress_bar.set(percent / 100)

        if status == "processing":
            self.progress_label.configure(
                text=_("msg_processing"),
                text_color=self.colors["accent2"]
            )
        else:
            self.progress_label.configure(
                text=f"⬇ {percent:.1f}%   🚀 {speed}   ⏱ {eta}",
                text_color=self.colors["text_primary"]
            )

    def _on_done(self):
        self.progress_bar.set(1)
        self.progress_label.configure(text=_("msg_dl_done"), text_color=self.colors["success"])
        self.dl_btn.configure(state="normal", text=_("btn_download"))

    def _on_error(self, error: str):
        self.progress_label.configure(
            text=f"❌ {error[:100]}",
            text_color=self.colors["error"]
        )
        self.dl_btn.configure(state="normal", text=_("btn_download"))
