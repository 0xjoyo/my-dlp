"""
clipboard_monitor.py — Lightweight clipboard monitor for YouTube URLs.

Runs a daemon thread that polls the clipboard every 1.5s.
When a YouTube URL is detected, fires a callback so the app
can suggest downloading it.
"""
import threading
import time
import re
import tkinter as tk

_YOUTUBE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:youtube\.com|youtu\.be|m\.youtube\.com)"
    r"(?:/watch\?v=|/embed/|/v/|/shorts/|/)([\w-]{11})"
)


class ClipboardMonitor:
    """Poll the clipboard for YouTube URLs.  Fires on_url callback once per distinct URL."""

    def __init__(self, root: tk.Tk, on_url=None, on_unsupported=None):
        self.root = root
        self.on_url = on_url
        self.on_unsupported = on_unsupported
        self._last_url = ""
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _poll(self):
        while self._running:
            try:
                url = self.root.clipboard_get().strip()
            except Exception:
                url = ""
            if url and url != self._last_url:
                m = _YOUTUBE_RE.match(url)
                if m and self.on_url:
                    self._last_url = url
                    self.root.after(0, lambda u=url: self.on_url(u))
            time.sleep(1.5)
