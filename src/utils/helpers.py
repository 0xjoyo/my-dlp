"""
Helpers — General utility functions
"""
import re
import os
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(url.strip())
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def is_spotify_url(url: str) -> bool:
    """Check if URL is a Spotify URL."""
    return "open.spotify.com" in url or "spotify.com" in url


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube URL."""
    return any(d in url for d in ["youtube.com", "youtu.be", "music.youtube.com"])


def is_playlist_url(url: str) -> bool:
    """Check if URL is a playlist."""
    return "playlist" in url or "/album/" in url or "/collection/" in url


def format_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "0:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_views(count: int) -> str:
    """Format view count with K, M abbreviations."""
    if not count:
        return "—"
    if count >= 1_000_000_000:
        return f"{count/1_000_000_000:.1f}B"
    if count >= 1_000_000:
        return f"{count/1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count/1_000:.1f}K"
    return str(count)


# Reserved device names on Windows that would silently fail to create
# (e.g. "CON.txt" gets the same treatment as "CON").
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename on Windows/macOS/Linux.

    - Strips characters that are invalid on Windows (`\\ / : * ? " < > |`)
    - Strips null bytes
    - Replaces `..` (path traversal)
    - Strips leading/trailing whitespace and dots
    - Rejects reserved Windows device names (CON, PRN, ...)
    - Truncates overly long names (255 bytes is the Windows max)
    """
    if name is None:
        return ""
    s = str(name)

    # 1. Replace invalid characters
    invalid = r'\/:*?"<>|'
    for ch in invalid:
        s = s.replace(ch, "_")

    # 2. Strip null bytes and other control characters
    s = "".join(ch for ch in s if ch.isprintable() or ch == " ")

    # 3. Defang path-traversal sequences
    while ".." in s:
        s = s.replace("..", "_")

    # 4. Strip leading/trailing whitespace and dots (prevents ".foo",
    #    "foo.", and " " / "." only filenames on Windows)
    s = s.strip(" .")

    # 5. If the result is a reserved Windows device name, prefix it
    if s.upper() in _WINDOWS_RESERVED:
        s = "_" + s

    # 6. Truncate to a safe length (255 bytes is the Windows MAX_PATH limit
    #    for a single component; leave some headroom for the extension)
    if len(s.encode("utf-8")) > 200:
        s = s.encode("utf-8")[:200].decode("utf-8", errors="ignore")

    return s


def get_platform_name(url: str) -> str:
    """Return human-readable platform name from URL."""
    if is_spotify_url(url):
        return "Spotify"
    if is_youtube_url(url):
        return "YouTube"
    if "soundcloud.com" in url:
        return "SoundCloud"
    if "tiktok.com" in url:
        return "TikTok"
    if "twitter.com" in url or "x.com" in url:
        return "X (Twitter)"
    if "instagram.com" in url:
        return "Instagram"
    if "facebook.com" in url or "fb.watch" in url:
        return "Facebook"
    if "vimeo.com" in url:
        return "Vimeo"
    return "Unknown"


def ms_to_seconds(ms: int) -> float:
    """Convert milliseconds to seconds."""
    return ms / 1000.0


def seconds_to_ms(seconds: float) -> int:
    """Convert seconds to milliseconds."""
    return int(seconds * 1000)
