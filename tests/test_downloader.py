"""Tests for the downloader: options, post-processors, thumbnail/metadata embedding."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.downloader import _build_ydl_opts, DownloadTask


def make_task(mode="audio", quality="192kbps", output_dir="C:/tmp"):
    return DownloadTask(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        mode=mode,
        quality=quality,
        output_dir=output_dir,
    )


def make_config(**overrides):
    base = {
        "default_audio_format": "mp3",
        "default_video_format": "mp4",
        "embed_thumbnail": True,
        "embed_lyrics": True,
        "filename_template": "%(title)s.%(ext)s",
        "speed_limit": 0,
        "subtitle_download": False,
    }
    base.update(overrides)
    return base


# ── Audio: thumbnail + metadata embedded ────────────────────────────

def test_audio_includes_embed_thumbnail():
    opts = _build_ydl_opts(make_task(mode="audio"), make_config())
    pp_keys = [p.get("key") for p in opts.get("postprocessors", [])]
    assert "EmbedThumbnail" in pp_keys, f"Audio missing EmbedThumbnail: {pp_keys}"
    assert opts.get("writethumbnail") is True


def test_audio_includes_ffmpeg_metadata():
    opts = _build_ydl_opts(make_task(mode="audio"), make_config())
    pp_keys = [p.get("key") for p in opts.get("postprocessors", [])]
    assert "FFmpegMetadata" in pp_keys, f"Audio missing FFmpegMetadata: {pp_keys}"


def test_audio_disables_thumbnail_when_config_false():
    opts = _build_ydl_opts(make_task(mode="audio"), make_config(embed_thumbnail=False))
    pp_keys = [p.get("key") for p in opts.get("postprocessors", [])]
    assert "EmbedThumbnail" not in pp_keys


# ── Video: thumbnail + metadata embedded (this is the bug fix) ─────

def test_video_includes_embed_thumbnail():
    """Regression: video mode should also embed the thumbnail."""
    opts = _build_ydl_opts(make_task(mode="video"), make_config())
    pp_keys = [p.get("key") for p in opts.get("postprocessors", [])]
    assert "EmbedThumbnail" in pp_keys, f"Video missing EmbedThumbnail: {pp_keys}"
    assert opts.get("writethumbnail") is True


def test_video_includes_ffmpeg_metadata():
    """Regression: video mode should also embed metadata."""
    opts = _build_ydl_opts(make_task(mode="video"), make_config())
    pp_keys = [p.get("key") for p in opts.get("postprocessors", [])]
    assert "FFmpegMetadata" in pp_keys, f"Video missing FFmpegMetadata: {pp_keys}"


def test_video_format_is_merged():
    opts = _build_ydl_opts(make_task(mode="video", quality="1080p"), make_config())
    assert "bestvideo" in opts["format"]
    assert opts.get("merge_output_format") == "mp4"


def test_video_4k_format():
    opts = _build_ydl_opts(make_task(mode="video", quality="4K"), make_config())
    assert "height<=2160" in opts["format"]


# ── Subtitles only for video ─────────────────────────────────────────

def test_subtitles_disabled_by_default():
    opts = _build_ydl_opts(make_task(mode="video"), make_config())
    assert opts.get("writesubtitles") is not True


def test_subtitles_enabled_only_for_video():
    """Audio shouldn't trigger subtitle download."""
    opts = _build_ydl_opts(make_task(mode="audio"), make_config(subtitle_download=True))
    assert opts.get("writesubtitles") is not True


def test_subtitles_enabled_for_video_when_config_true():
    opts = _build_ydl_opts(make_task(mode="video"), make_config(subtitle_download=True))
    assert opts.get("writesubtitles") is True
    assert "en" in opts.get("subtitleslangs", [])


# ── Thumbnail + metadata off independently ───────────────────────────

def test_disabling_metadata_keeps_thumbnail():
    opts = _build_ydl_opts(make_task(mode="video"), make_config(embed_lyrics=False))
    pp_keys = [p.get("key") for p in opts.get("postprocessors", [])]
    assert "EmbedThumbnail" in pp_keys
    assert "FFmpegMetadata" not in pp_keys


def test_disabling_thumbnail_keeps_metadata():
    opts = _build_ydl_opts(make_task(mode="video"), make_config(embed_thumbnail=False))
    pp_keys = [p.get("key") for p in opts.get("postprocessors", [])]
    assert "FFmpegMetadata" in pp_keys
    assert "EmbedThumbnail" not in pp_keys


# ── FFmpeg path passthrough ──────────────────────────────────────────

def test_ffmpeg_path_applied():
    opts = _build_ydl_opts(make_task(mode="audio"), make_config(ffmpeg_path="C:/custom/ffmpeg.exe"))
    assert opts.get("ffmpeg_location") == "C:/custom/ffmpeg.exe"


# ── Output template ──────────────────────────────────────────────────

def test_output_template_uses_title():
    opts = _build_ydl_opts(make_task(mode="audio"), make_config())
    assert "%(title)s" in opts["outtmpl"]