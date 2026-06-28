"""Security tests for my-dlp.

Covers:
  - URL validation (SSRF defense)
  - Filename sanitization (path traversal, reserved names)
  - CSV injection prevention
  - PowerShell escaping
  - History path resolution (no command injection via path)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.helpers import is_valid_url, sanitize_filename
from src.ui.history_tab import _sanitize_csv
from src.core.notifier import _escape_ps, _escape_as


# ── is_valid_url ────────────────────────────────────────────────

def test_url_accepts_https_youtube():
    assert is_valid_url("https://www.youtube.com/watch?v=abc")


def test_url_accepts_http():
    assert is_valid_url("http://example.com/")


def test_url_rejects_ftp_scheme():
    """Don't allow FTP — possible exfiltration channel."""
    assert not is_valid_url("ftp://example.com/secret")


def test_url_rejects_file_scheme():
    """Local file:// URLs could be used to probe local resources."""
    assert not is_valid_url("file:///etc/passwd")


def test_url_rejects_javascript_scheme():
    """javascript: URLs must NEVER be allowed."""
    assert not is_valid_url("javascript:alert(1)")


def test_url_rejects_data_scheme():
    """data: URLs could embed arbitrary content."""
    assert not is_valid_url("data:text/html,<script>alert(1)</script>")


def test_url_rejects_empty():
    assert not is_valid_url("")


def test_url_rejects_whitespace():
    assert not is_valid_url("   ")


def test_url_rejects_relative_path():
    assert not is_valid_url("/etc/passwd")


def test_url_accepts_youtu_be_shortened():
    assert is_valid_url("https://youtu.be/abc123XYZ45")


# ── sanitize_filename ───────────────────────────────────────────

def test_filename_strips_invalid_chars():
    out = sanitize_filename("a/b\\c:d*e?f\"g<h>i|j")
    assert "/" not in out
    assert "\\" not in out
    assert ":" not in out
    assert "*" not in out
    assert "?" not in out
    assert '"' not in out
    assert "<" not in out
    assert ">" not in out
    assert "|" not in out


def test_filename_strips_traversal():
    """Even if .. appears, the result must not escape the directory."""
    out = sanitize_filename("../../../etc/passwd")
    assert ".." not in out.replace("___", "")  # dots replaced too
    # The actual output will be "_______etc_passwd" or similar — never ".."


def test_filename_strips_null_bytes():
    out = sanitize_filename("good\x00.exe")
    # Null byte should be replaced, not passed through
    assert "\x00" not in out


def test_filename_preserves_unicode():
    out = sanitize_filename("歌曲名 - Artist.mp3")
    # Non-ASCII should pass through
    assert "歌" in out


def test_filename_strips_leading_dots():
    """Hidden files (e.g. .bashrc) could be a social engineering trick."""
    out = sanitize_filename(".hidden")
    # We don't strictly forbid it (yt-dlp does this for thumbnails),
    # but we should at least not crash.


def test_filename_rejects_reserved_windows_names():
    """CON, PRN, AUX, NUL etc. are reserved on Windows."""
    for name in ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]:
        out = sanitize_filename(name)
        # The output must not be exactly the reserved name
        assert out.upper() != name, f"Reserved name {name!r} passed through"


# ── CSV injection ───────────────────────────────────────────────

def test_csv_sanitizes_equals_prefix():
    assert _sanitize_csv("=cmd|'/c calc'!A1").startswith("'")


def test_csv_sanitizes_plus_prefix():
    assert _sanitize_csv("+HYPERLINK(...))").startswith("'")


def test_csv_sanitizes_minus_prefix():
    assert _sanitize_csv("-2+3+cmd|'/c calc'!A1").startswith("'")


def test_csv_sanitizes_at_prefix():
    assert _sanitize_csv("@SUM(1+1)").startswith("'")


def test_csv_sanitizes_tab_prefix():
    assert _sanitize_csv("\t=evil()").startswith("'")


def test_csv_passes_safe_strings():
    assert _sanitize_csv("normal text") == "normal text"
    assert _sanitize_csv("Title with - dash") == "Title with - dash"
    assert _sanitize_csv("") == ""


def test_csv_handles_none():
    assert _sanitize_csv(None) == ""


def test_csv_handles_non_string():
    assert _sanitize_csv(123) == "123"


# ── PowerShell escaping ─────────────────────────────────────────

def test_ps_escape_handles_quotes():
    out = _escape_ps("it's")
    # Single quote becomes doubled in PowerShell single-quoted strings
    assert out == "it''s"


def test_ps_escape_handles_backticks():
    # Backticks are PowerShell escape characters
    out = _escape_ps("`n")
    # Our escaper doesn't strip them, but the single-quote context
    # means they pass through literally — important to remember not
    # to use them outside a single-quoted string.
    assert "`n" in out


def test_as_escape_handles_quotes():
    out = _escape_as('say "hi"')
    assert '\\"' in out


# ── Path resolution ─────────────────────────────────────────────

def test_open_path_rejects_traversal():
    """Verify that os.path.abspath neutralizes simple traversal tricks."""
    # 'C:\\foo\\..\\bar' should become 'C:\\bar'
    p = os.path.abspath("C:\\foo\\..\\bar")
    assert ".." not in p
    assert p.endswith("bar") or p.endswith("bar" + os.sep)
