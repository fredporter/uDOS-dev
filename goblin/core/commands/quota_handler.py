"""
Quota Command Handler
=====================

TUI commands for viewing and managing API quotas.

Commands:
- QUOTA                 - Show quota dashboard summary
- QUOTA STATUS          - Detailed status of all providers
- QUOTA PROVIDER <name> - Status for specific provider
- QUOTA LIMIT <provider> <daily> [monthly] - Set budget limits
- QUOTA HISTORY [limit] - Recent API request history
- QUOTA QUEUE           - View queued requests
- QUOTA RESET <provider> [daily|monthly] - Reset counters (admin)

Version: 1.0.0
Alpha: v1.0.0.63+
"""

from typing import List, Optional
from pathlib import Path

from dev.goblin.core.commands.base_handler import BaseCommandHandler
from dev.goblin.core.commands.handler_utils import HandlerUtils
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("command-quota")

# Try to import quota tracker
try:
    from wizard.services.quota_tracker import (
        get_quota_tracker,
        APIProvider,
        QuotaStatus,
    )

    QUOTA_AVAILABLE = True
except ImportError:
    QUOTA_AVAILABLE = False
    logger.debug("[LOCAL] QuotaTracker not available")


class QuotaHandler(BaseCommandHandler):
    """Handler for QUOTA commands."""

    def __init__(self, config=None):
        """Initialize quota handler."""
        super().__init__(config or HandlerUtils.get_config())

    def handle_command(self, command: str, args: List[str]) -> str:
        """
        Route QUOTA commands.

        Args:
            command: Command name (QUOTA)
            args: Command arguments

        Returns:
            Formatted result string
        """
        if not QUOTA_AVAILABLE:
            return self._format_unavailable()

        if not args:
            return self._handle_summary()

        subcommand = args[0].upper()
        sub_args = args[1:] if len(args) > 1 else []

        handlers = {
            "STATUS": self._handle_status,
            "PROVIDER": self._handle_provider,
            "LIMIT": self._handle_limit,
            "LIMITS": self._handle_limit,
            "HISTORY": self._handle_history,
            "QUEUE": self._handle_queue,
            "CHECK": self._handle_check,
            "RESET": self._handle_reset,
            "HELP": self._handle_help,
        }

        handler = handlers.get(subcommand)
        if handler:
            return handler(sub_args)

        # If first arg looks like a provider name, show that provider
        try:
            provider = APIProvider(subcommand.lower())
            return self._handle_provider([subcommand])
        except ValueError:
            pass

        return f"❌ Unknown QUOTA subcommand: {subcommand}\n\n{self._handle_help([])}"

    def _format_unavailable(self) -> str:
        """Format message when quota tracker unavailable."""
        return """╔══════════════════════════════════════════╗
║  ⚠️  QUOTA TRACKER UNAVAILABLE          ║
╠══════════════════════════════════════════╣
║  Wizard Server required for quota        ║
║  tracking. This is a Realm B feature.    ║
║                                          ║
║  Install: pip install cryptography httpx ║
╚══════════════════════════════════════════╝"""

    def _handle_summary(self) -> str:
        """Show quota dashboard summary."""
        tracker = get_quota_tracker()
        summary = tracker.get_dashboard_summary()

        # Build output
        lines = [
            "╔══════════════════════════════════════════╗",
            "║         📊 API QUOTA DASHBOARD           ║",
            "╠══════════════════════════════════════════╣",
            f"║  💰 Today's Cost:     {summary['cost_today']:>15} ║",
            f"║  📈 Month Cost:       {summary['cost_this_month']:>15} ║",
            f"║  📡 Requests Today:   {summary['requests_today']:>15} ║",
            f"║  🔌 Active Providers: {summary['active_providers']:>15} ║",
            f"║  📋 Queue Size:       {summary['queue_size']:>15} ║",
        ]

        if summary.get("warnings"):
            lines.append("╠══════════════════════════════════════════╣")
            lines.append("║  ⚠️  WARNINGS:                           ║")
            for warning in summary["warnings"][:3]:
                lines.append(f"║  {warning:<38} ║")

        lines.extend(
            [
                "╠══════════════════════════════════════════╣",
                "║  Commands: QUOTA STATUS | QUOTA PROVIDER ║",
                "║            QUOTA LIMIT  | QUOTA HISTORY  ║",
                "╚══════════════════════════════════════════╝",
            ]
        )

        return "\n".join(lines)

    def _handle_status(self, args: List[str]) -> str:
        """Show detailed status of all providers."""
        tracker = get_quota_tracker()
        all_quotas = tracker.get_all_quotas()

        lines = [
            "┌──────────────┬────────────┬─────────────┬─────────────┬────────┐",
            "│ Provider     │ Status     │ Daily Used  │ Budget      │ Usage% │",
            "├──────────────┼────────────┼─────────────┼─────────────┼────────┤",
        ]

        for provider, data in all_quotas.get("providers", {}).items():
            status = data.get("status", "ok")
            status_icon = {
                "ok": "✅",
                "warning": "🟡",
                "critical": "🔴",
                "exceeded": "⛔",
                "rate_limited": "⏳",
            }.get(status, "❓")

            daily = data.get("daily", {})
            cost = f"${daily.get('cost', 0):.2f}"
            budget = f"${daily.get('budget', 0):.2f}"
            usage_pct = f"{daily.get('usage_percent', 0):.0f}%"

            lines.append(
                f"│ {provider:<12} │ {status_icon} {status:<7} │ {cost:>11} │ {budget:>11} │ {usage_pct:>6} │"
            )

        lines.extend(
            [
                "├──────────────┴────────────┴─────────────┴─────────────┴────────┤",
                f"│ TOTALS: ${all_quotas['totals']['cost_today']:.2f} today | ${all_quotas['totals']['cost_this_month']:.2f} this month | {all_quotas['totals']['requests_today']} requests │",
                "└─────────────────────────────────────────────────────────────────┘",
            ]
        )

        return "\n".join(lines)

    def _handle_provider(self, args: List[str]) -> str:
        """Show status for specific provider."""
        if not args:
            return "❌ Usage: QUOTA PROVIDER <name>\n   Example: QUOTA PROVIDER gemini"

        provider_name = args[0].lower()

        try:
            provider = APIProvider(provider_name)
        except ValueError:
            valid = ", ".join(p.value for p in APIProvider)
            return f"❌ Unknown provider: {provider_name}\n   Valid: {valid}"

        tracker = get_quota_tracker()
        status = tracker.get_quota_status(provider)

        if not status.get("configured"):
            return f"⚠️ Provider '{provider_name}' not configured"

        daily = status.get("daily", {})
        monthly = status.get("monthly", {})
        totals = status.get("totals", {})
        rate = status.get("rate_limit", {})

        status_icon = {
            "ok": "✅ OK",
            "warning": "🟡 WARNING",
            "critical": "🔴 CRITICAL",
            "exceeded": "⛔ EXCEEDED",
            "rate_limited": "⏳ RATE LIMITED",
        }.get(status.get("status", "ok"), "❓ UNKNOWN")

        return f"""
╔══════════════════════════════════════════════════╗
║  📡 {provider_name.upper():^42} ║
╠══════════════════════════════════════════════════╣
║  Status: {status_icon:<38} ║
╠══════════════════════════════════════════════════╣
║  📅 DAILY                                        ║
║    Requests: {daily.get('requests', 0):>8} / {daily.get('limit', 0):<8} ({daily.get('usage_percent', 0):.0f}%)     ║
║    Tokens:   {daily.get('tokens', 0):>8} / {daily.get('token_limit', 0):<8}            ║
║    Cost:     ${daily.get('cost', 0):<7.4f} / ${daily.get('budget', 0):<7.2f}           ║
╠══════════════════════════════════════════════════╣
║  📆 MONTHLY                                      ║
║    Requests: {monthly.get('requests', 0):>8} / {monthly.get('limit', 0):<8}            ║
║    Cost:     ${monthly.get('cost', 0):<7.4f} / ${monthly.get('budget', 0):<7.2f}           ║
╠══════════════════════════════════════════════════╣
║  ⚡ RATE LIMIT                                   ║
║    This minute: {rate.get('requests_this_minute', 0):>3} / {rate.get('limit_per_minute', 60):<3}                       ║
╠══════════════════════════════════════════════════╣
║  📊 LIFETIME                                     ║
║    Total requests: {totals.get('requests', 0):<10}                    ║
║    Total cost:     ${totals.get('cost', 0):<10.4f}                 ║
╚══════════════════════════════════════════════════╝"""

    def _handle_limit(self, args: List[str]) -> str:
        """Set budget limits for a provider."""
        if len(args) < 2:
            return """❌ Usage: QUOTA LIMIT <provider> <daily_budget> [monthly_budget]
   
   Examples:
     QUOTA LIMIT gemini 5.00        # Set $5/day
     QUOTA LIMIT gemini 5.00 50.00  # Set $5/day, $50/month
     QUOTA LIMIT anthropic 10.00"""

        provider_name = args[0].lower()

        try:
            provider = APIProvider(provider_name)
        except ValueError:
            return f"❌ Unknown provider: {provider_name}"

        try:
            daily_budget = float(args[1])
        except ValueError:
            return f"❌ Invalid daily budget: {args[1]}"

        monthly_budget = None
        if len(args) > 2:
            try:
                monthly_budget = float(args[2])
            except ValueError:
                return f"❌ Invalid monthly budget: {args[2]}"

        tracker = get_quota_tracker()
        tracker.update_provider_limits(
            provider,
            daily_budget=daily_budget,
            monthly_budget=monthly_budget,
        )

        return f"""✅ Updated {provider_name} limits:
   Daily budget:   ${daily_budget:.2f}
   Monthly budget: ${monthly_budget:.2f if monthly_budget else 'unchanged'}"""

    def _handle_history(self, args: List[str]) -> str:
        """Show recent API request history."""
        limit = 10
        if args:
            try:
                limit = int(args[0])
            except ValueError:
                pass

        tracker = get_quota_tracker()
        history = tracker._history[-limit:]

        if not history:
            return "📜 No API request history yet"

        lines = [
            "┌──────────────────────┬────────────┬────────┬──────────┐",
            "│ Timestamp            │ Provider   │ Tokens │ Cost     │",
            "├──────────────────────┼────────────┼────────┼──────────┤",
        ]

        for entry in reversed(history):
            ts = entry.get("timestamp", "")[:19]
            provider = entry.get("provider", "?")[:10]
            tokens = entry.get("tokens_input", 0) + entry.get("tokens_output", 0)
            cost = entry.get("cost", 0)
            success = "✓" if entry.get("success") else "✗"

            lines.append(f"│ {ts} │ {provider:<10} │ {tokens:>6} │ ${cost:<7.4f} │")

        lines.append("└──────────────────────┴────────────┴────────┴──────────┘")

        return "\n".join(lines)

    def _handle_queue(self, args: List[str]) -> str:
        """Show queued requests."""
        tracker = get_quota_tracker()
        queue_status = tracker.get_queue_status()

        lines = [
            "╔══════════════════════════════════════════╗",
            "║         📋 REQUEST QUEUE                 ║",
            "╠══════════════════════════════════════════╣",
            f"║  Pending:    {queue_status.get('pending', 0):>25} ║",
            f"║  Processing: {queue_status.get('processing', 0):>25} ║",
        ]

        by_priority = queue_status.get("by_priority", {})
        if by_priority:
            lines.append("╠══════════════════════════════════════════╣")
            lines.append("║  By Priority:                            ║")
            for priority, count in by_priority.items():
                lines.append(f"║    {priority:<15} {count:>20} ║")

        by_provider = queue_status.get("by_provider", {})
        if by_provider:
            lines.append("╠══════════════════════════════════════════╣")
            lines.append("║  By Provider:                            ║")
            for provider, count in by_provider.items():
                lines.append(f"║    {provider:<15} {count:>20} ║")

        est_cost = queue_status.get("estimated_cost", 0)
        lines.extend(
            [
                "╠══════════════════════════════════════════╣",
                f"║  Est. Cost:  ${est_cost:<25.4f} ║",
                "╚══════════════════════════════════════════╝",
            ]
        )

        return "\n".join(lines)

    def _handle_check(self, args: List[str]) -> str:
        """Check if a request can be made."""
        if not args:
            return "❌ Usage: QUOTA CHECK <provider> [tokens]"

        provider_name = args[0].lower()
        tokens = 1000
        if len(args) > 1:
            try:
                tokens = int(args[1])
            except ValueError:
                pass

        try:
            provider = APIProvider(provider_name)
        except ValueError:
            return f"❌ Unknown provider: {provider_name}"

        tracker = get_quota_tracker()
        can_request = tracker.can_request(provider, tokens)
        status = tracker.get_quota_status(provider)

        if can_request:
            return f"""✅ Request ALLOWED for {provider_name}
   Estimated tokens: {tokens}
   Daily usage: {status.get('daily', {}).get('usage_percent', 0):.0f}%"""
        else:
            return f"""⛔ Request BLOCKED for {provider_name}
   Reason: Quota exceeded or rate limited
   Status: {status.get('status', 'unknown')}
   Daily usage: {status.get('daily', {}).get('usage_percent', 0):.0f}%"""

    def _handle_reset(self, args: List[str]) -> str:
        """Reset counters for a provider (admin only)."""
        if not args:
            return "❌ Usage: QUOTA RESET <provider> [daily|monthly|all]"

        provider_name = args[0].lower()
        period = args[1].lower() if len(args) > 1 else "daily"

        try:
            provider = APIProvider(provider_name)
        except ValueError:
            return f"❌ Unknown provider: {provider_name}"

        tracker = get_quota_tracker()
        quota = tracker._quotas.get(provider)

        if not quota:
            return f"❌ Provider {provider_name} not found"

        if period in ("daily", "all"):
            quota.requests_today = 0
            quota.tokens_today = 0
            quota.cost_today = 0.0

        if period in ("monthly", "all"):
            quota.requests_this_month = 0
            quota.tokens_this_month = 0
            quota.cost_this_month = 0.0

        tracker._save_quotas()

        return f"✅ Reset {period} counters for {provider_name}"

    def _handle_help(self, args: List[str]) -> str:
        """Show help for QUOTA commands."""
        return """╔══════════════════════════════════════════════════╗
║              📊 QUOTA COMMANDS                   ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  QUOTA              Dashboard summary            ║
║  QUOTA STATUS       All providers status table   ║
║  QUOTA <provider>   Specific provider details    ║
║                                                  ║
║  QUOTA LIMIT <provider> <daily> [monthly]        ║
║                     Set budget limits            ║
║                                                  ║
║  QUOTA HISTORY [n]  Recent request history       ║
║  QUOTA QUEUE        View queued requests         ║
║  QUOTA CHECK <p> [tokens]                        ║
║                     Check if request allowed     ║
║                                                  ║
║  Providers: gemini, anthropic, openai, mistral,  ║
║             github, spotify, discord, notion     ║
║                                                  ║
╚══════════════════════════════════════════════════╝"""


# Module-level handler function for uDOS_commands.py
def handle_quota_command(command_line: str) -> str:
    """
    Handle QUOTA command from TUI.

    Args:
        command_line: Full command line (e.g., "QUOTA STATUS")

    Returns:
        Formatted result
    """
    parts = command_line.strip().split()

    if not parts or parts[0].upper() != "QUOTA":
        return "❌ Invalid command"

    args = parts[1:] if len(parts) > 1 else []

    handler = QuotaHandler()
    return handler.handle_command("QUOTA", args)
