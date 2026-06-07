"""
Spotify Search — Search for tracks/playlists via Spotify API and match on YouTube Music
"""
import threading
from typing import Callable, Optional, List, Dict

from src.utils.config_manager import load_config
from src.utils.helpers import format_duration


def _get_spotify_client():
    """Create and return authenticated Spotify client."""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        config = load_config()
        client_id = config.get("spotify_client_id", "")
        client_secret = config.get("spotify_client_secret", "")
        if not client_id or not client_secret:
            return None
        auth = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        return spotipy.Spotify(auth_manager=auth)
    except ImportError:
        return None
    except Exception:
        return None


def _search_youtube_music(query: str, limit: int = 5) -> List[Dict]:
    """Search YouTube Music for a query, return top results."""
    try:
        from ytmusicapi import YTMusic
        yt = YTMusic()
        results = yt.search(query, filter="songs", limit=limit)
        items = []
        for r in results[:limit]:
            vid_id = r.get("videoId", "")
            if not vid_id:
                continue
            duration_s = 0
            if r.get("duration"):
                parts = r["duration"].split(":")
                try:
                    if len(parts) == 2:
                        duration_s = int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 3:
                        duration_s = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                except ValueError:
                    pass
            thumbnails = r.get("thumbnails", [])
            thumb = thumbnails[-1]["url"] if thumbnails else ""
            artists = r.get("artists", [])
            artist_name = ", ".join(a["name"] for a in artists) if artists else "Unknown"
            items.append({
                "title": r.get("title", "Unknown"),
                "artist": artist_name,
                "duration": format_duration(duration_s),
                "duration_raw": duration_s,
                "thumbnail": thumb,
                "youtube_url": f"https://www.youtube.com/watch?v={vid_id}",
                "video_id": vid_id,
            })
        return items
    except Exception:
        return []


def _fuzzy_rank(query: str, results: List[Dict]) -> List[Dict]:
    """Rank results by fuzzy similarity to query."""
    try:
        from thefuzz import fuzz
        for r in results:
            title_artist = f"{r['title']} {r['artist']}"
            r["_score"] = fuzz.token_sort_ratio(query.lower(), title_artist.lower())
        return sorted(results, key=lambda x: x["_score"], reverse=True)
    except ImportError:
        return results


def search_by_name(query: str, callback: Callable, error_callback: Callable = None, limit: int = 5):
    """
    Search for a track by name/artist on YouTube Music.
    callback receives List[Dict] of results.
    """
    def _run():
        try:
            results = _search_youtube_music(query, limit=limit * 2)
            results = _fuzzy_rank(query, results)
            callback(results[:limit])
        except Exception as e:
            if error_callback:
                error_callback(str(e))

    threading.Thread(target=_run, daemon=True).start()


def search_by_spotify_url(spotify_url: str, callback: Callable, error_callback: Callable = None):
    """
    Extract track/album/playlist info from Spotify URL,
    then find matches on YouTube Music.
    callback receives a dict with:
        - type: "track" | "album" | "playlist"
        - name: str
        - results: List[Dict] (YouTube matches)
        - tracks: List[Dict] (for album/playlist, list of tracks with YouTube matches)
    """
    def _run():
        try:
            sp = _get_spotify_client()
            if not sp:
                if error_callback:
                    error_callback("يرجى إدخال Spotify Client ID و Client Secret في الإعدادات أولاً.")
                return

            # Determine URL type
            if "/track/" in spotify_url:
                _handle_track(sp, spotify_url, callback, error_callback)
            elif "/album/" in spotify_url:
                _handle_album(sp, spotify_url, callback, error_callback)
            elif "/playlist/" in spotify_url:
                _handle_playlist(sp, spotify_url, callback, error_callback)
            else:
                if error_callback:
                    error_callback("رابط Spotify غير مدعوم. يجب أن يكون track أو album أو playlist.")

        except Exception as e:
            if error_callback:
                error_callback(str(e))

    threading.Thread(target=_run, daemon=True).start()


def _extract_id(url: str) -> str:
    """Extract Spotify resource ID from URL."""
    # https://open.spotify.com/track/ABC123?si=xxx  →  ABC123
    parts = url.split("?")[0].rstrip("/").split("/")
    return parts[-1]


def _handle_track(sp, url: str, callback: Callable, error_callback: Callable):
    track_id = _extract_id(url)
    track = sp.track(track_id)
    name = track["name"]
    artist = ", ".join(a["name"] for a in track["artists"])
    album = track["album"]["name"]
    query = f"{name} {artist}"
    results = _search_youtube_music(query, limit=5)
    results = _fuzzy_rank(query, results)
    callback({
        "type": "track",
        "name": name,
        "artist": artist,
        "album": album,
        "spotify_url": url,
        "results": results[:3],
    })


def _handle_album(sp, url: str, callback: Callable, error_callback: Callable):
    album_id = _extract_id(url)
    album = sp.album(album_id)
    album_name = album["name"]
    artist = ", ".join(a["name"] for a in album["artists"])
    tracks_raw = album["tracks"]["items"]
    tracks = []
    for t in tracks_raw:
        name = t["name"]
        query = f"{name} {artist}"
        yt_results = _search_youtube_music(query, limit=3)
        yt_results = _fuzzy_rank(query, yt_results)
        tracks.append({
            "name": name,
            "artist": artist,
            "spotify_url": t["external_urls"].get("spotify", ""),
            "yt_results": yt_results[:1],
        })
    callback({
        "type": "album",
        "name": album_name,
        "artist": artist,
        "spotify_url": url,
        "tracks": tracks,
    })


def _handle_playlist(sp, url: str, callback: Callable, error_callback: Callable):
    playlist_id = _extract_id(url)
    playlist = sp.playlist(playlist_id)
    pl_name = playlist["name"]
    items = playlist["tracks"]["items"]
    tracks = []
    for item in items:
        t = item.get("track")
        if not t:
            continue
        name = t["name"]
        artist = ", ".join(a["name"] for a in t["artists"])
        query = f"{name} {artist}"
        yt_results = _search_youtube_music(query, limit=3)
        yt_results = _fuzzy_rank(query, yt_results)
        tracks.append({
            "name": name,
            "artist": artist,
            "spotify_url": t["external_urls"].get("spotify", ""),
            "yt_results": yt_results[:1],
        })
    callback({
        "type": "playlist",
        "name": pl_name,
        "spotify_url": url,
        "tracks": tracks,
    })
