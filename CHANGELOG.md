# Changelog

All notable changes to my-dlp are documented in this file.

## [1.1.0] - 2026-06-21

### Fixed
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