"""
Main Application Window — CustomTkinter with sidebar navigation (Modern & i18n)
"""
import customtkinter as ctk
from src.ui.downloader_tab import DownloaderTab
from src.ui.spotify_tab import SpotifyTab
from src.ui.lyrics_tab import LyricsTab
from src.ui.history_tab import HistoryTab
from src.ui.converter_tab import ConverterTab
from src.ui.settings_tab import SettingsTab
from src.utils.config_manager import load_config
from src.utils.i18n import _

# Modern Color palette
COLORS = {
    "bg_dark":       "#09090B", # Zinc 950
    "sidebar_bg":    "#18181B", # Zinc 900
    "card_bg":       "#121214", 
    "accent":        "#8B5CF6", # Vibrant Violet
    "accent_hover":  "#A78BFA",
    "accent2":       "#38BDF8", # Sky blue
    "success":       "#22C55E",
    "warning":       "#F59E0B",
    "error":         "#EF4444",
    "text_primary":  "#FAFAFA",
    "text_secondary":"#A1A1AA", # Zinc 400
    "border":        "#27272A", # Zinc 800
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

        # Set window icon if available
        try:
            self.iconbitmap("assets/icon.ico")
        except Exception:
            pass

        self._build_ui()
        self._select_tab(0)
        self._bind_shortcuts()

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
            (_("nav_settings"),   5, "settings"),
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

        # Version label at bottom
        ver_label = ctk.CTkLabel(self.sidebar, text=_("version_info"),
                                  font=ctk.CTkFont(size=11),
                                  text_color=COLORS["text_secondary"])
        ver_label.grid(row=10, column=0, padx=20, pady=24, sticky="sw")

        # Shortcuts hint
        shortcuts_label = ctk.CTkLabel(self.sidebar, text="Ctrl+D Download  •  Ctrl+1-6 Tabs",
                                       font=ctk.CTkFont(size=10),
                                       text_color=COLORS["border"])
        shortcuts_label.grid(row=11, column=0, padx=20, pady=(0, 16), sticky="sw")

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
            SettingsTab(self.content, colors=COLORS, refresh_callback=self._on_settings_saved),
        ]
        for tab in self._tabs:
            tab.grid(row=0, column=0, sticky="nsew")

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        # Ctrl+D = Go to Download tab
        self.bind("<Control-d>", lambda e: self._select_tab(0))
        # Ctrl+1-6 = Switch tabs
        for i in range(6):
            self.bind(f"<Control-Key-{i+1}>", lambda e, idx=i: self._select_tab(idx))
        # Ctrl+V = Paste into downloader textbox and fetch
        self.bind("<Control-v>", lambda e: self._quick_paste())

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

        self.title(_("app_name"))
        self._build_ui()
        self._select_tab(5)  # Stay on the Settings tab (now index 5)

    def _destroy_tabs(self):
        """Best-effort cleanup of tab instances before rebuilding the UI."""
        if not getattr(self, "_tabs", None):
            return
        for tab in self._tabs:
            try:
                # LyricsTab holds an AudioPlayer that wraps a VLC instance;
                # release it explicitly to free the libvlc handle.
                player = getattr(tab, "player", None)
                if player is not None and hasattr(player, "cleanup"):
                    try:
                        player.cleanup()
                    except Exception:
                        pass
                tab.destroy()
            except Exception:
                pass
