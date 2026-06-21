"""
create_shortcut.py — Create a desktop shortcut to my-dlp.

Usage:
    python create_shortcut.py

By default this creates "my-dlp.lnk" on the current user's desktop pointing
at the script's containing directory's my-dlp.exe (for the portable build).
On Linux/macOS this creates a .desktop file instead.

Safe to re-run: it overwrites any existing shortcut with the same name.
"""
import os
import sys
import platform
import subprocess


APP_NAME = "my-dlp"


def _desktop_dir() -> str:
    """Return the current user's desktop directory."""
    if sys.platform == "win32":
        # SHGetFolderPath / known folder via PowerShell to honour OneDrive
        # redirections — but the most common case is fine via USERPROFILE.
        # Try OneDrive Desktop first, fall back to the classic location.
        onedrive = os.environ.get("USERPROFILE", "")
        candidates = [
            os.path.join(onedrive, "OneDrive", "Desktop"),
            os.path.join(onedrive, "Desktop"),
            os.path.expanduser("~/Desktop"),
        ]
        for c in candidates:
            if c and os.path.isdir(c):
                return c
        return os.path.expanduser("~/Desktop")
    # Linux / macOS
    return os.path.expanduser("~/Desktop")


def _exe_path() -> str:
    """Resolve the path to my-dlp.exe (or just my-dlp on Linux)."""
    here = os.path.dirname(os.path.abspath(__file__))
    name = "my-dlp.exe" if sys.platform == "win32" else "my-dlp"
    candidate = os.path.join(here, name)
    if os.path.isfile(candidate):
        return candidate
    # One level up (when this script is next to the build, not inside it)
    candidate = os.path.join(os.path.dirname(here), name)
    if os.path.isfile(candidate):
        return candidate
    return os.path.join(here, name)


def create_windows_shortcut(exe: str, shortcut_path: str, icon: str | None = None) -> bool:
    """Create a .lnk on Windows using PowerShell so no extra deps needed."""
    ps = (
        "$s = (New-Object -COM WScript.Shell).CreateShortcut("
        f"'{shortcut_path}'"
        "); "
        f"$s.TargetPath = '{exe}'; "
        f"$s.WorkingDirectory = '{os.path.dirname(exe)}'; "
        f"$s.Description = 'my-dlp — premium yt-dlp desktop client'; "
        f"$s.WindowStyle = 7; "  # minimized — handy for tray-on-startup later
        f"$s.IconLocation = '{icon or exe}'; "
        "$s.Save()"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            check=True, capture_output=True, text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def create_desktop_file(exe: str, shortcut_path: str, icon: str | None = None) -> bool:
    """Create a freedesktop.org .desktop entry on Linux / macOS."""
    here = os.path.dirname(exe)
    body = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        "Comment=my-dlp — premium yt-dlp desktop client\n"
        f"Exec={exe}\n"
        f"Path={here}\n"
        f"Icon={icon or exe}\n"
        "Terminal=false\n"
        "Categories=Network;AudioVideo;\n"
    )
    try:
        with open(shortcut_path, "w", encoding="utf-8") as f:
            f.write(body)
        os.chmod(shortcut_path, 0o755)
        return True
    except OSError:
        return False


def main():
    exe = _exe_path()
    desktop = _desktop_dir()
    icon_candidate = os.path.join(os.path.dirname(exe), "assets", "icon.ico")
    icon = icon_candidate if os.path.isfile(icon_candidate) else None

    if sys.platform == "win32":
        shortcut = os.path.join(desktop, f"{APP_NAME}.lnk")
        if create_windows_shortcut(exe, shortcut, icon=icon):
            print(f"OK  Created: {shortcut}")
        else:
            print(f"ERR Could not create shortcut at {shortcut}")
            sys.exit(1)
    else:
        shortcut = os.path.join(desktop, f"{APP_NAME}.desktop")
        if create_desktop_file(exe, shortcut, icon=icon):
            print(f"OK  Created: {shortcut}")
        else:
            print(f"ERR Could not create .desktop file at {shortcut}")
            sys.exit(1)


if __name__ == "__main__":
    main()