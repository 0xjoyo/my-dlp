"""
Lyrics Fetcher — Fetch synced/plain lyrics from LRCLIB and syncedlyrics
"""
import threading
import requests
from typing import Callable, Optional, Tuple

from src.utils.config_manager import load_config


LRCLIB_API = "https://lrclib.net/api"


def _fetch_from_lrclib(title: str, artist: str, duration: int = 0) -> Optional[str]:
    """
    Fetch synced LRC lyrics from LRCLIB.
    Returns LRC string or None.
    """
    try:
        params = {"track_name": title, "artist_name": artist}
        if duration:
            params["duration"] = duration
        resp = requests.get(f"{LRCLIB_API}/get", params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            synced = data.get("syncedLyrics") or data.get("plainLyrics")
            return synced
        # Try search fallback
        search_resp = requests.get(f"{LRCLIB_API}/search",
                                   params={"q": f"{title} {artist}"}, timeout=10)
        if search_resp.status_code == 200:
            results = search_resp.json()
            if results:
                best = results[0]
                return best.get("syncedLyrics") or best.get("plainLyrics")
    except Exception:
        pass
    return None


def _fetch_from_syncedlyrics(query: str) -> Optional[str]:
    """Fetch lyrics from syncedlyrics library (multi-provider)."""
    try:
        import syncedlyrics
        lrc = syncedlyrics.search(query, enhanced=False)
        return lrc
    except ImportError:
        pass
    except Exception:
        pass
    return None


def _fetch_plain_from_lrclib(title: str, artist: str) -> Optional[str]:
    """Fallback: fetch plain lyrics."""
    try:
        resp = requests.get(f"{LRCLIB_API}/search",
                            params={"q": f"{title} {artist}"}, timeout=10)
        if resp.status_code == 200:
            results = resp.json()
            for r in results:
                plain = r.get("plainLyrics")
                if plain:
                    return plain
    except Exception:
        pass
    return None


def fetch_lyrics(title: str, artist: str, duration: int = 0,
                 callback: Callable = None, error_callback: Callable = None):
    """
    Fetch lyrics in background thread.
    callback receives (lrc_content: str, is_synced: bool)
    Tries: LRCLIB synced → syncedlyrics → LRCLIB plain → error
    """
    def _run():
        try:
            provider = load_config().get("lyrics_provider", "lrclib")
            lrc = None
            is_synced = False

            if provider == "lrclib":
                lrc = _fetch_from_lrclib(title, artist, duration)
                if lrc and "[" in lrc and "]" in lrc and ":" in lrc:
                    is_synced = True
                elif not lrc:
                    # Fallback to syncedlyrics
                    lrc = _fetch_from_syncedlyrics(f"{title} {artist}")
                    if lrc:
                        is_synced = True

            elif provider == "syncedlyrics":
                lrc = _fetch_from_syncedlyrics(f"{title} {artist}")
                if lrc:
                    is_synced = True
                if not lrc:
                    lrc = _fetch_from_lrclib(title, artist, duration)
                    if lrc and "[" in lrc:
                        is_synced = True

            # Final fallback: plain text
            if not lrc:
                lrc = _fetch_plain_from_lrclib(title, artist)
                is_synced = False

            if lrc and callback:
                callback(lrc, is_synced)
            elif not lrc:
                if error_callback:
                    error_callback("لم يتم العثور على كلمات لهذه الأغنية.")

        except Exception as e:
            if error_callback:
                error_callback(str(e))

    threading.Thread(target=_run, daemon=True).start()


def save_lrc_file(lrc_content: str, filepath: str) -> bool:
    """Save LRC content to a .lrc file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(lrc_content)
        return True
    except IOError:
        return False


def save_plain_file(text: str, filepath: str) -> bool:
    """Save plain text lyrics to a .txt file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except IOError:
        return False
