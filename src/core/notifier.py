"""
notifier.py — Cross-platform desktop notifications for my-dlp.

Windows: uses a PowerShell one-liner to show a native Toast notification
         (no extra dependencies needed).
macOS:   uses `osascript` to display a notification.
Linux:   tries `notify-send` (libnotify).
"""
import os
import sys
import subprocess
import threading
from typing import Optional


def notify(title: str, message: str, app_name: str = "my-dlp"):
    """
    Show a desktop notification. Runs in a background thread so the
    caller never blocks.

    Returns immediately. The notification is fire-and-forget.
    """
    t = threading.Thread(target=_notify_sync, args=(title, message, app_name), daemon=True)
    t.start()


def _notify_sync(title: str, message: str, app_name: str):
    """Synchronous implementation — one attempt per platform."""
    if sys.platform == "win32":
        _notify_windows(title, message, app_name)
    elif sys.platform == "darwin":
        _notify_macos(title, message, app_name)
    else:
        _notify_linux(title, message)


def _notify_windows(title: str, message: str, app_name: str):
    """Use PowerShell's built-in toast notification capabilities."""
    ps_script = f'''
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $textNodes = $template.GetElementsByTagName("text")
    $textNodes.Item(0).AppendChild($template.CreateTextNode("{_escape_ps(title)}")) > $null
    $textNodes.Item(1).AppendChild($template.CreateTextNode("{_escape_ps(message)}")) > $null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{_escape_ps(app_name)}").Show($toast)
    '''
    try:
        subprocess.run(
            ["powershell", "-Command", ps_script],
            timeout=5, capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
    except (subprocess.TimeoutExpired, OSError):
        # Fallback: use msg.exe on Windows
        try:
            subprocess.run(
                ["msg", "%username%", f"{title}: {message}"],
                timeout=3, capture_output=True,
            )
        except Exception:
            pass
    except Exception:
        pass


def _notify_macos(title: str, message: str, app_name: str):
    """Use osascript for macOS notifications."""
    script = f'display notification "{_escape_as(message)}" with title "{_escape_as(title)}"'
    try:
        subprocess.run(["osascript", "-e", script], timeout=5, capture_output=True)
    except Exception:
        pass


def _notify_linux(title: str, message: str):
    """Use notify-send (libnotify) on Linux."""
    try:
        subprocess.run(
            ["notify-send", title, message],
            timeout=5, capture_output=True,
        )
    except Exception:
        pass


def _escape_ps(s: str) -> str:
    """Escape a string for safe embedding in a PowerShell single-quoted context."""
    # PowerShell '...' literals only need '' to escape '
    return s.replace("'", "''")


def _escape_as(s: str) -> str:
    """Escape a string for safe embedding in AppleScript."""
    return s.replace('"', '\\"')
