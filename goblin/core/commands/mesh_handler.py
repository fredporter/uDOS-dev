#!/usr/bin/env python3
"""
MESH Command Handler - MeshCore network commands for Layer 600-650

Provides command interface for MeshCore mesh networking with offline-first
design. Manages device discovery, P2P messaging, network topology, and
signal analysis.

Commands (v1.3.0):
- MESH SCAN [tile] [timeout] - Discover nearby nodes
- MESH PAIR <device> - Pair with device
- MESH UNPAIR <device> - Unpair from device
- MESH SEND <device> <message> - Send message to device
- MESH BROADCAST <message> - Broadcast to all connected
- MESH ROUTE <source> <target> - Find/show route between devices
- MESH TOPOLOGY [tile] - Network visualization
- MESH DEVICES [tile] - List devices in network or tile
- MESH INFO <device_id> - Show detailed device information
- MESH HEATMAP [tile] - Display signal strength heatmap
- MESH REGISTER <id> <tile> <type> - Register new device
- MESH CONNECT <device_a> <device_b> - Connect two devices
- MESH STATS - Show network statistics
- MESH STATUS - Show service status

Layer Integration:
- 600-609: MeshCore network layer (devices, routes)
- 610-619: Signal heatmaps (coverage)
- 620-629: Network routes (paths)
- 650-659: Device status overlays

Version: v1.3.0
Author: Fred Porter
Date: December 24, 2025
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from extensions.transport.meshcore import (
        MeshCoreService,
        get_mesh_service,
        ConnectionState,
        NetworkEvent,
        Device,
        DeviceType,
        DeviceStatus,
        MessageType,
    )

    MESH_SERVICE_AVAILABLE = True
except ImportError:
    MESH_SERVICE_AVAILABLE = False

try:
    from dev.goblin.core.ui.grid_renderer import GridRenderer, GridCell, ViewportTier, Symbols
    from dev.goblin.core.ui.grid_template_loader import GridTemplateLoader

    GRID_SUPPORT = True
except ImportError:
    GRID_SUPPORT = False


class MeshCommandHandler:
    """Handler for MESH commands with offline-first mesh networking."""

    def __init__(
        self, device_registry=None, **kwargs
    ):
        """
        Initialize MESH command handler.

        Args:
            device_registry: Optional device registry instance
            **kwargs: Additional handler kwargs (theme, logger, etc.)
        """
        if device_registry is None:
            # Use transport layer device registry
            from extensions.transport.meshcore import get_device_registry
            device_registry = get_device_registry()

        self.manager = device_registry
        self.logger = kwargs.get("logger")

        # Initialize mesh service if available
        if MESH_SERVICE_AVAILABLE:
            self.service = get_mesh_service()
        else:
            self.service = None

        if GRID_SUPPORT:
            self.grid_renderer = GridRenderer()
            self.template_loader = GridTemplateLoader()
        else:
            self.grid_renderer = None
            self.template_loader = None

    def handle(self, command: str, args: List[str]) -> str:
        """
        Handle MESH command.

        Args:
            command: Command name (e.g., "DEVICES", "SCAN", "SEND")
            args: Command arguments

        Returns:
            Command output
        """
        command = command.upper()

        # New v1.3.0 commands
        if command == "SCAN":
            return self._handle_scan(args)
        elif command == "PAIR":
            return self._handle_pair(args)
        elif command == "UNPAIR":
            return self._handle_unpair(args)
        elif command == "SEND":
            return self._handle_send(args)
        elif command == "BROADCAST":
            return self._handle_broadcast(args)
        elif command == "STATUS":
            return self._handle_status(args)

        # v1.0.0.20 - Signal monitoring commands
        elif command == "SIGNAL":
            return self._handle_signal(args)
        elif command == "MONITOR":
            return self._handle_monitor(args)
        elif command == "PING":
            return self._handle_ping(args)

        # Existing commands
        elif command == "DEVICES":
            return self._handle_devices(args)
        elif command == "INFO":
            return self._handle_info(args)
        elif command == "HEATMAP":
            return self._handle_heatmap(args)
        elif command == "ROUTE":
            return self._handle_route(args)
        elif command == "TOPOLOGY":
            return self._handle_topology(args)
        elif command == "REGISTER":
            return self._handle_register(args)
        elif command == "CONNECT":
            return self._handle_connect(args)
        elif command == "STATS":
            return self._handle_stats(args)
        # v1.3.1 - Map integration
        elif command == "MAP":
            return self._handle_map(args)
        else:
            return self._help()

    # ─────────────────────────────────────────────────────────────
    # New v1.3.0 Commands
    # ─────────────────────────────────────────────────────────────

    def _handle_scan(self, args: List[str]) -> str:
        """Scan for nearby devices."""
        if not self.service:
            return "⚠️  Mesh service not available. Using device manager fallback."

        tile = args[0] if args else None
        timeout = float(args[1]) if len(args) > 1 else 5.0

        # Ensure service is running
        if not self.service._running:
            self.service.start()

        lines = []
        lines.append("=" * 60)
        lines.append(f"🔍 Scanning for devices{f' in {tile}' if tile else ''}...")
        lines.append("=" * 60)
        lines.append("")

        try:
            devices = self.service.scan(tile=tile, timeout=timeout)

            if devices:
                lines.append(f"Found {len(devices)} device(s):")
                lines.append("")
                lines.append(
                    f"{'ID':<8} {'Type':<10} {'Status':<10} {'Signal':<8} {'TILE':<12}"
                )
                lines.append("-" * 60)

                for device in devices:
                    lines.append(
                        f"{device.id:<8} "
                        f"{device.type.name:<10} "
                        f"{device.status.name:<10} "
                        f"{device.signal:>3}%{' '*4} "
                        f"{device.tile}-{device.layer}"
                    )
            else:
                lines.append("No devices found.")

            lines.append("")
            lines.append(f"💡 Use MESH PAIR <device_id> to connect")

        except Exception as e:
            lines.append(f"❌ Scan failed: {e}")

        return "\n".join(lines)

    def _handle_pair(self, args: List[str]) -> str:
        """Pair with a device."""
        if not args:
            return "Usage: MESH PAIR <device_id>"

        if not self.service:
            return "⚠️  Mesh service not available."

        device_id = args[0]

        # Ensure service is running
        if not self.service._running:
            self.service.start()

        success = self.service.pair(device_id)

        if success:
            device = self.manager.get_device(device_id)
            return f"✅ Paired with {device_id} ({device.type.value if device else 'unknown'})"
        else:
            return f"❌ Failed to pair with {device_id}. Device may not exist or be offline."

    def _handle_unpair(self, args: List[str]) -> str:
        """Unpair from a device."""
        if not args:
            return "Usage: MESH UNPAIR <device_id>"

        if not self.service:
            return "⚠️  Mesh service not available."

        device_id = args[0]

        success = self.service.unpair(device_id)

        if success:
            return f"✅ Unpaired from {device_id}"
        else:
            return f"❌ Failed to unpair from {device_id}. Not currently paired."

    def _handle_send(self, args: List[str]) -> str:
        """Send message to a device."""
        if len(args) < 2:
            return "Usage: MESH SEND <device_id> <message>"

        if not self.service:
            return "⚠️  Mesh service not available."

        device_id = args[0]
        message = " ".join(args[1:])

        # Ensure service is running
        if not self.service._running:
            self.service.start()

        success = self.service.send(device_id, message)

        if success:
            return f"✅ Message sent to {device_id} ({len(message)} bytes)"
        else:
            return f"❌ Failed to send message to {device_id}"

    def _handle_broadcast(self, args: List[str]) -> str:
        """Broadcast message to all connected devices."""
        if not args:
            return "Usage: MESH BROADCAST <message>"

        if not self.service:
            return "⚠️  Mesh service not available."

        message = " ".join(args)

        # Ensure service is running
        if not self.service._running:
            self.service.start()

        count = self.service.broadcast(message)

        if count > 0:
            return f"✅ Broadcast sent to {count} device(s) ({len(message)} bytes)"
        else:
            return "⚠️  No connected devices to broadcast to."

    def _handle_status(self, args: List[str]) -> str:
        """Show mesh service status."""
        if not self.service:
            return "⚠️  Mesh service not available."

        status = self.service.get_status()
        stats = status.get("stats", {})

        # Format uptime
        uptime = status.get("uptime_seconds", 0)
        if uptime >= 3600:
            uptime_str = f"{uptime/3600:.1f}h"
        elif uptime >= 60:
            uptime_str = f"{uptime/60:.1f}m"
        else:
            uptime_str = f"{uptime:.0f}s"

        lines = []
        lines.append("=" * 60)
        lines.append("📡 MeshCore Service Status")
        lines.append("=" * 60)
        lines.append("")
        lines.append(
            f"  Running:          {'✅ Yes' if status.get('running') else '❌ No'}"
        )
        lines.append(f"  State:            {status.get('state', 'unknown').upper()}")
        lines.append(f"  Local Device ID:  {status.get('local_device_id', 'N/A')}")
        lines.append(f"  Uptime:           {uptime_str}")
        lines.append("")
        lines.append("Statistics:")
        lines.append(f"  Messages Sent:     {stats.get('messages_sent', 0)}")
        lines.append(f"  Messages Received: {stats.get('messages_received', 0)}")
        lines.append(f"  Bytes Sent:        {stats.get('bytes_sent', 0)}")
        lines.append(f"  Bytes Received:    {stats.get('bytes_received', 0)}")
        lines.append(f"  Devices Found:     {stats.get('devices_discovered', 0)}")
        lines.append(f"  Routes Computed:   {stats.get('routes_computed', 0)}")
        lines.append("")

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────
    # v1.0.0.20 - Signal Monitoring Commands
    # ─────────────────────────────────────────────────────────────

    def _handle_signal(self, args: List[str]) -> str:
        """Show signal strength for devices.

        Usage:
            MESH SIGNAL              - Show all devices with signal
            MESH SIGNAL <device_id>  - Show signal for specific device
        """
        try:
            from extensions.transport.meshcore import get_mesh_transport

            transport = get_mesh_transport()
        except ImportError:
            transport = None

        if not transport:
            # Fallback to device manager data
            return self._handle_signal_fallback(args)

        lines = []
        lines.append("=" * 60)
        lines.append("📶 Signal Strength Monitor")
        lines.append("=" * 60)
        lines.append("")

        if args:
            # Specific device
            device_id = args[0]
            strength = transport.get_signal_strength(device_id)
            quality = transport.get_signal_quality(device_id)

            if strength is None:
                return f"⚠️  Device {device_id} not found or signal unavailable."

            bars = transport._dbm_to_bars(strength)
            bar_display = "█" * bars + "░" * (5 - bars)

            lines.append(f"  Device:   {device_id}")
            lines.append(f"  Signal:   {strength} dBm")
            lines.append(f"  Quality:  {quality.upper()}")
            lines.append(f"  Bars:     [{bar_display}] {bars}/5")
            lines.append("")
            lines.append(f"💡 Use MESH MONITOR {device_id} for real-time tracking")
        else:
            # All devices
            signals = transport.get_all_signal_strengths()

            if not signals:
                lines.append("No devices found.")
            else:
                lines.append(
                    f"{'DEVICE':<12} {'SIGNAL':>8} {'QUALITY':<10} {'BARS':<8} {'STATUS':<10}"
                )
                lines.append("-" * 60)

                for device_id, info in sorted(signals.items()):
                    bars = info.get("bars", 0)
                    bar_display = "█" * bars + "░" * (5 - bars)
                    lines.append(
                        f"{device_id:<12} "
                        f"{info.get('signal_dbm', 'N/A'):>6} dB "
                        f"{info.get('quality', 'unknown'):<10} "
                        f"[{bar_display}] "
                        f"{info.get('status', 'unknown'):<10}"
                    )

                lines.append("")
                lines.append(f"Total: {len(signals)} device(s)")

        lines.append("")
        return "\n".join(lines)

    def _handle_signal_fallback(self, args: List[str]) -> str:
        """Fallback signal display using device manager."""
        devices = self.manager.list_devices()

        lines = []
        lines.append("=" * 60)
        lines.append("📶 Signal Strength (Device Manager)")
        lines.append("=" * 60)
        lines.append("")

        if args:
            device_id = args[0]
            device = self.manager.get_device(device_id)
            if device:
                lines.append(f"  Device:  {device_id}")
                lines.append(f"  Signal:  {device.signal}%")
                lines.append(f"  Status:  {device.status.value}")
            else:
                return f"⚠️  Device {device_id} not found."
        else:
            lines.append(f"{'DEVICE':<10} {'SIGNAL':>8} {'STATUS':<10}")
            lines.append("-" * 40)
            for device in devices:
                lines.append(
                    f"{device.id:<10} {device.signal:>6}% {device.status.value:<10}"
                )
            lines.append("")
            lines.append(f"Total: {len(devices)} device(s)")

        lines.append("")
        lines.append("⚠️  Using device manager fallback (transport not available)")
        return "\n".join(lines)

    def _handle_monitor(self, args: List[str]) -> str:
        """Monitor signal strength over time.

        Usage:
            MESH MONITOR <device_id> [duration] [interval]

        Examples:
            MESH MONITOR node1          - Monitor for 10 seconds
            MESH MONITOR node1 30       - Monitor for 30 seconds
            MESH MONITOR node1 60 2     - Monitor for 60 seconds, sample every 2s
        """
        if not args:
            return (
                "Usage: MESH MONITOR <device_id> [duration_seconds] [interval_seconds]"
            )

        device_id = args[0]
        duration = float(args[1]) if len(args) > 1 else 10.0
        interval = float(args[2]) if len(args) > 2 else 1.0

        try:
            from extensions.transport.meshcore import get_mesh_transport

            transport = get_mesh_transport()
        except ImportError:
            return "⚠️  MeshCore transport not available."

        if not transport:
            return "⚠️  Could not initialize transport."

        lines = []
        lines.append("=" * 60)
        lines.append(f"📊 Signal Monitor - {device_id}")
        lines.append(f"   Duration: {duration}s | Interval: {interval}s")
        lines.append("=" * 60)
        lines.append("")
        lines.append("Collecting samples...")
        lines.append("")

        # Collect samples
        samples = transport.monitor_signal(device_id, duration, interval)

        if not samples or all(s.get("signal_dbm") is None for s in samples):
            lines.append(f"⚠️  No signal data received from {device_id}")
            lines.append("   Device may be offline or out of range.")
            return "\n".join(lines)

        # Get statistics
        stats = transport.get_signal_stats(samples)

        lines.append(f"{'TIME':>6} {'SIGNAL':>8} {'QUALITY':<10} {'BARS':<8}")
        lines.append("-" * 40)

        for s in samples:
            elapsed = s.get("elapsed", 0)
            signal = s.get("signal_dbm")
            quality = s.get("quality", "unknown")
            bars = s.get("bars", 0)
            bar_display = "█" * bars + "░" * (5 - bars)

            if signal is not None:
                lines.append(
                    f"{elapsed:>5.1f}s {signal:>6} dB {quality:<10} [{bar_display}]"
                )
            else:
                lines.append(f"{elapsed:>5.1f}s {'N/A':>8} {'--':<10} [░░░░░]")

        lines.append("")
        lines.append("Statistics:")
        lines.append(f"  Samples:    {stats.get('sample_count', 0)}")
        lines.append(f"  Min:        {stats.get('min_dbm', 'N/A')} dBm")
        lines.append(f"  Max:        {stats.get('max_dbm', 'N/A')} dBm")
        lines.append(f"  Average:    {stats.get('avg_dbm', 'N/A')} dBm")
        lines.append(f"  Std Dev:    {stats.get('std_dev', 'N/A')}")
        lines.append(f"  Stability:  {stats.get('stability', 'unknown').upper()}")
        lines.append(f"  Quality:    {stats.get('avg_quality', 'unknown').upper()}")
        lines.append("")

        return "\n".join(lines)

    def _handle_ping(self, args: List[str]) -> str:
        """Ping a device and measure latency.

        Usage:
            MESH PING <device_id> [count]
        """
        if not args:
            return "Usage: MESH PING <device_id> [count]"

        device_id = args[0]
        count = int(args[1]) if len(args) > 1 else 3

        try:
            from extensions.transport.meshcore import get_mesh_transport

            transport = get_mesh_transport()
        except ImportError:
            return "⚠️  MeshCore transport not available."

        if not transport:
            return "⚠️  Could not initialize transport."

        lines = []
        lines.append(f"🏓 PING {device_id}")
        lines.append("")

        latencies = []
        for i in range(count):
            latency = transport.ping(device_id)
            if latency is not None:
                latencies.append(latency)
                lines.append(f"  Reply from {device_id}: time={latency:.1f}ms")
            else:
                lines.append(f"  Request timeout for {device_id}")

        lines.append("")

        if latencies:
            avg = sum(latencies) / len(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            loss = ((count - len(latencies)) / count) * 100

            lines.append(f"--- {device_id} ping statistics ---")
            lines.append(
                f"{count} packets transmitted, {len(latencies)} received, {loss:.0f}% packet loss"
            )
            lines.append(f"rtt min/avg/max = {min_lat:.1f}/{avg:.1f}/{max_lat:.1f} ms")
        else:
            lines.append(f"--- {device_id} ping statistics ---")
            lines.append(f"{count} packets transmitted, 0 received, 100% packet loss")

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────
    # Existing Commands (unchanged)
    # ─────────────────────────────────────────────────────────────

    def _handle_devices(self, args: List[str]) -> str:
        """List devices in network or tile."""
        tile = args[0] if args else None
        layer = int(args[1]) if len(args) > 1 else None

        devices = self.manager.list_devices(tile=tile, layer=layer)

        if not devices:
            return "No devices found."

        # Build table
        lines = []
        lines.append("=" * 80)
        lines.append(f"MeshCore Devices{f' - {tile}' if tile else ''}")
        lines.append("=" * 80)
        lines.append("")

        # Header
        header = f"{'ID':<6} {'Type':<8} {'Status':<8} {'Signal':<8} {'Uptime':<10} {'Msgs/s':<8} {'TILE':<12}"
        lines.append(header)
        lines.append("-" * 80)

        # Device rows
        for device in sorted(devices, key=lambda d: d.id):
            row = (
                f"{device.id:<6} "
                f"{device.type.value:<8} "
                f"{device.status.value:<8} "
                f"{device.signal:>3}%{' '*4} "
                f"{device.uptime:>5.1f}h{' '*4} "
                f"{device.msgs_per_sec:>5}{' '*3} "
                f"{device.tile}-{device.layer}"
            )
            lines.append(row)

        lines.append("")
        lines.append(f"Total: {len(devices)} devices")

        return "\n".join(lines)

    def _handle_info(self, args: List[str]) -> str:
        """Show detailed device information."""
        if not args:
            return "Usage: MESH INFO <device_id>"

        device_id = args[0]
        device = self.manager.get_device(device_id)

        if not device:
            return f"Device not found: {device_id}"

        lines = []
        lines.append("=" * 60)
        lines.append(f"Device Information - {device.id}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"  TILE Code:        {device.full_code}")
        lines.append(f"  Type:             {device.type.name} {device.type.value}")
        lines.append(f"  Status:           {device.status.name} {device.status.value}")
        lines.append(f"  Signal Strength:  {device.signal}%")
        lines.append(
            f"  Firmware:         v{device.firmware_version} {device.firmware_status.value}"
        )
        lines.append(f"  Uptime:           {device.uptime:.1f} hours")
        lines.append(f"  Throughput:       {device.msgs_per_sec} msgs/sec")
        lines.append("")

        if device.connections:
            lines.append(f"  Connections ({len(device.connections)}):")
            for conn_id in device.connections:
                conn_device = self.manager.get_device(conn_id)
                if conn_device:
                    lines.append(
                        f"    → {conn_id} ({conn_device.type.value} {conn_device.status.value})"
                    )
        else:
            lines.append("  Connections: None")

        return "\n".join(lines)

    def _handle_heatmap(self, args: List[str]) -> str:
        """Display signal strength heatmap."""
        if not GRID_SUPPORT:
            return "Grid rendering not available (missing grid_renderer module)"

        tile = args[0] if args else "AA340"

        # Generate heatmap data
        heatmap_data = self.manager.get_signal_heatmap(tile, width=6, height=4)

        # Render using template
        try:
            # Update template with actual heatmap data
            result = self.template_loader.render_template(
                "meshcore_heatmap", {"tile_base": tile}
            )
            return result
        except Exception as e:
            # Fallback to simple rendering
            lines = []
            lines.append(f"Signal Coverage Grid - {tile}")
            lines.append("=" * 40)

            for row in heatmap_data:
                row_str = ""
                for signal in row:
                    row_str += Symbols.signal_gradient(signal) * 4 + " "
                lines.append(row_str)

            lines.append("")
            lines.append("Legend: █=100% ▓=75% ▒=50% ░=25% ' '=0%")

            return "\n".join(lines)

    def _handle_route(self, args: List[str]) -> str:
        """Find route between devices."""
        if len(args) < 2:
            return "Usage: MESH ROUTE <source> <target>"

        source = args[0]
        target = args[1]

        # Try using mesh service first (has better routing)
        route = None
        if self.service and self.service._running:
            route = self.service.find_route(source, target)

        # Fallback to device manager
        if not route:
            route = self.manager.find_route(source, target)

        if not route:
            return f"❌ No route found between {source} and {target}"

        lines = []
        lines.append("=" * 60)
        lines.append(f"📍 Route: {source} → {target}")
        lines.append("=" * 60)
        lines.append("")

        # Build route visualization
        route_str = " → ".join(route)
        lines.append(f"  {route_str}")
        lines.append("")

        # Show hop details
        lines.append("Hop Details:")
        total_signal = 0
        for i, device_id in enumerate(route):
            device = self.manager.get_device(device_id)
            if device:
                total_signal += device.signal
                lines.append(
                    f"  {i+1}. {device.id} ({device.type.value}) - "
                    f"Signal: {device.signal}% - "
                    f"Status: {device.status.value}"
                )

        lines.append("")
        lines.append(f"Total Hops: {len(route) - 1}")
        if len(route) > 1:
            avg_signal = total_signal // len(route)
            lines.append(f"Avg Signal: {avg_signal}%")

        return "\n".join(lines)

    def _handle_topology(self, args: List[str]) -> str:
        """Show network topology grid."""
        if not GRID_SUPPORT:
            return "Grid rendering not available (missing grid_renderer module)"

        tile = args[0] if args else "AA340"

        try:
            # Render topology template
            result = self.template_loader.render_template(
                "meshcore_topology", {"tile_base": tile}
            )
            return result
        except Exception as e:
            return f"Failed to render topology: {e}"

    def _handle_register(self, args: List[str]) -> str:
        """Register new device."""
        if len(args) < 3:
            return "Usage: MESH REGISTER <device_id> <tile> <type>\nTypes: NODE, GATEWAY, SENSOR, REPEATER, END_DEVICE"

        device_id = args[0]
        tile = args[1]
        type_str = args[2].upper()

        # Validate device type
        try:
            device_type = DeviceType[type_str]
        except KeyError:
            return f"Invalid device type: {type_str}\nValid types: NODE, GATEWAY, SENSOR, REPEATER, END_DEVICE"

        # Check if device already exists
        if self.manager.get_device(device_id):
            return f"Device already exists: {device_id}"

        # Register device
        device = self.manager.register_device(
            device_id=device_id, tile=tile, layer=600, device_type=device_type
        )

        return f"✓ Registered device {device_id} ({device_type.value}) at {device.full_code}"

    def _handle_connect(self, args: List[str]) -> str:
        """Connect two devices."""
        if len(args) < 2:
            return "Usage: MESH CONNECT <device_a> <device_b>"

        device_a = args[0]
        device_b = args[1]

        # Validate devices exist
        if not self.manager.get_device(device_a):
            return f"Device not found: {device_a}"

        if not self.manager.get_device(device_b):
            return f"Device not found: {device_b}"

        # Connect devices
        success = self.manager.connect_devices(device_a, device_b)

        if success:
            return f"✓ Connected {device_a} ↔ {device_b}"
        else:
            return f"Failed to connect {device_a} and {device_b}"

    def _handle_stats(self, args: List[str]) -> str:
        """Show network statistics."""
        stats = self.manager.get_network_stats()

        lines = []
        lines.append("=" * 60)
        lines.append("MeshCore Network Statistics")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"  Total Devices:      {stats['total_devices']}")
        lines.append(f"  Online:             {stats['online']}")
        lines.append(f"  Offline:            {stats['offline']}")
        lines.append(f"  Connecting:         {stats['connecting']}")
        lines.append(f"  Average Signal:     {stats['avg_signal']}%")
        lines.append(f"  Total Connections:  {stats['total_connections']}")
        lines.append("")

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────
    # v1.3.1 - Map Integration
    # ─────────────────────────────────────────────────────────────

    def _handle_map(self, args: List[str]) -> str:
        """
        Show MeshCore devices on a map overlay.

        Usage: MESH MAP [subcommand]
        Subcommands:
          VIEW       - Show map with device overlay
          TOGGLE     - Toggle device overlay on/off
          SYNC       - Sync devices to map grid
        """
        try:
            from dev.goblin.core.ui.map_grid import get_map_grid

            map_grid = get_map_grid()
        except ImportError:
            return "⚠️  Map grid system not available."

        subcommand = args[0].upper() if args else "VIEW"

        if subcommand == "VIEW":
            # Sync devices to map then render
            self._sync_devices_to_map(map_grid)

            # Enable network overlay
            map_grid.viewport.show_network = True

            # Render the map
            output = map_grid.render(include_frame=True)

            # Add device legend
            devices = map_grid.get_visible_devices()
            if devices:
                output += f"\n\n📡 MeshCore Devices ({len(devices)} visible):"
                for d in devices[:5]:  # Top 5
                    status_icon = {
                        "online": "●",
                        "offline": "○",
                        "connecting": "◐",
                        "error": "◑",
                    }.get(d["status"], "?")
                    output += f"\n  {status_icon} {d['device_id']} ({d['type']}) - Signal: {d['signal']}%"
                if len(devices) > 5:
                    output += f"\n  ... and {len(devices) - 5} more"
            else:
                output += "\n\nNo devices in current viewport."

            return output

        elif subcommand == "TOGGLE":
            map_grid.viewport.show_network = not map_grid.viewport.show_network
            state = "ENABLED" if map_grid.viewport.show_network else "DISABLED"
            return f"📡 MeshCore map overlay: {state}"

        elif subcommand == "SYNC":
            count = self._sync_devices_to_map(map_grid)
            return f"✅ Synced {count} devices to map grid."

        else:
            return """Usage: MESH MAP [VIEW|TOGGLE|SYNC]

