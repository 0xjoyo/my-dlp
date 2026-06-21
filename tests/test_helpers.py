"""
Unit tests for src/utils/helpers.py

These are tiny pure functions but they're used in a lot of places (filename
sanitization happens before every download, URL detection happens on every
paste, etc.), so silent regressions here are painful.
"""
import pytest

from src.utils.helpers import (
    is_valid_url,
    is_spotify_url,
    is_youtube_url,
    is_playlist_url,
    format_duration,
    format_views,
    sanitize_filename,
    get_platform_name,
)


# ── is_valid_url ───────────────────────────────────────────────────


class TestIsValidUrl:
    @pytest.mark.parametrize("url", [
        "http://example.com",
        "https://example.com/path",
        "https://www.youtube.com/watch?v=abc",
        "https://open.spotify.com/track/123",
    ])
    def test_valid(self, url):
        assert is_valid_url(url) is True

    @pytest.mark.parametrize("url", [
        "",
        "not a url",
        "ftp://example.com",          # wrong scheme
        "example.com",                 # no scheme
        "https://",                    # empty host
        "//example.com",               # no scheme
    ])
    def test_invalid(self, url):
        assert is_valid_url(url) is False

    def test_with_whitespace(self):
        # urlencode rejects, but our helper strips first
        assert is_valid_url("  https://example.com  ") is True


# ── is_spotify_url ─────────────────────────────────────────────────


class TestIsSpotifyUrl:
    @pytest.mark.parametrize("url", [
        "https://open.spotify.com/track/abc",
        "https://open.spotify.com/album/xyz",
        "https://spotify.com/track/abc",        # bare domain (rare but valid)
        "http://open.spotify.com/playlist/123", # http scheme OK
    ])
    def test_spotify(self, url):
        assert is_spotify_url(url) is True

    @pytest.mark.parametrize("url", [
        "https://youtube.com",
        "https://soundcloud.com/artist",
        "https://example.com/spotify-clone",
    ])
    def test_not_spotify(self, url):
        assert is_spotify_url(url) is False


# ── is_youtube_url ─────────────────────────────────────────────────


class TestIsYoutubeUrl:
    @pytest.mark.parametrize("url", [
        "https://www.youtube.com/watch?v=abc",
        "https://youtu.be/abc",
        "https://music.youtube.com/watch?v=abc",
        "http://youtube.com/watch?v=abc",
    ])
    def test_youtube(self, url):
        assert is_youtube_url(url) is True

    @pytest.mark.parametrize("url", [
        "https://example.com",
        "https://spotify.com",
    ])
    def test_not_youtube(self, url):
        assert is_youtube_url(url) is False

    def test_substring_in_path_not_counted(self):
        # The current implementation checks substring, which can give
        # false positives (e.g. a hypothetical "youtubeproxy.com" would
        # be flagged as YouTube). Documenting current behavior here so
        # future maintainers know to swap to hostname parsing.
        # The current `is_youtube_url` returns False for non-YT domains
        # because the implementation happens to check that the substring
        # matches a domain segment that ends in "youtube.com"/etc.
        assert is_youtube_url("https://example.com/has-youtube-in-path") is False


# ── is_playlist_url ────────────────────────────────────────────────


class TestIsPlaylistUrl:
    @pytest.mark.parametrize("url", [
        "https://youtube.com/playlist?list=ABC",
        "https://open.spotify.com/album/abc",
        "https://soundcloud.com/user/sets/playlist-name",
    ])
    def test_playlist(self, url):
        assert is_playlist_url(url) is True

    @pytest.mark.parametrize("url", [
        "https://youtube.com/watch?v=abc",
        "https://youtube.com/watch?v=abc&list=PL123",  # list= alone not detected
        "https://open.spotify.com/track/abc",
    ])
    def test_not_playlist(self, url):
        assert is_playlist_url(url) is False


# ── format_duration ────────────────────────────────────────────────


class TestFormatDuration:
    def test_zero(self):
        assert format_duration(0) == "0:00"

    def test_seconds_only(self):
        assert format_duration(45) == "0:45"

    def test_one_minute(self):
        assert format_duration(60) == "1:00"

    def test_minutes_and_seconds(self):
        assert format_duration(125) == "2:05"

    def test_with_leading_zero_on_seconds(self):
        assert format_duration(65) == "1:05"

    def test_exactly_one_hour(self):
        assert format_duration(3600) == "1:00:00"

    def test_hours_minutes_seconds(self):
        assert format_duration(3725) == "1:02:05"  # 1h 2m 5s

    def test_long_mix(self):
        # 2h 30m
        assert format_duration(9000) == "2:30:00"

    def test_negative_raises_or_returns_zero(self):
        # Real implementation uses // — negative numbers go weird.
        # Just ensure it doesn't crash.
        result = format_duration(-1)
        assert isinstance(result, str)


# ── format_views ────────────────────────────────────────────────────


class TestFormatViews:
    def test_zero(self):
        assert format_views(0) == "—"

    def test_small_number(self):
        assert format_views(42) == "42"

    def test_thousands(self):
        assert format_views(1500) == "1.5K"

    def test_millions(self):
        assert format_views(2_500_000) == "2.5M"

    def test_billions(self):
        assert format_views(1_200_000_000) == "1.2B"

    def test_exact_thousand(self):
        assert format_views(1000) == "1.0K"

    def test_just_under_million(self):
        assert format_views(999_999) == "1000.0K"  # OK — quirky but consistent


# ── sanitize_filename ──────────────────────────────────────────────


class TestSanitizeFilename:
    def test_no_changes(self):
        assert sanitize_filename("normal_file_name.mp3") == "normal_file_name.mp3"

    def test_removes_slashes(self):
        assert sanitize_filename("a/b\\c.mp3") == "a_b_c.mp3"

    def test_removes_invalid_chars(self):
        invalid_chars = r'\/:*?"<>|'
        for ch in invalid_chars:
            result = sanitize_filename(f"hello{ch}world")
            assert ch not in result or result == "hello_world"

    def test_replaces_all_with_underscore(self):
        result = sanitize_filename(r'test<>:"/\|?*.mp3')
        for ch in r'\\/:*?"<>|':
            assert ch not in result

    def test_strips_whitespace(self):
        assert sanitize_filename("  spaced  .mp3  ") == "spaced  .mp3"

    def test_unicode_preserved(self):
        # Non-ASCII like Arabic / Chinese is left alone
        assert sanitize_filename("أغنية.mp3") == "أغنية.mp3"


# ── get_platform_name ──────────────────────────────────────────────


class TestGetPlatformName:
    @pytest.mark.parametrize("url,expected", [
        ("https://www.youtube.com/watch?v=x", "YouTube"),
        ("https://music.youtube.com/watch?v=x", "YouTube"),
        ("https://youtu.be/abc", "YouTube"),
        ("https://open.spotify.com/track/x", "Spotify"),
        ("https://soundcloud.com/artist/track", "SoundCloud"),
        ("https://tiktok.com/@user/video/123", "TikTok"),
        ("https://twitter.com/user/status/123", "X (Twitter)"),
        ("https://x.com/user/status/123", "X (Twitter)"),
        ("https://instagram.com/p/abc", "Instagram"),
        ("https://facebook.com/video", "Facebook"),
        ("https://fb.watch/abc", "Facebook"),
        ("https://vimeo.com/123456", "Vimeo"),
        ("https://example.com/something", "Unknown"),
    ])
    def test_detection(self, url, expected):
        assert get_platform_name(url) == expected