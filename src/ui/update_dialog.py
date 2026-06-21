"""
Update Dialog — Modal pop-up shown when a new version is available.

Bilingual (Arabic + English) by virtue of the i18n strings passed in by the
caller. Renders the release name, current version, target version, and the
release notes (markdown-rendered as monospaced plain text — we deliberately
don't pull in a markdown library to keep the bundle small).

Actions:
    "update"   — caller hands the asset URL to the user's browser
    "later"    — pop-up dismissed; a subtle badge remains in the sidebar
    "skip"     — pop-up dismissed and the version is recorded as 'do not
                 show again' until the next release bumps it
"""
import os
import re
import threading
import webbrowser
import customtkinter as ctk

from src.utils.i18n import _


# Reasonable size for a modal dialog
_DIALOG_W = 640
_DIALOG_H = 560


class UpdateDialog(ctk.CTkToplevel):
    """
    Modal pop-up. Construct, then `wait_window()` from the caller if you
    want to block; otherwise the caller can grab `self.result` after the
    dialog is destroyed.
    """

    def __init__(self, parent, info: dict, colors: dict):
        super().__init__(parent)
        self.info = info
        self.colors = colors
        self.result = None  # one of: "update" | "later" | "skip"

        # Window setup
        self.title(_("upd_dialog_title"))
        self.configure(fg_color=colors["card_bg"])
        self.geometry(f"{_DIALOG_W}x{_DIALOG_H}")
        self.minsize(_DIALOG_W, _DIALOG_H)
        self.resizable(False, False)

        # Try to use the same icon as the main window. On Linux tkinter
        # only reads PNG/GIF, so prefer the PNG and fall back to ICO.
        try:
            if os.path.exists("assets/icon.png"):
                import tkinter as tk
                self.iconphoto(True, tk.PhotoImage(file="assets/icon.png"))
            elif os.path.exists("assets/icon.ico"):
                self.iconbitmap("assets/icon.ico")
        except Exception:
            pass

        # Make it modal — user can't interact with the main window
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

        # Close on Escape -> treat as "later"
        self.bind("<Escape>", lambda e: self._on_later())

    # ── UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        c = self.colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ─────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=c["sidebar_bg"], corner_radius=0, height=88)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        # Icon / glyph
        glyph = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=c["accent"],
            width=48,
        )
        glyph.grid(row=0, column=0, padx=(28, 12), pady=20, sticky="w")

        title = ctk.CTkLabel(
            header,
            text=_("upd_title"),
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=c["text_primary"],
            anchor="w",
        )
        title.grid(row=0, column=1, sticky="w", pady=(20, 0))

        subtitle_text = _("upd_subtitle",
                          current=self.info.get("current_version", ""),
                          latest=self.info.get("latest_version", ""))
        subtitle = ctk.CTkLabel(
            header,
            text=subtitle_text,
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=c["text_secondary"],
            anchor="w",
        )
        subtitle.grid(row=1, column=1, sticky="w", pady=(2, 0))

        # ── Release name strip ─────────────────────────────────────
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.grid(row=1, column=0, sticky="ew", padx=28, pady=(20, 6))
        name_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            name_frame, text=_("upd_release_label"),
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=c["text_secondary"],
        ).grid(row=0, column=0, sticky="w")

        release_name = self.info.get("release_name") or f"v{self.info.get('latest_version', '')}"
        ctk.CTkLabel(
            name_frame, text=release_name,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=c["accent"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        # ── Release notes body ─────────────────────────────────────
        body = ctk.CTkTextbox(
            self,
            fg_color=c["bg_dark"],
            border_color=c["border"],
            border_width=1,
            corner_radius=12,
            text_color=c["text_primary"],
            font=ctk.CTkFont("Consolas" if os.name == "nt" else "Monospace", 12),
            wrap="word",
        )
        body.grid(row=2, column=0, sticky="nsew", padx=28, pady=(6, 16))

        # Render markdown-ish text: strip heading markers, list bullets,
        # bold/italic. We render as monospaced plain text to avoid pulling
        # in a markdown dependency.
        notes = self._render_notes(self.info.get("release_notes") or _("upd_no_notes"))
        body.insert("1.0", notes)
        body.configure(state="disabled")  # read-only

        # ── Footer / buttons ───────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 24))
        footer.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            footer, text=_("upd_btn_skip"),
            height=46, corner_radius=12,
            fg_color=c["border"], hover_color=c["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._on_skip,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            footer, text=_("upd_btn_later"),
            height=46, corner_radius=12,
            fg_color=c["border"], hover_color=c["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._on_later,
        ).grid(row=0, column=1, sticky="ew", padx=6)

        ctk.CTkButton(
            footer, text=_("upd_btn_update"),
            height=46, corner_radius=12,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            command=self._on_update,
        ).grid(row=0, column=2, sticky="ew", padx=(6, 0))

    # ── Notes rendering ────────────────────────────────────────────────

    @staticmethod
    def _render_notes(text: str) -> str:
        """
        Light markdown cleanup for the release notes. Removes the most
        common MD syntax that doesn't render well as plain text:
        - Leading '#', '##', '###' on lines (headers)
        - Leading '-', '*' (list bullets -> bullet glyph)
        - '**bold**' -> bold
        - '[text](url)' -> text (url)
        - Extra blank lines collapsed to one
        """
        if not text:
            return ""

        out = []
        for line in text.splitlines():
            stripped = line.rstrip()
            if not stripped:
                out.append("")
                continue
            # Headings
            stripped = re.sub(r"^#{1,6}\s+", "", stripped)
            # List bullets
            stripped = re.sub(r"^[\-\*]\s+", "• ", stripped)
            # Bold
            stripped = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            # Italic
            stripped = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", stripped)
            # Links: [text](url) -> text
            stripped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", stripped)
            # Inline code
            stripped = re.sub(r"`([^`]+)`", r"\1", stripped)
            out.append(stripped)

        # Collapse 3+ blank lines into 1
        result = "\n".join(out)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    # ── Button actions ─────────────────────────────────────────────────

    def _on_update(self):
        """User clicked 'Update'. Open the release page in their browser."""
        self.result = "update"
        url = self.info.get("html_url") or ""
        if url:
            try:
                # Open in a background thread so we never block tkinter
                threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
            except Exception:
                pass
        self._close()

    def _on_later(self):
        """User clicked 'Later'. Pop-up will reappear next launch."""
        self.result = "later"
        self._close()

    def _on_skip(self):
        """User clicked 'Skip this version'. Pop-up will not reappear for this version."""
        self.result = "skip"
        self._close()

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()