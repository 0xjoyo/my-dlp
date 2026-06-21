"""
Info Fetcher — Fetch video/playlist metadata and thumbnails using yt-dlp
"""
import threading
import io
import requests
from typing import Callable, Optional
import yt_dlp

from src.utils.helpers import format_duration, format_views


def fetch_info(url: str, callback: Callable, error_callback: Callable = None):
    """
    Fetch video/playlist info in background thread.
    callback receives a dict with video/playlist info.
    """
    def _run():
        try:
            opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": "in_playlist",  # fast playlist scan
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                raise ValueError("لم يتم العثور على معلومات.")

            # Determine if it's a playlist or single video
            is_playlist = info.get("_type") == "playlist" or "entries" in info

            if is_playlist:
                entries = info.get("entries", [])
                # Pick the best thumbnail: playlist thumb first, then first
                # entry's thumb that actually resolves, else empty string.
                playlist_thumb = info.get("thumbnail", "") or ""
                result = {
                    "type": "playlist",
                    "title": info.get("title", "Playlist"),
                    "uploader": info.get("uploader", info.get("channel", "Unknown")),
                    "count": len([e for e in entries if e]),
                    "thumbnail": playlist_thumb,
                    "entries": [
                        {
                            "title": e.get("title", "Unknown"),
                            "duration": format_duration(e.get("duration", 0)),
                            "url": e.get("url") or e.get("webpage_url", ""),
                            "thumbnail": e.get("thumbnails", [{}])[-1].get("url", "") if e.get("thumbnails") else "",
                        }
                        for e in entries if e
                    ],
                }
            else:
                thumbnails = info.get("thumbnails", [])
                # Pick best thumbnail (highest resolution)
                thumb_url = ""
                if thumbnails:
                    best = max(thumbnails, key=lambda t: (t.get("width", 0) or 0) * (t.get("height", 0) or 0), default=None)
                    thumb_url = best.get("url", "") if best else thumbnails[-1].get("url", "")
                if not thumb_url:
                    thumb_url = info.get("thumbnail", "")

                result = {
                    "type": "video",
                    "title": info.get("title", "Unknown"),
                    "uploader": info.get("uploader") or info.get("channel", "Unknown"),
                    "duration_raw": info.get("duration", 0),
                    "duration": format_duration(info.get("duration", 0)),
                    "view_count": format_views(info.get("view_count", 0)),
                    "like_count": format_views(info.get("like_count", 0)),
                    "upload_date": info.get("upload_date", ""),
                    "description": (info.get("description", "") or "")[:300],
                    "thumbnail": thumb_url,
                    "webpage_url": info.get("webpage_url", url),
                    "formats": _parse_formats(info.get("formats", [])),
                }

            callback(result)

        except Exception as e:
            if error_callback:
                error_callback(str(e))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def _parse_formats(formats: list) -> dict:
    """Parse available formats into video/audio quality options."""
    video_qualities = set()
    audio_qualities = set()

    for f in formats:
        if f.get("vcodec") != "none" and f.get("acodec") != "none":
            h = f.get("height")
            if h:
                if h >= 2160:
                    video_qualities.add("4K")
                elif h >= 1080:
                    video_qualities.add("1080p")
                elif h >= 720:
                    video_qualities.add("720p")
                elif h >= 480:
                    video_qualities.add("480p")
                elif h >= 360:
                    video_qualities.add("360p")
        elif f.get("vcodec") == "none" and f.get("acodec") != "none":
            abr = f.get("abr", 0) or 0
            if abr >= 256:
                audio_qualities.add("320kbps")
            elif abr >= 160:
                audio_qualities.add("192kbps")
            else:
                audio_qualities.add("128kbps")

    quality_order = ["4K", "1080p", "720p", "480p", "360p"]
    audio_order = ["320kbps", "192kbps", "128kbps"]

    return {
        "video": [q for q in quality_order if q in video_qualities] or ["1080p", "720p", "480p", "360p"],
        "audio": [q for q in audio_order if q in audio_qualities] or ["192kbps", "128kbps"],
    }


def fetch_thumbnail_bytes(url: str) -> Optional[bytes]:
    """Download thumbnail image bytes synchronously."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None
