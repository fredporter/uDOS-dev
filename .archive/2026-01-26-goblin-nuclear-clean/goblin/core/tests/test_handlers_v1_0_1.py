"""
Extended Command Handler Tests - v1.0.1 Test Coverage

Tests critical command handlers for Stable Alpha release:
- FileHandler (file operations)
- BundleHandler (content packages)
- BackupHandler (backup/restore)
- DatabaseManager (unified database interface)
- UdosMdParser (template parsing)

Run with: pytest core/tests/test_handlers_v1_0_1.py -v
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()

    # Create directory structure
    (workspace / "memory").mkdir()
    (workspace / "memory" / "logs").mkdir()
    (workspace / "memory" / "sandbox").mkdir()
    (workspace / "memory" / "bank").mkdir()
    (workspace / "memory" / "bank" / "user").mkdir()
    (workspace / "memory" / "bank" / "wizard").mkdir()
    (workspace / "memory" / "templates").mkdir()
    (workspace / "memory" / "backup").mkdir()
    (workspace / "knowledge").mkdir()
    (workspace / "knowledge" / "survival").mkdir()

    # Create test files
    (workspace / "test.txt").write_text("Hello, uDOS!")
    (workspace / "test.md").write_text("# Test Document\n\nContent here.")
    (workspace / "data.json").write_text('{"key": "value"}')

    yield workspace

    shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
def mock_grid():
    """Create a mock grid for command execution."""
    grid = MagicMock()
    grid.update_main_content = MagicMock()
    grid.update_status = MagicMock()
    grid.get_current_content = MagicMock(return_value=[])
    return grid


# ============================================================================
# FILE HANDLER TESTS
# ============================================================================


class TestFileHandler:
    """Tests for FileCommandHandler."""

    def test_file_handler_import(self):
        """FileCommandHandler should be importable."""
        from dev.goblin.core.commands.file_handler import FileCommandHandler

        handler = FileCommandHandler()
        assert handler is not None

    def test_file_handler_handle_exists(self):
        """FileCommandHandler should have handle method."""
        from dev.goblin.core.commands.file_handler import FileCommandHandler

        handler = FileCommandHandler()
        assert hasattr(handler, "handle")
        assert callable(handler.handle)

    @pytest.mark.skip(reason="Requires interactive workspace selection")
    def test_new_file_command(self, temp_workspace, mock_grid):
        """NEW command requires interactive workspace selection - skipped in automated tests."""
        pass

    def test_new_command_exists(self):
        """FileCommandHandler should have NEW handling."""
        from dev.goblin.core.commands.file_handler import FileCommandHandler

        handler = FileCommandHandler()
        assert hasattr(handler, "_handle_new")
        assert callable(handler._handle_new)

    def test_show_file_command(self, temp_workspace, mock_grid):
        """SHOW command should display file content."""
        from dev.goblin.core.commands.file_handler import FileCommandHandler

        handler = FileCommandHandler()

        # SHOW command should handle file path
        result = handler.handle("SHOW", [str(temp_workspace / "test.txt")], mock_grid)

        # Should return result (content or error)
        assert result is not None

    def test_unknown_command_handled(self, mock_grid):
        """Unknown commands should return error message."""
        from dev.goblin.core.commands.file_handler import FileCommandHandler

        handler = FileCommandHandler()
        result = handler.handle("NONEXISTENT", [], mock_grid)

        assert result is not None
        assert "error" in str(result).lower() or "unknown" in str(result).lower()


# ============================================================================
# BUNDLE HANDLER TESTS
# ============================================================================


class TestBundleHandler:
    """Tests for BundleHandler."""

    def test_bundle_handler_import(self):
        """BundleHandler should be importable."""
        from dev.goblin.core.commands.bundle_handler import BundleHandler

        handler = BundleHandler()
        assert handler is not None

    def test_bundle_list_command(self, mock_grid):
        """BUNDLE LIST should return bundle list."""
        from dev.goblin.core.commands.bundle_handler import BundleHandler

        handler = BundleHandler()
        result = handler.handle("BUNDLE", ["LIST"], mock_grid)

        assert result is not None

    def test_bundle_empty_command(self, mock_grid):
        """BUNDLE with no params should default to LIST."""
        from dev.goblin.core.commands.bundle_handler import BundleHandler

        handler = BundleHandler()
        result = handler.handle("BUNDLE", [], mock_grid)

        assert result is not None

    def test_bundle_status_command(self, mock_grid):
        """BUNDLE STATUS should return status info."""
        from dev.goblin.core.commands.bundle_handler import BundleHandler

        handler = BundleHandler()
        result = handler.handle("BUNDLE", ["STATUS"], mock_grid)

        assert result is not None


# ============================================================================
# DATABASE MANAGER TESTS
# ============================================================================


class TestDatabaseManager:
    """Tests for DatabaseManager service."""

    def test_database_manager_import(self):
        """DatabaseManager should be importable."""
        from dev.goblin.core.services.database_manager import DatabaseManager

        db = DatabaseManager()
        assert db is not None
        db.close_all()

    def test_database_manager_has_databases(self):
        """DatabaseManager should have all 5 database connections."""
        from dev.goblin.core.services.database_manager import DatabaseManager

        db = DatabaseManager()

        assert hasattr(db, "knowledge")
        assert hasattr(db, "core")
        assert hasattr(db, "contacts")
        assert hasattr(db, "devices")
        assert hasattr(db, "scripts")

        db.close_all()

    def test_database_initialize(self, temp_workspace):
        """DatabaseManager should initialize all schemas."""
        from dev.goblin.core.services.database_manager import DatabaseManager

        db = DatabaseManager(base_path=temp_workspace / "memory" / "bank")
        db.initialize_all()

        # Check databases were created
        assert (temp_workspace / "memory" / "bank" / "knowledge.db").exists()
        assert (temp_workspace / "memory" / "bank" / "core.db").exists()
        assert (temp_workspace / "memory" / "bank" / "user" / "contacts.db").exists()
        assert (temp_workspace / "memory" / "bank" / "wizard" / "devices.db").exists()
        assert (temp_workspace / "memory" / "bank" / "wizard" / "scripts.db").exists()

        db.close_all()

    def test_database_stats(self, temp_workspace):
        """DatabaseManager should return statistics."""
        from dev.goblin.core.services.database_manager import DatabaseManager

        db = DatabaseManager(base_path=temp_workspace / "memory" / "bank")
        db.initialize_all()

        stats = db.stats()

        assert "knowledge" in stats
        assert "core" in stats
        assert "contacts" in stats
        assert "devices" in stats
        assert "scripts" in stats

        db.close_all()

    def test_knowledge_search(self, temp_workspace):
        """Knowledge database should support search."""
        from dev.goblin.core.services.database_manager import DatabaseManager

        db = DatabaseManager(base_path=temp_workspace / "memory" / "bank")
        db.initialize_all()

        # Index a test file
        db.knowledge.index_file(
            "test/water-guide.md",
            {"title": "Water Purification", "tags": ["water", "survival"], "tier": 4},
            "How to purify water in the wild.",
        )

        # Search for it
        results = db.knowledge.search("water")

        assert len(results) > 0
        assert "Water Purification" in results[0]["title"]

        db.close_all()

    def test_device_registry(self, temp_workspace):
        """Devices database should register devices."""
        from dev.goblin.core.services.database_manager import DatabaseManager

        db = DatabaseManager(base_path=temp_workspace / "memory" / "bank")
        db.initialize_all()

        # Register a device
        db.devices.register_device(
            "D1",
            "ESP32-C3",
            firmware_version="1.0.2",
            device_role="node",
            friendly_name="Test Node",
        )

        # Retrieve it
        device = db.devices.get("D1")

        assert device is not None
        assert device["hardware_type"] == "ESP32-C3"
        assert device["friendly_name"] == "Test Node"

        db.close_all()

    def test_context_manager(self, temp_workspace):
        """DatabaseManager should work as context manager."""
        from dev.goblin.core.services.database_manager import DatabaseManager

        with DatabaseManager(base_path=temp_workspace / "memory" / "bank") as db:
            db.initialize_all()
            stats = db.stats()
            assert "knowledge" in stats


# ============================================================================
# UDOS MD PARSER TESTS
# ============================================================================


class TestUdosMdParser:
    """Tests for UdosMdParser template service."""

    def test_parser_import(self):
        """UdosMdParser should be importable."""
        from dev.goblin.core.services.udos_md_parser import UdosMdParser

        parser = UdosMdParser()
        assert parser is not None

    def test_parse_frontmatter(self):
        """Parser should extract YAML frontmatter."""
        from dev.goblin.core.services.udos_md_parser import UdosMdParser

        parser = UdosMdParser()

        content = """---
