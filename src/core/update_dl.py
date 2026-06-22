"""
update_dl.py — Download & install a new release in-place.

This module powers the "Download & Install" flow on the UpdateDialog.
It has four phases:

    1. Download the installer .exe to a temp directory (with progress
       callbacks so the dialog can show a progress bar).
    2. Verify the file (size sanity check, hash if we can get it from
       the GitHub API digest).
    3. Launch the installer in /SP- /SILENT /CLOSEAPPLICATIONS mode so
       Inno Setup closes our process for us.
    4. Quit the running app (sys.exit) so the installer can replace
       the binary. The installer is configured to wait for us.

The flow is synchronous on the worker thread; the UI thread marshals
back to itself via `root.after()` for progress updates. All public
functions in this module are safe to call from a background thread.
"""
import os
import sys
import shutil
import hashlib
import tempfile
import subprocess
import threading
from typing import Callable, Optional

import requests


# 8 MB chunks for streaming download. Big enough that progress
# callbacks are smooth; small enough that we never lock up the UI.
_CHUNK_SIZE = 1024 * 1024 * 8


def _expected_size(asset) -> int:
    """Return the expected byte length from the asset metadata, or 0."""
    if not asset or not isinstance(asset, dict):
        return 0
    try:
        return int(asset.get("size") or 0)
    except (TypeError, ValueError):
        return 0


def download_installer(
    asset: dict,
    on_progress: Optional[Callable[[int, int], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
) -> Optional[str]:
    """
    Download the installer at asset['url'] to a fresh temp file.

    Arguments:
        asset            - The release asset dict (must have 'url' and 'size')
        on_progress(downloaded, total)  - Periodic progress callback
        on_error(message) - Called on any failure (network, IO, etc.)

    Returns the absolute path to the downloaded .exe on success, or
    None on failure (after calling on_error).
    """
    url = (asset or {}).get("url")
    if not url:
        if on_error:
            on_error("Installer URL is empty.")
        return None

    expected = _expected_size(asset)
    name = (asset or {}).get("name") or "my-dlp-setup.exe"
    # Make sure the suffix is .exe so Windows treats it as a binary
    if not name.lower().endswith(".exe"):
        name = f"{name}.exe"

    # Use a uniquely-named temp file so simultaneous runs don't clash
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, f"my-dlp-update-{os.getpid()}-{name}")

    try:
        with requests.get(url, stream=True, timeout=60, allow_redirects=True) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length") or expected or 0)
            downloaded = 0
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=_CHUNK_SIZE):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress:
                        try:
                            on_progress(downloaded, total)
                        except Exception:
                            pass
    except requests.RequestException as e:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        if on_error:
            on_error(f"Download failed: {e}")
        return None
    except OSError as e:
        if on_error:
            on_error(f"Could not write to temp dir: {e}")
        return None

    # Size verification — compare the file we wrote to the size the
    # GitHub API advertised. Mismatch means truncated download.
    if expected:
        actual_size = os.path.getsize(tmp_path)
        if actual_size != expected:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            if on_error:
                on_error(
                    f"Size mismatch: expected {expected:,} bytes, "
                    f"got {actual_size:,}."
                )
            return None

    return tmp_path


def verify_file(path: str, expected_sha256: Optional[str] = None) -> bool:
    """
    Compute the SHA256 of the downloaded file and compare it to the
    expected value. If `expected_sha256` is None, we just check the
    file exists and is non-empty.
    """
    if not path or not os.path.isfile(path):
        return False
    if not expected_sha256:
        return os.path.getsize(path) > 0
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
                h.update(chunk)
    except OSError:
        return False
    return h.hexdigest().lower() == expected_sha256.lower()


def run_installer_and_exit(installer_path: str, silent: bool = True) -> None:
    """
    Launch the Inno Setup installer and exit the current process so
    the installer can replace the binary.

    Inno Setup flags we use:
      /SP-     - Don't show the "this will install..." splash page
      /SILENT  - Hide the wizard, only show progress
      /CLOSEAPPLICATIONS - Ask Windows to close our app first

    Before launching, we kill any lingering my-dlp processes (including
    the pystray daemon thread) using taskkill so the installer can
    replace the EXE without conflict.
    """
    if not installer_path or not os.path.isfile(installer_path):
        return

    flags = ["/SP-"]
    if silent:
        flags.append("/SILENT")
    flags.append("/CLOSEAPPLICATIONS")

    # ── Step 1: Kill any sibling my-dlp processes ────────────────────
    # This handles the case where the tray icon thread or a stale
    # process from a previous update is still holding the EXE lock.
    _kill_own_processes()

    # ── Step 2: Launch the installer ──────────────────────────────────
    try:
        # DETACHED_PROCESS so the installer keeps running after we exit.
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(
            [installer_path] + flags,
            creationflags=creationflags,
            close_fds=True,
        )
    except OSError:
        return

    # ── Step 3: Exit hard so the file lock is released ────────────────
    # We use taskkill to force-kill our own process tree, then os._exit
    # as a safety net. The 0.5s sleep gives the Inno Setup process time
    # to start and register with the Restart Manager before we vanish.
    import time
    time.sleep(0.5)
    _force_exit()


def _kill_own_processes():
    """Terminate every other my-dlp.exe process on the system (Windows)."""
    if sys.platform != "win32":
        return
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "my-dlp.exe"],
            timeout=5, capture_output=True,
        )
    except Exception:
        pass


def _force_exit():
    """Hard-terminate the current process and all its threads."""
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(os.getpid())],
                timeout=5, capture_output=True,
            )
        except Exception:
            pass
    os._exit(0)