Commands:
  MESH MAP VIEW   - Show map with device overlay
  MESH MAP TOGGLE - Toggle overlay on/off
  MESH MAP SYNC   - Sync devices to map grid

The map overlay shows MeshCore devices at their TILE locations
with status indicators and signal strength."""

    def _sync_devices_to_map(self, map_grid) -> int:
        """
        Sync MeshCore devices to map grid.

        Args:
            map_grid: MapGrid instance

        Returns:
            Number of devices synced
        """
        count = 0

        # Get devices from device manager
        devices = self.manager.get_devices()

        for device in devices:
            try:
                # Parse tile code to get column/row
                tile = device.tile
                if not tile:
                    continue

                # Convert tile to grid position
                col_code = tile[:2].upper()
                row = int(tile[2:]) if tile[2:].isdigit() else 0

                # Column code to number (AA=0, AB=1, ..., SL=479)
                col = (ord(col_code[0]) - 65) * 26 + (ord(col_code[1]) - 65)

                # Add device to map grid
                map_grid.set_network_device(
                    col=col,
                    row=row,
                    device_id=device.id,
                    device_type=device.type.name.lower(),
                    signal=device.signal or 0,
                    status=device.status.name.lower() if device.status else "offline",
                )
                count += 1
            except Exception:
                continue

        return count

    def _help(self) -> str:
        """Show MESH command help."""
        return """
