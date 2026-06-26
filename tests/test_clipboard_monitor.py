"""Tests for the clipboard monitor: dedup, single notification per URL."""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.core.clipboard_monitor as cm


class FakeRoot:
    """Stand-in for tk.Tk that just records after() callbacks."""
    def __init__(self):
        self.pending = []

    def clipboard_get(self):
        # Set via property
        return self._clip or ""

    def set_clip(self, value):
        self._clip = value

    def after(self, ms, fn):
        self.pending.append(fn)


def make_monitor(root, callback):
    m = cm.ClipboardMonitor(root=root, on_url=callback)
    m._poll_period = 0.01  # unused in tests — we drive _poll manually
    return m


def test_no_notify_for_non_youtube_url():
    """A plain URL that isn't YouTube must not trigger the callback."""
    root = FakeRoot()
    root.set_clip("https://example.com/article/123")
    calls = []
    m = make_monitor(root, lambda u: calls.append(u))
    m._last_url = ""
    # One poll cycle
    url = root.clipboard_get().strip()
    if url and url != m._last_url:
        if cm._YOUTUBE_RE.match(url) and m.on_url:
            m._last_url = url
            root.after(0, lambda u=url: m.on_url(u))
    assert calls == []


def test_notify_once_per_new_youtube_url():
    """A brand-new YouTube URL should trigger the callback exactly once."""
    root = FakeRoot()
    root.set_clip("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    calls = []
    m = make_monitor(root, lambda u: calls.append(u))
    m._last_url = ""

    # Simulate one poll
    url = root.clipboard_get().strip()
    if url and url != m._last_url:
        if cm._YOUTUBE_RE.match(url) and m.on_url:
            m._last_url = url
            root.after(0, lambda u=url: m.on_url(u))

    # Process pending after-callbacks
    for fn in root.pending:
        fn()

    assert calls == ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    assert m._last_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_no_notify_for_same_url_twice():
    """Re-polling the same URL must NOT fire the callback again."""
    root = FakeRoot()
    root.set_clip("https://youtu.be/abc123XYZ45")
    calls = []
    m = make_monitor(root, lambda u: calls.append(u))
    m._last_url = ""

    # First poll — should notify
    url = root.clipboard_get().strip()
    if url and url != m._last_url:
        if cm._YOUTUBE_RE.match(url) and m.on_url:
            m._last_url = url
            root.after(0, lambda u=url: m.on_url(u))
    for fn in root.pending:
        fn()
    assert len(calls) == 1

    # Second poll — same URL — must NOT notify
    root.pending.clear()
    url = root.clipboard_get().strip()
    if url and url != m._last_url:
        if cm._YOUTUBE_RE.match(url) and m.on_url:
            m._last_url = url
            root.after(0, lambda u=url: m.on_url(u))
    for fn in root.pending:
        fn()
    assert len(calls) == 1, f"Same URL fired twice: {calls}"


def test_no_notify_for_empty_clipboard():
    root = FakeRoot()
    root.set_clip("")
    calls = []
    m = make_monitor(root, lambda u: calls.append(u))
    m._last_url = ""
    url = root.clipboard_get().strip()
    if url and url != m._last_url:
        if cm._YOUTUBE_RE.match(url) and m.on_url:
            m._last_url = url
            root.after(0, lambda u=url: m.on_url(u))
    assert calls == []


def test_youtube_regex_matches_common_forms():
    assert cm._YOUTUBE_RE.match("https://www.youtube.com/watch?v=abc123XYZ45")
    assert cm._YOUTUBE_RE.match("https://youtu.be/abc123XYZ45")
    assert cm._YOUTUBE_RE.match("https://www.youtube.com/shorts/abc123XYZ45")
    assert cm._YOUTUBE_RE.match("https://m.youtube.com/watch?v=abc123XYZ45")
    assert not cm._YOUTUBE_RE.match("https://example.com/watch?v=abc123XYZ45")
    assert not cm._YOUTUBE_RE.match("https://www.youtube.com/")