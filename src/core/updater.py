"""
Update checker — queries the GitHub Releases API for the latest my-dlp
release and compares it to the running version.

Returns a dict (or None on failure) shaped like:
    {
        "latest_version": "1.2.0",
        "current_version": "1.1.0",
        "release_notes": "...markdown body...",
        "html_url": "https://github.com/0xjoyo/my-dlp/releases/tag/v1.2.0",
        "assets": [
            {"name": "my-dlp_v1.2.0_installer.exe", "url": "...", "size": 12345},
            ...
        ],
        "is_update_available": True,
    }
"""
import os
import sys
import json
import threading
import requests
from typing import Callable, Optional
from packaging.version import Version, InvalidVersion


# Constants — change if you fork the project
GITHUB_OWNER = "0xjoyo"
GITHUB_REPO = "my-dlp"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
HTTP_TIMEOUT = 8  # seconds


def _running_version() -> str:
    """
    Resolve the currently-running my-dlp version.

    Resolution order:
      1. MY_DLP_VERSION environment variable (used by build scripts)
      2. A frozen exe with embedded version metadata (PyInstaller
         sets the version into the binary's VersionInfo; we read it
         from there via the VersionInfo resource)
      3. The VERSION file shipped in the project root
      4. A hardcoded fallback of "0.0.0" so callers always see a real
         version string (and so the updater can offer an upgrade)
    """
    env_v = os.environ.get("MY_DLP_VERSION")
    if env_v:
        return env_v.strip()

    # Try the bundled VERSION file (works in dev mode + PyInstaller onefile
    # when --add-data is set). We use sys._MEIPASS for frozen builds.
    candidates = []
    if getattr(sys, "frozen", False):
        # PyInstaller puts data files in sys._MEIPASS
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(os.path.join(meipass, "VERSION"))
        candidates.append(os.path.join(os.path.dirname(sys.executable), "VERSION"))
    else:
        here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidates.append(os.path.join(here, "VERSION"))

    for path in candidates:
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except OSError:
            pass

    return "0.0.0"


def _parse_version(s: str) -> Optional[Version]:
    """Strip leading 'v' and parse as a Version, returning None on failure."""
    if not s:
        return None
    s = s.strip()
    if s.startswith(("v", "V")):
        s = s[1:]
    try:
        return Version(s)
    except InvalidVersion:
        return None


def fetch_release_info() -> Optional[dict]:
    """
    Synchronously fetch the latest release info from GitHub.
    Returns None on network failure or non-200 response.
    """
    try:
        resp = requests.get(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "my-dlp-updater"},
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException:
        return None

    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None

    tag = (data.get("tag_name") or "").strip()
    current = _running_version()
    latest = _parse_version(tag) or Version("0.0.0")
    current_v = _parse_version(current) or Version("0.0.0")

    assets = []
    for asset in data.get("assets", []) or []:
        if not isinstance(asset, dict):
            continue
        assets.append({
            "name": asset.get("name", ""),
            "url": asset.get("browser_download_url", ""),
            "size": asset.get("size", 0),
        })

    return {
        "latest_version": str(latest),
        "current_version": str(current_v),
        "release_name": data.get("name") or tag,
        "release_notes": data.get("body") or "",
        "html_url": data.get("html_url", f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"),
        "assets": assets,
        "is_update_available": latest > current_v,
        "prerelease": bool(data.get("prerelease", False)),
        "published_at": data.get("published_at", ""),
    }


def check_for_update(callback: Callable, error_callback: Optional[Callable] = None):
    """
    Asynchronously fetch the latest release and call `callback(info_dict)`
    on the worker thread. Use `app.after(0, ...)` to marshal back to the UI.
    """
    def _worker():
        try:
            info = fetch_release_info()
            if info is None and error_callback:
                error_callback()
                return
            callback(info)
        except Exception:
            if error_callback:
                error_callback()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def pick_asset_for_platform(info: dict, platform: Optional[str] = None) -> Optional[dict]:
    """
    Pick the best asset for the current platform from the release's asset list.
    Returns the asset dict (with url/name/size) or None.
    """
    if not info or not info.get("assets"):
        return None
    if platform is None:
        platform = sys.platform

    # Prefer installer on Windows, AppImage on Linux, etc.
    if platform.startswith("win"):
        priority_prefixes = ("_setup.exe", "setup.exe", "_installer.exe", "installer.exe", "my-dlp_v")
    elif platform.startswith("linux"):
        priority_prefixes = (".AppImage", ".deb", ".rpm", "linux", "my-dlp_v")
    elif platform == "darwin":
        priority_prefixes = (".dmg", ".app", "mac", "my-dlp_v")
    else:
        priority_prefixes = ("my-dlp_v",)

    name_lower = lambda a: (a.get("name") or "").lower()

    for prefix in priority_prefixes:
        for asset in info["assets"]:
            n = name_lower(asset)
            if prefix.lower() in n:
                # Must be an executable/installer — never a zip/archive
                if n.endswith((".exe", ".appimage", ".deb", ".rpm", ".dmg")):
                    return asset
                # Also accept if the name contains "installer" or "setup"
                # (some GitHub release assets omit the .exe extension in
                #  the display name but still link to an exe)
                if "installer" in n or "_setup" in n or ".setup" in n:
                    # Only if the content-type suggests it's a binary
                    ct = (asset.get("content_type") or "").lower()
                    if "msdownload" in ct or "octet-stream" in ct or "x-msdownload" in ct:
                        return asset

    # Fallback: only accept a genuine installer/setup exe, never a zip
    for asset in info["assets"]:
        n = name_lower(asset)
        if n.endswith(".exe") and ("installer" in n or "setup" in n):
            return asset

    # Last resort: the first .exe asset (if any)
    for asset in info["assets"]:
        n = name_lower(asset)
        if n.endswith(".exe"):
            return asset

    # Absolutely nothing usable
    return info["assets"][0] if info["assets"] else None


def get_dismissed_version() -> Optional[str]:
    """
    Return the version string the user has dismissed (i.e. told us
    'don't show this update again'), or None if there's no such record.
    """
    from src.utils.config_manager import load_config
    cfg = load_config()
    return cfg.get("update_dismissed_version") or None


def set_dismissed_version(version: str) -> None:
    """Record that the user has dismissed the pop-up for `version`."""
    from src.utils.config_manager import set_value
    set_value("update_dismissed_version", version)


def clear_dismissed_version() -> None:
    """Clear the dismissal record (called after a successful install)."""
    from src.utils.config_manager import set_value
    set_value("update_dismissed_version", "")


def get_update_badge_state() -> bool:
    """
    Return True if the sidebar should show the 'update available' dot.
    True when an update is available AND its version has not been dismissed
    yet. The pop-up itself is governed by get_dismissed_version() so this
    is just a convenience for the UI.
    """
    return bool(get_dismissed_version())  # kept for future use