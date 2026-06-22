"""
Update Dialog — Modal pop-up shown when a new version is available.

Bilingual (Arabic + English) via i18n. Supports two modes:

  **Browse mode** (default on open)
    Shows release notes + three buttons: Skip / Later / Open in Browser.
    A new "Download & Install" button kicks off the download flow.

  **Download mode** (after clicking "Download & Install")
    Shows progress bar + status text while the installer downloads.
    On success: prompts the user to confirm app closure, then runs the
    installer and exits.
    On failure: shows error message + Retry button.
"""
import os
import sys
import re
import threading
import webbrowser
import customtkinter as ctk

from src.utils.i18n import _


_DIALOG_W = 660
_DIALOG_H = 620


class UpdateDialog(ctk.CTkToplevel):
    """
    Modal pop-up. Use from app.py:

        dlg = UpdateDialog(parent, info, colors)
        self.wait_window(dlg)
        action = dlg.result   # "update" | "later" | "skip"

    Or fire-and-forget if you don't need the result (the dialog handles
    download + install internally).
    """

    def __init__(self, parent, info: dict, colors: dict):
        super().__init__(parent)
        self.info = info
        self.colors = colors
        self.result = None            # one of: "update" | "later" | "skip"
        self._parent = parent
        self._installer_path = None   # set by download thread
        self._is_downloading = False  # guard against double-click
        self._cancel_download = False

        # Window setup
        self.title(_("upd_dialog_title"))
        self.configure(fg_color=colors["card_bg"])
        self.geometry(f"{_DIALOG_W}x{_DIALOG_H}")
        self.minsize(_DIALOG_W, _DIALOG_H)
        self.resizable(False, False)

        # Icon
        try:
            if os.path.exists("assets/icon.png"):
                import tkinter as tk
                self.iconphoto(True, tk.PhotoImage(file="assets/icon.png"))
            elif os.path.exists("assets/icon.ico"):
                self.iconbitmap("assets/icon.ico")
        except Exception:
            pass

        # Modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw - _DIALOG_W) // 2
            y = py + (ph - _DIALOG_H) // 2
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()

        self.bind("<Escape>", lambda e: self._on_later())

    # ── UI Builders ──────────────────────────────────────────────────

    def _build_ui(self):
        """Build the default browse-mode UI (release notes + action buttons)."""
        c = self.colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ─────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=c["sidebar_bg"], corner_radius=0, height=88)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=c["accent"], width=48,
        ).grid(row=0, column=0, padx=(28, 12), pady=20, sticky="w")

        ctk.CTkLabel(
            header, text=_("upd_title"),
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=c["text_primary"], anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(20, 0))

        subtitle_text = _("upd_subtitle",
                          current=self.info.get("current_version", ""),
                          latest=self.info.get("latest_version", ""))
        ctk.CTkLabel(
            header, text=subtitle_text,
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=c["text_secondary"], anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(2, 0))

        # ── Release name strip ─────────────────────────────────────
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.grid(row=1, column=0, sticky="ew", padx=28, pady=(20, 6))
        name_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            name_frame, text=_("upd_release_label"),
            font=ctk.CTkFont("Segoe UI", 12), text_color=c["text_secondary"],
        ).grid(row=0, column=0, sticky="w")

        release_name = self.info.get("release_name") or f"v{self.info.get('latest_version', '')}"
        ctk.CTkLabel(
            name_frame, text=release_name,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=c["accent"], anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        # ── Content area (release notes) ──────────────────────────
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.grid(row=2, column=0, sticky="nsew", padx=28, pady=(6, 16))
        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.grid_rowconfigure(0, weight=1)

        self._body = ctk.CTkTextbox(
            self._content_frame,
            fg_color=c["bg_dark"], border_color=c["border"],
            border_width=1, corner_radius=12,
            text_color=c["text_primary"],
            font=ctk.CTkFont("Consolas" if os.name == "nt" else "Monospace", 12),
            wrap="word",
        )
        self._body.grid(row=0, column=0, sticky="nsew")

        notes = self._render_notes(self.info.get("release_notes") or _("upd_no_notes"))
        self._body.insert("1.0", notes)
        self._body.configure(state="disabled")

        # ── Progress area (hidden until download starts) ──────────
        self._progress_frame = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        self._progress_frame.grid(row=0, column=0, sticky="nsew")
        self._progress_frame.grid_columnconfigure(0, weight=1)
        self._progress_frame.grid_rowconfigure(1, weight=0)

        self._status_lbl = ctk.CTkLabel(
            self._progress_frame, text="",
            font=ctk.CTkFont("Segoe UI", 13), text_color=c["text_secondary"],
        )
        self._status_lbl.grid(row=0, column=0, sticky="w", pady=(4, 6))

        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame, height=12, corner_radius=6,
            fg_color=c["border"], progress_color=c["accent"],
        )
        self._progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._progress_bar.set(0)

        # Error label (hidden by default)
        self._error_lbl = ctk.CTkLabel(
            self._progress_frame, text="",
            font=ctk.CTkFont("Segoe UI", 12), text_color=c["error"],
        )
        self._error_lbl.grid(row=2, column=0, sticky="w", pady=(4, 0))

        self._progress_frame.grid_remove()  # hidden initially

        # ── Footer / buttons ──────────────────────────────────────
        self._footer = ctk.CTkFrame(self, fg_color="transparent")
        self._footer.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 24))
        self._footer.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._build_browse_buttons()

    def _build_browse_buttons(self):
        """Show Skip / Later / Open in Browser / Download & Install."""
        c = self.colors
        self._clear_footer()

        ctk.CTkButton(
            self._footer, text=_("upd_btn_skip"),
            height=46, corner_radius=12,
            fg_color=c["border"], hover_color=c["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._on_skip,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            self._footer, text=_("upd_btn_later"),
            height=46, corner_radius=12,
            fg_color=c["border"], hover_color=c["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._on_later,
        ).grid(row=0, column=1, sticky="ew", padx=6)

        ctk.CTkButton(
            self._footer, text=_("upd_btn_update"),
            height=46, corner_radius=12,
            fg_color=c["border"], hover_color=c["accent_hover"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._on_open_browser,
        ).grid(row=0, column=2, sticky="ew", padx=6)

        ctk.CTkButton(
            self._footer, text=_("upd_btn_dl_install"),
            height=46, corner_radius=12,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=c.get("sidebar_text", "#fff"),
            command=self._start_download,
        ).grid(row=0, column=3, sticky="ew", padx=(6, 0))

    def _build_download_buttons(self):
        """Show Cancel / (empty) / (empty) / (empty) during download."""
        c = self.colors
        self._clear_footer()

        ctk.CTkButton(
            self._footer, text=_("upd_btn_later"),  # reuse "Cancel" semantics
            height=46, corner_radius=12,
            fg_color=c["border"], hover_color=c["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._on_cancel_download,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

    def _build_error_buttons(self):
        """Show Retry + Cancel buttons."""
        c = self.colors
        self._clear_footer()

        ctk.CTkButton(
            self._footer, text=_("upd_dl_retry"),
            height=46, corner_radius=12,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            command=self._start_download,
        ).grid(row=0, column=2, columnspan=1, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            self._footer, text=_("upd_dl_btn_no"),
            height=46, corner_radius=12,
            fg_color=c["border"], hover_color=c["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._on_later,
        ).grid(row=0, column=3, sticky="ew", padx=(6, 0))

    def _clear_footer(self):
        for w in self._footer.winfo_children():
            w.destroy()

    # ── Download Flow ──────────────────────────────────────────────

    def _start_download(self):
        if self._is_downloading:
            return
        self._is_downloading = True
        self._cancel_download = False
        self._error_lbl.configure(text="")

        # Switch to progress view
        self._body.grid_remove()
        self._progress_frame.grid()
        self._build_download_buttons()

        self._status_lbl.configure(text=_("upd_dl_status_downloading",
                                           downloaded="0 B", total="..."))
        self._progress_bar.set(0)

        # Pick the first installer asset
        from src.core.updater import pick_asset_for_platform
        asset = pick_asset_for_platform(self.info)
        if not asset:
            self._on_dl_error(_("upd_dl_error", error="No installer asset found"))
            return

        def _worker():
            from src.core.update_dl import download_installer, verify_file
            path = download_installer(
                asset,
                on_progress=self._on_dl_progress,
                on_error=lambda msg: self.after(0, lambda: self._on_dl_error(msg)),
            )
            if path and not self._cancel_download:
                self.after(0, lambda: self._on_dl_done(path))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_dl_progress(self, downloaded: int, total: int):
        if self._cancel_download:
            return
        fraction = downloaded / max(total, 1)
        self._progress_bar.set(fraction)

        # Format sizes
        for v, unit in [(total, ""), (total, "")]:
            break
        dl_str = _format_bytes(downloaded)
        total_str = _format_bytes(total) if total else "..."
        self._status_lbl.configure(
            text=_("upd_dl_status_downloading", downloaded=dl_str, total=total_str)
        )

    def _on_dl_done(self, path: str):
        self._is_downloading = False
        self._progress_bar.set(1)
        self._status_lbl.configure(text=_("upd_dl_status_verifying"))

        # Verify
        from src.core.update_dl import verify_file
        if not verify_file(path):
            self._on_dl_error(_("upd_dl_error", error="Verification failed"))
            return

        # Confirm close with user
        self._status_lbl.configure(text=_("upd_dl_status_running"))

        confirm = ctk.CTkInputDialog(
            title=_("upd_dl_confirm_title"),
            text=_("upd_dl_confirm_close"),
        )
        # CustomTkinter's InputDialog doesn't let us customise buttons
        # well, so we use a simple Yes/No via a temporary toplevel.
        self._show_confirm_dialog(path)

    def _show_confirm_dialog(self, installer_path: str):
        """Show a Yes/No dialog. On Yes, run installer and exit."""
        c = self.colors

        win = ctk.CTkToplevel(self)
        win.title(_("upd_dl_confirm_title"))
        win.configure(fg_color=c["card_bg"])
        win.geometry("480x200")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        # Center
        win.update_idletasks()
        try:
            px = self.winfo_rootx()
            py = self.winfo_rooty()
            pw = self.winfo_width()
            ph = self.winfo_height()
            x = px + (pw - 480) // 2
            y = py + (ph - 200) // 2
            win.geometry(f"+{x}+{y}")
        except Exception:
            pass

        ctk.CTkLabel(
            win, text=_("upd_dl_confirm_close"),
            font=ctk.CTkFont("Segoe UI", 14),
            text_color=c["text_primary"], wraplength=440, justify="center",
        ).pack(expand=True, padx=24, pady=24)

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=(0, 24))

        ctk.CTkButton(
            btn_frame, text=_("upd_dl_btn_no"),
            width=160, height=46, corner_radius=12,
            fg_color=c["border"], hover_color=c["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 14),
            command=lambda: (win.destroy(), self._on_later()),
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text=_("upd_dl_btn_yes"),
            width=160, height=46, corner_radius=12,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            command=lambda: (win.destroy(), self._do_install(installer_path)),
        ).pack(side="left", padx=8)

        win.protocol("WM_DELETE_WINDOW", lambda: (win.destroy(), self._on_later()))

    def _do_install(self, installer_path: str):
        """Run the installer and exit the app."""
        from src.core.update_dl import run_installer_and_exit
        run_installer_and_exit(installer_path, silent=True)

    def _on_dl_error(self, msg: str):
        self._is_downloading = False
        self._error_lbl.configure(text=msg)
        self._status_lbl.configure(text="")
        self._build_error_buttons()

    def _on_cancel_download(self):
        self._cancel_download = True
        self._is_downloading = False
        self._on_later()

    # ── Button actions ─────────────────────────────────────────────────

    def _on_open_browser(self):
        self.result = "update"
        url = self.info.get("html_url") or ""
        if url:
            try:
                threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
            except Exception:
                pass
        self._close()

    def _on_later(self):
        self.result = "later"
        self._close()

    def _on_skip(self):
        self.result = "skip"
        self._close()

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    # ── Notes rendering ────────────────────────────────────────────────

    @staticmethod
    def _render_notes(text: str) -> str:
        if not text:
            return ""
        out = []
        for line in text.splitlines():
            stripped = line.rstrip()
            if not stripped:
                out.append("")
                continue
            stripped = re.sub(r"^#{1,6}\s+", "", stripped)
            stripped = re.sub(r"^[\-\*]\s+", "• ", stripped)
            stripped = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            stripped = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", stripped)
            stripped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", stripped)
            stripped = re.sub(r"`([^`]+)`", r"\1", stripped)
            out.append(stripped)
        result = "\n".join(out)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()


def _format_bytes(n: int) -> str:
    """Format bytes to human-readable string (KB, MB)."""
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    elif n < 1024 * 1024 * 1024:
        return f"{n / (1024*1024):.1f} MB"
    return f"{n / (1024*1024*1024):.1f} GB"
