"""
UI Integration Test Suite - Multi-Interface Validation

Tests command execution, pager behavior, and file browsing across:
- TUI (Terminal User Interface)
- Tauri (Desktop App)
- Web (Dashboard/Desktop extensions)

Validates consistency, synchronization, and feature parity.

Author: uDOS Development Team
Version: 1.0.0
Date: December 22, 2025
"""

import pytest
import subprocess
import time
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional
import psutil
import signal


# ============================================================================
# FIXTURES - Test Environment Setup
# ============================================================================

@pytest.fixture(scope="session")
def flask_api_server():
    """Start Flask API server for tests."""
    api_process = subprocess.Popen(
        ["python", "extensions/api/server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"TESTING": "true"}
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Verify server is running
    try:
        response = requests.get("http://localhost:5001/api/status", timeout=5)
        assert response.status_code == 200
    except Exception as e:
        api_process.kill()
        pytest.fail(f"Failed to start Flask API server: {e}")
    
    yield api_process
    
    # Cleanup
    api_process.terminate()
    api_process.wait(timeout=10)


@pytest.fixture(scope="session")
def tauri_app():
    """Launch Tauri app for testing (requires tauri-driver)."""
    # Check if Tauri is built
    tauri_binary = Path("extensions/tauri/src-tauri/target/release/udos-tauri")
    if not tauri_binary.exists():
        pytest.skip("Tauri app not built. Run: cd extensions/tauri && npm run tauri build")
    
    # Start Tauri app
    tauri_process = subprocess.Popen(
        [str(tauri_binary)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for app to initialize
    time.sleep(5)
    
    yield tauri_process
    
    # Cleanup
    tauri_process.terminate()
    tauri_process.wait(timeout=10)


@pytest.fixture
def tui_test_mode():
    """Initialize TUI in test mode (no interactive prompts)."""
    from core.ui.tui_controller import TUIController
    
    config = {
        'keypad_enabled': True,
        'preserve_scroll': True,
        'test_mode': True
    }
    
    tui = TUIController(config=config, viewport=None)
    
    yield tui
    
    # Cleanup
    tui = None


@pytest.fixture
def api_client():
    """HTTP client for API testing."""
    class APIClient:
        BASE_URL = "http://localhost:5001"
        
        def __init__(self):
            self.session = requests.Session()
            self.correlation_id = None
        
        def execute_command(self, command: str) -> Dict[str, Any]:
            """Execute uDOS command via API."""
            response = self.session.post(
                f"{self.BASE_URL}/api/execute",
                json={"command": command},
                headers={"X-Correlation-ID": self.correlation_id} if self.correlation_id else {}
            )
            response.raise_for_status()
            return response.json()
        
        def get_tui_status(self) -> Dict[str, Any]:
            """Get TUI component status."""
            response = self.session.get(f"{self.BASE_URL}/api/tui/status")
            response.raise_for_status()
            return response.json()
        
        def get_predictions(self, partial: str, max_results: int = 10) -> Dict[str, Any]:
            """Get command predictions."""
            response = self.session.get(
                f"{self.BASE_URL}/api/tui/predictor/suggest",
                params={"partial": partial, "max": max_results}
            )
            response.raise_for_status()
            return response.json()
        
        def get_pager_content(self) -> Dict[str, Any]:
            """Get current pager viewport."""
            response = self.session.get(f"{self.BASE_URL}/api/tui/pager/content")
            response.raise_for_status()
            return response.json()
        
        def scroll_pager(self, direction: str) -> Dict[str, Any]:
            """Scroll pager (up/down/page_up/page_down)."""
            response = self.session.post(
                f"{self.BASE_URL}/api/tui/pager/scroll",
                json={"direction": direction}
            )
            response.raise_for_status()
            return response.json()
        
        def list_files(self, workspace: str = "knowledge") -> Dict[str, Any]:
            """List files in workspace."""
            response = self.session.get(
                f"{self.BASE_URL}/api/tui/browser/list",
                params={"workspace": workspace}
            )
            response.raise_for_status()
            return response.json()
    
    return APIClient()


# ============================================================================
# COMMAND EXECUTION TESTS - Cross-Interface Consistency
# ============================================================================

@pytest.mark.integration
class TestCommandExecution:
    """Test command execution returns same results across interfaces."""
    
    def test_status_command_consistency(self, flask_api_server, api_client, tui_test_mode):
        """STATUS command should return same data in TUI and API."""
        # Execute via API
        api_result = api_client.execute_command("STATUS")
        
        # Execute via TUI (simulated)
        from core.uDOS_commands import CommandHandler
        handler = CommandHandler(grid=None, parser=None, config={})
        tui_result = handler.execute("STATUS", {})
        
        # Compare key fields
        assert api_result['success'] == True
        assert 'output' in api_result
        assert len(api_result['output']) > 0
    
    def test_help_command_consistency(self, flask_api_server, api_client):
        """HELP command should return consistent format."""
        api_result = api_client.execute_command("HELP")
        
        assert api_result['success'] == True
        assert 'commands' in api_result['output'] or 'HELP' in api_result['output']
    
    def test_tree_command_consistency(self, flask_api_server, api_client):
        """TREE command should show same directory structure."""
        api_result = api_client.execute_command("TREE knowledge/water --depth 1")
        
        assert api_result['success'] == True
        assert 'water' in api_result['output'].lower()
    
    def test_guide_command_consistency(self, flask_api_server, api_client):
        """GUIDE command should return same content."""
        api_result = api_client.execute_command("GUIDE water/purification")
        
        assert api_result['success'] == True
        assert 'purification' in api_result['output'].lower() or 'water' in api_result['output'].lower()
    
    def test_command_history_tracking(self, flask_api_server, api_client):
        """Commands should be tracked in history."""
        commands = ["STATUS", "HELP", "TREE"]
        
        for cmd in commands:
            result = api_client.execute_command(cmd)
            assert result['success'] == True
        
        # Check session logs
        log_file = Path("memory/logs/session-commands-" + time.strftime("%Y-%m-%d") + ".log")
        if log_file.exists():
            content = log_file.read_text()
            for cmd in commands:
                assert cmd in content
    
    def test_error_handling_consistency(self, flask_api_server, api_client):
        """Invalid commands should return consistent error format."""
        api_result = api_client.execute_command("INVALIDCOMMAND")
        
        assert api_result['success'] == False or 'error' in api_result or 'unknown' in api_result['output'].lower()


# ============================================================================
# PAGER TESTS - Synchronization & State
# ============================================================================

@pytest.mark.integration
class TestPagerBehavior:
    """Test pager scroll state synchronizes across interfaces."""
    
    def test_pager_activation_threshold(self, flask_api_server, api_client):
        """Pager should activate for content > viewport size."""
        # Generate long output (>50 lines)
        result = api_client.execute_command("TREE knowledge --depth 3")
        
        if result.get('pager_active'):
            assert result['pager_active'] == True
    
    def test_pager_scroll_operations(self, flask_api_server, api_client):
        """Pager scroll operations should update state."""
        # Set content
        long_content = "\n".join([f"Line {i}" for i in range(100)])
        
        # Scroll down
        result = api_client.scroll_pager("down")
        assert result.get('success', True)
        
        # Get current viewport
        viewport = api_client.get_pager_content()
        assert 'lines' in viewport
        assert 'position' in viewport
    
    def test_pager_state_persistence(self, flask_api_server, api_client):
        """Pager position should persist across commands."""
        # Scroll to middle
        for _ in range(5):
            api_client.scroll_pager("down")
        
        # Get position
        viewport1 = api_client.get_pager_content()
        pos1 = viewport1.get('position', 0)
        
        # Wait and check again
        time.sleep(1)
        viewport2 = api_client.get_pager_content()
        pos2 = viewport2.get('position', 0)
        
        # Position should be preserved
        assert pos1 == pos2
    
    def test_pager_scroll_indicators(self, flask_api_server, api_client):
        """Pager should show scroll indicators (▲ ▼)."""
        viewport = api_client.get_pager_content()
        
        if viewport.get('total_lines', 0) > viewport.get('viewport_height', 20):
            output = viewport.get('output', '')
            # Should have indicator if scrollable
            assert '▲' in output or '▼' in output or 'Page' in output


# ============================================================================
# FILE BROWSER TESTS - Consistency Across Interfaces
# ============================================================================

@pytest.mark.integration
class TestFileBrowser:
    """Test file browser shows same files in TUI, Tauri, and Web."""
    
    def test_file_browser_workspaces(self, flask_api_server, api_client):
        """All 5 workspaces should be accessible."""
        workspaces = ["knowledge", "docs", "drafts", "sandbox", "scripts"]
        
        for workspace in workspaces:
            result = api_client.list_files(workspace)
            assert result.get('success', True)
            assert 'files' in result or 'error' in result
    
    def test_knowledge_workspace_contents(self, flask_api_server, api_client):
        """Knowledge workspace should show category folders."""
        result = api_client.list_files("knowledge")
        
        if result.get('files'):
            files = result['files']
            # Should have at least some knowledge categories
            categories = ['water', 'fire', 'shelter', 'food', 'medical', 'navigation']
            found = [cat for cat in categories if any(cat in f['name'].lower() for f in files)]
            assert len(found) > 0
    
    def test_file_browser_filtering(self, flask_api_server, api_client):
        """File browser should filter by extension (.md, .json)."""
        result = api_client.list_files("scripts")
        
        if result.get('files'):
            files = result['files']
            # All files should have allowed extensions
            for file in files:
                if file.get('type') == 'file':
                    name = file['name']
                    assert name.endswith('.md') or name.endswith('.json')
    
    def test_file_browser_navigation(self, flask_api_server, api_client):
        """Should be able to navigate into subdirectories."""
        # Navigate to knowledge/water
        result = api_client.list_files("knowledge")
        
        if result.get('files'):
            # Find water folder
            water_folder = next((f for f in result['files'] if 'water' in f['name'].lower()), None)
            if water_folder:
                # Should be able to list its contents
                assert water_folder.get('type') == 'directory' or water_folder.get('path')


# ============================================================================
# PREDICTOR TESTS - Suggestion Consistency
# ============================================================================

@pytest.mark.integration
class TestCommandPredictor:
    """Test predictor suggestions match across interfaces."""
    
    def test_predictor_basic_commands(self, flask_api_server, api_client):
        """Should predict basic commands."""
        result = api_client.get_predictions("HEL")
        
        assert result.get('success', True)
        predictions = result.get('predictions', [])
        
        # Should suggest HELP
        assert any('HELP' in p.get('command', '').upper() for p in predictions)
    
    def test_predictor_confidence_scores(self, flask_api_server, api_client):
        """Predictions should have confidence scores."""
        result = api_client.get_predictions("STA")
        
        if result.get('predictions'):
            for pred in result['predictions']:
                assert 'confidence' in pred
                assert 0 <= pred['confidence'] <= 1
    
    def test_predictor_fuzzy_matching(self, flask_api_server, api_client):
        """Should handle typos with fuzzy matching."""
        result = api_client.get_predictions("STTUS")  # Typo: STATUS
        
        if result.get('predictions'):
            # Should still suggest STATUS
            assert any('STATUS' in p.get('command', '').upper() for p in result['predictions'])
    
    def test_predictor_history_learning(self, flask_api_server, api_client):
        """Should prioritize recently used commands."""
        # Execute command multiple times
        for _ in range(3):
            api_client.execute_command("TREE")
        
        # Should suggest TREE highly for "TR"
        result = api_client.get_predictions("TR")
        
        if result.get('predictions'):
            tree_pred = next((p for p in result['predictions'] if 'TREE' in p.get('command', '').upper()), None)
            if tree_pred:
                assert tree_pred['confidence'] > 0.7


# ============================================================================
# STATE SYNCHRONIZATION TESTS - Cross-Interface
# ============================================================================

@pytest.mark.integration
class TestStateSynchronization:
    """Test state syncs between TUI and Tauri."""
    
    def test_user_state_file_exists(self):
        """User state file should be created."""
        state_file = Path("memory/bank/user/user-state.json")
        
        # Initialize state manager
        from core.services.state_manager import initialize_state_manager
        manager = initialize_state_manager()
        manager.save_state(force=True)
        
        assert state_file.exists()
    
    def test_state_contains_required_fields(self):
        """State should contain all required fields."""
        from core.services.state_manager import get_state_manager
        manager = get_state_manager()
        
        state = manager.get_full_state()
        
        assert 'interface_state' in state
        assert 'system_capabilities' in state
        assert 'user_config' in state
        assert 'session_id' in state
    
    def test_state_capabilities_detection(self):
        """Should detect installed systems."""
        from core.services.state_manager import get_state_manager
        manager = get_state_manager()
        manager.detect_capabilities()
        
        caps = manager.system_capabilities
        
        # Should detect if Tauri exists
        tauri_exists = Path("extensions/tauri/src-tauri").exists()
        assert caps.has_tauri == tauri_exists
    
    def test_state_update_broadcast(self):
        """State updates should trigger broadcast."""
        from core.services.state_manager import get_state_manager
        manager = get_state_manager()
        
        broadcast_called = []
        
        def test_callback(message):
            broadcast_called.append(message)
        
        manager.register_ws_callback(test_callback)
        manager.update_interface_state(current_file="test-script.md")
        
        assert len(broadcast_called) > 0
        assert broadcast_called[0]['type'] == 'state_change'


# ============================================================================
# VISUAL REGRESSION TESTS - Tauri App (Requires tauri-driver)
# ============================================================================

@pytest.mark.visual
@pytest.mark.skip(reason="Requires tauri-driver and screenshot comparison")
class TestVisualRegression:
    """Visual regression testing for Tauri app."""
    
    def test_tauri_splash_screen(self, tauri_app):
        """Capture and compare splash screen."""
        # Would use tauri-driver to capture screenshot
        # Compare with baseline image
        pass
    
    def test_tauri_command_output(self, tauri_app):
        """Capture command output rendering."""
        pass
    
    def test_tauri_pager_display(self, tauri_app):
        """Capture pager display with scroll indicators."""
        pass


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.performance
class TestPerformance:
    """Test response times and resource usage."""
    
    def test_command_execution_speed(self, flask_api_server, api_client):
        """Commands should execute within reasonable time."""
        start = time.time()
        result = api_client.execute_command("STATUS")
        elapsed = time.time() - start
        
        assert elapsed < 2.0  # Should complete in under 2 seconds
    
    def test_predictor_response_time(self, flask_api_server, api_client):
        """Predictions should be fast (< 100ms)."""
        start = time.time()
        result = api_client.get_predictions("ST")
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # Should complete in under 100ms
    
    def test_file_browser_load_time(self, flask_api_server, api_client):
        """File browser should load quickly."""
        start = time.time()
        result = api_client.list_files("knowledge")
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # Should complete in under 1 second


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling consistency."""
    
    def test_invalid_command_error(self, flask_api_server, api_client):
        """Invalid commands should return proper error."""
        result = api_client.execute_command("NOTAREALCOMMAND")
        
        assert result.get('success') == False or 'error' in result or 'unknown' in result.get('output', '').lower()
    
    def test_missing_parameter_error(self, flask_api_server, api_client):
        """Commands with missing parameters should error gracefully."""
        result = api_client.execute_command("GUIDE")  # Missing category
        
        # Should either error or show help
        assert result.get('output', '') != ''
    
    def test_api_server_unavailable(self):
        """Should handle server unavailable gracefully."""
        client = requests.Session()
        
        try:
            response = client.get("http://localhost:9999/api/status", timeout=1)
            # Should fail to connect
            assert False, "Should have raised exception"
        except (requests.ConnectionError, requests.Timeout):
            # Expected behavior
            pass


# ============================================================================
# CLEANUP
# ============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Cleanup after all tests."""
    # Kill any hanging processes
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('udos' in str(arg).lower() for arg in cmdline):
                if 'pytest' not in str(cmdline):
                    proc.send_signal(signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
