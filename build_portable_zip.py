"""Build the portable zip from the dist/my-dlp bundle."""
import zipfile
import os
import sys

src_dir = "dist/my-dlp"
out = "dist/my-dlp_v1.3.9_portable.zip"

# Remove any existing file
if os.path.exists(out):
    os.remove(out)

# Exclude user-specific files (so the zip is fresh for every downloader)
EXCLUDE_SUBSTRINGS = ("history.json", "config.json")

added = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    # Add create_shortcut.py at the zip root (next to my-dlp.exe)
    sc_path = "create_shortcut.py"
    if os.path.isfile(sc_path):
        zf.write(sc_path, sc_path)
        added += 1
        print(f"  + {sc_path}")

    for root, dirs, files in os.walk(src_dir):
        # Skip noisy directories
        dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
        for f in files:
            if f.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, src_dir)
            if any(ex in rel for ex in EXCLUDE_SUBSTRINGS):
                continue
            zf.write(full, rel)
            added += 1

print(f"Done. {added} files in {out} ({os.path.getsize(out) / 1024 / 1024:.1f} MB)")