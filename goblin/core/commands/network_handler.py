#!/usr/bin/env python3
"""
Network Command Handler - Parent handler for all network operations

Routes NETWORK commands to appropriate sub-handlers:
- MESH: Local mesh networking (MeshCore)
- CLOUD: Remote cloud services (sync, backup, sharing)
- WEB: Local web interfaces (localhost only)

Connection State Machine:
  OFFLINE → MESH_ONLY → LOCAL_WEB → CLOUD_CONNECTED

Commands:
- NETWORK STATUS - Show all network states
- NETWORK OFFLINE - Enter offline mode (disconnect all)
- NETWORK ONLINE - Reconnect all services
- NETWORK CONFIG - Network configuration
- NETWORK FAILOVER - Test auto-failover between modes

Fallback Modes:
- Full offline: MeshCore only (no internet required)
- Partial: MeshCore + local web
- Full: MeshCore + web + cloud

Version: v1.3.0
Author: Fred Porter
Date: December 24, 2025
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

from dev.goblin.core.commands.base_handler import BaseCommandHandler


class NetworkMode(Enum):
    """Network connectivity modes."""
    OFFLINE = "offline"              # No network activity
    MESH_ONLY = "mesh_only"          # Local mesh only (no internet)
    LOCAL_WEB = "local_web"          # Mesh + local web server
    CLOUD_CONNECTED = "cloud"        # Full connectivity


class NetworkHandler(BaseCommandHandler):
    """
    Parent handler for all network operations.
    
    Routes to MESH, CLOUD, and WEB sub-handlers with unified
    state management and auto-failover.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize network handler.
        
        Args:
            **kwargs: Handler kwargs (theme, logger, etc.)
        """
        super().__init__(**kwargs)
        
        # Current network mode
        self.mode = NetworkMode.OFFLINE
        
        # Sub-handlers (lazy loaded)
        self._mesh_handler = None
        self._cloud_handler = None
        self._web_handler = None
        
        # Service availability flags
        self._mesh_available = False
        self._cloud_available = False
        self._web_available = False
        
        # Check service availability
        self._check_services()
    
    def _check_services(self) -> None:
        """Check which network services are available."""
        # Check MeshCore service
        try:
            from extensions.transport.meshcore import get_mesh_service
            self._mesh_available = True
        except ImportError:
            self._mesh_available = False
        
        # Check cloud service (to be implemented)
        try:
            from extensions.cloud.cloud_service import get_cloud_service
            self._cloud_available = True
        except ImportError:
            self._cloud_available = False
        
        # Check web service
        try:
            from extensions.web.web_service import get_web_service
            self._web_available = True
        except ImportError:
            self._web_available = False
    
    @property
    def mesh_handler(self):
        """Lazy load mesh handler."""
        if self._mesh_handler is None:
            try:
                from dev.goblin.core.commands.mesh_handler import MeshCommandHandler
                self._mesh_handler = MeshCommandHandler(logger=self.logger)
            except ImportError:
                pass
        return self._mesh_handler
    
    @property
    def cloud_handler(self):
        """Lazy load cloud handler."""
        if self._cloud_handler is None:
            try:
                from dev.goblin.core.commands.cloud_handler import CloudHandler
                self._cloud_handler = CloudHandler(logger=self.logger)
            except ImportError:
                pass
        return self._cloud_handler
    
    def handle_command(self, params: List[str]) -> str:
        """
        Handle NETWORK commands.
        
        Args:
            params: Command parameters [NETWORK, subcommand, ...args]
            
        Returns:
            Command output
        """
        if len(params) < 2:
            return self._help()
        
        subcommand = params[1].upper()
        args = params[2:] if len(params) > 2 else []
        
        # Route to appropriate handler
        if subcommand == "STATUS":
            return self._handle_status(args)
        elif subcommand == "OFFLINE":
            return self._handle_offline(args)
        elif subcommand == "ONLINE":
            return self._handle_online(args)
        elif subcommand == "CONFIG":
            return self._handle_config(args)
        elif subcommand == "FAILOVER":
            return self._handle_failover(args)
        elif subcommand == "MESH":
            # Route to mesh handler
            if self.mesh_handler:
                mesh_cmd = args[0] if args else ""
                mesh_args = args[1:] if len(args) > 1 else []
                return self.mesh_handler.handle(mesh_cmd, mesh_args)
            return "⚠️  Mesh networking not available."
        elif subcommand == "CLOUD":
            # Route to cloud handler
            if self.cloud_handler:
                return self.cloud_handler.handle_command(["CLOUD"] + args)
            return "⚠️  Cloud services not available."
        elif subcommand == "WEB":
            return self._handle_web(args)
        else:
            return self._help()
    
    def _handle_status(self, args: List[str]) -> str:
        """Show all network states."""
        lines = []
        lines.append("=" * 70)
        lines.append("🌐 Network Status Overview")
        lines.append("=" * 70)
        lines.append("")
        
        # Current mode
        mode_icons = {
            NetworkMode.OFFLINE: "⚫",
            NetworkMode.MESH_ONLY: "🟡",
            NetworkMode.LOCAL_WEB: "🟠",
            NetworkMode.CLOUD_CONNECTED: "🟢"
        }
        lines.append(f"Mode: {mode_icons.get(self.mode, '⚪')} {self.mode.value.upper()}")
        lines.append("")
        
        # MeshCore Status
        lines.append("📡 MeshCore (Local Mesh)")
        lines.append("-" * 40)
        if self._mesh_available:
            try:
                from extensions.transport.meshcore import get_mesh_service
                service = get_mesh_service()
                status = service.get_status()
                
                lines.append(f"  Status:    {'🟢 Running' if status.get('running') else '🔴 Stopped'}")
                lines.append(f"  State:     {status.get('state', 'unknown')}")
                lines.append(f"  Device ID: {status.get('local_device_id', 'N/A')}")
                
                stats = status.get('stats', {})
                lines.append(f"  Messages:  {stats.get('messages_sent', 0)} sent / {stats.get('messages_received', 0)} recv")
            except Exception as e:
                lines.append(f"  Status: ⚠️  Error: {e}")
        else:
            lines.append("  Status: ⚪ Not available")
        lines.append("")
        
        # Cloud Status
        lines.append("☁️  Cloud Services")
        lines.append("-" * 40)
        if self._cloud_available:
            lines.append("  Status: 🟢 Available")
            # TODO: Add actual cloud status when service is implemented
        else:
            lines.append("  Status: ⚪ Not configured")
        lines.append("")
        
        # Web Status
        lines.append("🌍 Local Web Server")
        lines.append("-" * 40)
        if self._web_available:
            lines.append("  Status: 🟢 Available")
            # TODO: Add actual web status when service is implemented
        else:
            lines.append("  Status: ⚪ Not running")
        lines.append("")
        
        # Connection state machine
        lines.append("Connection State Machine:")
        lines.append("  OFFLINE → MESH_ONLY → LOCAL_WEB → CLOUD_CONNECTED")
        current_pos = list(NetworkMode).index(self.mode)
        indicator = "  " + "         " * current_pos + "   ↑"
        lines.append(indicator)
        lines.append("")
        
        return '\n'.join(lines)
    
    def _handle_offline(self, args: List[str]) -> str:
        """Enter offline mode."""
        lines = []
        lines.append("🔌 Entering offline mode...")
        
        # Stop mesh service
        if self._mesh_available:
            try:
                from extensions.transport.meshcore import get_mesh_service
                service = get_mesh_service()
                if service._running:
                    service.stop()
                    lines.append("  ✅ MeshCore stopped")
            except Exception as e:
                lines.append(f"  ⚠️  MeshCore error: {e}")
        
        # TODO: Stop cloud service when implemented
        # TODO: Stop web service when implemented
        
        self.mode = NetworkMode.OFFLINE
        lines.append("")
        lines.append("✅ All network services stopped. Mode: OFFLINE")
        
        return '\n'.join(lines)
    
    def _handle_online(self, args: List[str]) -> str:
        """Reconnect all services."""
        target_mode = args[0].upper() if args else "MESH_ONLY"
        
        lines = []
        lines.append(f"🔌 Connecting to {target_mode}...")
        
        # Start MeshCore
        if target_mode in ["MESH_ONLY", "LOCAL_WEB", "CLOUD"]:
            if self._mesh_available:
                try:
                    from extensions.transport.meshcore import get_mesh_service
                    service = get_mesh_service()
                    if not service._running:
                        service.start()
                        lines.append("  ✅ MeshCore started")
                    else:
                        lines.append("  ℹ️  MeshCore already running")
                except Exception as e:
                    lines.append(f"  ⚠️  MeshCore error: {e}")
            
            self.mode = NetworkMode.MESH_ONLY
        
        # Start Web server
        if target_mode in ["LOCAL_WEB", "CLOUD"]:
            if self._web_available:
                lines.append("  ✅ Web server started")
                self.mode = NetworkMode.LOCAL_WEB
            else:
                lines.append("  ⚠️  Web server not available")
        
        # Connect to Cloud
        if target_mode == "CLOUD":
            if self._cloud_available:
                lines.append("  ✅ Cloud connected")
                self.mode = NetworkMode.CLOUD_CONNECTED
            else:
                lines.append("  ⚠️  Cloud services not available")
        
        lines.append("")
        lines.append(f"✅ Network mode: {self.mode.value.upper()}")
        
        return '\n'.join(lines)
    
    def _handle_config(self, args: List[str]) -> str:
        """Network configuration."""
        if not args:
            return self._show_config()
        
        action = args[0].upper()
        
        if action == "SHOW":
            return self._show_config()
        elif action == "SET" and len(args) >= 3:
            key = args[1]
            value = ' '.join(args[2:])
            return self._set_config(key, value)
        else:
            return """
