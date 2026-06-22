# Changelog

All notable changes to my-dlp are documented in this file.

## [1.3.3] - 2026-06-22

### Added
- **[Download presets]** Quick-select buttons (MP3, HD, 4K, High Quality Audio)
  that switch mode/quality and auto-fetch the URL.
- **[Duplicate check]** Before downloading, warns if the output file already
  exists and asks whether to overwrite.
- **[Export history]** One-click CSV export of the download history to your
  Downloads folder.
- **[Keyboard shortcuts popup]** Press Ctrl+/ (or ⌘+/) to see all available
  shortcuts in a clean overlay.
- **[Tray icon]** Replaced fragile file-dependent icon loading with an embedded
  base64 fallback — the tray icon now always works, even if assets are missing.

### Fixed
- **[Update close]** `run_installer_and_exit()` now forcefully kills all
  sibling my-dlp.exe processes and uses `taskkill` on its own PID before
  `os._exit(0)`, ensuring the EXE is fully unlocked for the installer.
- **[Row shift]** Swapped download and quality formatting for better metadata
  consistency.

## [1.3.2] - 2026-06-22

### Added
- **[Stats tab]** Statistics page with total downloads count, video/audio
  breakdown, storage usage, and recent downloads list.
- **[History search]** Search/filter by title and mode (video/audio) in the
  download history tab.
- **[Desktop notification]** Native toast notification on Windows when a
  download completes.
- **[Filename template]** Customisable output filename template in Settings
  (%(title)s, %(uploader)s, %(id)s, %(ext)s).
- **[Tray icon fix]** System-tray icon now probes _MEIPASS paths correctly
  for frozen (PyInstaller) builds.

### Changed
- **Sidebar**: Statistics tab added between History and Settings (Ctrl+6).

## [1.3.1] - 2026-06-21

### Added
- **In-app download & install** for updates. The Update dialog now has a
  "Download & Install" button that downloads the installer, shows a progress
  bar, verifies the download, and prompts the user before closing the app.
- `src/core/update_dl.py` — download, verify (SHA-256 / size), and launch
  the Inno Setup installer with `/CLOSEAPPLICATIONS` so it safely replaces the
  running binary.
- **Progress bar + status label** in the update dialog during download.
- **Confirmation dialog** before closing the app for installation.
- i18n strings (ar + en) for the new download & install flow.

### Fixed
- Desktop shortcut icon now uses the embedded EXE icon (removed broken
  `IconFilename` from `setup.iss`).
- Portable `create_shortcut.py` now finds the icon in `_internal/assets/`
  (frozen build) as well as `assets/` (dev mode).
- `build_portable_zip.py` now includes `create_shortcut.py` in the zip.

## [1.3.0] - 2026-06-21

### Added
- **Drag & drop URLs** into the downloader. The new `src/utils/dnd.py` helper
  wraps `tkinterdnd2` so the user can drag a link from the browser straight
  onto the URL box. A small accent-colored hint label appears below the box
  when DnD is wired up. If `tkinterdnd2` isn't available (or the platform is
  Wayland) the app silently falls back to the existing paste shortcut.
- **Spotify search history chips.** Last 10 searches render as clickable
  chips above the results. Click to re-run; click the × to delete; the new
  `sp_clear_history` button wipes the list. Persists across launches in
  `config.json` under the `spotify_search_history` key.
- **Test suite.** 148 unit tests cover `lrc_parser`, `helpers`,
  `config_manager`, `history_manager`, `updater`, and `search_history`.
  13% overall coverage with 100% on the trickiest piece (the LRC regex).
  Run locally with `pytest` from the project root.
- **GitHub Actions CI** runs `pytest` on every push and PR against
  `main`, `feat/**`, and `fix/**` — Python 3.11 and 3.12, on
  both Ubuntu and Windows. The Linux job also installs `ffmpeg` and
  VLC so the audio postprocessor tests have everything they need.

### Changed
- `search_history` reads `config_manager` lazily so test fixtures that
  swap the config dir mid-test work correctly.
- `config_manager._get_config_dir()` now reads `MY_DLP_CONFIG_DIR` from
  the environment on every call (testable), and falls back to
  APPDATA / XDG_CONFIG_HOME correctly on Windows / macOS / Linux.
- `spotify_tab` now uses `search_by_name` (the public async API) instead
  of the long-removed `search_spotify`. Asynchronous thumbnail loading
  and a `_map_youtube_to_spotify_shape` helper turn YouTube Music
  results into the row layout the UI expects.

### Fixed
- The Spotify tab no longer crashes on platforms where `search_spotify`
  doesn't exist (it was renamed to `search_by_name` back in v1.1.0).
- The persistent config / history test no longer leaks files between
  test runs.

