#!/usr/bin/env python3
"""
uDOS v1.2.30 Modular Services Integration Tests

Tests all shared services created in v1.2.30:
- FilePickerService
- MenuService
- PredictorService
- DebugPanelService
- WebSocketStreamingService
- UnifiedPager

Run: python dev/test_modular_services.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test results tracking
results = []
passed = 0
failed = 0


def test(name: str, condition: bool, details: str = ""):
    """Record test result"""
    global passed, failed
    if condition:
        passed += 1
        status = "✅ PASS"
    else:
        failed += 1
        status = "❌ FAIL"
    
    result = f"{status}: {name}"
    if details and not condition:
        result += f" ({details})"
    results.append(result)
    print(result, flush=True)


def section(name: str):
    """Print section header"""
    print(f"\n{'='*60}", flush=True)
    print(f"  {name}", flush=True)
    print(f"{'='*60}", flush=True)


# ============================================================================
# FILE PICKER SERVICE TESTS
# ============================================================================

def test_file_picker_service():
    """Test FilePickerService"""
    section("FilePickerService Tests")
    
    try:
        from core.services.file_picker_service import (
            FilePickerService, Workspace, FileEntry, get_file_picker_service
        )
        test("Import FilePickerService", True)
    except ImportError as e:
        test("Import FilePickerService", False, str(e))
        return
    
    # Singleton
    service1 = get_file_picker_service()
    service2 = get_file_picker_service()
    test("Singleton pattern", service1 is service2)
    
    # Workspaces
    test("Has 5 workspaces", len(Workspace) == 5)
    test("KNOWLEDGE workspace exists", hasattr(Workspace, 'KNOWLEDGE'))
    test("SCRIPTS workspace exists", hasattr(Workspace, 'SCRIPTS'))
    
    # Set workspace
    service1.set_workspace(Workspace.KNOWLEDGE)
    test("Set workspace to KNOWLEDGE", service1.state.workspace == Workspace.KNOWLEDGE)
    
    # Navigate
    service1.navigate_to("")
    test("Navigate to root", service1.state.current_path is not None)
    
    # List entries via state
    entries = service1.state.entries
    test("State entries is list", isinstance(entries, list))
    
    # Get state
    state = service1.get_state_dict()
    test("Get state returns dict", isinstance(state, dict))
    test("State has workspace key", 'workspace' in state)
    
    # API methods
    api_list = service1.list_directory()
    test("API list_directory returns dict", isinstance(api_list, dict))
    test("API list_directory has files", 'files' in api_list)
    
    # Search (may return empty if no files match)
    search_results = service1.search("water")
    test("Search returns list", isinstance(search_results, list))


# ============================================================================
# MENU SERVICE TESTS
# ============================================================================

def test_menu_service():
    """Test MenuService"""
    section("MenuService Tests")
    
    try:
        from core.services.menu_service import (
            MenuService, MenuItem, MenuDefinition, MenuItemType, get_menu_service
        )
        test("Import MenuService", True)
    except ImportError as e:
        test("Import MenuService", False, str(e))
        return
    
    # Singleton
    service1 = get_menu_service()
    service2 = get_menu_service()
    test("Singleton pattern", service1 is service2)
    
    # Menus loaded
    test("Has menus", len(service1.menus) > 0)
    test("Has 6 menus", len(service1.menus) == 6)
    
    # Get menu
    file_menu = service1.get_menu('file')
    test("Get file menu", file_menu is not None)
    test("File menu has items", len(file_menu.items) > 0 if file_menu else False)
    
    # Menu bar
    menu_bar = service1.get_menu_bar()
    test("Get menu bar", len(menu_bar) > 0)
    test("Menu bar has file", any(m.id == 'file' for m in menu_bar))
    
    # Get menu item
    new_item = service1.get_menu_item('file', 'new')
    test("Get menu item 'new'", new_item is not None)
    
    # Execute action
    result = service1.execute_action('about')  # Safe action
    test("Execute action returns", result is not None or result is None)  # Just test it doesn't crash
    
    # Open/close menu
    service1.open_menu('file')
    test("Open menu sets active", service1.active_menu == 'file')
    service1.close_menu()
    test("Close menu clears active", service1.active_menu is None)
    
    # Menu HTML
    html = service1.get_menu_html('file')
    test("Get menu HTML", html is not None and len(html) > 0)
    
    # To dict
    state_dict = service1.to_dict()
    test("to_dict returns dict", isinstance(state_dict, dict))
    test("to_dict has menus", 'menus' in state_dict)


# ============================================================================
# PREDICTOR SERVICE TESTS
# ============================================================================

def test_predictor_service():
    """Test PredictorService"""
    section("PredictorService Tests")
    
    try:
        from core.services.predictor_service import (
            PredictorService, Prediction, Token, get_predictor_service
        )
        test("Import PredictorService", True)
    except ImportError as e:
        test("Import PredictorService", False, str(e))
        return
    
    # Singleton
    service1 = get_predictor_service()
    service2 = get_predictor_service()
    test("Singleton pattern", service1 is service2)
    
    # Commands loaded
    test("Commands loaded", len(service1.commands) > 0)
    test("Has 90+ commands", len(service1.commands) >= 90)
    
    # Predict
    predictions = service1.predict("HEL")
    test("Predict returns list", isinstance(predictions, list))
    test("Predict finds HELP", any(p.text == "HELP" for p in predictions))
    
    # Predict with max
    limited = service1.predict("F", max_results=3)
    test("Predict respects max_results", len(limited) <= 3)
    
    # Tokenize
    tokens = service1.tokenize("HELP commands")
    test("Tokenize returns list", isinstance(tokens, list))
    test("Tokenize has tokens", len(tokens) > 0)
    
    # Token has token_type string
    if tokens:
        test("Token has token_type", hasattr(tokens[0], 'token_type'))
    
    # Highlight (returns ANSI string)
    highlighted = service1.get_highlighted("HELP --verbose")
    test("Highlight returns string", isinstance(highlighted, str))
    
    # Is valid command (check if command exists)
    info = service1.get_command_info("HELP")
    test("HELP command exists", info is not None)
    bad_info = service1.get_command_info("XYZABC")
    test("XYZABC command doesn't exist", bad_info is None)
    
    # Get command info
    test("Command info has syntax", 'syntax' in info if info else False)
    
    # Record usage
    service1.record_command("HELP")
    test("Record command doesn't crash", True)
    
    # Prediction to_dict
    if predictions:
        pred_dict = predictions[0].to_dict()
        test("Prediction to_dict", isinstance(pred_dict, dict))
        test("Prediction has text", 'text' in pred_dict)
    
    # Token to_dict
    if tokens:
        token_dict = tokens[0].to_dict()
        test("Token to_dict", isinstance(token_dict, dict))


# ============================================================================
# DEBUG PANEL SERVICE TESTS
# ============================================================================

def test_debug_panel_service():
    """Test DebugPanelService"""
    section("DebugPanelService Tests")
    
    try:
        from core.services.debug_panel_service import (
            DebugPanelService, LogEntry, LogSource, LogLevel, get_debug_panel_service
        )
        test("Import DebugPanelService", True)
    except ImportError as e:
        test("Import DebugPanelService", False, str(e))
        return
    
    # Singleton
    service1 = get_debug_panel_service()
    service2 = get_debug_panel_service()
    test("Singleton pattern", service1 is service2)
    
    # Log levels
    test("LogLevel DEBUG exists", hasattr(LogLevel, 'DEBUG'))
    test("LogLevel ERROR exists", hasattr(LogLevel, 'ERROR'))
    
    # Has sources
    test("Has sources", len(service1.sources) > 0)
    
    # Get available sources
    available = service1.get_available_sources()
    test("Get available sources", isinstance(available, list))
    
    # Load all logs
    service1.load_all(max_lines=50)
    test("Load all logs", True)
    
    # Get entries
    test("Has entries list", isinstance(service1.entries, list))
    
    # Set filter level
    service1.set_min_level(LogLevel.INFO)
    test("Set min level", service1.min_level == LogLevel.INFO)
    
    # Set search
    service1.set_search("test")
    test("Set search term", service1.search_term == "test")
    
    # Clear filters
    service1.clear_filters()
    test("Clear filters", service1.search_term is None)
    
    # Get filtered entries
    filtered = service1.get_filtered_entries()
    test("Get filtered entries", isinstance(filtered, list))
    
    # Get stats
    stats = service1.get_stats()
    test("Get stats", isinstance(stats, dict))
    
    # Subscribe/unsubscribe
    callback_list = []
    def test_callback(entry):
        callback_list.append(entry)
    
    service1.subscribe(test_callback)
    test("Subscribe callback", test_callback in service1._subscribers)
    
    service1.unsubscribe(test_callback)
    test("Unsubscribe callback", test_callback not in service1._subscribers)
    
    # Export
    export_result = service1.export()
    test("Export returns dict", isinstance(export_result, dict))
    
    # Render
    rendered = service1.render(width=80)
    test("Render returns string", isinstance(rendered, str))


# ============================================================================
# STREAMING SERVICE TESTS
# ============================================================================

def test_streaming_service():
    """Test WebSocketStreamingService"""
    section("WebSocketStreamingService Tests")
    
    try:
        from core.services.streaming_service import (
            WebSocketStreamingService, StreamEvent, StreamMessage, 
            StreamSubscription, get_streaming_service
        )
        test("Import StreamingService", True)
    except ImportError as e:
        test("Import StreamingService", False, str(e))
        return
    
    # Singleton
    service1 = get_streaming_service()
    service2 = get_streaming_service()
    test("Singleton pattern", service1 is service2)
    
    # Create fresh instance for testing
    service = WebSocketStreamingService()
    
    # Stream events
    test("StreamEvent CONNECT exists", hasattr(StreamEvent, 'CONNECT'))
    test("StreamEvent COMMAND_OUTPUT exists", hasattr(StreamEvent, 'COMMAND_OUTPUT'))
    test("StreamEvent DEBUG_LOG exists", hasattr(StreamEvent, 'DEBUG_LOG'))
    
    # Connect client
    sub = service.connect('test-client-1')
    test("Connect returns subscription", isinstance(sub, StreamSubscription))
    test("Client registered", 'test-client-1' in service.subscriptions)
    
    # Subscribe
    service.subscribe('test-client-1', ['command_output', 'debug_log'])
    test("Subscribe to events", StreamEvent.COMMAND_OUTPUT in sub.subscribed_events)
    
    # Get subscribers
    subscribers = service.get_subscribers(StreamEvent.COMMAND_OUTPUT)
    test("Get subscribers", 'test-client-1' in subscribers)
    
    # Emit (no handler, will queue)
    service.emit(StreamEvent.COMMAND_OUTPUT, {'line': 'Test output'})
    test("Emit event (queued)", service.total_messages > 0)
    
    # Get stats
    stats = service.get_stats()
    test("Get stats", isinstance(stats, dict))
    test("Stats has connected_clients", 'connected_clients' in stats)
    test("Stats has total_messages", 'total_messages' in stats)
    
    # Get client info
    client_info = service.get_client_info('test-client-1')
    test("Get client info", client_info is not None)
    test("Client info has subscribed_events", 'subscribed_events' in client_info)
    
    # StreamMessage
    msg = StreamMessage(
        event=StreamEvent.COMMAND_OUTPUT,
        data={'line': 'Test'},
        correlation_id='test-123'
    )
    test("StreamMessage creation", msg is not None)
    test("StreamMessage to_dict", isinstance(msg.to_dict(), dict))
    test("StreamMessage to_json", isinstance(msg.to_json(), str))
    
    # Unsubscribe
    service.unsubscribe('test-client-1', ['command_output'])
    test("Unsubscribe", StreamEvent.COMMAND_OUTPUT not in sub.subscribed_events)
    
    # Disconnect
    service.disconnect('test-client-1')
    test("Disconnect client", 'test-client-1' not in service.subscriptions)
    
    # Helper methods
    service.connect('test-client-2')
    service.emit_command_start("HELP", "corr-123")
    service.emit_command_output("Help output", "corr-123")
    service.emit_command_complete({'status': 'success'}, "corr-123")
    test("Helper emit methods", service.total_messages >= 3)


# ============================================================================
# UNIFIED PAGER TESTS
# ============================================================================

def test_unified_pager():
    """Test UnifiedPager"""
    section("UnifiedPager Tests")
    
    try:
        from core.utils.pager import (
            UnifiedPager, PagerState, ScrollDirection
        )
        test("Import UnifiedPager", True)
    except ImportError as e:
        test("Import UnifiedPager", False, str(e))
        return
    
    # Create pager
    pager = UnifiedPager(preserve_scroll=True, show_indicators=True)
    test("Create pager", pager is not None)
    
    # Set content
    lines = [f"Line {i}" for i in range(50)]
    pager.set_content(lines)
    test("Set content", pager.state.total_lines == 50)
    
    # Get viewport
    visible = pager.get_viewport()
    test("Get viewport", len(visible) > 0)
    
    # Scroll down
    pager.scroll(ScrollDirection.DOWN)
    test("Scroll down", pager.state.offset > 0)
    
    # Scroll up
    old_offset = pager.state.offset
    pager.scroll(ScrollDirection.UP)
    test("Scroll up", pager.state.offset < old_offset)
    
    # Page down (using scroll)
    pager.scroll(ScrollDirection.PAGE_DOWN)
    test("Page down", pager.state.offset > 0)
    
    # Go to top (via handle_key)
    pager.handle_key('g')
    test("Go to top", pager.state.offset == 0)
    
    # Go to bottom (via handle_key)
    pager.handle_key('G')
    test("Go to bottom", pager.state.offset > 0)
    
    # Has more above/below (using at_top/at_bottom)
    pager.state.offset = 0
    test("At top when offset=0", pager.state.at_top)
    test("Not at bottom when offset=0", not pager.state.at_bottom)
    
    # Get state
    state = pager.state
    test("Get state", isinstance(state, PagerState))
    test("State has offset", hasattr(state, 'offset'))
    
    # Search
    pager.state.offset = 0
    found = pager.search("Line 25")
    test("Search finds text", found)
    
    # Get status line
    status = pager.get_status_line()
    test("Get status line", isinstance(status, str))
    
    # Render
    rendered = pager.render()
    test("Render returns string", isinstance(rendered, str))
    
    # Clear
    pager.clear()
    test("Clear pager", pager.state.total_lines == 0)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  uDOS v1.2.30 Modular Services Integration Tests")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # Run all test suites
    test_file_picker_service()
    test_menu_service()
    test_predictor_service()
    test_debug_panel_service()
    test_streaming_service()
    test_unified_pager()
    
    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    print(f"\n  Total: {passed + failed} tests")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if failed == 0:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print(f"\n  ⚠️  {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
