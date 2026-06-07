"""
Config Manager — Read/Write settings to config.json
"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.json")

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
