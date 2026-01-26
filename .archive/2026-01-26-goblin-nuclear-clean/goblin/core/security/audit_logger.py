"""
uDOS Security Audit Logger
Alpha v1.0.0.2+

Logs security-relevant events to memory/logs/security-audit-YYYY-MM-DD.log
Tracks policy violations, unauthorized access attempts, and sensitive operations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from enum import Enum


class AuditEventType(Enum):
    """Types of audit events"""

    POLICY_VIOLATION = "policy_violation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ROLE_ESCALATION_ATTEMPT = "role_escalation_attempt"
    KEY_ACCESS = "key_access"
    TRANSPORT_VIOLATION = "transport_violation"
    WIZARD_OPERATION = "wizard_operation"
    SENSITIVE_OPERATION = "sensitive_operation"


class SecurityAuditor:
    """
    Security audit logger for policy violations and sensitive operations.

    All audit events are logged to memory/logs/security-audit-YYYY-MM-DD.log
    with structured JSON format for analysis.
    """

    def __init__(self, logs_dir: Path = None):
        """
        Initialize security auditor.

        Args:
            logs_dir: Directory for audit logs (default: memory/logs)
        """
        if logs_dir is None:
            logs_dir = Path(__file__).parent.parent.parent / "memory" / "logs"

        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Current audit log file (rotates daily)
        today = datetime.now().strftime("%Y-%m-%d")
        self.audit_log = self.logs_dir / f"security-audit-{today}.log"

    def log_event(
        self,
        event_type: AuditEventType,
        severity: str,
        message: str,
        context: Dict[str, Any],
        user: str = None,
        role: str = None,
        transport: str = None,
    ):
        """
        Log a security audit event.

        Args:
            event_type: Type of audit event
            severity: CRITICAL, ERROR, WARNING, INFO
            message: Human-readable description
            context: Additional context (command, module, params, etc.)
            user: User identifier (if available)
            role: Role attempting operation
            transport: Transport used
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "severity": severity,
            "message": message,
            "context": context,
            "user": user,
            "role": role,
            "transport": transport,
        }

        # Write to audit log
        with open(self.audit_log, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")

        # Also print to console for immediate visibility
        severity_symbols = {
            "CRITICAL": "🔴",
            "ERROR": "🚨",
            "WARNING": "⚠️",
            "INFO": "ℹ️",
        }
        symbol = severity_symbols.get(severity, "•")
        print(f"{symbol} [AUDIT] {severity}: {message}")

    def log_policy_violation(
        self,
        code: str,
        message: str,
        rule: str,
        command: str,
        role: str,
        transport: str,
        realm: str,
        recommendation: str = None,
    ):
        """
        Log a transport policy violation.

        Args:
            code: Error code (e.g., WIZARD_ONLY_VIOLATION)
            message: Violation description
            rule: Policy rule violated
            command: Command that was blocked
            role: Role attempting command
            transport: Transport used
            realm: Realm context
            recommendation: Suggested alternative
        """
        context = {
            "code": code,
            "rule": rule,
            "command": command,
            "realm": realm,
            "recommendation": recommendation,
        }

        self.log_event(
            event_type=AuditEventType.POLICY_VIOLATION,
            severity="ERROR",
            message=message,
            context=context,
            role=role,
            transport=transport,
        )

    def log_transport_violation(
        self, transport: str, violation_type: str, command: str, role: str, message: str
    ):
        """
        Log a transport-specific violation (e.g., Bluetooth Public data attempt).

        Args:
            transport: Transport used
            violation_type: Type of violation
            command: Command attempted
            role: Role attempting
            message: Description
        """
        context = {"violation_type": violation_type, "command": command}

        self.log_event(
            event_type=AuditEventType.TRANSPORT_VIOLATION,
            severity="CRITICAL" if transport == "bluetooth_public" else "ERROR",
            message=message,
            context=context,
            role=role,
            transport=transport,
        )

    def log_wizard_operation(
        self, operation: str, details: Dict[str, Any], cost: float = None
    ):
        """
        Log a Wizard Server operation (for accountability and cost tracking).

        Args:
            operation: Operation type (web_fetch, api_call, gmail_send, etc.)
            details: Operation details
            cost: Associated cost (if applicable)
        """
        context = {"operation": operation, "details": details, "cost": cost}

        self.log_event(
            event_type=AuditEventType.WIZARD_OPERATION,
            severity="INFO",
            message=f"Wizard operation: {operation}",
            context=context,
            role="wizard_server",
            transport="internet",
        )

    def log_key_access(
        self,
        key_name: str,
        realm: str,
        role: str,
        access_granted: bool,
        reason: str = None,
    ):
        """
        Log key access attempts (both successful and denied).

        Args:
            key_name: Key identifier
            realm: Key realm (user_mesh, wizard_only)
            role: Role requesting access
            access_granted: Whether access was granted
            reason: Denial reason (if applicable)
        """
        context = {
            "key_name": key_name,
            "realm": realm,
            "access_granted": access_granted,
            "reason": reason,
        }

        severity = "INFO" if access_granted else "WARNING"
        message = f"Key access {'granted' if access_granted else 'denied'}: {key_name}"

        self.log_event(
            event_type=AuditEventType.KEY_ACCESS,
            severity=severity,
            message=message,
            context=context,
            role=role,
        )

    def query_recent(
        self, event_type: AuditEventType = None, severity: str = None, limit: int = 100
    ) -> list:
        """
        Query recent audit events.

        Args:
            event_type: Filter by event type
            severity: Filter by severity
            limit: Maximum events to return

        Returns:
            List of audit events (most recent first)
        """
        if not self.audit_log.exists():
            return []

        events = []
        with open(self.audit_log, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())

                    # Apply filters
                    if event_type and event.get("event_type") != event_type.value:
                        continue
                    if severity and event.get("severity") != severity:
                        continue

                    events.append(event)
                except:
                    pass

        # Return most recent first
        return list(reversed(events))[-limit:]

    def get_violation_summary(self, days: int = 7) -> Dict[str, int]:
        """
        Get summary of policy violations over the past N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with violation counts by type
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        summary = {}

        # Check logs from past N days
        for i in range(days + 1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = self.logs_dir / f"security-audit-{date}.log"

            if not log_file.exists():
                continue

            with open(log_file, "r") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())

                        # Only count policy violations
                        if (
                            event.get("event_type")
                            == AuditEventType.POLICY_VIOLATION.value
                        ):
                            code = event.get("context", {}).get("code", "UNKNOWN")
                            summary[code] = summary.get(code, 0) + 1
                    except:
                        pass

        return summary


# Singleton instance
_auditor = None


def get_auditor() -> SecurityAuditor:
    """Get global security auditor instance"""
    global _auditor
    if _auditor is None:
        _auditor = SecurityAuditor()
    return _auditor


def log_policy_violation(
    code: str,
    message: str,
    rule: str,
    command: str,
    role: str,
    transport: str,
    realm: str,
    recommendation: str = None,
):
    """Convenience function to log policy violation"""
    auditor = get_auditor()
    auditor.log_policy_violation(
        code=code,
        message=message,
        rule=rule,
        command=command,
        role=role,
        transport=transport,
        realm=realm,
        recommendation=recommendation,
    )


# Example usage
if __name__ == "__main__":
    print("🔐 Security Audit Logger Test\n")

    auditor = SecurityAuditor()

    # Test policy violation
    auditor.log_policy_violation(
        code="WIZARD_ONLY_VIOLATION",
        message="User Mesh device attempted web access",
        rule="user_mesh_offline",
        command="WEB",
        role="device_owner",
        transport="internet",
        realm="user_mesh",
        recommendation="Use Wizard Server for web operations",
    )

    # Test transport violation
    auditor.log_transport_violation(
        transport="bluetooth_public",
        violation_type="DATA_TRANSFER_ATTEMPT",
        command="MESH",
        role="device_owner",
        message="Bluetooth Public used for data transfer (FORBIDDEN)",
    )

    # Test Wizard operation
    auditor.log_wizard_operation(
        operation="api_call",
        details={"provider": "gemini", "model": "gemini-pro"},
        cost=0.0003,
    )

    # Test key access
    auditor.log_key_access(
        key_name="gemini_api_key",
        realm="wizard_only",
        role="device_owner",
        access_granted=False,
        reason="Key realm mismatch (wizard_only vs user_mesh)",
    )

    print("\n📋 Recent audit events:")
    recent = auditor.query_recent(limit=10)
    for event in recent:
        print(f"  - [{event['severity']}] {event['message']}")

    print("\n📊 Violation summary (last 7 days):")
    summary = auditor.get_violation_summary(days=7)
    for code, count in summary.items():
        print(f"  {code}: {count}")

    print("\n✅ Audit logger test complete")
    print(f"📂 Log file: {auditor.audit_log}")