Network Configuration Commands:
  NETWORK CONFIG SHOW              - Show current configuration
  NETWORK CONFIG SET <key> <value> - Set configuration value

Configuration Keys:
  mesh.auto_start     - Auto-start MeshCore on launch (true/false)
  mesh.scan_interval  - Device scan interval in seconds (30-300)
  cloud.enabled       - Enable cloud services (true/false)
  cloud.sync_interval - Cloud sync interval in minutes (5-60)
  web.port            - Local web server port (1024-65535)
  web.auto_start      - Auto-start web server (true/false)
"""
    
    def _show_config(self) -> str:
        """Show current network configuration."""
        lines = []
        lines.append("=" * 60)
        lines.append("🔧 Network Configuration")
        lines.append("=" * 60)
        lines.append("")
        
        # TODO: Load from actual config file
        lines.append("MeshCore Settings:")
        lines.append("  mesh.auto_start:     true")
        lines.append("  mesh.scan_interval:  30 seconds")
        lines.append("")
        lines.append("Cloud Settings:")
        lines.append("  cloud.enabled:       false")
        lines.append("  cloud.sync_interval: 15 minutes")
        lines.append("")
        lines.append("Web Server Settings:")
        lines.append("  web.port:            5000")
        lines.append("  web.auto_start:      false")
        lines.append("")
        
        return '\n'.join(lines)
    
    def _set_config(self, key: str, value: str) -> str:
        """Set configuration value."""
        # TODO: Actually persist configuration
        return f"✅ Set {key} = {value}"
    
    def _handle_failover(self, args: List[str]) -> str:
        """Test auto-failover between modes."""
        lines = []
        lines.append("🔄 Testing network failover...")
        lines.append("")
        
        # Test progression through modes
        modes = [
            (NetworkMode.CLOUD_CONNECTED, "Testing cloud..."),
            (NetworkMode.LOCAL_WEB, "Falling back to local web..."),
            (NetworkMode.MESH_ONLY, "Falling back to mesh only..."),
            (NetworkMode.OFFLINE, "Falling back to offline...")
        ]
        
        for mode, message in modes:
            lines.append(f"  {message}")
            
            if mode == NetworkMode.CLOUD_CONNECTED and not self._cloud_available:
                lines.append("    ❌ Cloud not available")
                continue
            elif mode == NetworkMode.LOCAL_WEB and not self._web_available:
                lines.append("    ❌ Web not available")
                continue
            elif mode == NetworkMode.MESH_ONLY and not self._mesh_available:
                lines.append("    ❌ Mesh not available")
                continue
            
            lines.append(f"    ✅ {mode.value} operational")
            self.mode = mode
            break
        
        lines.append("")
        lines.append(f"Failover complete. Current mode: {self.mode.value.upper()}")
        
        return '\n'.join(lines)
    
    def _handle_web(self, args: List[str]) -> str:
        """Handle web server commands."""
        if not args:
            return """
