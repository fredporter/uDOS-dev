"""
PAIR Command Handler v1.0.0
Manages mobile console pairing from the TUI.

Commands:
  PAIR                    - Show pairing status / help
  PAIR NEW [name]         - Generate new pairing code (display + QR)
  PAIR LIST               - List paired mobile devices
  PAIR REVOKE <id>        - Revoke a paired device
  PAIR REVOKE ALL         - Revoke all paired devices
  PAIR STATUS             - Show pairing system status
  PAIR HELP               - Show this help

Pairing Flow:
  1. Run PAIR NEW on host device
  2. QR code + 6-digit code displayed
  3. Mobile scans QR or enters code
  4. Challenge-response verification
  5. Session token issued for mobile
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class PairHandler:
    """Handler for PAIR commands - Mobile console pairing."""

    def __init__(self, viewport=None, logger=None):
        """Initialize pair handler."""
        self.viewport = viewport
        self.logger = logger
        self._manager = None  # Lazy load

    @property
    def manager(self):
        """Lazy load pairing manager."""
        if self._manager is None:
            from dev.goblin.core.security.pairing_manager import get_pairing_manager

            self._manager = get_pairing_manager(logger=self.logger)
        return self._manager

    def handle_command(self, params: List[str]) -> str:
        """
        Route PAIR commands.

        Args:
            params: Command parameters

        Returns:
            Command result message
        """
        if not params or params[0].upper() in ["HELP", "?"]:
            return self._show_help()

        subcommand = params[0].upper()

        if subcommand == "NEW":
            device_name = " ".join(params[1:]) if len(params) > 1 else "Mobile Console"
            return self._generate_pairing(device_name)

        elif subcommand == "LIST":
            return self._list_devices()

        elif subcommand == "REVOKE":
            if len(params) < 2:
                return "❌ Usage: PAIR REVOKE <device_id> or PAIR REVOKE ALL"
            target = params[1].upper()
            if target == "ALL":
                return self._revoke_all()
            return self._revoke_device(params[1])

        elif subcommand == "STATUS":
            return self._show_status()

        else:
            # No subcommand = show status
            return self._show_status()

    def _generate_pairing(self, device_name: str) -> str:
        """Generate new pairing code and display QR."""
        code, qr_data = self.manager.generate_pairing_code(device_name)

        # Generate ASCII QR representation
        qr_ascii = self._generate_qr_ascii(qr_data)

        lines = [
            "╔═══════════════════════════════════════════════════════════════╗",
            "║              📱 MOBILE CONSOLE PAIRING                        ║",
            "╠═══════════════════════════════════════════════════════════════╣",
            f"║  Device Name: {device_name:<47}║",
            "╟───────────────────────────────────────────────────────────────╢",
            "║                                                               ║",
            f"║           PAIRING CODE:  {code}                            ║",
            "║                                                               ║",
            "║    Scan QR code or enter code in mobile uDOS app              ║",
            "║                                                               ║",
            "╟───────────────────────────────────────────────────────────────╢",
        ]

        # Add QR code
        for qr_line in qr_ascii.split("\n"):
            lines.append(f"║  {qr_line:<61}║")

        lines.extend(
            [
                "╟───────────────────────────────────────────────────────────────╢",
                f"║  ⏱️  Expires in {self.manager.PAIRING_CODE_EXPIRY_MINUTES} minutes                                      ║",
                "║                                                               ║",
                "║  📋 Mobile Console Capabilities:                              ║",
                "║     • Read-only access to workflows                           ║",
                "║     • Sandboxed file viewing                                  ║",
                "║     • Restricted command set (VIEW, LIST, HELP, etc.)         ║",
                "║     • No file write or system access                          ║",
                "╚═══════════════════════════════════════════════════════════════╝",
            ]
        )

        return "\n".join(lines)

    def _generate_qr_ascii(self, qr_data: Dict[str, Any]) -> str:
        """
        Generate ASCII representation of QR data.

        For actual QR generation, we'd use qrcode library.
        This is a placeholder showing the data structure.
        """
        import json

        data_str = json.dumps(qr_data, separators=(",", ":"))

        # Try to use qrcode library if available
        try:
            import qrcode

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=1,
                border=1,
            )
            qr.add_data(data_str)
            qr.make(fit=True)

            # Generate ASCII art
            lines = []
            matrix = qr.get_matrix()
            for row in matrix:
                line = ""
                for cell in row:
                    line += "██" if cell else "  "
                lines.append(line)
            return "\n".join(lines)
        except ImportError:
            # Fallback: show data as text
            return f"""┌─────────────────────────────────────────┐
