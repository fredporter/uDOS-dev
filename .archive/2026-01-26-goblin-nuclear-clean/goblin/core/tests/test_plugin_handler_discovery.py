"""
Tests for Plugin Handler Discovery Integration (v1.1.0+)

Tests the integration of PluginDiscovery system into the existing PluginHandler.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the handler
from dev.goblin.core.commands.plugin_handler import PluginHandler


class TestPluginHandlerDiscovery:
    """Test Plugin Handler with Discovery Integration"""

    @pytest.fixture
    def mock_discovery(self):
        """Mock PluginDiscovery instance"""
        discovery = Mock()
        discovery.discover_all = Mock(
            return_value={
                "api": Mock(name="api", version="1.1.0", tier="ucode"),
                "transport": Mock(name="transport", version="1.0.1", tier="ucode"),
                "meshcore": Mock(name="meshcore", version="1.0.0", tier="ucode"),
            }
        )
        discovery.get_plugin = Mock(
            return_value=Mock(
                name="api", version="1.1.0", dependencies=["core", "transport"]
            )
        )
        discovery.get_dependencies = Mock(return_value=["core", "transport"])
        discovery.get_dependents = Mock(return_value=["wizard"])
        discovery.validate_dependencies = Mock(return_value={})
        discovery.format_plugin_list = Mock(return_value="Plugin list output")
        discovery.save_registry = Mock()
        discovery.plugins = {"api": Mock(), "transport": Mock()}
        return discovery

    @pytest.fixture
    def handler(self, mock_discovery):
        """Create handler with mocked discovery"""
        handler = PluginHandler(viewport=None, logger=Mock())
        handler.discovery = mock_discovery
        return handler

    def test_scan_plugins_basic(self, handler, mock_discovery):
        """Test PLUGIN SCAN command"""
        result = handler.handle_command(["SCAN"])

        assert "Plugin list output" in result
        mock_discovery.discover_all.assert_called_once()
        mock_discovery.save_registry.assert_called_once()

    def test_scan_plugins_with_save_path(self, handler, mock_discovery):
        """Test PLUGIN SCAN with custom save path"""
        result = handler.handle_command(["SCAN", "--save", "/tmp/registry.json"])

        mock_discovery.discover_all.assert_called_once()
        # Should call save_registry with the custom path
        assert mock_discovery.save_registry.called

    def test_deps_forward(self, handler, mock_discovery):
        """Test PLUGIN DEPS showing forward dependencies"""
        result = handler.handle_command(["DEPS", "api"])

        assert "Dependencies for 'api'" in result
        assert "core" in result or "transport" in result
        mock_discovery.get_plugin.assert_called_with("api")
        mock_discovery.get_dependencies.assert_called()

    def test_deps_recursive(self, handler, mock_discovery):
        """Test PLUGIN DEPS with --recursive flag"""
        result = handler.handle_command(["DEPS", "api", "--recursive"])

        assert "Dependencies for 'api'" in result
        mock_discovery.get_dependencies.assert_called()
        # Check that recursive=True was passed
        call_args = mock_discovery.get_dependencies.call_args
        if call_args and len(call_args) > 1:
            assert call_args[1].get("recursive") == True or call_args[0][1] == True

    def test_deps_reverse(self, handler, mock_discovery):
        """Test PLUGIN DEPS with --reverse flag"""
        result = handler.handle_command(["DEPS", "api", "--reverse"])

        assert "depending on 'api'" in result
        mock_discovery.get_dependents.assert_called_with("api")

    def test_deps_missing_plugin(self, handler, mock_discovery):
        """Test PLUGIN DEPS with non-existent plugin"""
        mock_discovery.get_plugin.return_value = None

        result = handler.handle_command(["DEPS", "nonexistent"])

        assert "not found" in result.lower()

    def test_deps_missing_name(self, handler):
        """Test PLUGIN DEPS without plugin name"""
        result = handler.handle_command(["DEPS"])

        assert "Usage:" in result

    def test_validate_all_ok(self, handler, mock_discovery):
        """Test PLUGIN VALIDATE with all deps satisfied"""
        mock_discovery.validate_dependencies.return_value = {}

        result = handler.handle_command(["VALIDATE"])

        assert "✅" in result
        assert "satisfied" in result.lower()
        mock_discovery.validate_dependencies.assert_called_once()

    def test_validate_missing_deps(self, handler, mock_discovery):
        """Test PLUGIN VALIDATE with missing dependencies"""
        mock_discovery.validate_dependencies.return_value = {
            "api": ["missing_plugin"],
            "wizard": ["another_missing"],
        }

        result = handler.handle_command(["VALIDATE"])

        assert "❌" in result
        assert "api" in result
        assert "missing_plugin" in result
        assert "wizard" in result

    def test_discovery_not_available(self):
        """Test commands when discovery system not available"""
        handler = PluginHandler(viewport=None, logger=Mock())
        handler.discovery = None

        result_scan = handler.handle_command(["SCAN"])
        result_deps = handler.handle_command(["DEPS", "api"])
        result_validate = handler.handle_command(["VALIDATE"])

        assert "not available" in result_scan.lower()
        assert "not available" in result_deps.lower()
        assert "not available" in result_validate.lower()

    def test_help_includes_discovery(self, handler):
        """Test that HELP shows discovery commands"""
        result = handler.handle_command(["HELP"])

        assert "SCAN" in result
        assert "DEPS" in result
        assert "VALIDATE" in result
        assert "PLUGIN DISCOVERY" in result or "v1.1.0" in result

    def test_help_no_params(self, handler):
        """Test HELP with no parameters"""
        result = handler.handle_command([])

        assert "PLUGIN COMMAND HELP" in result

    def test_error_handling_scan(self, handler, mock_discovery):
        """Test error handling in PLUGIN SCAN"""
        mock_discovery.discover_all.side_effect = Exception("Test error")

        result = handler.handle_command(["SCAN"])

        assert "❌" in result
        assert "failed" in result.lower()

    def test_error_handling_deps(self, handler, mock_discovery):
        """Test error handling in PLUGIN DEPS"""
        mock_discovery.get_plugin.side_effect = Exception("Test error")

        result = handler.handle_command(["DEPS", "api"])

        assert "❌" in result or "Could not" in result

    def test_error_handling_validate(self, handler, mock_discovery):
        """Test error handling in PLUGIN VALIDATE"""
        mock_discovery.validate_dependencies.side_effect = Exception("Test error")

        result = handler.handle_command(["VALIDATE"])

        assert "❌" in result
        assert "failed" in result.lower()


class TestPluginHandlerBackwardCompatibility:
    """Ensure existing container commands still work"""

    @pytest.fixture
    def handler(self):
        """Create handler"""
        return PluginHandler(viewport=None, logger=Mock())

    def test_list_command_still_works(self, handler):
        """Test that PLUGIN LIST still works for containers"""
        result = handler.handle_command(["LIST"])

        # Should not error out
        assert isinstance(result, str)
        # Should mention containers or plugins
        assert len(result) > 0

    def test_help_command_still_works(self, handler):
        """Test that PLUGIN HELP still works"""
        result = handler.handle_command(["HELP"])

        assert "PLUGIN COMMAND HELP" in result

    def test_unknown_command_shows_help(self, handler):
        """Test that unknown commands show help"""
        result = handler.handle_command(["INVALID_COMMAND"])

        assert "Unknown subcommand" in result or "HELP" in result


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
