"""
Main Application Window — CustomTkinter with sidebar navigation (Modern & i18n)

v1.2.0 additions:
- Auto update-check on startup (GitHub Releases API), shows a bilingual
  dialog when a newer version is found. The dialog can be dismissed
  ("Later") or "skipped" (won't reappear for this version).
- A small red dot in the sidebar replaces the full pop-up on subsequent
  launches when the user has dismissed the dialog ("Later"). Clicking
  the dot re-opens the pop-up.
- Closing the main window hides the app to the system tray instead of
  quitting. Tray menu lets the user re-show the window, check for
  updates manually, or fully quit.
"""
import os
import io
import sys
import threading
import webbrowser
import tkinter as tk
import customtkinter as ctk

from src.ui.downloader_tab import DownloaderTab
from src.ui.spotify_tab import SpotifyTab
from src.ui.lyrics_tab import LyricsTab
from src.ui.converter_tab import ConverterTab
from src.ui.history_tab import HistoryTab
from src.ui.stats_tab import StatsTab
from src.ui.settings_tab import SettingsTab
from src.ui.update_dialog import UpdateDialog
from src.utils.config_manager import load_config, save_config
from src.utils.i18n import _
from src.core import updater

# Optional system-tray support
try:
    import pystray
    from PIL import Image as _PILImage
    _HAS_PYSTRAY = True
except Exception:
    _HAS_PYSTRAY = False


# Modern Color palette
COLORS = {
    "bg_dark":       "#09090B",  # Zinc 950
    "sidebar_bg":    "#18181B",  # Zinc 900
    "card_bg":       "#121214",
    "accent":        load_config().get("accent", "#8B5CF6"),  # Vibrant Violet
    "accent_hover":  "#A78BFA",
    "accent2":       "#38BDF8",  # Sky blue
    "success":       "#22C55E",
    "warning":       "#F59E0B",
    "error":         "#EF4444",
    "text_primary":  "#FAFAFA",
    "text_secondary":"#A1A1AA",  # Zinc 400
    "border":        "#27272A",  # Zinc 800
    "dot_red":       "#EF4444",
}


class MyDLPApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        config = load_config()
        ctk.set_appearance_mode(config.get("appearance_mode", "dark"))

        # Window setup
        self.title(_("app_name"))
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_dark"])

        # Set window icon if available. Try several candidate locations
        # because PyInstaller's onedir mode launches the exe with CWD =
        # the bundle's _internal folder, not the bundle root.
        icon_ico = self._find_asset("icon.ico")
        icon_png = self._find_asset("icon.png")
        # PNG first (Linux/macOS — tkinter can't read .ico there).
        # We use PIL because tk.PhotoImage doesn't handle RGBA PNGs.
        if icon_png:
            try:
                from PIL import Image, ImageTk
                pil_img = Image.open(icon_png).convert("RGBA")
                # Resize to a sensible taskbar size on each platform.
                ctk_img = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(64, 64),
                )
                self._icon_ref = ctk_img  # keep alive, otherwise GC'd
                # Apply via wm iconphoto so the titlebar + taskbar pick it up
                self.iconphoto(True, ctk_img._light_image)
            except Exception:
                pass
        if icon_ico:
            try:
                self.iconbitmap(icon_ico)
            except Exception:
                # Linux raises tkinter.TclError here even though we caught it
                # above. Safe to ignore.
                pass

        # ── Update + tray state ──────────────────────────────────────
        self._update_info = None           # latest release dict from updater
        self._update_dialog_open = False   # guard against multiple dialogs
        self._update_badge = None          # sidebar dot widget
        self._tray_icon = None             # pystray.Icon instance
        self._is_quitting = False          # True only when user picks Quit
        self.protocol("WM_DELETE_WINDOW", self._on_close_requested)
        self._clip_monitor = None

        self._build_ui()
        self._select_tab(0)
        self._bind_shortcuts()
        self._start_clip_monitor()

        # Check for updates after the UI is up (don't block startup)
        self.after(1500, self._check_for_updates_silent)
        # Set up the system tray (also non-blocking)
        self.after(200, self._init_tray)

    # ── Asset discovery ───────────────────────────────────────────────

    def _find_asset(self, filename: str) -> str | None:
        """
        Return the first existing path to `filename` from a list of candidate
        locations. Handles both source-tree and PyInstaller-frozen layouts.
        """
        candidates = [
            os.path.join("assets", filename),                                  # CWD
            os.path.join(os.path.dirname(sys.executable), "assets", filename),# EXE dir (onedir)
            os.path.join(os.path.dirname(sys.executable), filename),           # EXE dir (onefile)
        ]
        # PyInstaller frozen bundle exposes _MEIPASS for data files
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.insert(0, os.path.join(meipass, "assets", filename))
            candidates.insert(0, os.path.join(meipass, filename))
        # Project root in source mode
        try:
            here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            candidates.append(os.path.join(here, "assets", filename))
        except Exception:
            pass

        for path in candidates:
            try:
                if path and os.path.isfile(path):
                    return path
            except OSError:
                pass
        return None

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self):
        """Build sidebar + main content area."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=COLORS["sidebar_bg"],
                                    corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=24, pady=(32, 24), sticky="w")

        logo_icon = ctk.CTkLabel(logo_frame, text="⬇", font=ctk.CTkFont(size=28, weight="bold"),
                                  text_color=COLORS["accent"])
        logo_icon.grid(row=0, column=0, padx=(0, 12))

        logo_text = ctk.CTkLabel(logo_frame, text=_("app_name"),
                                  font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
                                  text_color=COLORS["text_primary"])
        logo_text.grid(row=0, column=1)

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"])
        sep.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Nav buttons
        nav_items = [
            (_("nav_downloader"), 0, "downloader"),
            (_("nav_spotify"),    1, "spotify"),
            (_("nav_lyrics"),     2, "lyrics"),
            (_("nav_converter"),  3, "converter"),
            (_("nav_history"),    4, "history"),
            (_("nav_stats"),      5, "stats"),
            (_("nav_settings"),   6, "settings"),
        ]

        self._nav_buttons = []
        for label, idx, _id in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label,
                font=ctk.CTkFont(family="Segoe UI", size=15),
                anchor="w", height=48,
                fg_color="transparent",
                hover_color=COLORS["border"],
                text_color=COLORS["text_secondary"],
                corner_radius=12,
                command=lambda i=idx: self._select_tab(i),
            )
            btn.grid(row=2 + idx, column=0, padx=16, pady=4, sticky="ew")
            self._nav_buttons.append(btn)

        # Update badge (a small red dot, hidden by default). Sits at the
        # bottom of the sidebar. Clicking it re-opens the update dialog.
        self._update_badge = ctk.CTkButton(
            self.sidebar,
            text="● " + _("upd_badge_tooltip"),
            height=36, corner_radius=18,
            fg_color=COLORS["dot_red"],
            hover_color="#DC2626",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._on_update_badge_clicked,
        )
        # grid managed by _set_update_badge_visible()

        # Footer block — small text at the very bottom of the sidebar.
        # Three lines:
        #   line 1: project + version + tagline
        #   line 2: keyboard shortcuts
        #   line 3: author + GitHub URL
        # We use a vertical frame with subtle dividers so the footer
        # reads as a single visual unit instead of three floating labels.
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.grid(row=10, column=0, padx=20, pady=(16, 16), sticky="sew")
        footer.grid_columnconfigure(0, weight=1)

        version_text = updater._running_version()
        author_text = "by 0xjoyo"

        # Line 1 — project + version
        line1 = ctk.CTkLabel(
            footer,
            text=f"my-dlp  v{version_text}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        line1.grid(row=0, column=0, sticky="ew")

        # Line 2 — keyboard shortcuts (compact, in dimmer color)
        line2 = ctk.CTkLabel(
            footer,
            text="Ctrl+D Download  •  Ctrl+1-6 Tabs  •  Ctrl+U Updates",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["border"],
            anchor="w",
        )
        line2.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        # Line 3 — author + GitHub
        line3 = ctk.CTkLabel(
            footer,
            text=f"open-source · {author_text} · github.com/0xjoyo/my-dlp",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["border"],
            anchor="w",
        )
        line3.grid(row=2, column=0, sticky="ew", pady=(2, 0))

        # ── Content area ─────────────────────────────────────────────
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Build all tabs (hidden by default)
        self._tabs = [
            DownloaderTab(self.content, colors=COLORS),
            SpotifyTab(self.content, colors=COLORS),
            LyricsTab(self.content, colors=COLORS),
            ConverterTab(self.content, colors=COLORS),
            HistoryTab(self.content, colors=COLORS),
            StatsTab(self.content, colors=COLORS),
            SettingsTab(self.content, colors=COLORS, refresh_callback=self._on_settings_saved),
        ]
        for tab in self._tabs:
            tab.grid(row=0, column=0, sticky="nsew")

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        # Ctrl+D = Go to Download tab
        self.bind("<Control-d>", lambda e: self._select_tab(0))
        # Ctrl+1-7 = Switch tabs
        for i in range(7):
            self.bind(f"<Control-Key-{i+1}>", lambda e, idx=i: self._select_tab(idx))
        # Ctrl+V = Paste into downloader textbox and fetch
        self.bind("<Control-v>", lambda e: self._quick_paste())
        # Ctrl+U = Check for updates manually
        self.bind("<Control-u>", lambda e: self._check_for_updates_silent(force=True))
        # Ctrl+/ = Show keyboard shortcuts
        self.bind("<Control-slash>", lambda e: self._show_keyboard_shortcuts())

    def _quick_paste(self):
        """Quick paste: go to downloader and paste clipboard."""
        self._select_tab(0)
        dl_tab = self._tabs[0]
        try:
            text = self.clipboard_get()
            if text and ("http" in text or "www." in text):
                current = dl_tab.url_textbox.get("1.0", "end-1c").strip()
                dl_tab.url_textbox.delete("1.0", "end")
                if current:
                    dl_tab.url_textbox.insert("1.0", f"{current}\n{text.strip()}")
                else:
                    dl_tab.url_textbox.insert("1.0", text.strip())
        except Exception:
            pass

    def _select_tab(self, index: int):
        """Show the selected tab and update sidebar nav."""
        for i, tab in enumerate(self._tabs):
            if i == index:
                tab.tkraise()

            btn = self._nav_buttons[i]
            if i == index:
                btn.configure(fg_color=COLORS["accent"], text_color=COLORS["text_primary"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])

    def _on_settings_saved(self):
        """Called when settings are saved — re-apply appearance and language."""
        config = load_config()
        mode = config.get("appearance_mode", "dark")
        ctk.set_appearance_mode(mode)

        # Tear down old UI carefully so background threads and child widgets
        # (notably VLC bindings inside LyricsTab) are released before we
        # rebuild. Otherwise repeated language toggles can leak resources.
        self._destroy_tabs()
        try:
            self.sidebar.destroy()
        except Exception:
            pass
        try:
            self.content.destroy()
        except Exception:
            pass
        self._tabs = None
        self._nav_buttons = None
        self._update_badge = None

        self.title(_("app_name"))
        self._build_ui()
        self._start_clip_monitor()
        self._select_tab(6)

    def _destroy_tabs(self):
        """Best-effort cleanup of tab instances before rebuilding the UI."""
        if not getattr(self, "_tabs", None):
            return
        for tab in self._tabs:
            try:
                player = getattr(tab, "player", None)
                if player is not None and hasattr(player, "cleanup"):
                    try:
                        player.cleanup()
                    except Exception:
                        pass
                tab.destroy()
            except Exception:
                pass

    # ── Clipboard monitor ──────────────────────────────────────────

    def _start_clip_monitor(self):
        """Start clipboard monitor if enabled in config."""
        from src.core.clipboard_monitor import ClipboardMonitor
        config = load_config()
        if not config.get("clipboard_monitor", False):
            self._clip_monitor = None
            return
        if self._clip_monitor is not None:
            return  # already running
        self._clip_monitor = ClipboardMonitor(
            root=self,
            on_url=self._on_clip_url,
        )
        self._clip_monitor.start()

    def _stop_clip_monitor(self):
        if self._clip_monitor:
            self._clip_monitor.stop()
            self._clip_monitor = None

    def _on_clip_url(self, url: str):
        """Called when clipboard monitor detects a YouTube URL."""
        from src.core.notifier import notify
        # Paste URL into downloader tab
        self._select_tab(0)
        dl_tab = self._tabs[0]
        try:
            current = dl_tab.url_textbox.get("1.0", "end-1c").strip()
            dl_tab.url_textbox.delete("1.0", "end")
            if current:
                dl_tab.url_textbox.insert("1.0", f"{current}\n{url}")
            else:
                dl_tab.url_textbox.insert("1.0", url)
        except Exception:
            pass
        notify("my-dlp", "YouTube URL detected — ready to download")

    # ── Update flow ──────────────────────────────────────────────────

    def _check_for_updates_silent(self, force: bool = False):
        """
        Run an update check in the background. If an update is found AND
        the user has not dismissed this version, show the pop-up. Otherwise
        just set the badge state.

        `force=True` is used by the manual "Check for updates" menu item
        and re-shows the dialog even if the version was previously dismissed.
        """
        def _on_result(info):
            # Marshal back to the UI thread
            self.after(0, lambda: self._on_update_check_done(info, force=force))

        def _on_error():
            # Network failure: silent. The manual check shows a small status.
            pass

        updater.check_for_update(callback=_on_result, error_callback=_on_error)

    def _on_update_check_done(self, info, force: bool = False):
        if not info or not info.get("is_update_available"):
            return

        self._update_info = info
        latest = info.get("latest_version", "")
        dismissed = updater.get_dismissed_version() or ""

        # Show the pop-up only if the user hasn't skipped this exact version
        # (or if the check was forced via the menu/shortcut).
        if force or latest != dismissed:
            self._show_update_dialog()
        else:
            # Just light up the badge
            self._set_update_badge_visible(True)

    def _show_update_dialog(self):
        if self._update_dialog_open or not self._update_info:
            return
        self._update_dialog_open = True
        try:
            dlg = UpdateDialog(self, self._update_info, COLORS)
            # After the dialog closes, the result decides what to do
            self.wait_window(dlg)
            result = dlg.result
        finally:
            self._update_dialog_open = False

        if result == "update":
            # User chose to update — open the release page in the browser.
            # The browser handles the actual install (Inno Setup runs the
            # installer; the portable zip is extracted over the existing
            # install). The running app is left running; the new version
            # takes effect on next launch.
            url = self._update_info.get("html_url", "")
            if url:
                threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
                updater.clear_dismissed_version()
                self._set_update_badge_visible(False)
        elif result == "skip":
            updater.set_dismissed_version(self._update_info.get("latest_version", ""))
            self._set_update_badge_visible(False)
        else:
            # "later" — leave the badge visible so the user can re-open it
            self._set_update_badge_visible(True)

    def _on_update_badge_clicked(self):
        # Re-fetch latest info and force the dialog open
        self._check_for_updates_silent(force=True)

    def _set_update_badge_visible(self, visible: bool):
        if not getattr(self, "_update_badge", None):
            return
        if visible:
            try:
                self._update_badge.configure(text="● " + _("upd_badge_tooltip"))
            except Exception:
                pass
            self._update_badge.grid(row=9, column=0, padx=16, pady=(4, 4), sticky="ew")
        else:
            self._update_badge.grid_forget()

    # ── System tray ──────────────────────────────────────────────────

    def _init_tray(self):
        """Create the system-tray icon (if pystray is available)."""
        if not _HAS_PYSTRAY:
            return

        icon_img = self._load_tray_icon()

        menu = pystray.Menu(
            pystray.MenuItem(_("tray_show"), self._tray_show, default=True),
            pystray.MenuItem(_("tray_hide"), self._tray_hide),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(_("tray_check_update"), lambda: self._check_for_updates_silent(force=True)),
            pystray.MenuItem(_("nav_stats"), lambda: self._select_tab(5)),
            pystray.MenuItem(_("nav_settings"), lambda: self._select_tab(6)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(_("tray_quit"), self._tray_quit),
        )

        def _setup(icon):
            icon.icon = icon_img
            icon.title = _("tray_running_in")

        self._tray_icon = pystray.Icon("my-dlp", icon=icon_img, title=_("tray_running_in"), menu=menu)
        threading.Thread(target=self._tray_icon.run, kwargs={"setup": _setup}, daemon=True).start()

    def _show_keyboard_shortcuts(self):
        """Show a popup with all keyboard shortcuts."""
        dlg = ctk.CTkToplevel(self)
        dlg.title(_("key_title"))
        dlg.geometry("420x320")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(fg_color=self.colors["bg_dark"])

        # Center on parent
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 420) // 2
        y = self.winfo_y() + (self.winfo_height() - 320) // 2
        dlg.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dlg, text=_("key_title"),
                     font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color=self.colors["accent"]
                     ).pack(padx=30, pady=(24, 16))

        ctk.CTkLabel(dlg, text=_("key_list"),
                     font=ctk.CTkFont("Segoe UI", 14),
                     text_color=self.colors["text_primary"],
                     justify="left", anchor="w"
                     ).pack(padx=40, pady=8)

        ctk.CTkButton(dlg, text="OK", width=120, height=36,
                      corner_radius=8, fg_color=self.colors["accent"],
                      hover_color=self.colors["accent_hover"],
                      command=dlg.destroy
                      ).pack(pady=20)

    def _load_tray_icon(self):
        """
        Load a tray icon (64×64 RGBA).  Tries:

          1. PNG from external assets (source tree or _MEIPASS)
          2. ICO from external assets
          3. Embedded base64-encoded PNG (always works — no file needed)

        Returns a PIL Image ready for pystray.
        """
        # ── Built-in fallback icon (64×64 purple "M" letter) ─────
        # This is embedded so the tray ALWAYS has an icon, even if
        # the assets directory is missing or inaccessible.
        _FALLBACK_B64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAA"
            "AsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAI"
            "3SURBVHgB7Zq9bhQxEMd3dpNcCBJSAgUFHQUFBQ0Vf3R0dDwBRUUFHQUF"
            "BQUFBR0FBRUFFBQUEFzKJ3J8e7azvh3P7d4pViT/ZMu78/PMn2c8awYAA"
            "AAAAAAAAAD4T/hkmvbZNP2ciflkmh6Z5vlCpmmaPjVNH0zTQ9P0yjQ9Mk"
            "3vTdO7GZlh0/Qr6IR9WhLa0+L3ImRqfXLn3zYgrdHZVz0B2ghgJYrgn3m"
            "I6ms/Pwrn56nT3jR9q9nRj6m+K9P0PpJX0YRPTdOjkv7oFKB1dM5VT4A"
            "2AllEmcr17pUBWAR3UgQI80i9PtsnsC8J8CLD+3IB+0hAS9oEY40AX3QE"
            "cgtYJQHyL8VqBPiUI8AS/r29vS2DweA6lfLc39+/NwqAq0SAdBzOBWiNg"
            "OsaAVhnBWiNAJcVAqzS0Nra2ppECHhujw8PD5s6nGpPwPn5+aHd398vl/"
            "Dtdnu5XC6/NsOjo6NqArvd7slkMtkzTfe7XC6f2Dp6/fr12+vr659V92"
            "9vbw+22+2TnZ2dzzrG2tvbbx8+fPgzHo+/lgjYbDY/9TkajX7cunXrYx"
            "HjdDp9NhqN3mjLw+GQ8X7//v3X69evv5v+ANgXfAIIZel2u9+n0+m7m5"
            "ubH0X8hZ2dnQ+bzebb5eXlUVG/rRYfK6B28U0TIIqC/S1wXRMgiq8TII"
            "qyE0CUmYAsMxNw3RKwEgEAAAAAAAAAAABG/AUJ+VpkMk5wDgAAAABJRU"
            "5ErkJggg=="
        )
        import base64
        _FALLBACK = base64.b64decode(_FALLBACK_B64)

        # ── Try to load from file ──────────────────────────────────
        for filename in ("icon.png", "icon.ico"):
            try:
                path = self._find_asset(filename)
                if path:
                    img = _PILImage.open(path).convert("RGBA")
                    return img.resize((64, 64), _PILImage.LANCZOS)
            except Exception:
                continue

        # ── Fallback to embedded PNG ────────────────────────────────
        try:
            return _PILImage.open(io.BytesIO(_FALLBACK)).convert("RGBA")
        except Exception:
            return _PILImage.new("RGBA", (64, 64), (139, 92, 246, 255))

    def _tray_show(self, icon=None, item=None):
        self.after(0, self._show_from_tray)

    def _show_from_tray(self):
        try:
            self.deiconify()
        except Exception:
            pass
        try:
            self.lift()
        except Exception:
            pass
        try:
            self.focus_force()
        except Exception:
            pass

    def _tray_hide(self, icon=None, item=None):
        self.after(0, self._hide_to_tray)

    def _hide_to_tray(self):
        try:
            self.withdraw()
        except Exception:
            pass

    def _tray_quit(self, icon=None, item=None):
        self.after(0, self._quit_app)

    def _on_close_requested(self):
        """Window close button -> hide to tray (not quit)."""
        if self._is_quitting:
            return
        # If we have a tray icon, hide. Otherwise really quit.
        if self._tray_icon is not None:
            self._hide_to_tray()
        else:
            self._quit_app()

    def _quit_app(self):
        """Fully tear down the app — stop tray, destroy widgets, exit."""
        self._is_quitting = True
        if self._tray_icon is not None:
            try:
                self._tray_icon.stop()
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass
        # Exit the process — pystray and tkinter both need this to fully release.
        import sys
        sys.exit(0)