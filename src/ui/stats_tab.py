"""
Statistics Tab — Show download stats and storage usage
"""
import os
import customtkinter as ctk

from src.utils.history_manager import load_history
from src.utils.i18n import _


class StatsTab(ctk.CTkFrame):
    def __init__(self, parent, colors: dict):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.colors = colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=self.colors["bg_dark"], corner_radius=0)
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        self.bind("<Visibility>", lambda e: self._refresh())

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=90)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        title = ctk.CTkLabel(header, text=_("nav_stats"),
                             font=ctk.CTkFont("Segoe UI", 24, "bold"),
                             text_color=self.colors["text_primary"])
        title.grid(row=0, column=0, padx=36, pady=(24, 0), sticky="w")
        ctk.CTkLabel(header, text=_("stats_subtitle"),
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=self.colors["text_secondary"]
                     ).grid(row=1, column=0, padx=36, pady=(4, 16), sticky="w")

    def _refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        history = load_history() or []
        self._show_stats(history)

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card_bg"], corner_radius=16,
                             border_width=1, border_color=self.colors["border"])
        frame.grid_columnconfigure(0, weight=1)
        if title:
            ctk.CTkLabel(frame, text=title,
                         font=ctk.CTkFont("Segoe UI", 15, "bold"),
                         text_color=self.colors["accent"]
                         ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 0))
        return frame

    def _stat_row(self, parent, row: int, label: str, value: str, color: str = None):
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont("Segoe UI", 14),
                     text_color=self.colors["text_secondary"]
                     ).grid(row=row, column=0, sticky="w", padx=24, pady=(8, 2))
        ctk.CTkLabel(parent, text=value,
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=color or self.colors["text_primary"]
                     ).grid(row=row, column=1, sticky="e", padx=24, pady=(8, 2))

    def _format_size(self, bytes_val: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} TB"

    def _show_stats(self, history: list):
        # ── Overview Card ──
        card = self._card(self.scroll, _("card_stats_overview"))
        card.grid(row=0, column=0, padx=36, pady=(32, 16), sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        total = len(history)
        videos = sum(1 for h in history if h.get("mode") == "video")
        audios = sum(1 for h in history if h.get("mode") == "audio")

        # Compute total file size
        total_size = 0
        for h in history:
            fp = h.get("path")
            if fp and os.path.isfile(fp):
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass

        self._stat_row(card, 1, _("stats_total"), str(total), self.colors["accent"])
        self._stat_row(card, 2, _("stats_videos"), str(videos))
        self._stat_row(card, 3, _("stats_audio"), str(audios))
        self._stat_row(card, 4, _("stats_storage"), self._format_size(total_size))

        if history:
            # ── Recent Downloads ──
            recent_card = self._card(self.scroll, _("card_stats_recent"))
            recent_card.grid(row=1, column=0, padx=36, pady=16, sticky="ew")
            recent_card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(recent_card, text=_("stats_date"),
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=self.colors["text_secondary"]
                         ).grid(row=1, column=0, sticky="w", padx=24, pady=(12, 4))
            ctk.CTkLabel(recent_card, text=_("stats_file"),
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=self.colors["text_secondary"]
                         ).grid(row=1, column=1, sticky="w", padx=24, pady=(12, 4))

            for i, item in enumerate(reversed(history[-5:])):
                title = item.get("title", "")
                date = item.get("date", "")
                ctk.CTkLabel(recent_card,
                             text=date[:10] if len(date) > 10 else date,
                             font=ctk.CTkFont("Segoe UI", 12),
                             text_color=self.colors["text_primary"]
                             ).grid(row=i + 2, column=0, sticky="w", padx=24, pady=2)
                ctk.CTkLabel(recent_card,
                             text=title[:60],
                             font=ctk.CTkFont("Segoe UI", 12),
                             text_color=self.colors["text_primary"]
                             ).grid(row=i + 2, column=1, sticky="w", padx=24, pady=2)

        if not history:
            ctk.CTkLabel(self.scroll, text=_("hist_empty"),
                         font=ctk.CTkFont("Segoe UI", 16),
                         text_color=self.colors["text_secondary"]
                         ).grid(row=2, column=0, pady=50)
