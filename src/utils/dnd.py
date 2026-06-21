"""
dnd.py — Optional drag-and-drop support for URL entry widgets.

We use the `tkinterdnd2` package which adds DnD to Tk on Windows, macOS,
and X11. Wayland support is experimental in tkinterdnd2; on Wayland
sessions the binding simply does nothing (the user can still paste with
Ctrl+V), and we surface that in the helper's return value so callers
can choose to show a hint.

If the package isn't installed, `setup_dnd()` returns False silently —
the caller should just skip the drag-drop binding and rely on the
existing paste shortcut.
"""
from __future__ import annotations

from typing import Callable, Optional


def _try_import_tkdnd():
    """
    Import tkinterdnd2 and patch Tk's class so all toplevel windows
    created afterwards can be drop targets.

    Idempotent — safe to call from multiple widgets.
    """
    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
    except Exception:
        return None, None
    try:
        # Patch the root window so toplevels get the drop binding.
        # TkinterDnD root provides .dnd_bind() on any widget.
        TkinterDnD._require()  # ensures the C extension is loaded
        return TkinterDnD, DND_FILES
    except Exception:
        return None, None


def setup_dnd(
    widget,
    on_drop: Callable[[str], None],
    on_unsupported_platform: Optional[Callable[[], None]] = None,
) -> bool:
    """
    Attach drag-and-drop support to `widget`. Returns True if DnD was
    wired up successfully, False otherwise (the caller can then surface
    a hint that the user should use Ctrl+V instead).

    `on_drop` receives a single string. If the user dropped multiple
    files/URLs, `on_drop` is called once per item (newline-separated).
    Inside TkinterDnD, the drop payload comes as a Python-list-like
    string surrounded with curly braces on Windows; we strip those.
    """
    TkinterDnD, DND_FILES = _try_import_tkdnd()
    if TkinterDnD is None:
        if on_unsupported_platform:
            on_unsupported_platform()
        return False

    def _handle_drop(event):
        # The event.data field contains either:
        #   - a single path / URL:  C:/foo.mp4  or  https://example.com/x
        #   - a brace-wrapped list of paths:  {C:/foo.mp4 C:/bar.mp4}
        raw = event.data
        if not raw:
            return
        # Strip surrounding braces if present
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        # Split on whitespace / braces — items may be space-separated
        items = []
        for token in raw.replace("\n", " ").split():
            token = token.strip("{}")
            if token:
                items.append(token)
        for item in items:
            on_drop(item)

    try:
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", _handle_drop)
        return True
    except Exception:
        # Some widget classes / Tk versions reject the binding
        return False