## [1.2.1] - 2026-06-21

### Fixed
- **Program icon not showing in the titlebar or taskbar.** The previous
  icon setup only worked when the CWD was the project root, which is
  rarely the case for installed programs. The new `_find_asset()` helper
  probes CWD, the EXE directory, PyInstaller's `_MEIPASS`, and the
  project root before giving up. The multi-size .ico is also rebuilt
  with 6 resolutions (16–256px) so it looks crisp at every DPI.
- **Desktop shortcut created automatically** by the Inno Setup installer
  (no longer an opt-in checkbox). The portable release now ships a
  `create_shortcut.py` helper so users of the zip can do the same.
- **Footer with project name, version, and author** added to the
  sidebar — three small lines that read like a polite byline.

## [1.2.0] - 2026-06-21

### Added
- **Auto-update notifications via GitHub Releases.** On startup the app
  calls `https://api.github.com/repos/0xjoyo/my-dlp/releases/latest`,
  compares the version, and shows a bilingual pop-up with the release
  notes if newer. "Update now" opens the browser to the download page,
  "Later" records the dismissal so the dot appears in the sidebar,
  "Skip" hides it for that version permanently.
- **Sidebar update badge** — a small red dot on the Settings tab when
  an update is available and the user dismissed the pop-up. Clicking
  the dot reopens the dialog.
- **System tray icon.** Closing the window minimises to the tray
  instead of quitting. Tray menu has Show / Hide / Check for Updates
  / Settings / Quit. The icon uses the same `.ico` as the titlebar.
- **Manual update check** via `Ctrl+U` or the Settings tab.
- **`pystray` dependency** added to `requirements.txt` (graceful
  fallback if not installed — window-close still quits normally).
- **Cross-platform polish:** `assets/icon.png` for the titlebar on
  Linux/macOS (Tkinter only reads .ico on Windows). VLC launch args
  are platform-aware.

## [1.1.0] - 2026-06-21

### Fixed
- **Karaoke player crash:** `lyrics_tab.py` was calling
  `lrc_parser.parse_lrc()` as if it returned a single value, while the
  function actually returned `(lines, metadata)`. Both halves of the
  tuple are now unpacked.
- **LRC parser regex mis-handled tracks longer than 1 hour.** The
  original regex only matched `[mm:ss.xx]`; some providers emit
  `[hh:mm:ss.xx]` for long DJ sets and podcasts. A second regex
  handles that format and the timestamps convert correctly (e.g.
  `[01:05:30.50]` becomes 3,930,500 ms).
- **`has_lrc_timestamps()`** added to `lrc_parser` so the UI can
  decide whether to render the karaoke view or fall back to plain
  text.
- **Spotify tab called a non-existent function `search_spotify`.** The
  real entry point is `search_by_name` (an async wrapper around
  YouTube Music). The UI now uses that path and includes a
  `_map_youtube_to_spotify_shape` helper plus async thumbnail
  loading.
- **`config.json` and `history.json` were saved next to the EXE**, so
  on installed builds under `Program Files` they were silently dropped
  (admin permissions required). Both now write to `%APPDATA%/my-dlp/`
  on Windows and the XDG-equivalent on Linux/macOS.
- **Playlist detection** in `downloader.py` is now done by a small
  `_is_playlist_url()` helper that matches both `?list=` query
  parameters and `/playlist` URL segments. Previously a playlist was
  only detected for `soundcloud.com/.../sets/...` URLs.
- **Playlist thumbnail fall-through.** `info_fetcher.py` now uses the
  playlist's own thumbnail when present, otherwise the first entry's
  thumbnail. Previously the playlist often came back with a generic
  grey cover.
- **Settings tab had a hack that hid a "maintenance" card** based on a
  `HIDE_FOR_PROD` constant. The hack is gone and the surrounding
  block is a straightforward i18n string lookup.
- **Memory leak in `app.py`**: changing the language rebuilt the
  audio player and the tabs but never freed the old Tk widgets. A
  `_destroy_tabs()` method now runs `audio_player.cleanup()` and
  destroys the tab frames before `_build_ui()` recreates them.
- **`build.py` was missing `--collect-all` flags** for VLC,
  spotipy, ytmusicapi, syncedlyrics, and thefuzz. The frozen EXE
  crashed on launch for users without those deps installed
  system-wide.

## [1.0.0] - 2026-06-21

### Added
- Initial public release of my-dlp.
- 6 tabs: Downloader, Spotify, Lyrics, Converter, History, Settings.
- Bilingual UI (Arabic + English).
- Audio + video downloads via yt-dlp.
- In-house LRC karaoke player with synchronized highlighting.
- Spotify search via YouTube Music fallback.
- Custom themes (dark / light).
- Windows installer (Inno Setup) and portable .zip.