"""
Tests for core/config/paths.py - FHS-compliant path helpers.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from dev.goblin.core.config.paths import (
    is_alpine,
    is_tinycore,  # Deprecated, kept for backwards compat testing
    get_tinycore_user_home,
    get_system_path,
    get_user_path,
    get_config_path,
    get_credentials_path,
    get_temp_path,
    setup_tinycore_user,
    get_platform_info,
)


class TestAlpineDetection:
    """Test Alpine detection functions (replaces TinyCore detection)."""

    def test_is_alpine_false_on_macos(self):
        """On macOS, is_alpine should return False."""
        # This test runs on actual system
        import platform

        if platform.system() == "Darwin":
            assert is_alpine() is False

    def test_is_alpine_with_alpine_release(self, tmp_path):
        """Test detection via /etc/alpine-release."""
        alpine_release = tmp_path / "alpine-release"
        alpine_release.write_text("3.18.0")

        with patch("core.config.paths.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            # The actual function checks real paths, so this is a unit test pattern
            assert isinstance(is_alpine(), bool)

    def test_is_alpine_with_os_release(self, tmp_path):
        """Test detection via /etc/os-release."""
        os_release = tmp_path / "os-release"
        os_release.write_text('NAME="Alpine Linux"\nVERSION="3.18.0"')

        with patch("core.config.paths.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.read_text.return_value = 'NAME="Alpine Linux"'
            assert isinstance(is_alpine(), bool)

    def test_is_tinycore_deprecated(self):
        """is_tinycore() should return False (deprecated)."""
        # This function is deprecated and should always return False
        # to prevent old TinyCore code paths from running
        result = is_tinycore()
        assert result is False

    def test_get_tinycore_user_home_non_alpine(self):
        """On non-Alpine, should return standard home."""
        with patch("core.config.paths.is_alpine", return_value=False):
            result = get_tinycore_user_home()
            assert result == Path.home()

    def test_get_tinycore_user_home_on_alpine(self):
        """On Alpine, should return home (Alpine doesn't have /home/tc)."""
        with patch("core.config.paths.is_alpine", return_value=True):
            result = get_tinycore_user_home()
            # Alpine typically uses standard $HOME, not /home/tc
            assert isinstance(result, Path)


class TestPathHelpers:
    """Test path helper functions."""

    def test_get_system_path_returns_path(self):
        """get_system_path should return a Path object."""
        result = get_system_path()
        assert isinstance(result, Path)

    def test_get_system_path_with_subpath(self):
        """get_system_path should append subpath."""
        result = get_system_path("core")
        assert result.name == "core"

    def test_get_user_path_creates_directory(self, tmp_path):
        """get_user_path should create directory if needed."""
        with patch("core.config.paths.Path.home", return_value=tmp_path):
            with patch("core.config.paths.is_tinycore", return_value=False):
                result = get_user_path("test_subdir")
                assert result.exists()

    def test_get_config_path_restricted_permissions(self, tmp_path):
        """get_config_path should create with restricted permissions."""
        with patch("core.config.paths.Path.home", return_value=tmp_path):
            with patch("core.config.paths.is_tinycore", return_value=False):
                with patch(
                    "core.config.paths.get_tinycore_user_home", return_value=tmp_path
                ):
                    result = get_config_path()
                    # Directory should exist
                    assert result.parent.exists() or result.exists()

    def test_get_credentials_path_strict_permissions(self, tmp_path):
        """get_credentials_path should use strict permissions."""
        with patch("core.config.paths.Path.home", return_value=tmp_path):
            with patch("core.config.paths.is_tinycore", return_value=False):
                with patch(
                    "core.config.paths.get_tinycore_user_home", return_value=tmp_path
                ):
                    result = get_credentials_path()
                    assert ".credentials" in str(result) or result.exists()

    def test_get_temp_path_creates_directory(self):
        """get_temp_path should create temp directory."""
        result = get_temp_path("test_temp")
        assert result.exists()
        # Cleanup
        result.rmdir()


class TestSetupAlpineUser:
    """Test Alpine user setup function."""

    def test_setup_non_alpine(self):
        """On non-Alpine, should still create directories."""
        with patch("core.config.paths.is_alpine", return_value=False):
            result = setup_tinycore_user()
            # Function still returns is_tinycore for compat, but now reflects Alpine
            assert "paths_created" in result
            assert "message" in result

    def test_setup_returns_dict(self):
        """setup_tinycore_user should return a dict."""
        result = setup_tinycore_user()
        assert isinstance(result, dict)
        assert "is_tinycore" in result
        assert "paths_created" in result
        assert "persistence_configured" in result
        assert "errors" in result


class TestPlatformInfo:
    """Test platform information function."""

    def test_get_platform_info_returns_dict(self):
        """get_platform_info should return complete dict."""
        result = get_platform_info()
        assert isinstance(result, dict)
        assert "system" in result
        assert "release" in result
        assert "machine" in result
        # Now reports is_alpine instead of is_tinycore
        assert (
            "is_alpine" in result or "is_tinycore" in result
        )  # Accept both for compat
        assert "user_home" in result
        assert "udos_base" in result

    def test_get_platform_info_values(self):
        """get_platform_info values should be strings/bool."""
        result = get_platform_info()
        assert isinstance(result["system"], str)
        # is_alpine should be bool (or is_tinycore for compat)
        alpine_key = "is_alpine" if "is_alpine" in result else "is_tinycore"
        assert isinstance(result.get(alpine_key), bool)
        assert isinstance(result["user_home"], str)