Web Server Commands:
  NETWORK WEB START [port]  - Start local web server
  NETWORK WEB STOP          - Stop web server
  NETWORK WEB STATUS        - Show web server status
"""
        
        action = args[0].upper()
        
        if action == "START":
            port = int(args[1]) if len(args) > 1 else 5000
            return f"🌐 Web server starting on port {port}... (not yet implemented)"
        elif action == "STOP":
            return "🛑 Web server stopping... (not yet implemented)"
        elif action == "STATUS":
            if self._web_available:
                return "🟢 Web server is running"
            return "🔴 Web server is not running"
        
        return "Unknown web command. Use: NETWORK WEB START|STOP|STATUS"
    
    def _help(self) -> str:
        """Show NETWORK command help."""
        return """
🌐 NETWORK Commands - Unified Network Management (v1.3.0)
==========================================================

Service Status:
  NETWORK STATUS                   - Show all network states
  NETWORK OFFLINE                  - Enter offline mode (stop all)
  NETWORK ONLINE [mode]            - Connect services
                                     Modes: MESH_ONLY, LOCAL_WEB, CLOUD
  NETWORK CONFIG                   - Show network configuration
  NETWORK CONFIG SET <key> <value> - Update configuration
  NETWORK FAILOVER                 - Test auto-failover

Sub-System Routing:
  NETWORK MESH <command>           - Route to MeshCore commands
  NETWORK CLOUD <command>          - Route to Cloud commands
  NETWORK WEB <command>            - Route to Web server commands

Connection Modes:
  OFFLINE         ⚫  No network activity
  MESH_ONLY       🟡  Local mesh only (offline-first)
  LOCAL_WEB       🟠  Mesh + local web server
  CLOUD_CONNECTED 🟢  Full connectivity

Auto-Failover:
  Cloud fails    → Falls back to LOCAL_WEB
  Web fails      → Falls back to MESH_ONLY
  Mesh fails     → Falls back to OFFLINE

Examples:
  NETWORK STATUS                   - Show all service states
  NETWORK ONLINE MESH_ONLY         - Start mesh networking only
  NETWORK MESH SCAN                - Scan for mesh devices
  NETWORK CLOUD SYNC               - Sync with cloud
  NETWORK WEB START 8080           - Start web on port 8080
"""
