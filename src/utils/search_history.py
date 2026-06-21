"""
search_history.py — Persistent Spotify search history.

Stores the last N search queries per-user in config.json under the key
`spotify_search_history` (a list of strings, newest first). The Spotify
tab reads this to render "recent searches" chips above the results.
"""
from typing import List

# We import the *module* (not specific functions) so any later
# importlib.reload() of config_manager is honoured here too. This
# matters for the test suite where the fixture swaps CONFIG_PATH
# between tests.
from src.utils import config_manager


MAX_ENTRIES = 10
_KEY = "spotify_search_history"


def get_history() -> List[str]:
    """Return the recent search list (newest first), max MAX_ENTRIES."""
    cfg = config_manager.load_config()
    history = cfg.get(_KEY) or []
    # Defensive: ensure it's a list of strings
    if not isinstance(history, list):
        return []
    return [str(x) for x in history if x][:MAX_ENTRIES]


def add_query(query: str) -> List[str]:
    """
    Record a new search query. Returns the updated history list.

    - Trims and skips empty strings.
    - Removes any existing duplicates (the new query takes its place
      at the top of the list).
    - Caps at MAX_ENTRIES.
    """
    q = (query or "").strip()
    if not q:
        return get_history()

    history = get_history()
    # Remove existing matches so the new one goes to the top
    history = [h for h in history if h.lower() != q.lower()]
    history.insert(0, q)
    history = history[:MAX_ENTRIES]

    # Persist via the module so a test that reloaded config_manager
    # is still picking up the correct CONFIG_PATH.
    cfg = config_manager.load_config()
    cfg[_KEY] = history
    config_manager.save_config(cfg)
    return history


def clear_history() -> bool:
    """Wipe the search history. Returns True on success."""
    return config_manager.set_value(_KEY, [])


def remove_query(query: str) -> List[str]:
    """Remove a single query from history. Returns the updated list."""
    q = (query or "").strip()
    if not q:
        return get_history()
    history = [h for h in get_history() if h.lower() != q.lower()]
    config_manager.set_value(_KEY, history)
    return history