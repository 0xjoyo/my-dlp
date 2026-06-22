"""
Unit tests for src/core/update_dl.py

The downloader is small but security-sensitive: it shells out to the
OS installer after writing a file to disk. We test:
- size-mismatch detection (truncated download)
- empty URL handling
- the verify_file helper (sha256 path + size-only fallback)
- _expected_size robust to bad types
- run_installer_and_exit doesn't crash on missing files

We don't run a real download in tests (would need internet + a
working Inno setup); we patch `requests.get` instead.
"""
import hashlib
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

import pytest


# Make sure we can import the module under test. The conftest.py in
# this folder sets up sys.path.
import src.core.update_dl as update_dl


# ────────────────────────────────────────────────────────────────────
# Pure helpers
# ────────────────────────────────────────────────────────────────────

class TestExpectedSize:
    def test_zero_for_missing_key(self):
        assert update_dl._expected_size({}) == 0

    def test_zero_for_none(self):
        assert update_dl._expected_size(None) == 0

    def test_int_conversion(self):
        assert update_dl._expected_size({"size": 12345}) == 12345

    def test_string_size_coerced(self):
        assert update_dl._expected_size({"size": "9876"}) == 9876

    def test_garbage_size_returns_zero(self):
        assert update_dl._expected_size({"size": "not a number"}) == 0


class TestVerifyFile:
    def test_missing_file_returns_false(self, tmp_path):
        assert update_dl.verify_file(str(tmp_path / "nope.exe")) is False

    def test_empty_file_returns_false(self, tmp_path):
        p = tmp_path / "zero.exe"
        p.write_bytes(b"")
        assert update_dl.verify_file(str(p)) is False

    def test_size_only_check_passes_on_nonempty(self, tmp_path):
        p = tmp_path / "ok.exe"
        p.write_bytes(b"x" * 100)
        assert update_dl.verify_file(str(p), expected_sha256=None) is True

    def test_sha256_match(self, tmp_path):
        p = tmp_path / "f.exe"
        content = b"hello world"
        p.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert update_dl.verify_file(str(p), expected_sha256=expected) is True

    def test_sha256_mismatch(self, tmp_path):
        p = tmp_path / "f.exe"
        p.write_bytes(b"real content")
        assert update_dl.verify_file(str(p), expected_sha256="0" * 64) is False

    def test_sha256_case_insensitive(self, tmp_path):
        p = tmp_path / "f.exe"
        content = b"data"
        p.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest().upper()
        assert update_dl.verify_file(str(p), expected_sha256=expected) is True

    def test_empty_sha256_skips_check(self, tmp_path):
        """Empty expected hash is treated as 'unknown' — fall back to size."""
        p = tmp_path / "f.exe"
        p.write_bytes(b"x" * 10)
        assert update_dl.verify_file(str(p), expected_sha256="") is True


# ────────────────────────────────────────────────────────────────────
# download_installer
# ────────────────────────────────────────────────────────────────────

class TestDownloadInstaller:
    def test_empty_url_calls_error(self):
        errors = []
        result = update_dl.download_installer(
            asset={"url": "", "size": 100},
            on_error=errors.append,
        )
        assert result is None
        assert errors and "empty" in errors[0].lower()

    def test_no_url_key(self):
        errors = []
        result = update_dl.download_installer(
            asset={"size": 100},
            on_error=errors.append,
        )
        assert result is None
        assert errors

    def test_successful_download(self, tmp_path, monkeypatch):
        # We patch `requests.get` to return a fake streaming response
        # and patch `tempfile.gettempdir` to put the file in tmp_path
        monkeypatch.setattr(update_dl.tempfile, "gettempdir", lambda: str(tmp_path))

        fake_content = b"x" * 1000
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = lambda s, *a: None
        fake_resp.raise_for_status = lambda: None
        fake_resp.headers = {"Content-Length": str(len(fake_content))}
        fake_resp.iter_content = lambda chunk_size: [fake_content]

        with patch.object(update_dl.requests, "get", return_value=fake_resp):
            progress = []
            errors = []
            result = update_dl.download_installer(
                asset={"url": "http://x/y.exe", "size": len(fake_content)},
                on_progress=lambda d, t: progress.append((d, t)),
                on_error=errors.append,
            )

        assert errors == []
        assert result is not None
        assert os.path.isfile(result)
        with open(result, "rb") as f:
            assert f.read() == fake_content
        # Progress should be reported at least once
        assert progress
        last_d, last_t = progress[-1]
        assert last_d == len(fake_content)
        assert last_t == len(fake_content)

    def test_size_mismatch_cleans_up(self, tmp_path, monkeypatch):
        monkeypatch.setattr(update_dl.tempfile, "gettempdir", lambda: str(tmp_path))

        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = lambda s, *a: None
        fake_resp.raise_for_status = lambda: None
        fake_resp.headers = {"Content-Length": "100"}
        # Return 50 bytes even though we advertised 200
        fake_resp.iter_content = lambda chunk_size: [b"x" * 50]

        with patch.object(update_dl.requests, "get", return_value=fake_resp):
            errors = []
            result = update_dl.download_installer(
                asset={"url": "http://x/y.exe", "size": 200},  # expected 200
                on_error=errors.append,
            )

        assert result is None
        assert any("mismatch" in e.lower() or "size" in e.lower() for e in errors)
        # Temp file should have been cleaned up
        leftovers = list(tmp_path.glob("my-dlp-update-*"))
        assert leftovers == []

    def test_network_failure_calls_error(self, monkeypatch):
        import requests as _r
        def _raise(*a, **k):
            raise _r.ConnectionError("nope")
        with patch.object(update_dl.requests, "get", _raise):
            errors = []
            result = update_dl.download_installer(
                asset={"url": "http://x/y.exe", "size": 10},
                on_error=errors.append,
            )
        assert result is None
        assert errors
        assert "download" in errors[0].lower() or "failed" in errors[0].lower()

    def test_name_without_exe_gets_suffix(self, tmp_path, monkeypatch):
        monkeypatch.setattr(update_dl.tempfile, "gettempdir", lambda: str(tmp_path))

        fake_content = b"x" * 5
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = lambda s, *a: None
        fake_resp.raise_for_status = lambda: None
        fake_resp.headers = {"Content-Length": "5"}
        fake_resp.iter_content = lambda chunk_size: [fake_content]

        with patch.object(update_dl.requests, "get", return_value=fake_resp):
            result = update_dl.download_installer(
                asset={"url": "http://x/setup", "size": 5, "name": "setup"},
            )

        assert result is not None
        assert result.lower().endswith(".exe")