title: Test Template
type: guide
tags: [test, example]
---

# Test Content

Hello world!
"""

        result = parser.parse(content)

        assert result.frontmatter is not None
        assert result.frontmatter.get("title") == "Test Template"
        assert result.frontmatter.get("type") == "guide"
        assert "test" in result.frontmatter.get("tags", [])

    def test_parse_shortcodes(self):
        """Parser should extract shortcodes."""
        from dev.goblin.core.services.udos_md_parser import UdosMdParser

        parser = UdosMdParser()

        content = """---
title: Test
---

[SPLASH]

Hello, [USER_NAME]!

[SYSTEM_STATUS]
"""

        result = parser.parse(content)

        assert len(result.shortcodes) > 0
        shortcode_names = [s.name for s in result.shortcodes]
        assert "SPLASH" in shortcode_names

    def test_parse_code_blocks(self):
        """Parser should extract code blocks."""
        from dev.goblin.core.services.udos_md_parser import UdosMdParser

        parser = UdosMdParser()

        content = """---
title: Test
---

# Content

```upy @SPLASH
PRINT "Welcome!"
```

```json @config
{"theme": "dark"}
```
"""

        result = parser.parse(content)

        # code_blocks is a Dict keyed by name
        assert len(result.code_blocks) > 0
        assert "SPLASH" in result.code_blocks or any(
            "SPLASH" in k for k in result.code_blocks.keys()
        )

    def test_variable_interpolation(self):
        """Parser should interpolate variables."""
        from dev.goblin.core.services.udos_md_parser import UdosMdParser

        parser = UdosMdParser()

        content = """---
