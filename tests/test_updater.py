"""
Unit tests for src/core/updater.py

The updater has two responsibilities:
1. Parse version strings robustly (so "v1.2.0", "1.2.0", "1.2.0-rc1" all
   compare correctly).
2. Hit the GitHub Releases API and return a usable info dict.

We mock the network for the API tests so they run offline.
"""
import json
import pytest
from unittest.mock import patch, MagicMock


# ── version parsing ─────────────────────────────────────────────────


class TestParseVersion:
    def test_simple(self):
        from src.core.updater import _parse_version
        from packaging.version import Version
        assert _parse_version("1.2.0") == Version("1.2.0")

    def test_with_v_prefix(self):
        from src.core.updater import _parse_version
        from packaging.version import Version
        assert _parse_version("v1.2.0") == Version("1.2.0")
        assert _parse_version("V1.2.0") == Version("1.2.0")

    def test_empty(self):
        from src.core.updater import _parse_version
        assert _parse_version("") is None
        assert _parse_version(None) is None

    def test_invalid(self):
        from src.core.updater import _parse_version
        # "abc" cannot be parsed as a version
        assert _parse_version("not-a-version") is None


class TestVersionOrdering:
    """Verify version comparison works the way auto-update expects."""

    def test_newer_is_greater(self):
        from src.core.updater import _parse_version
        a = _parse_version("1.2.0")
        b = _parse_version("1.1.0")
        assert a > b

    def test_patch_bump(self):
        from src.core.updater import _parse_version
        assert _parse_version("1.2.1") > _parse_version("1.2.0")

    def test_minor_bump(self):
        from src.core.updater import _parse_version
        assert _parse_version("1.3.0") > _parse_version("1.2.9")

    def test_major_bump(self):
        from src.core.updater import _parse_version
        assert _parse_version("2.0.0") > _parse_version("1.99.99")

    def test_equal(self):
        from src.core.updater import _parse_version
        assert _parse_version("1.2.0") == _parse_version("v1.2.0")


# ── asset selection ─────────────────────────────────────────────────


class TestPickAssetForPlatform:
    INFO = {
        "assets": [
            {"name": "my-dlp_v1.2.0_installer.exe", "url": "win", "size": 100},
            {"name": "my-dlp_v1.2.0_portable.zip", "url": "any", "size": 100},
            {"name": "my-dlp_v1.2.0_amd64.deb", "url": "deb", "size": 100},
            {"name": "my-dlp_v1.2.0_x86_64.AppImage", "url": "app", "size": 100},
        ]
    }

    def test_windows_prefers_installer(self):
        from src.core.updater import pick_asset_for_platform
        asset = pick_asset_for_platform(self.INFO, "win32")
        assert asset["name"].endswith(".exe")

    def test_linux_prefers_appimage(self):
        from src.core.updater import pick_asset_for_platform
        asset = pick_asset_for_platform(self.INFO, "linux")
        assert asset["name"].endswith(".AppImage")

    def test_empty_assets(self):
        from src.core.updater import pick_asset_for_platform
        assert pick_asset_for_platform({"assets": []}, "win32") is None
        assert pick_asset_for_platform({}, "win32") is None
        assert pick_asset_for_platform(None, "win32") is None


# ── fetch_release_info (mocked network) ─────────────────────────────


class TestFetchReleaseInfo:
    def _mock_response(self, status_code, json_data):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        return resp

    @patch("src.core.updater.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = self._mock_response(200, {
            "tag_name": "v1.2.0",
            "name": "v1.2.0",
            "body": "## Changes\n- bug fix",
            "html_url": "https://github.com/0xjoyo/my-dlp/releases/tag/v1.2.0",
            "prerelease": False,
            "published_at": "2026-06-21T10:00:00Z",
            "assets": [
                {"name": "my-dlp_v1.2.0_installer.exe", "browser_download_url": "https://...", "size": 33000000},
            ],
        })

        from src.core import updater
        info = updater.fetch_release_info()
        assert info is not None
        assert info["latest_version"] == "1.2.0"
        assert info["release_name"] == "v1.2.0"
        assert "bug fix" in info["release_notes"]
        assert len(info["assets"]) == 1
        assert info["prerelease"] is False

    @patch("src.core.updater.requests.get")
    def test_update_available(self, mock_get):
        # The test runner is on a version lower than 1.5.0
        mock_get.return_value = self._mock_response(200, {
            "tag_name": "v1.5.0",
            "name": "v1.5.0",
            "body": "",
            "html_url": "https://github.com/0xjoyo/my-dlp/releases/tag/v1.5.0",
            "assets": [],
        })

        from src.core import updater
        info = updater.fetch_release_info()
        assert info is not None
        # Whether True or False depends on VERSION file but the field exists
        assert "is_update_available" in info
        assert isinstance(info["is_update_available"], bool)

    @patch("src.core.updater.requests.get")
    def test_404_returns_none(self, mock_get):
        mock_get.return_value = self._mock_response(404, {"message": "Not Found"})
        from src.core import updater
        assert updater.fetch_release_info() is None

    @patch("src.core.updater.requests.get")
    def test_invalid_json_returns_none(self, mock_get):
        resp = self._mock_response(200, {"weird": "shape"})
        # has 'tag_name' would have been parsed... let's force a bad JSON
        resp.json.side_effect = ValueError("not json")
        mock_get.return_value = resp
        from src.core import updater
        assert updater.fetch_release_info() is None

    @patch("src.core.updater.requests.get")
    def test_network_error_returns_none(self, mock_get):
        import requests as r
        mock_get.side_effect = r.ConnectionError("no internet")
        from src.core import updater
        assert updater.fetch_release_info() is None


# ── dismiss logic ───────────────────────────────────────────────────


class TestDismissLogic:
    def test_get_dismissed_empty(self, tmp_config_dir):
        from src.core import updater
        # First, ensure config is fresh in this dir
        updater.clear_dismissed_version()
        assert updater.get_dismissed_version() in (None, "")

    def test_set_then_get(self, tmp_config_dir):
        from src.core import updater
        updater.set_dismissed_version("1.5.0")
        assert updater.get_dismissed_version() == "1.5.0"

    def test_clear(self, tmp_config_dir):
        from src.core import updater
        updater.set_dismissed_version("1.5.0")
        updater.clear_dismissed_version()
        assert updater.get_dismissed_version() in (None, "")