📡 MESH Commands - MeshCore Network Operations (v1.3.0)
========================================================

Service Management:
  MESH STATUS                      - Show mesh service status
  MESH SCAN [tile] [timeout]       - Discover nearby nodes
  MESH PAIR <device_id>            - Pair with a device
  MESH UNPAIR <device_id>          - Unpair from a device

Messaging:
  MESH SEND <device_id> <message>  - Send message to device
  MESH BROADCAST <message>         - Broadcast to all connected

Device Management:
  MESH DEVICES [tile] [layer]      - List all devices (optionally filtered)
  MESH INFO <device_id>            - Show detailed device information
  MESH REGISTER <id> <tile> <type> - Register new device
  MESH CONNECT <dev_a> <dev_b>     - Connect two devices

Network Visualization:
  MESH TOPOLOGY [tile]             - Show network topology grid
  MESH HEATMAP [tile]              - Display signal strength heatmap
  MESH ROUTE <source> <target>     - Find route between devices
  MESH STATS                       - Show network statistics

Device Types:
  NODE       ⊚  - Primary node/hub
  GATEWAY    ⊕  - Gateway/router
  SENSOR     ⊗  - Sensor/monitor
  REPEATER   ⊙  - Repeater/relay
  END_DEVICE ⊘  - End device/client

