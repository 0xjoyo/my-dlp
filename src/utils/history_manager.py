"""
Download History Manager

Stored next to the user config (e.g. %APPDATA%/my-dlp/history.json) so the
history is preserved across reinstalls and works with the PyInstaller-frozen
build installed under Program Files.
"""
import json
import os
import datetime

from src.utils.config_manager import _get_config_dir

HISTORY_PATH = os.path.join(_get_config_dir(), "history.json")


def load_history() -> list:
    """Load download history from history.json."""
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history_list: list) -> bool:
    """Save download history to history.json."""
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def add_to_history(title: str, url: str, path: str, mode: str):
    """Add a new download record to the history."""
    history = load_history()

    # Remove if url already exists to push it to the top
    history = [item for item in history if item.get("url") != url]

    record = {
        "title": title,
        "url": url,
        "path": path,
        "mode": mode,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    history.insert(0, record)  # Add to top
    save_history(history)


def clear_history() -> bool:
    """Clear all download history."""
    return save_history([])