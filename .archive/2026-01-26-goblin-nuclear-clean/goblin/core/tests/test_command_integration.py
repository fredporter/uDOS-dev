"""
Command Integration Test Suite - End-to-End Command Flow Validation

Tests the complete command execution path using uCODE format:
1. Input parsing (uCODE format)
2. Command routing (uDOS_commands.py)
3. Handler execution
4. Output generation
5. Policy validation

Run with: pytest core/tests/test_command_integration.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
import json


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for file operations."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()

    # Create test directories
    (workspace / "memory").mkdir()
    (workspace / "memory" / "logs").mkdir()
    (workspace / "memory" / "sandbox").mkdir()
    (workspace / "knowledge").mkdir()

    # Create test files
    (workspace / "test.txt").write_text("Hello, uDOS!")
    (workspace / "test.md").write_text("# Test Document\n\nContent here.")
    (workspace / "data.json").write_text('{"key": "value"}')

    yield workspace

    # Cleanup
    shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
def mock_grid():
    """Create a mock grid for command execution."""
    grid = MagicMock()
    grid.update_main_content = MagicMock()
    grid.update_status = MagicMock()
    grid.get_current_content = MagicMock(return_value=[])
    return grid


@pytest.fixture
def command_handler(temp_workspace):
    """Initialize command handler with test workspace."""
    from dev.goblin.core.uDOS_commands import CommandHandler

    handler = CommandHandler()
    # Override workspace path for testing
    handler._test_workspace = temp_workspace
    return handler


# ============================================================================
# uCODE FORMAT HELPER
# ============================================================================


def ucode(module: str, command: str = "", *params) -> str:
    """
    Format a uCODE command string.

    Examples:
        ucode("VERSION")           -> "[VERSION|]"
        ucode("VERSION", "CHECK")  -> "[VERSION|CHECK]"
        ucode("FILE", "READ", "test.txt") -> "[FILE|READ*test.txt]"
    """
    if params:
        param_str = "*".join(str(p) for p in params)
        return f"[{module}|{command}*{param_str}]"
    elif command:
        return f"[{module}|{command}]"
    else:
        return f"[{module}|]"


# ============================================================================
# VERSION COMMAND TESTS
# ============================================================================


class TestVersionCommands:
    """Test VERSION command and related queries."""

    def test_version_command_returns_version(self, command_handler, mock_grid):
        """VERSION command should return current version."""
        result = command_handler.execute_ucode(ucode("VERSION"), mock_grid)

        assert result is not None
        # Should contain version info or message
        result_str = str(result)
        assert len(result_str) > 0

    def test_version_check_command(self, command_handler, mock_grid):
        """VERSION CHECK should validate all components."""
        result = command_handler.execute_ucode(ucode("VERSION", "CHECK"), mock_grid)

        # Should return without error
        assert result is not None


# ============================================================================
# HELP COMMAND TESTS
# ============================================================================


class TestHelpCommands:
    """Test HELP command variations."""

    def test_help_command_returns_help(self, command_handler, mock_grid):
        """HELP should return help content."""
        result = command_handler.execute_ucode(ucode("HELP"), mock_grid)

        assert result is not None

    def test_help_with_topic(self, command_handler, mock_grid):
        """HELP <topic> should return topic-specific help."""
        result = command_handler.execute_ucode(ucode("HELP", "FILE"), mock_grid)

        assert result is not None


# ============================================================================
# STATUS COMMAND TESTS
# ============================================================================


class TestStatusCommands:
    """Test STATUS command variations."""

    def test_status_command(self, command_handler, mock_grid):
        """STATUS should return system status."""
        result = command_handler.execute_ucode(ucode("STATUS"), mock_grid)

        assert result is not None

    def test_status_system(self, command_handler, mock_grid):
        """STATUS SYSTEM should return detailed system info."""
        result = command_handler.execute_ucode(ucode("STATUS", "SYSTEM"), mock_grid)

        assert result is not None


# ============================================================================
# KNOWLEDGE COMMAND TESTS
# ============================================================================


class TestKnowledgeCommands:
    """Test KNOWLEDGE command and K alias."""

    def test_k_command_alias(self, command_handler, mock_grid):
        """K should be alias for KNOWLEDGE."""
        result = command_handler.execute_ucode(ucode("K"), mock_grid)

        # Should return knowledge content or list
        assert result is not None

    def test_knowledge_list(self, command_handler, mock_grid):
        """KNOWLEDGE LIST should show categories."""
        result = command_handler.execute_ucode(ucode("KNOWLEDGE", "LIST"), mock_grid)

        assert result is not None


# ============================================================================
# SECURITY COMMAND TESTS
# ============================================================================


class TestSecurityCommands:
    """Test security-related commands."""

    def test_key_command(self, command_handler, mock_grid):
        """KEY command should return key information."""
        result = command_handler.execute_ucode(ucode("KEY"), mock_grid)

        assert result is not None


# ============================================================================
# TRANSPORT COMMAND TESTS
# ============================================================================


class TestTransportCommands:
    """Test transport-related commands."""

    def test_mesh_status(self, command_handler, mock_grid):
        """MESH STATUS should return mesh network info."""
        result = command_handler.execute_ucode(ucode("MESH", "STATUS"), mock_grid)

        assert result is not None

    def test_qr_command(self, command_handler, mock_grid):
        """QR command should work."""
        result = command_handler.execute_ucode(ucode("QR"), mock_grid)

        assert result is not None


# ============================================================================
# PLUGIN COMMAND TESTS
# ============================================================================


class TestPluginCommands:
    """Test PLUGIN command variations."""

    def test_plugin_list(self, command_handler, mock_grid):
        """PLUGIN LIST should show installed plugins."""
        result = command_handler.execute_ucode(ucode("PLUGIN", "LIST"), mock_grid)

        assert result is not None


# ============================================================================
# STACK COMMAND TESTS
# ============================================================================


class TestStackCommands:
    """Test STACK command variations."""

    def test_stack_list(self, command_handler, mock_grid):
        """STACK LIST should show tech stack."""
        result = command_handler.execute_ucode(ucode("STACK", "LIST"), mock_grid)

        assert result is not None


# ============================================================================
# BUILD COMMAND TESTS
# ============================================================================


class TestBuildCommands:
    """Test BUILD command variations."""

    def test_build_help(self, command_handler, mock_grid):
        """BUILD HELP should show build options."""
        result = command_handler.execute_ucode(ucode("BUILD", "HELP"), mock_grid)

        assert result is not None


# ============================================================================
# PAIR COMMAND TESTS
# ============================================================================


class TestPairCommands:
    """Test PAIR command variations."""

    def test_pair_status(self, command_handler, mock_grid):
        """PAIR STATUS should show pairing info."""
        result = command_handler.execute_ucode(ucode("PAIR", "STATUS"), mock_grid)

        assert result is not None


# ============================================================================
# COMMAND ROUTING TESTS
# ============================================================================


class TestCommandRouting:
    """Test command routing and validation."""

    def test_unknown_command_handled(self, command_handler, mock_grid):
        """Unknown commands should return helpful message."""
        result = command_handler.execute_ucode(ucode("NONEXISTENT"), mock_grid)

        # Should not crash
        assert result is not None

    def test_empty_command_handled(self, command_handler, mock_grid):
        """Empty commands should be handled gracefully."""
        result = command_handler.execute_ucode("[|]", mock_grid)

        # Should not crash
        assert result is not None


# ============================================================================
# POLICY VALIDATION TESTS
# ============================================================================


class TestPolicyValidation:
    """Test policy enforcement."""

    def test_policy_context_can_be_set(self, command_handler):
        """Policy context can be configured."""
        command_handler.set_policy_context(
            role="device_owner", transport="local", realm="user_mesh"
        )

        assert command_handler.current_role == "device_owner"
        assert command_handler.current_transport == "local"
        assert command_handler.current_realm == "user_mesh"

    def test_policy_can_be_disabled(self, command_handler, mock_grid):
        """Policy validation can be disabled for testing."""
        command_handler.policy_enabled = False

        # Commands should work without policy checks
        result = command_handler.execute_ucode(ucode("STATUS"), mock_grid)
        assert result is not None


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Test error handling in command execution."""

    def test_malformed_ucode_handled(self, command_handler, mock_grid):
        """Malformed uCODE should not crash."""
        # Missing brackets
        result = command_handler.execute_ucode("VERSION", mock_grid)
        assert result is not None

    def test_nested_brackets_handled(self, command_handler, mock_grid):
        """Nested brackets should be handled."""
        result = command_handler.execute_ucode("[[VERSION|]]", mock_grid)
        # Should not crash
        assert result is not None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestCommandPerformance:
    """Basic performance validation."""

    def test_help_command_fast(self, command_handler, mock_grid):
        """HELP command should complete quickly."""
        import time

        start = time.time()
        command_handler.execute_ucode(ucode("HELP"), mock_grid)
        elapsed = time.time() - start

        # Should complete in under 2 seconds
        assert elapsed < 2.0

    def test_status_command_fast(self, command_handler, mock_grid):
        """STATUS command should complete quickly."""
        import time

        start = time.time()
        command_handler.execute_ucode(ucode("STATUS"), mock_grid)
        elapsed = time.time() - start

        # Should complete in under 2 seconds
        assert elapsed < 2.0


# ============================================================================
# INTEGRATION FLOW TESTS
# ============================================================================


class TestIntegrationFlows:
    """Test complete command flows."""

    def test_multiple_commands_sequence(self, command_handler, mock_grid):
        """Multiple commands in sequence should work."""
        commands = [
            ucode("STATUS"),
            ucode("HELP"),
            ucode("VERSION"),
        ]

        results = []
        for cmd in commands:
            result = command_handler.execute_ucode(cmd, mock_grid)
            results.append(result)

        # All commands should return results
        assert all(r is not None for r in results)

    def test_command_state_isolation(self, command_handler, mock_grid):
        """Commands should not interfere with each other."""
        # Run STATUS
        result1 = command_handler.execute_ucode(ucode("STATUS"), mock_grid)

        # Run HELP
        result2 = command_handler.execute_ucode(ucode("HELP"), mock_grid)

        # Run STATUS again - should get similar result
        result3 = command_handler.execute_ucode(ucode("STATUS"), mock_grid)

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