Layer Integration:
  600-609: MeshCore network (devices, routes)
  610-619: Signal heatmaps (coverage)
  620-629: Network routes (paths)
  650-659: Device status overlays

Examples:
  MESH SCAN                       - Discover all nearby devices
  MESH SCAN AA340 10              - Scan tile AA340 for 10 seconds
  MESH PAIR D1                    - Pair with device D1
  MESH SEND D1 Hello World        - Send message to D1
  MESH BROADCAST Emergency alert  - Broadcast to all
  MESH ROUTE D1 D5                - Find route from D1 to D5
  MESH REGISTER D9 JF57 SENSOR    - Register new sensor at JF57
"""


def demo_mesh_commands():
    """Demonstrate MESH command handler."""

    print("=" * 80)
    print("MESH Command Handler Demo - v1.2.14")
    print("=" * 80)
    print()

    # Create handler with temp data
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = DeviceRegistry(Path(tmpdir))
        handler = MeshCommandHandler(manager)

        # Setup test network
        print("Setting up test network...")
        manager.register_device("D1", "AA340", 600, DeviceType.NODE, "2.4.1")
        manager.register_device("D2", "AA340", 600, DeviceType.GATEWAY, "2.4.1")
        manager.register_device("D3", "AA340", 600, DeviceType.SENSOR, "2.4.1")
        manager.register_device("D4", "AA340", 600, DeviceType.REPEATER, "2.3.0")
        manager.register_device("D5", "AA340", 600, DeviceType.END_DEVICE, "2.4.1")

        manager.update_device_status(
            "D1", DeviceStatus.ONLINE, signal=82, uptime=24.0, msgs_per_sec=145
        )
        manager.update_device_status(
            "D2", DeviceStatus.ONLINE, signal=76, uptime=18.0, msgs_per_sec=203
        )
        manager.update_device_status(
            "D3", DeviceStatus.ONLINE, signal=91, uptime=36.0, msgs_per_sec=87
        )
        manager.update_device_status(
            "D4", DeviceStatus.OFFLINE, signal=0, uptime=0.0, msgs_per_sec=0
        )
        manager.update_device_status(
            "D5", DeviceStatus.ONLINE, signal=68, uptime=12.0, msgs_per_sec=54
        )

        manager.connect_devices("D1", "D2")
        manager.connect_devices("D1", "D3")
        manager.connect_devices("D2", "D5")
        manager.connect_devices("D3", "D5")
        print("  ✓ Test network ready (5 devices, 4 connections)")
        print()

        # Demo commands
        commands = [
            ("MESH STATS", []),
            ("MESH DEVICES", ["AA340"]),
            ("MESH INFO", ["D1"]),
            ("MESH ROUTE", ["D1", "D5"]),
            ("MESH HEATMAP", ["AA340"]),
        ]

        for cmd, args in commands:
            print(f"Command: {cmd} {' '.join(args)}")
            print("-" * 80)

            # Extract command name
            cmd_name = cmd.split()[1] if " " in cmd else cmd
            result = handler.handle(cmd_name, args)
            print(result)
            print()


if __name__ == "__main__":
    demo_mesh_commands()
