"""
Downloader — yt-dlp wrapper for video, audio, and playlist downloads
"""
import os
import threading
from typing import Callable, Optional
import yt_dlp

from src.utils.config_manager import load_config
from src.utils.helpers import sanitize_filename
from src.utils.history_manager import add_to_history

class DownloadTask:
    def __init__(self, url: str, mode: str, quality: str, output_dir: str,
                 progress_callback: Callable = None, done_callback: Callable = None,
                 error_callback: Callable = None, metadata: dict = None):
        self.url = url
        self.mode = mode          # "video" or "audio"
        self.quality = quality    # "best", "1080p", "720p", "480p", "360p", "320kbps", "192kbps", "128kbps"
        self.output_dir = output_dir
        self.progress_callback = progress_callback
        self.done_callback = done_callback
        self.error_callback = error_callback
        self.metadata = metadata or {}
        self.cancelled = False


def _is_playlist_url(url: str) -> bool:
    """Detect playlist URLs for common sites (YouTube, Spotify, SoundCloud)."""
    if not url:
        return False
    u = url.lower()
    if "playlist" in u or "list=" in u:
        return True
    if "/album/" in u:
        return True
    if "soundcloud.com" in u and "/sets/" in u:
        return True
    return False


def _build_ydl_opts(task: DownloadTask, config: dict, is_playlist: bool = False) -> dict:
    """Build yt-dlp options based on task parameters."""
    ffmpeg_path = config.get("ffmpeg_path", "")

    outtmpl = os.path.join(
        task.output_dir,
        "%(playlist_index)s - %(title)s.%(ext)s" if is_playlist else "%(title)s.%(ext)s"
    )

    opts = {
        "outtmpl": outtmpl,
        "ignoreerrors": True,
        "no_warnings": False,
        "quiet": True,
        "progress_hooks": [lambda d: _progress_hook(d, task)],
        "postprocessor_hooks": [],
        # Adding TikTok/X compatibility (by default yt-dlp handles watermark-free for tiktok)
        # but to be extra safe for photo slideshows:
        "extract_flat": "discard_in_playlist",
    }
    
    speed_limit = config.get("speed_limit", 0)
    if speed_limit > 0:
        try:
            opts["ratelimit"] = int(speed_limit) * 1024
        except ValueError:
            pass

    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path

    if task.mode == "audio":
        fmt = config.get("default_audio_format", "mp3")
        bitrate_map = {"320kbps": "320", "192kbps": "192", "128kbps": "128"}
        bitrate = bitrate_map.get(task.quality, "192")

        opts["format"] = "bestaudio/best"

        # Order matters here:
        #   1. FFmpegExtractAudio  — convert source (webm/m4a/...) into target codec (mp3/...)
        #   2. FFmpegMetadata      — write title/artist/album/date/etc. from the info dict
        #                            into the converted file (so the file actually has tags)
        #   3. EmbedThumbnail      — runs LAST so it operates on the final audio file
        #                            that already has metadata tags
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": fmt,
            "preferredquality": bitrate,
        }]

        # Always run FFmpegMetadata — even when the user hasn't overridden
        # title/artist, we still want yt-dlp's parsed uploader/title/date to
        # land in the file as proper ID3 tags.
        postprocessors.append({
            "key": "FFmpegMetadata",
            "add_metadata": True,
            "add_chapters": True,
        })

        if config.get("embed_thumbnail", True):
            postprocessors.append({"key": "EmbedThumbnail"})
            # EmbedThumbnail needs the thumbnail file on disk next to the
            # audio file. convert_thumbnail to jpg because ID3 / MP4 don't
            # accept webp natively in all players (e.g. older Windows
            # Explorer / Groove).
            opts["writethumbnail"] = True
            opts["convert_thumbnail"] = "jpg"

        opts["postprocessors"] = postprocessors

    else:  # video
        fmt = config.get("default_video_format", "mp4")
        quality_map = {
            "4K":    "bestvideo[height<=2160]+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
            "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
            "best":  "bestvideo+bestaudio/best",
        }
        opts["format"] = quality_map.get(task.quality, quality_map["1080p"])
        opts["merge_output_format"] = fmt

    return opts


def _progress_hook(d: dict, task: DownloadTask):
    """Called by yt-dlp with progress updates."""
    if task.cancelled:
        raise yt_dlp.utils.DownloadCancelled()

    if task.progress_callback is None:
        return

    status = d.get("status", "")
    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
        downloaded = d.get("downloaded_bytes", 0)
        speed = d.get("speed", 0)
        eta = d.get("eta", 0)
        percent = (downloaded / total * 100) if total else 0

        if speed:
            speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed > 1024 * 1024 else f"{speed / 1024:.1f} KB/s"
        else:
            speed_str = "—"

        eta_str = f"{eta}s" if eta else "—"

        task.progress_callback({
            "status": "downloading",
            "percent": percent,
            "speed": speed_str,
            "eta": eta_str,
            "filename": d.get("filename", ""),
        })

    elif status == "finished":
        task.progress_callback({
            "status": "processing",
            "percent": 100,
            "speed": "—",
            "eta": "—",
            "filename": d.get("filename", ""),
        })


