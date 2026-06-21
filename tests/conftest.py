"""
Shared pytest fixtures for the my-dlp test suite.

Goals:
- Tests run in an isolated environment (temp config dir, temp CWD).
- The real `src.utils.config_manager` is patched at import time so all
  tests use a tmp dir instead of touching the user's real APPDATA.
- tkinter / customtkinter imports are NOT triggered because we only
  test pure-Python modules in `src/core` and `src/utils`.
"""
import os
import sys
import shutil
import tempfile
import pytest


# Automatically prepend the project root to sys.path for the whole
# test session so `from src.core import lrc_parser` etc. always works.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.fixture
def tmp_config_dir(monkeypatch, tmp_path):
    """
    Point the user-config helpers at a fresh temp dir for the duration
    of one test. Returns the Path.

    IMPORTANT: we wipe the cached config_manager module BEFORE patching
    the env var so the module picks up the new _get_config_dir() at
    import time. We also clear history_manager for the same reason.
    """
    for mod_name in list(sys.modules):
        if mod_name.startswith("src.utils.config_manager") or mod_name.startswith(
            "src.utils.history_manager"
        ):
            del sys.modules[mod_name]

    monkeypatch.setenv("MY_DLP_CONFIG_DIR", str(tmp_path))

    # Now import fresh — _get_config_dir() will see our env var
    import importlib
    import src.utils.config_manager as cm
    import src.utils.history_manager as hm
    importlib.reload(cm)
    importlib.reload(hm)
    return tmp_path


@pytest.fixture
def project_root():
    """Return the absolute path to the project root."""
    return _PROJECT_ROOT


@pytest.fixture
def fresh_cwd(tmp_path, monkeypatch):
    """
    Run the test from a clean tmp directory. Useful when a module under
    test looks for files relative to CWD (e.g. assets/ for the icon).
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path