│  QR Code (install qrcode for display)   │
├─────────────────────────────────────────┤
│  Type: {qr_data.get('type', 'udos_pairing'):<32}│
│  Code: {qr_data.get('code', '??????'):<32}│
│  Host: {qr_data.get('host_id', '???')[:32]:<32}│
└─────────────────────────────────────────┘
💡 Install qrcode: pip install qrcode"""

    def _list_devices(self) -> str:
        """List all paired mobile devices."""
        devices = self.manager.list_devices()

        lines = [
            "╔═══════════════════════════════════════════════════════════════╗",
            "║                  PAIRED MOBILE DEVICES                        ║",
            "╠═══════════════════════════════════════════════════════════════╣",
        ]

        if not devices:
            lines.append(
                "║  No devices paired                                            ║"
            )
        else:
            lines.append(
                "║  ID              │ Name            │ Status  │ Last Seen      ║"
            )
            lines.append(
                "╟─────────────────┼─────────────────┼─────────┼────────────────╢"
            )

            for device in devices:
                dev_id = device["device_id"][:15]
                name = device["device_name"][:15]
                status = "🟢 Active" if device["active"] else "🔴 Expired"

                # Parse last seen
                last_seen = device["last_seen"]
                try:
                    dt = datetime.fromisoformat(last_seen.rstrip("Z"))
                    last_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    last_str = "Unknown"

                lines.append(
                    f"║  {dev_id:<15}│ {name:<15} │ {status:<7} │ {last_str:<14} ║"
                )

        lines.append(
            "╚═══════════════════════════════════════════════════════════════╝"
        )

        if devices:
            lines.append("")
            lines.append("Commands:")
            lines.append("  PAIR REVOKE <id>  - Revoke specific device")
            lines.append("  PAIR REVOKE ALL   - Revoke all devices")

        return "\n".join(lines)

    def _revoke_device(self, device_id: str) -> str:
        """Revoke a specific paired device."""
        success, message = self.manager.revoke_device(device_id)

        if success:
            return f"✅ {message}"
        else:
            return f"❌ {message}"

    def _revoke_all(self) -> str:
        """Revoke all paired devices."""
        count, message = self.manager.revoke_all()
        return f"✅ {message}"

    def _show_status(self) -> str:
        """Show pairing system status."""
        devices = self.manager.list_devices()
        active_count = sum(1 for d in devices if d["active"])

        lines = [
            "╔═══════════════════════════════════════════════════════════════╗",
            "║                  MOBILE PAIRING STATUS                        ║",
            "╠═══════════════════════════════════════════════════════════════╣",
            f"║  Paired Devices: {len(devices)}/{self.manager.MAX_PAIRED_DEVICES:<44}║",
            f"║  Active Sessions: {active_count:<43}║",
            f"║  Code Expiry: {self.manager.PAIRING_CODE_EXPIRY_MINUTES} minutes{'':<41}║",
            f"║  Session Expiry: {self.manager.SESSION_TOKEN_EXPIRY_HOURS} hours{'':<39}║",
            "╟───────────────────────────────────────────────────────────────╢",
            "║  Commands:                                                    ║",
            "║    PAIR NEW [name]    - Generate pairing code                 ║",
            "║    PAIR LIST          - List paired devices                   ║",
            "║    PAIR REVOKE <id>   - Revoke device                         ║",
            "║    PAIR STATUS        - This screen                           ║",
            "╚═══════════════════════════════════════════════════════════════╝",
        ]

        return "\n".join(lines)

    def _show_help(self) -> str:
        """Show PAIR command help."""
        return """
╔═══════════════════════════════════════════════════════════════╗
║                    PAIR COMMAND HELP                          ║
╚═══════════════════════════════════════════════════════════════╝

📱 MOBILE CONSOLE PAIRING
─────────────────────────────────────────────────────────────────
  PAIR                    Show pairing status
  PAIR NEW [name]         Generate new pairing code
  PAIR LIST               List paired mobile devices
  PAIR REVOKE <id>        Revoke a paired device
  PAIR REVOKE ALL         Revoke all paired devices
  PAIR STATUS             Show pairing system status
  PAIR HELP               Show this help

🔐 PAIRING FLOW
─────────────────────────────────────────────────────────────────
  1. Run PAIR NEW on host device
  2. QR code + 6-digit code displayed
  3. Mobile scans QR or enters code manually
  4. Challenge-response verification
  5. Session token issued for 24 hours

📋 MOBILE CONSOLE CAPABILITIES
─────────────────────────────────────────────────────────────────
  ✓ Read-only access to workflows
  ✓ Sandboxed file viewing
  ✓ Restricted commands: VIEW, LIST, HELP, SEARCH, READ
  ✗ No file write access
  ✗ No system configuration
  ✗ No security settings

🔒 SECURITY
─────────────────────────────────────────────────────────────────
  • Pairing codes expire in 5 minutes
  • Session tokens expire in 24 hours
  • Maximum 5 paired devices
  • All communication via private transports only

📚 EXAMPLES
─────────────────────────────────────────────────────────────────
  PAIR NEW "Mom's iPad"
  PAIR LIST
  PAIR REVOKE abc123
"""
