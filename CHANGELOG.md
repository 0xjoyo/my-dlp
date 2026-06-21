# Changelog

All notable changes to my-dlp are documented in this file.

## [1.2.1] - 2026-06-21

### Fixed
- **Program icon not showing in the titlebar or taskbar.** The previous icon setup only worked when the assets/ folder was in the current working directory; under PyInstaller's onedir mode the working directory is the EXE folder, not the project root, so `iconbitmap("assets/icon.ico")` silently failed. `app.py` now has a `_find_asset()` helper that probes a list of candidate locations (CWD, EXE dir, `sys._MEIPASS`, project root). Both the PNG and the ICO are applied — `iconphoto()` for the titlebar/taskbar via `CTkImage`, and `iconbitmap()` as a fallback for Windows.
- **`assets/icon.ico` rebuilt as a multi-size ICO.** It now contains 16, 32, 48, 64, 128 and 256 pixel frames instead of only 32 and 64, so the taskbar icon is crisp at every DPI scale.
- **`_protocol` typo in the close-window handler.** Replaced with `protocol()` so the window-close → hide-to-tray wiring actually fires.

### Added
- **Desktop shortcut for portable users.** `setup.iss` now creates a `my-dlp` icon on the user's desktop **unconditionally** on every install (was previously gated behind an unchecked task the user had to opt into). For portable users, the zip ships with a `create_shortcut.py` that builds the same `.lnk` (Windows) or `.desktop` (Linux/macOS) using PowerShell COM or a freedesktop entry respectively.
- **Sidebar footer with version + author.** The two floating labels at the bottom of the sidebar (`v1.2.0 — powered by yt-dlp` and the shortcuts hint) were replaced with a single 3-line footer that reads:
  - line 1 — `my-dlp  v<version>` (bold, dim)
  - line 2 — `Ctrl+D Download  •  Ctrl+1-6 Tabs  •  Ctrl+U Updates`
  - line 3 — `open-source · by 0xjoyo · github.com/0xjoyo/my-dlp`

  The version is read live from the `VERSION` file shipped at the bundle root (works in dev mode and in the frozen exe), so it always matches what the auto-updater sees.

## [1.2.0] - 2026-06-21

