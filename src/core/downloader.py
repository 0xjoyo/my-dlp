"""
Downloader — yt-dlp wrapper for video, audio, and playlist downloads
"""
import os
import threading
import queue
from typing import Callable, Optional
import yt_dlp

from src.utils.config_manager import load_config
from src.utils.helpers import sanitize_filename


class DownloadTask:
    def __init__(self, url: str, mode: str, quality: str, output_dir: str,
                 progress_callback: Callable = None, done_callback: Callable = None,
                 error_callback: Callable = None):
        self.url = url
        self.mode = mode          # "video" or "audio"
        self.quality = quality    # "best", "1080p", "720p", "480p", "360p", "320kbps", "192kbps", "128kbps"
        self.output_dir = output_dir
        self.progress_callback = progress_callback
        self.done_callback = done_callback
        self.error_callback = error_callback
        self.cancelled = False


def _build_ydl_opts(task: DownloadTask, config: dict) -> dict:
    """Build yt-dlp options based on task parameters."""
    ffmpeg_path = config.get("ffmpeg_path", "")

    # Output template
    outtmpl = os.path.join(task.output_dir, "%(playlist_index)s - %(title)s.%(ext)s"
                           if "playlist" in task.url.lower() or "album" in task.url.lower()
                           else "%(title)s.%(ext)s")

    opts = {
        "outtmpl": outtmpl,
        "ignoreerrors": True,
        "no_warnings": False,
        "quiet": True,
        "progress_hooks": [lambda d: _progress_hook(d, task)],
        "postprocessor_hooks": [],
    }

    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path

    if task.mode == "audio":
        fmt = config.get("default_audio_format", "mp3")
        bitrate_map = {
            "320kbps": "320",
            "192kbps": "192",
            "128kbps": "128",
        }
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

        # Format speed
        if speed:
            if speed > 1024 * 1024:
                speed_str = f"{speed / 1024 / 1024:.1f} MB/s"
            else:
                speed_str = f"{speed / 1024:.1f} KB/s"
        else:
            speed_str = "—"

        # ETA
        if eta:
            eta_str = f"{eta}s"
        else:
            eta_str = "—"

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
                ydl.download([task.url])
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