# ────────────────────────────────────────────────────────────────────
# run_installer_and_exit
# ────────────────────────────────────────────────────────────────────

class TestRunInstallerAndExit:
    def test_missing_path_is_noop(self, monkeypatch):
        # Should not raise and should not call Popen
        with patch.object(update_dl.subprocess, "Popen") as popen:
            update_dl.run_installer_and_exit("/nope/missing.exe")
        popen.assert_not_called()

    def test_existing_path_spawns_and_exits(self, tmp_path, monkeypatch):
        installer = tmp_path / "inst.exe"
        installer.write_bytes(b"x" * 4)
        monkeypatch.setattr(update_dl.os, "_exit", lambda c: None)
        # Mock subprocess.run (used by _kill_own_processes + _force_exit)
        monkeypatch.setattr(update_dl.subprocess, "run", lambda *a, **k: None)

        popen_calls = []
        class FakePopen:
            def __init__(self, args, **kw):
                popen_calls.append((args, kw))
        monkeypatch.setattr(update_dl.subprocess, "Popen", FakePopen)

        exit_calls = []
        monkeypatch.setattr(update_dl.os, "_exit", lambda c: exit_calls.append(c))

        update_dl.run_installer_and_exit(str(installer))
        assert len(popen_calls) == 1
        args, _kwargs = popen_calls[0]
        # Args: [installer, "/SP-", "/SILENT", "/CLOSEAPPLICATIONS"]
        assert args[0] == str(installer)
        assert "/SP-" in args
        assert "/SILENT" in args
        assert "/CLOSEAPPLICATIONS" in args
        # And we exited cleanly
        assert exit_calls == [0]

    def test_silent_false_omits_silent_flag(self, tmp_path, monkeypatch):
        installer = tmp_path / "inst.exe"
        installer.write_bytes(b"x" * 4)
        monkeypatch.setattr(update_dl.os, "_exit", lambda c: None)
        # Mock subprocess.run (used by _kill_own_processes + _force_exit)
        monkeypatch.setattr(update_dl.subprocess, "run", lambda *a, **k: None)

        popen_calls = []
        class FakePopen:
            def __init__(self, args, **kw):
                popen_calls.append((args, kw))
        monkeypatch.setattr(update_dl.subprocess, "Popen", FakePopen)

        update_dl.run_installer_and_exit(str(installer), silent=False)
        args, _kw = popen_calls[0]
        assert "/SILENT" not in args
        assert "/SP-" in args
        assert "/CLOSEAPPLICATIONS" in args

    def test_popen_failure_does_not_exit(self, tmp_path, monkeypatch):
        installer = tmp_path / "inst.exe"
        installer.write_bytes(b"x" * 4)

        def _raise(*a, **k):
            raise OSError("blocked")
        monkeypatch.setattr(update_dl.subprocess, "Popen", _raise)
        exit_calls = []
        monkeypatch.setattr(update_dl.os, "_exit", lambda c: exit_calls.append(c))

        # Should NOT call os._exit because Popen failed
        update_dl.run_installer_and_exit(str(installer))
        assert exit_calls == []