### Added
- **Auto-update notifications via GitHub Releases.** On startup the app calls `https://api.github.com/repos/0xjoyo/my-dlp/releases/latest`, parses the JSON, and compares the tag to the running version (read from the new `VERSION` file shipped at the bundle root). When an update is available, a bilingual modal dialog shows the release name, current vs. latest version, and the release notes (with light Markdown cleanup so headings/bullets render as plain text). Three actions: **Update Now** (opens the release page in the user's browser so they can run the new installer or extract the new zip — never touches files in the user's currently-running install), **Later** (dismisses the pop-up but leaves a red badge in the sidebar so it can be re-opened next session), and **Skip this version** (records the version in `config.json` so it never re-appears until a newer version is published).
- **Sidebar update badge.** A red dot labeled "● Update available" appears in the sidebar when an update has been dismissed with **Later**. Clicking it re-opens the dialog manually. `Ctrl+U` is also bound as a keyboard shortcut for a manual check.
- **System tray integration.** Closing the main window (the X button) now hides the app to the system tray instead of quitting. A tray icon with a context menu lets the user show / hide the window, manually check for updates, jump to Settings, or fully quit. The tray runs on its own daemon thread so it never blocks the tkinter event loop, and gracefully falls back to "really quit on close" if `pystray` is not installed. Tray strings are localized.
- **Cross-platform icon support.** The build now extracts a 256x256 PNG (`assets/icon.png`) from the existing `.ico` so Linux/macOS builds (where tkinter doesn't read .ico) can set a window icon via `iconphoto`. Both `app.py` and `update_dialog.py` try PNG first and fall back to ICO.
- **Linux-friendly VLC init.** `audio_player.AudioPlayer` now picks the right `vlc.Instance()` flags per platform: `--no-xlib` on Windows only; on Linux/macOS it relies on the platform-native VLC bindings.
- **Project metadata.** New `VERSION` file (single source of truth for the version, read by the updater at runtime), new `docs/` folder placeholder for screenshots, new `LICENSE` is referenced from the README.
- **README overhaul.** Professional structure with table of contents, badges, Windows / Linux / macOS / from-source install instructions, full config-keys table, project-tree diagram, troubleshooting section, and an explicit AI-assisted-design disclosure at the end.

### Improved
- **PyInstaller build script.** Added `--collect-all=pystray` and ships `VERSION` as `--add-data` so the updater works in the frozen exe.
- **Updater is lazy and silent.** The GitHub API call happens 1.5 s after startup, on a worker thread, with no UI impact. Network failures are silent (the manual check via `Ctrl+U` or the tray menu still works when the user has connectivity again).

## [1.1.0] - 2026-06-21

### Fixed
- **Audio metadata & cover art missing after download:** `FFmpegMetadata` was only added when the user toggled "embed lyrics" in settings, so most downloads had no tags at all, and `EmbedThumbnail` was only run when metadata was enabled too. The postprocessor pipeline was also misordered, so even when the cover was embedded it landed in a file that had no title/artist tags. The new pipeline always writes tags from yt-dlp's parsed info (uploader→artist, release_date→year, album, track number) and runs `FFmpegMetadata` BEFORE `EmbedThumbnail`, so the cover art is embedded into a properly-tagged file. A second `_apply_metadata_tags()` pass rewrites the tags cleanly using `mutagen` for MP3/ID3, M4A/MP4, FLAC, and WAV. Added `convert_thumbnail=jpg` so the embedded cover is universally readable, and added `_cleanup_thumb_sidecar()` to remove the leftover `.jpg/.webp` file that `EmbedThumbnail` left in the downloads folder.
- **Karaoke player crash:** `lyrics_tab.py` was calling `lrc_parser.parse_lrc()` as if it returned a single value, while the function actually returned `(lines, metadata)`. The karaoke-style sync display is now functional again.
- **Spotify tab crash:** `spotify_tab.py` was calling a non-existent `spotify_search.search_spotify()` function. Now correctly calls `search_by_name()` (which works against YouTube Music without requiring Spotify API keys). Spotify result rows now show real track thumbnails and durations.
- **Config & history files were silently read-only after install:** the app was writing `config.json` / `history.json` next to the project root, which is read-only under `Program Files`. Both files now live under `%APPDATA%/my-dlp/` (with a cross-platform fallback for macOS/Linux) so user settings and history survive reinstalls.
- **Playlist URL detection:** the URL-based heuristic that toggles the `%(playlist_index)s - %(title)s` template was too coarse and could misfire on URLs that merely contained the word "playlist". Replaced with a dedicated `_is_playlist_url()` helper that checks for `list=`, `/playlist`, `/album/`, and SoundCloud `/sets/`.
- **Playlist thumbnails:** when yt-dlp is invoked with `extract_flat=in_playlist`, individual entries have no `thumbnail` key but a `thumbnails` list. The info fetcher now picks the last (highest resolution) thumbnail from that list.
- **Sync lyrics parser:** `[00:12.50]` was the only pattern recognised, which silently dropped lyrics from long mixes and live recordings. Now supports both standard `[mm:ss.xx]` and extended `[hh:mm:ss.xx]` LRC formats, and a pre-flight `has_lrc_timestamps()` check uses a proper regex instead of a substring check.
- **VLC handle leak on language/theme switch:** `_on_settings_saved()` in `app.py` was destroying and rebuilding the sidebar/content frames without releasing the `AudioPlayer` (libvlc) instance held by `LyricsTab`. Each toggle could leak a VLC binding. Added a `_destroy_tabs()` helper that calls `player.cleanup()` before destruction.
- **Settings tab:** dropped the `_(...) if _(...) != ... else "Maintenance"` dead branch — the key was already present in the i18n table.

### Improved
- **PyInstaller build script:** added `--collect-all` for `customtkinter`, `yt_dlp`, `ytmusicapi`, `spotipy`, `syncedlyrics`, `thefuzz`, `python_Levenshtein`, `mutagen`, and `PIL`. Without these, the frozen executable crashed on first launch with `ModuleNotFoundError` for various sub-modules.

## [1.0.0] - 2026-06-20
- Initial public release.