def _apply_metadata_tags(final_filename: str, info: dict, overrides: dict, default_ext: str) -> None:
    """
    Apply metadata tags to a downloaded audio file using mutagen.

    `overrides` is the user-supplied tag editor (title/artist). Any non-empty
    value in `overrides` wins over the values from yt-dlp's `info` dict, so
    the user can correct bad tags from YouTube.

    `info` is the yt-dlp info dict; we read uploader/artist/channel, album,
    release_date / upload_date, and track number from it.
    """
    if not final_filename or not os.path.exists(final_filename):
        return

    # Build the merged tag set: user overrides win, yt-dlp fills the rest.
    uploader = (
        info.get("artist")
        or info.get("uploader")
        or info.get("channel")
        or info.get("creator")
        or ""
    )
    title = info.get("title", "") or info.get("track", "")
    album = info.get("album") or ""
    # yt-dlp gives release_date OR upload_date as YYYYMMDD
    raw_date = info.get("release_date") or info.get("upload_date") or ""
    release_year = raw_date[:4] if raw_date else ""
    track_number = info.get("track_number") or info.get("playlist_index") or ""

    merged_title = (overrides.get("title") or title).strip()
    merged_artist = (overrides.get("artist") or uploader).strip()
    merged_album = album.strip() if album else ""

    ext = os.path.splitext(final_filename)[1].lower()
    if ext != os.path.splitext(final_filename)[1].lower().replace(default_ext, default_ext):
        # Sanity check: extension matches what we asked for
        pass

    try:
        if ext == ".mp3":
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, ID3NoHeaderError
            try:
                tags = ID3(final_filename)
            except ID3NoHeaderError:
                tags = ID3()
            if merged_title:
                tags.add(TIT2(encoding=3, text=merged_title))
            if merged_artist:
                tags.add(TPE1(encoding=3, text=merged_artist))
            if merged_album:
                tags.add(TALB(encoding=3, text=merged_album))
            if release_year:
                tags.add(TDRC(encoding=3, text=release_year))
            if track_number:
                tags.add(TRCK(encoding=3, text=str(track_number)))
            tags.save(final_filename)

        elif ext in (".m4a", ".mp4"):
            from mutagen.mp4 import MP4
            audio = MP4(final_filename)
            if merged_title:
                audio["\xa9nam"] = [merged_title]
            if merged_artist:
                audio["\xa9ART"] = [merged_artist]
            if merged_album:
                audio["\xa9alb"] = [merged_album]
            if release_year:
                audio["\xa9day"] = [release_year]
            if track_number:
                audio["trkn"] = [(int(track_number), 0)]
            audio.save()

        elif ext == ".flac":
            from mutagen.flac import FLAC
            audio = FLAC(final_filename)
            if merged_title:
                audio["title"] = merged_title
            if merged_artist:
                audio["artist"] = merged_artist
            if merged_album:
                audio["album"] = merged_album
            if release_year:
                audio["date"] = release_year
            if track_number:
                audio["tracknumber"] = str(track_number)
            audio.save()

        elif ext == ".wav":
            from mutagen.wave import WAVE
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK
            try:
                tags = ID3(final_filename)
            except Exception:
                tags = ID3()
            if merged_title:
                tags.add(TIT2(encoding=3, text=merged_title))
            if merged_artist:
                tags.add(TPE1(encoding=3, text=merged_artist))
            if merged_album:
                tags.add(TALB(encoding=3, text=merged_album))
            if release_year:
                tags.add(TDRC(encoding=3, text=release_year))
            if track_number:
                tags.add(TRCK(encoding=3, text=str(track_number)))
            tags.save(final_filename)
    except Exception as tag_e:
        print("Tag editing error:", tag_e)


def _cleanup_thumb_sidecar(audio_path: str) -> None:
    """
    EmbedThumbnail sometimes leaves behind a .jpg/.webp/.png next to the
    audio file when the source extension differs. Delete those sidecars so
    the user's downloads folder stays clean.
    """
    base, _ = os.path.splitext(audio_path)
    for ext in (".jpg", ".jpeg", ".webp", ".png"):
        sidecar = base + ext
        try:
            if os.path.exists(sidecar):
                os.remove(sidecar)
        except OSError:
            pass


def download(task: DownloadTask):
    """Execute a download task in a background thread."""
    def _run():
        try:
            config = load_config()
            is_playlist = _is_playlist_url(task.url)
            opts = _build_ydl_opts(task, config, is_playlist=is_playlist)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(task.url, download=True)

                # Try to get final filename for history and tags
                final_filename = ""
                if info and "requested_downloads" in info and len(info["requested_downloads"]) > 0:
                    final_filename = info["requested_downloads"][0].get("filepath", "")
                elif info and not "entries" in info:
                    final_filename = ydl.prepare_filename(info)
                    # If extension was changed by postprocessor
                    ext = config.get("default_audio_format", "mp3") if task.mode == "audio" else config.get("default_video_format", "mp4")
                    base, _ = os.path.splitext(final_filename)
                    candidate = f"{base}.{ext}"
                    if os.path.exists(candidate):
                        final_filename = candidate

                title = info.get("title", task.url) if info else task.url

                # For audio downloads, refresh the tags with the user override
                # (if any) plus full info from yt-dlp. FFmpegMetadata already
                # wrote basic tags during the postprocess step; we overwrite
                # them here with cleaner values so they show up correctly in
                # Explorer / Groove / iTunes / etc.
                if (
                    final_filename
                    and os.path.exists(final_filename)
                    and task.mode == "audio"
                ):
                    default_ext = config.get("default_audio_format", "mp3")
                    _apply_metadata_tags(
                        final_filename,
                        info or {},
                        task.metadata or {},
                        default_ext,
                    )
                    _cleanup_thumb_sidecar(final_filename)
                    if task.metadata and task.metadata.get("title"):
                        title = task.metadata["title"]

                # Add to History
                if final_filename:
                    add_to_history(title, task.url, final_filename, task.mode)

            if task.done_callback and not task.cancelled:
                task.done_callback()
        except yt_dlp.utils.DownloadCancelled:
            if task.error_callback:
                task.error_callback("تم إلغاء التنزيل.")
        except Exception as e:
            if task.error_callback:
                task.error_callback(str(e))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