title: Test
---

Hello, $user_name!
"""

        result = parser.parse(content)
        # raw_content contains the content after frontmatter
        rendered = parser.interpolate_variables(
            result.raw_content, {"user_name": "Hero", "$user_name": "Hero"}
        )

        assert "Hero" in rendered

    def test_parse_file(self, temp_workspace):
        """Parser should parse files from disk."""
        from dev.goblin.core.services.udos_md_parser import UdosMdParser

        parser = UdosMdParser()

        # Create test template
        template_file = temp_workspace / "test.udos.md"
        template_file.write_text(
            """---
title: Test Template
type: guide
---

# Welcome

This is a test.
"""
        )

        result = parser.parse_file(template_file)

        assert result is not None
        assert result.frontmatter.get("title") == "Test Template"


# ============================================================================
# BACKUP HANDLER TESTS
# ============================================================================


class TestBackupHandler:
    """Tests for BackupHandler."""

    def test_backup_handler_import(self):
        """BackupHandler should be importable."""
        from dev.goblin.core.commands.backup_handler import BackupHandler

        handler = BackupHandler()
        assert handler is not None

    def test_backup_list_command(self, mock_grid):
        """BACKUP LIST should return backup list."""
        from dev.goblin.core.commands.backup_handler import BackupHandler

        handler = BackupHandler()
        result = handler.handle("BACKUP", ["LIST"], mock_grid)

        assert result is not None


# ============================================================================
# WELLBEING HANDLER TESTS
# ============================================================================


class TestWellbeingHandler:
    """Tests for WellbeingHandler."""

    def test_wellbeing_handler_import(self):
        """WellbeingHandler should be importable."""
        from dev.goblin.core.commands.wellbeing_handler import WellbeingHandler

        handler = WellbeingHandler()
        assert handler is not None

    def test_wellbeing_status_command(self, mock_grid):
        """WELLBEING STATUS should return status."""
        from dev.goblin.core.commands.wellbeing_handler import WellbeingHandler

        handler = WellbeingHandler()
        result = handler.handle("WELLBEING", ["STATUS"], mock_grid)

        assert result is not None


# ============================================================================
# CAPTURE HANDLER TESTS
# ============================================================================


class TestCaptureHandler:
    """Tests for CaptureHandler."""

    def test_capture_handler_import(self):
        """CaptureHandler should be importable."""
        from dev.goblin.core.commands.capture_handler import CaptureHandler

        handler = CaptureHandler()
        assert handler is not None

    def test_capture_help_command(self, mock_grid):
        """CAPTURE HELP should show help."""
        from dev.goblin.core.commands.capture_handler import CaptureHandler

        handler = CaptureHandler()
        result = handler.handle("CAPTURE", ["HELP"], mock_grid)

        assert result is not None


# ============================================================================
# GEOGRAPHY HANDLER TESTS
# ============================================================================


class TestGeographyHandler:
    """Tests for GeographyHandler (v1.0.2.0+ feature)."""

    def test_geography_handler_import(self):
        """GeographyHandler should be importable."""
        from dev.goblin.core.commands.geography_handler import GeographyHandler

        handler = GeographyHandler()
        assert handler is not None

    def test_geography_tile_lookup(self, mock_grid):
        """GEO TILE should perform tile lookup."""
        from dev.goblin.core.commands.geography_handler import GeographyHandler

        handler = GeographyHandler()
        # Pass params as string (as the handler expects)
        result = handler.handle("GEO", "TILE AB34", mock_grid)

        assert result is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestHandlerIntegration:
    """Integration tests across multiple handlers."""

    def test_all_critical_handlers_loadable(self):
        """All critical handlers should be importable."""
        handlers = [
            "core.commands.file_handler.FileCommandHandler",
            "core.commands.bundle_handler.BundleHandler",
            "core.commands.backup_handler.BackupHandler",
            "core.commands.wellbeing_handler.WellbeingHandler",
            "core.commands.capture_handler.CaptureHandler",
            "core.commands.geography_handler.GeographyHandler",
            "core.commands.repair_handler.RepairHandler",
            "core.commands.shakedown_handler.ShakedownHandler",
        ]

        for handler_path in handlers:
            parts = handler_path.rsplit(".", 1)
            module_path, class_name = parts

            try:
                import importlib

                module = importlib.import_module(module_path)
                handler_class = getattr(module, class_name)
                instance = handler_class()
                assert instance is not None
            except Exception as e:
                pytest.fail(f"Failed to load {handler_path}: {e}")

    def test_database_knowledge_integration(self, temp_workspace):
        """Database and knowledge systems should integrate."""
        from dev.goblin.core.services.database_manager import DatabaseManager

        db = DatabaseManager(base_path=temp_workspace / "memory" / "bank")
        db.initialize_all()

        # Create a knowledge file
        knowledge_file = temp_workspace / "knowledge" / "survival" / "water.md"
        knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        knowledge_file.write_text(
            """---
title: Water Purification
tier: 4
tags: [water, survival, purification]
---

# Water Purification

Methods for making water safe to drink.
"""
        )

        # Index it
        db.knowledge.index_file(
            str(knowledge_file.relative_to(temp_workspace)),
            {"title": "Water Purification", "tier": 4, "tags": ["water", "survival"]},
            knowledge_file.read_text(),
        )

        # Search should find it
        results = db.knowledge.search("purification")
        assert len(results) > 0

        db.close_all()


# ============================================================================
# VERSION VALIDATION TESTS
# ============================================================================


class TestVersionValidation:
    """Tests for version file integrity."""

    def test_core_version_valid(self):
        """core/version.json should be valid."""
        version_file = Path(__file__).parent.parent.parent / "version.json"
        if version_file.exists():
            data = json.loads(version_file.read_text())
            assert "component" in data
            assert "version" in data
            assert data["component"] == "core"

    def test_knowledge_version_valid(self):
        """knowledge/version.json should be valid."""
        version_file = (
            Path(__file__).parent.parent.parent.parent / "knowledge" / "version.json"
        )
        if version_file.exists():
            data = json.loads(version_file.read_text())
            assert "component" in data
            assert "version" in data
            assert data["component"] == "knowledge"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
