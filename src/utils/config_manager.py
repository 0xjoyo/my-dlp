"""
Config Manager — Read/Write settings to config.json
Stores the user config in %APPDATA%/my-dlp/config.json on Windows so it
survives reinstalls and works correctly when the app is frozen by PyInstaller
and installed under Program Files (where Program Files paths are read-only).
"""
import json
import os
import sys


def _get_config_dir() -> str:
    """
    Return the directory where the user-specific config.json lives.

    Resolution order:
      1. MY_DLP_CONFIG_DIR env var (useful for tests / portable mode)
      2. Windows: %APPDATA%/my-dlp
      3. macOS:   ~/Library/Application Support/my-dlp
      4. Linux:   $XDG_CONFIG_HOME/my-dlp or ~/.config/my-dlp
    """
    override = os.environ.get("MY_DLP_CONFIG_DIR")
    if override:
        return override

    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~/AppData/Roaming")
        path = os.path.join(base, "my-dlp")
    elif sys.platform == "darwin":
        path = os.path.expanduser("~/Library/Application Support/my-dlp")
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
        path = os.path.join(xdg, "my-dlp")

    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        # Fall back to user home if we cannot create the config dir
        path = os.path.expanduser("~")
    return path


CONFIG_PATH = os.path.join(_get_config_dir(), "config.json")

DEFAULTS = {
    "download_path": os.path.expanduser("~/Downloads"),
    "appearance_mode": "dark",
    "color_theme": "purple",
    "default_video_format": "mp4",
    "default_audio_format": "mp3",
    "default_video_quality": "1080p",
    "default_audio_quality": "192kbps",
    "ffmpeg_path": "",
    "spotify_client_id": "",
    "spotify_client_secret": "",
    "lyrics_provider": "lrclib",
    "embed_lyrics": True,
    "embed_thumbnail": True,
    "language": "en",
    "speed_limit": 0,
    "update_dismissed_version": "",
    # YouTube authentication — empty = no cookies
    "youtube_cookies_file": "",   # path to Netscape cookies.txt
    "youtube_cookies_browser": "",  # "chrome" / "firefox" / "edge" / "brave" / "opera" / "vivaldi" / ""
}


def load_config() -> dict:
    """Load config from file, filling in defaults for missing keys."""
    config = DEFAULTS.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    # Ensure download path exists
    if not config["download_path"]:
        config["download_path"] = os.path.expanduser("~/Downloads")
    return config


def save_config(config: dict) -> bool:
    """Save config to file. Returns True on success."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def get(key: str, default=None):
    """Get a single config value."""
    return load_config().get(key, default)


def set_value(key: str, value) -> bool:
    """Set a single config value and save."""
    config = load_config()
    config[key] = value
    return save_config(config)