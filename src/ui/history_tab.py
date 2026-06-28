"""
History Tab — View and search previous downloads
"""
import os
import subprocess
import customtkinter as ctk

from src.utils.history_manager import load_history, clear_history
from src.utils.i18n import _


# Characters that Excel/LibreOffice treat as the start of a formula
# when they appear at the beginning of a cell. We prepend a single quote
# so the value is rendered as text instead of being evaluated.
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_csv(value) -> str:
    """Neutralize CSV formula injection in user-controlled strings."""
    s = str(value) if value is not None else ""
    if s and s[0] in _CSV_FORMULA_PREFIXES:
        return "'" + s
    return s


class HistoryTab(ctk.CTkFrame):
    def __init__(self, parent, colors: dict):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.colors = colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._all_history = []  # full unfiltered list

        self._build_header()
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=self.colors["bg_dark"], corner_radius=0)
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        self.bind("<Visibility>", lambda e: self._refresh_history())
        self._refresh_history()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=130)
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
        subtitle.grid(row=1, column=0, padx=36, pady=(2, 8), sticky="w")

        # ── Search bar + filter row ──
        search_row = ctk.CTkFrame(header, fg_color="transparent")
        search_row.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 16))
        search_row.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._apply_filter())
        search_entry = ctk.CTkEntry(
            search_row, textvariable=self.search_var,
            placeholder_text=_("hist_search_ph"),
            height=38, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=self.colors["bg_dark"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        self.mode_filter_var = ctk.StringVar(value=_("hist_all"))
        mode_menu = ctk.CTkOptionMenu(
            search_row, variable=self.mode_filter_var,
            values=[_("hist_all"), _("opt_video"), _("opt_audio")],
            height=38, corner_radius=10,
            fg_color=self.colors["bg_dark"],
            button_color=self.colors["accent"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=lambda c: self._apply_filter(),
        )
        mode_menu.grid(row=0, column=1, padx=(0, 12))

        clear_btn = ctk.CTkButton(
            search_row, text=_("btn_clear_hist"), width=120, height=38,
            corner_radius=10, fg_color=self.colors["error"],
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self._on_clear,
        )
        clear_btn.grid(row=0, column=2)

        export_btn = ctk.CTkButton(search_row, text=_("btn_export_csv"), width=120, height=36,
                                   corner_radius=8, fg_color=self.colors["border"],
                                   hover_color=self.colors["accent"],
                                   command=self._export_csv)
        export_btn.grid(row=0, column=3, padx=(8, 0))

    def _apply_filter(self):
        """Filter displayed history by search text + mode."""
        query = self.search_var.get().strip().lower()
        mode_filter = self.mode_filter_var.get()

        filtered = []
        for item in self._all_history:
            title = (item.get("title") or "").lower()
            url = (item.get("url") or "").lower()
            # Text search
            if query and query not in title and query not in url:
                continue
            # Mode filter
            if mode_filter != _("hist_all"):
                item_mode = item.get("mode", "")
                if mode_filter == _("opt_video") and item_mode != "video":
                    continue
                if mode_filter == _("opt_audio") and item_mode != "audio":
                    continue
            filtered.append(item)

        self._render_items(filtered)

    def _refresh_history(self):
        self._all_history = load_history() or []
        # Reset filter when refreshing
        self.mode_filter_var.set(_("hist_all"))
        self.search_var.set("")
        self._apply_filter()

    def _render_items(self, items):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not items:
            lbl = ctk.CTkLabel(self.scroll, text=_("hist_empty"),
                               font=ctk.CTkFont("Segoe UI", 16),
                               text_color=self.colors["text_secondary"])
            lbl.grid(row=0, column=0, pady=50)
            return

        for i, item in enumerate(items):
            card = ctk.CTkFrame(self.scroll, fg_color=self.colors["card_bg"], corner_radius=16,
                                border_width=1, border_color=self.colors["border"])
            card.grid(row=i, column=0, padx=36, pady=(16 if i == 0 else 8, 8), sticky="ew")
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
        if not path:
            return
        # Resolve to absolute path to defend against path tricks
        try:
            path = os.path.abspath(path)
        except (OSError, ValueError):
            return
        if os.name == 'nt':
            if os.path.exists(path):
                if os.path.isfile(path):
                    # Use a list (no shell) and avoid shell metacharacters
                    # in the path. explorer.exe accepts /select,<path> as
                    # a single argument.
                    try:
                        subprocess.Popen(["explorer", f"/select,{path}"])
                    except (OSError, FileNotFoundError):
                        # Fall back to opening the parent folder
                        try:
                            os.startfile(os.path.dirname(path))
                        except OSError:
                            pass
                else:
                    try:
                        os.startfile(path)
                    except OSError:
                        pass
            else:
                dir_path = os.path.dirname(path)
                if dir_path and os.path.exists(dir_path):
                    try:
                        os.startfile(dir_path)
                    except OSError:
                        pass

    def _export_csv(self):
        """Export history to a CSV file in the Downloads folder."""
        import csv
        from pathlib import Path

        dest = Path.home() / "Downloads" / f"my-dlp_history_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(dest, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["title", "url", "path", "mode", "date"])
                for item in self._all_history:
                    w.writerow([
                        _sanitize_csv(item.get("title", "")),
                        _sanitize_csv(item.get("url", "")),
                        _sanitize_csv(item.get("path", "")),
                        _sanitize_csv(item.get("mode", "")),
                        _sanitize_csv(item.get("date", "")),
                    ])
            # Show a quick status message
            from tkinter import messagebox
            messagebox.showinfo(_("msg_export_done"), f"{dest}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))
