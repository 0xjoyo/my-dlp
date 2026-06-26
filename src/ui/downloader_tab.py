"""
Downloader Tab — Main download UI with video info, quality selector, progress
"""
import os
import io
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

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
        self._download_queue = []
        self._current_task = None

        self._build_header()
        self._build_body()

    def _build_header(self):
        # Header needs to fit title (24pt) + subtitle (13pt) + search bar (36px).
        # 24 + ~20 + 13 + 16 + 8 + 36 + padding = ~120px, but we keep a single
        # compact row by placing the search bar in column 1 with sticky="e"
        # (right edge) and letting the title/subtitle sit vertically in column 0.
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=110)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)  # title/subtitle area
        header.grid_columnconfigure(1, weight=0)  # search bar — fixed width
        header.grid_propagate(False)

        title = ctk.CTkLabel(header, text=_("dl_title"),
                              font=ctk.CTkFont("Segoe UI", 24, "bold"),
                              text_color=self.colors["text_primary"])
        title.grid(row=0, column=0, padx=36, pady=(24, 0), sticky="w")

        subtitle = ctk.CTkLabel(header, text=_("dl_subtitle"),
                                 font=ctk.CTkFont("Segoe UI", 13),
                                 text_color=self.colors["text_secondary"])
        subtitle.grid(row=1, column=0, padx=36, pady=(4, 16), sticky="w")

        # ── Search bar ──
        search_row = ctk.CTkFrame(header, fg_color="transparent")
        search_row.grid(row=0, column=1, rowspan=2, padx=(0, 36), sticky="e")
        search_row.grid_columnconfigure(0, weight=0)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search_typing())
        self.search_entry = ctk.CTkEntry(
            search_row, textvariable=self.search_var,
            placeholder_text=_("dl_search_ph"),
            width=260, height=36, corner_radius=18,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=self.colors["bg_dark"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        self.search_entry.grid(row=0, column=0, sticky="e", padx=(0, 6))
        self.search_entry.bind("<Return>", lambda e: self._run_search())

        ctk.CTkButton(search_row, text=_("dl_search"), width=70, height=36,
                      corner_radius=18, fg_color=self.colors["accent"],
                      hover_color=self.colors["accent_hover"],
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      command=self._run_search
                      ).grid(row=0, column=1)

    def _build_body(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=self.colors["bg_dark"], corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        # ── URL Input Card ──
        url_card = self._card(scroll, _("card_url"))
        url_card.grid(row=0, column=0, padx=36, pady=(32, 16), sticky="ew")
        url_card.grid_columnconfigure(0, weight=1)

        hint = ctk.CTkLabel(url_card, text=_("dl_batch_hint"), font=ctk.CTkFont("Segoe UI", 12), text_color=self.colors["text_secondary"])
        hint.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 4))

        url_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_row.grid(row=2, column=0, sticky="ew", padx=0, pady=(8, 0))
        url_row.grid_columnconfigure(0, weight=1)

        self.url_textbox = ctk.CTkTextbox(
            url_row, height=80, corner_radius=12,
            font=ctk.CTkFont("Segoe UI", 14),
            fg_color=self.colors["bg_dark"],
            border_color=self.colors["border"],
            border_width=1,
            text_color=self.colors["text_primary"],
        )
        self.url_textbox.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        # Drag & drop support. We try to install tkinterdnd2 bindings on
        # the textbox so the user can drag URLs from their browser into
        # the field. If tkinterdnd2 isn't available (or the platform is
        # Wayland with no support), the helper returns False and we
        # fall back to the existing paste shortcut.
        from src.utils.dnd import setup_dnd
        dnd_ok = setup_dnd(
            self.url_textbox,
            on_drop=self._on_url_dropped,
            on_unsupported_platform=self._on_dnd_unsupported,
        )
        # Show the hint label only when DnD is wired up — otherwise it'd
        # just be a tease.
        if dnd_ok:
            dnd_hint = ctk.CTkLabel(
                url_card,
                text=_("drag_drop_hint"),
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=self.colors["accent2"],
            )
            dnd_hint.grid(row=3, column=0, sticky="w", padx=24, pady=(4, 0))

        btn_frame = ctk.CTkFrame(url_row, fg_color="transparent")
        btn_frame.grid(row=0, column=1)

        paste_btn = ctk.CTkButton(btn_frame, text=_("btn_paste"), width=120, height=36,
                                   corner_radius=8, fg_color=self.colors["border"], hover_color=self.colors["accent"],
                                   command=self._paste_url)
        paste_btn.pack(pady=(0, 8))

        fetch_btn = ctk.CTkButton(btn_frame, text=_("btn_fetch"), width=120, height=36,
                                   corner_radius=8, fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"), command=self._on_fetch)
        fetch_btn.pack()

        self.fetch_status = ctk.CTkLabel(url_card, text="", font=ctk.CTkFont("Segoe UI", 12))
        self.fetch_status.grid(row=4, column=0, sticky="w", pady=(8, 0))

        # ── Download Presets ──
        presets = [(_("preset_mp3"), "audio", "192kbps"),
                    (_("preset_hd"), "video", "1080p"),
                    (_("preset_4k"), "video", "4K"),
                    (_("preset_best_audio"), "audio", "320kbps")]
        preset_card = self._card(scroll, _("card_presets"))
        preset_card.grid(row=1, column=0, padx=36, pady=16, sticky="ew")
        preset_card.grid_columnconfigure(0, weight=1)
   
        preset_row = ctk.CTkFrame(preset_card, fg_color="transparent")
        preset_row.grid(row=1, column=0, padx=12, pady=(4, 16))
        for txt, mode, quality in presets:
            btn = ctk.CTkButton(preset_row, text=txt, width=120, height=36,
                                corner_radius=8, fg_color=self.colors["border"],
                                hover_color=self.colors["accent"],
                                font=ctk.CTkFont("Segoe UI", 12))
            btn.configure(command=lambda m=mode, q=quality: self._apply_preset(m, q))
            btn.pack(side="left", padx=8)

        # ── Info & Tag Editor Card ──
        self.info_card = self._card(scroll, "")
        self.info_card.grid(row=2, column=0, padx=36, pady=16, sticky="ew")
        self.info_card.grid_columnconfigure(1, weight=1)
        self.info_card.grid_remove()

        self.thumb_label = ctk.CTkLabel(self.info_card, text="", width=180, height=100)
        self.thumb_label.grid(row=0, column=0, rowspan=5, padx=(0, 24), pady=12, sticky="nw")

        self.vid_title = ctk.CTkLabel(self.info_card, text="", wraplength=500,
                                       font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=self.colors["text_primary"], anchor="w", justify="left")
        self.vid_title.grid(row=0, column=1, sticky="ew", pady=(12, 4))
        self.vid_meta = ctk.CTkLabel(self.info_card, text="", font=ctk.CTkFont("Segoe UI", 12), text_color=self.colors["text_secondary"], anchor="w")
        self.vid_meta.grid(row=1, column=1, sticky="ew", pady=(0, 12))

        # Tag Editor (Only visible if 1 URL is entered)
        self.tag_frame = ctk.CTkFrame(self.info_card, fg_color="transparent")
        self.tag_frame.grid(row=2, column=1, sticky="ew")
        self.tag_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.tag_frame, text=_("lbl_tag_title"), font=ctk.CTkFont("Segoe UI", 12)).grid(row=0, column=0, sticky="w", padx=(0,8))
        self.tag_title = ctk.CTkEntry(self.tag_frame, height=28, corner_radius=6, border_color=self.colors["border"], fg_color=self.colors["bg_dark"])
        self.tag_title.grid(row=0, column=1, sticky="ew", pady=4)
        
        ctk.CTkLabel(self.tag_frame, text=_("lbl_tag_artist"), font=ctk.CTkFont("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=(0,8))
        self.tag_artist = ctk.CTkEntry(self.tag_frame, height=28, corner_radius=6, border_color=self.colors["border"], fg_color=self.colors["bg_dark"])
        self.tag_artist.grid(row=1, column=1, sticky="ew", pady=4)

        # ── Options Card ──
        opt_card = self._card(scroll, _("card_options"))
        opt_card.grid(row=3, column=0, padx=36, pady=16, sticky="ew")
        opt_card.grid_columnconfigure((0, 1, 2), weight=1)

        mode_frame = ctk.CTkFrame(opt_card, fg_color="transparent")
        mode_frame.grid(row=1, column=0, sticky="ew", padx=(0, 20), pady=16)
        self.mode_var = ctk.StringVar(value="video")
        for txt, val in [(_("opt_video"), "video"), (_("opt_audio"), "audio")]:
            ctk.CTkRadioButton(mode_frame, text=txt, variable=self.mode_var, value=val,
                               font=ctk.CTkFont("Segoe UI", 14), fg_color=self.colors["accent"],
                               command=self._on_mode_change).pack(side="left", padx=(0, 20))

        self.quality_var = ctk.StringVar(value="1080p")
        self.quality_menu = ctk.CTkOptionMenu(
            opt_card, variable=self.quality_var,
            values=["4K", "1080p", "720p", "480p", "360p"],
            height=42, corner_radius=10, fg_color=self.colors["bg_dark"], button_color=self.colors["accent"], font=ctk.CTkFont("Segoe UI", 14),
        )
        self.quality_menu.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=16)

        folder_row = ctk.CTkFrame(opt_card, fg_color="transparent")
        folder_row.grid(row=1, column=2, sticky="ew", pady=16)
        folder_row.grid_columnconfigure(0, weight=1)

        config = load_config()
        self.folder_var = ctk.StringVar(value=config.get("download_path", os.path.expanduser("~/Downloads")))
        ctk.CTkEntry(folder_row, textvariable=self.folder_var, height=42, corner_radius=10,
                     fg_color=self.colors["bg_dark"], border_color=self.colors["border"]).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(folder_row, text="📁", width=42, height=42, corner_radius=10,
                      fg_color=self.colors["border"], hover_color=self.colors["accent"], command=self._browse_folder).grid(row=0, column=1)

        # ── Progress Card ──
        prog_card = self._card(scroll, _("card_progress"))
        prog_card.grid(row=4, column=0, padx=36, pady=16, sticky="ew")
        prog_card.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(prog_card, height=16, corner_radius=8, fg_color=self.colors["bg_dark"], progress_color=self.colors["accent"])
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(16, 8))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(prog_card, text=_("prog_ready"), font=ctk.CTkFont("Segoe UI", 13), text_color=self.colors["text_secondary"])
        self.progress_label.grid(row=2, column=0, sticky="w", pady=(0, 12))

        # ── Download Button ──
        self.dl_btn = ctk.CTkButton(
            scroll, text=_("btn_download"), height=60, corner_radius=16, font=ctk.CTkFont("Segoe UI", 18, "bold"),
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._on_download_click,
        )
        self.dl_btn.grid(row=5, column=0, padx=36, pady=(12, 40), sticky="ew")

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        """Build a card frame. The title (if any) takes row=0.

        Callers should place their own content starting at row=1 — using
        row=0 would overlap with the title label.
        """
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card_bg"], corner_radius=16, border_width=1, border_color=self.colors["border"])
        frame.grid_columnconfigure(0, weight=1)
        if title:
            ctk.CTkLabel(frame, text=title, font=ctk.CTkFont("Segoe UI", 15, "bold"), text_color=self.colors["accent"]).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 12))
        return frame

    def _paste_url(self):
        try:
            text = self.clipboard_get()
            # Append if empty, else insert on new line
            current = self.url_textbox.get("1.0", "end-1c").strip()
            self.url_textbox.delete("1.0", "end")
            if current:
                self.url_textbox.insert("1.0", f"{current}\n{text.strip()}")
            else:
                self.url_textbox.insert("1.0", text.strip())
        except Exception:
            pass

    def _on_url_dropped(self, item: str):
        """
        Called by the DnD helper when the user drops a URL (or file path)
        onto the URL textbox. We accept URLs and ignore local file paths
        (those wouldn't make sense for yt-dlp).
        """
        # Strip file:// prefix that some drag sources add
        if item.startswith("file://"):
            item = item[len("file://"):]
        # Quick sanity check: is this an HTTP(S) URL?
        if not (item.startswith("http://") or item.startswith("https://")):
            return

        # If the user already pasted something, append on a new line
        current = self.url_textbox.get("1.0", "end-1c").strip()
        self.url_textbox.delete("1.0", "end")
        if current:
            self.url_textbox.insert("1.0", f"{current}\n{item}")
        else:
            self.url_textbox.insert("1.0", item)

        # Briefly highlight the textbox so the user sees the drop landed
        try:
            self.url_textbox.configure(border_color=self.colors["accent"])
            self.after(800, lambda: self.url_textbox.configure(
                border_color=self.colors["border"]
            ))
        except Exception:
            pass

    def _on_dnd_unsupported(self):
        """Called once at startup if tkinterdnd2 isn't available."""
        # Silent — the user can still paste with Ctrl+V. Could surface a
        # one-time toast but the existing paste shortcut covers the case.
        pass

    def _browse_folder(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title=_("lbl_folder"))
        if path: self.folder_var.set(path)

    def _on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "audio":
            self.quality_menu.configure(values=["320kbps", "192kbps", "128kbps"])
            self.quality_var.set("192kbps")
            self.tag_frame.grid() # show tag editor
        else:
            self.quality_menu.configure(values=["4K", "1080p", "720p", "480p", "360p"])
            self.quality_var.set("1080p")
            self.tag_frame.grid_remove() # hide tag editor

    def _get_urls(self):
        text = self.url_textbox.get("1.0", "end-1c")
        return [u.strip() for u in text.split("\n") if is_valid_url(u.strip())]

    def _on_fetch(self):
        urls = self._get_urls()
        if not urls:
            self.fetch_status.configure(text=_("err_invalid_url"), text_color=self.colors["error"])
            return
        
        self.fetch_status.configure(text=_("msg_fetching"), text_color=self.colors["text_secondary"])
        self.info_card.grid_remove()
        
        if len(urls) > 1:
            self.fetch_status.configure(text=f"Batch: {len(urls)} URLs loaded.", text_color=self.colors["success"])
            self.tag_frame.grid_remove()
            return
        
        url = urls[0]
        if self.mode_var.get() == "audio": self.tag_frame.grid()
        
        info_fetcher.fetch_info(url, callback=lambda i: self.after(0, lambda: self._on_info_ready(i)),
                                error_callback=lambda e: self.after(0, lambda: self._on_fetch_error(e)))

    def _on_info_ready(self, info: dict):
        self._info = info
        self.fetch_status.configure(text=_("msg_fetch_done"), text_color=self.colors["success"])
        self.info_card.grid()

        if info["type"] == "playlist":
            self.vid_title.configure(text=f"📋 {info['title']}")
            self.vid_meta.configure(text=_("dl_pl_count").format(count=info['count']))
            self.tag_frame.grid_remove()
            self.after(100, lambda: self._show_playlist_browser(info))
        else:
            self.vid_title.configure(text=info["title"])
            self.vid_meta.configure(text=f"⏱ {info['duration']}   👁 {info['view_count']} " + _("lbl_views"))
            
            # Fill Tag Editor defaults
            self.tag_title.delete(0, "end")
            self.tag_title.insert(0, info.get("title", ""))
            self.tag_artist.delete(0, "end")
            self.tag_artist.insert(0, info.get("uploader", ""))

            fmts = info.get("formats", {})
            if fmts:
                mode = self.mode_var.get()
                if mode == "video" and fmts.get("video"):
                    self.quality_menu.configure(values=fmts["video"])
                    self.quality_var.set(fmts["video"][0])
                elif fmts.get("audio"):
                    self.quality_menu.configure(values=fmts["audio"])
                    self.quality_var.set(fmts["audio"][0])

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
            except Exception: pass

    def _on_fetch_error(self, error: str):
        self.fetch_status.configure(text=f"❌ {error[:80]}", text_color=self.colors["error"])

    # ── Search YouTube ───────────────────────────────────────────

    def _on_search_typing(self):
        """Placeholder for debounced search (future)."""
        pass

    def _run_search(self, event=None):
        query = self.search_var.get().strip()
        if len(query) < 2:
            return
        from src.core.info_fetcher import search_youtube
        self.fetch_status.configure(text=_("msg_searching"), text_color=self.colors["text_secondary"])
        search_youtube(query, max_results=8,
                       callback=lambda r: self.after(0, lambda: self._show_search_results(r)),
                       error_callback=lambda e: self.after(0, lambda: self.fetch_status.configure(
                           text=f"❌ {e[:60]}", text_color=self.colors["error"])))

    def _show_search_results(self, results: list):
        if not results:
            self.fetch_status.configure(text=_("err_no_results"), text_color=self.colors["error"])
            return
        self.fetch_status.configure(text=f"🔍 {len(results)} results", text_color=self.colors["success"])

        win = ctk.CTkToplevel(self)
        win.title(_("dl_search_results"))
        win.geometry("620x500")
        win.configure(fg_color=self.colors["bg_dark"])
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(win, text=_("dl_search_results"), font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=self.colors["accent"]).pack(padx=24, pady=(20, 8), anchor="w")

        scroll = ctk.CTkScrollableFrame(win, fg_color=self.colors["bg_dark"], corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for i, r in enumerate(results):
            card = ctk.CTkFrame(scroll, fg_color=self.colors["card_bg"], corner_radius=12,
                                border_width=1, border_color=self.colors["border"])
            card.grid(row=i, column=0, padx=12, pady=6, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=f"🎬 {r['title'][:70]}",
                         font=ctk.CTkFont("Segoe UI", 14, "bold"),
                         text_color=self.colors["text_primary"]).grid(row=0, column=0, padx=16, pady=(12, 2), sticky="w")
            ctk.CTkLabel(card, text=f"👤 {r['uploader'][:40]}  ⏱ {r['duration']}  👁 {r.get('views','')}",
                         font=ctk.CTkFont("Segoe UI", 12),
                         text_color=self.colors["text_secondary"]).grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

            ctk.CTkButton(card, text=_("dl_search_paste"), width=100, height=30, corner_radius=8,
                          fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
                          font=ctk.CTkFont("Segoe UI", 12),
                          command=lambda u=r["url"]: self._paste_search_url(u, win)
                          ).grid(row=0, column=1, rowspan=2, padx=12, pady=8)

    def _paste_search_url(self, url: str, win):
        """Paste the selected search result URL into the textbox and close search."""
        current = self.url_textbox.get("1.0", "end-1c").strip()
        self.url_textbox.delete("1.0", "end")
        if current:
            self.url_textbox.insert("1.0", f"{current}\n{url}")
        else:
            self.url_textbox.insert("1.0", url)
        win.destroy()

    # ── Playlist browser ────────────────────────────────────────

    def _show_playlist_browser(self, info: dict):
        """Show playlist items with checkboxes for selective download."""
        win = ctk.CTkToplevel(self)
        win.title(_("dl_pl_title"))
        win.geometry("640x520")
        win.configure(fg_color=self.colors["bg_dark"])
        win.transient(self)
        win.grab_set()

        # Header
        ctk.CTkLabel(win, text=f"📋 {info['title']}",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=self.colors["accent"]).pack(padx=24, pady=(20, 4), anchor="w")
        ctk.CTkLabel(win, text=_("dl_pl_count").format(count=info['count']),
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=self.colors["text_secondary"]).pack(padx=24, pady=(0, 12), anchor="w")

        scroll = ctk.CTkScrollableFrame(win, fg_color=self.colors["bg_dark"], corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        var_map = {}
        entries = info.get("entries", [])
        for i, e in enumerate(entries):
            chk_row = ctk.CTkFrame(scroll, fg_color=self.colors["card_bg"], corner_radius=10)
            chk_row.grid(row=i, column=0, padx=12, pady=4, sticky="ew")
            chk_row.grid_columnconfigure(0, weight=1)

            var = ctk.BooleanVar(value=True)
            var_map[var] = e["url"]
            ctk.CTkCheckBox(chk_row, text=f"{i+1}. {e['title'][:60]}", variable=var,
                            font=ctk.CTkFont("Segoe UI", 13),
                            fg_color=self.colors["accent"],
                            text_color=self.colors["text_primary"]
                            ).grid(row=0, column=0, padx=16, pady=10, sticky="w")
            ctk.CTkLabel(chk_row, text=f"⏱ {e.get('duration','?')}",
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=self.colors["text_secondary"]
                         ).grid(row=0, column=1, padx=16)

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(padx=24, pady=(0, 16), fill="x")

        ctk.CTkButton(btn_row, text=_("dl_pl_sel_all"), width=120, height=36, corner_radius=8,
                      fg_color=self.colors["border"], hover_color=self.colors["accent"],
                      command=lambda: self._toggle_all_checks(var_map, True)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text=_("dl_pl_unsel_all"), width=120, height=36, corner_radius=8,
                      fg_color=self.colors["border"], hover_color=self.colors["accent"],
                      command=lambda: self._toggle_all_checks(var_map, False)
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text=_("btn_download"), width=140, height=40, corner_radius=10,
                      fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      command=lambda: self._download_selected(var_map, win)
                      ).pack(side="right")

    def _toggle_all_checks(self, var_map: dict, state: bool):
        for var in var_map:
            var.set(state)

    def _download_selected(self, var_map: dict, win):
        """Put selected playlist URLs into the textbox and close."""
        selected = []
        for var, url in var_map.items():
            if var.get():
                selected.append(url)
        if not selected:
            return
        self.url_textbox.delete("1.0", "end")
        self.url_textbox.insert("1.0", "\n".join(selected))
        win.destroy()
        self._on_fetch()

    # ── Presets ──────────────────────────────────────────────────

    def _apply_preset(self, mode: str, quality: str):
        """Apply a download preset: switches mode + quality and starts fetch."""
        self.mode_var.set(mode)
        self._on_mode_change()
        self.quality_var.set(quality)
        self._on_fetch()

    def _check_duplicates(self, urls: list) -> bool:
        """Return True if we should continue downloading (user clicked OK)."""
        out_dir = self.folder_var.get()
        config = load_config()
        tmpl = config.get("filename_template", "%(title)s.%(ext)s")
        dupes = []
        for url in urls:
            # Rough estimate: we can't know the exact title before fetch,
            # so we just warn generically for batch, or check the fetched info
            if self._info and self._info.get("type") != "playlist":
                title = self._info.get("title", url)
                # Guess extensions
                ext = ".mp4" if self.mode_var.get() == "video" else ".m4a"
                # Try common patterns
                safe_tmpl = tmpl.replace("%(title)s", title[:80]) \
                                 .replace("%(ext)s", ext.lstrip(".")) \
                                 .replace("%(uploader)s", "").replace("%(id)s", "")
                safe_name = "".join(c for c in safe_tmpl if c not in r'<>:"/\|?*').strip()
                if safe_name and os.path.isfile(os.path.join(out_dir, safe_name)):
                    dupes.append(safe_name)
        if dupes:
            from tkinter import messagebox
            msg = _("dup_warn").format(files="\n".join(dupes[:5]))
            return messagebox.askyesno(_("dup_title"), msg)
        return True

    def _on_download_click(self):
        urls = self._get_urls()
        if not urls:
            self.progress_label.configure(text=_("err_no_url"), text_color=self.colors["error"])
            return

        out_dir = self.folder_var.get()
        if not os.path.isdir(out_dir):
            try: os.makedirs(out_dir, exist_ok=True)
            except Exception:
                self.progress_label.configure(text=_("err_invalid_folder"), text_color=self.colors["error"])
                return

        if not self._check_duplicates(urls):
            return

        self._download_queue = urls
        self.dl_btn.configure(state="disabled")
        self._process_queue()

    def _process_queue(self):
        if not self._download_queue:
            self.progress_bar.set(1)
            self.progress_label.configure(text="✅ All downloads completed!", text_color=self.colors["success"])
            self.dl_btn.configure(state="normal", text=_("btn_download"))
            return

        url = self._download_queue.pop(0)
        out_dir = self.folder_var.get()
        
        # Gather metadata only if it's the first and only item fetched
        meta = {}
        if self.tag_frame.winfo_ismapped() and self.mode_var.get() == "audio":
            meta["title"] = self.tag_title.get().strip()
            meta["artist"] = self.tag_artist.get().strip()

        self.progress_bar.set(0)
        self.progress_label.configure(text=f"⬇ Downloading: {url}", text_color=self.colors["text_secondary"])

        task = downloader.DownloadTask(
            url=url, mode=self.mode_var.get(), quality=self.quality_var.get(), output_dir=out_dir,
            progress_callback=lambda d: self.after(0, lambda: self._on_progress(d)),
            done_callback=lambda: self.after(0, self._process_queue), # Proceed to next
            error_callback=lambda e: self.after(0, lambda: self._on_error(e)),
            metadata=meta
        )
        # Track the active task so the app can cancel it on shutdown
        self.current_task = task
        self._download_thread = downloader.download(task)

    def _on_progress(self, data: dict):
        status = data.get("status", "")
        percent = data.get("percent", 0)
        self.progress_bar.set(percent / 100)

        if status == "processing":
            self.progress_label.configure(text=_("msg_processing"), text_color=self.colors["accent2"])
        else:
            self.progress_label.configure(text=f"⬇ {percent:.1f}%   🚀 {data.get('speed','—')}   ⏱ {data.get('eta','—')}", text_color=self.colors["text_primary"])

    def _on_error(self, error: str):
        self.progress_label.configure(text=f"❌ {error[:100]}", text_color=self.colors["error"])
        # Continue to next in queue after 2 seconds
        self.after(2000, self._process_queue)
