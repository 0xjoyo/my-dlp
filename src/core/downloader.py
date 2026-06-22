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
from src.core.notifier import notify

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


def _build_ydl_opts(task: DownloadTask, config: dict) -> dict:
    """Build yt-dlp options based on task parameters."""
    ffmpeg_path = config.get("ffmpeg_path", "")

    outtmpl = os.path.join(task.output_dir, config.get("filename_template", "%(title)s.%(ext)s"))

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
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": fmt,
            "preferredquality": bitrate,
        }]
        if config.get("embed_thumbnail", True):
            opts["postprocessors"].append({"key": "EmbedThumbnail"})
            opts["writethumbnail"] = True
        if config.get("embed_lyrics", True):
            opts["postprocessors"].append({"key": "FFmpegMetadata", "add_metadata": True})

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


def download(task: DownloadTask):
    """Execute a download task in a background thread."""
    def _run():
        try:
            config = load_config()
            opts = _build_ydl_opts(task, config)
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
                    if os.path.exists(f"{base}.{ext}"):
                        final_filename = f"{base}.{ext}"

                title = info.get("title", task.url) if info else task.url
                
                # Apply custom metadata tags if requested and file exists
                if final_filename and os.path.exists(final_filename) and task.metadata and task.mode == "audio":
                    try:
                        import mutagen
                        from mutagen.easyid3 import EasyID3
                        from mutagen.mp4 import MP4
                        
                        ext = os.path.splitext(final_filename)[1].lower()
                        if ext == ".mp3":
                            try:
                                tags = EasyID3(final_filename)
                            except mutagen.id3.ID3NoHeaderError:
                                tags = mutagen.File(final_filename, easy=True)
                                tags.add_tags()
                            if task.metadata.get("title"): tags["title"] = task.metadata["title"]
                            if task.metadata.get("artist"): tags["artist"] = task.metadata["artist"]
                            tags.save()
                            title = task.metadata.get("title", title)
                        elif ext in [".m4a", ".mp4"]:
                            tags = MP4(final_filename)
                            if task.metadata.get("title"): tags["\xa9nam"] = task.metadata["title"]
                            if task.metadata.get("artist"): tags["\xa9ART"] = task.metadata["artist"]
                            tags.save()
                            title = task.metadata.get("title", title)
                    except Exception as tag_e:
                        print("Tag editing error:", tag_e)

                # Add to History
                if final_filename:
                    add_to_history(title, task.url, final_filename, task.mode)

                # Desktop notification
                notify(
                    title if task.mode == "video" else "🎵 Download complete",
                    f"{title[:80]}" if len(title) > 80 else title,
                )

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
