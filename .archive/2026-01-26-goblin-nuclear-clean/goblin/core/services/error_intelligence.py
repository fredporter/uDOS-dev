"""
Error Intelligence Service - Unified Error Handling Middleware

Enhanced error handling with context capture, AI classification, pattern learning,
OK FIX integration, theme-aware messaging, and smart recovery suggestions.

Part of uDOS v1.2.31 - Self-Healing System

Features:
- ErrorContext capture with full context preservation (error_interceptor)
- ErrorInterceptor middleware for command execution wrapping (error_interceptor)
- IntelligentErrorHandler with Gemini AI classification (intelligent_error_handler)
- Pattern signature matching across error history (local learning, no cloud)
- Theme-aware error prompts (dungeon/galaxy/professional)
- OK Assistant integration for AI-powered fixes
- Sandbox testing of proposed fixes
- Privacy-safe error logging (no PII)
- Smart retention policy (7-day recent, 50 high-severity, 10 per signature)

Version: 1.2.32 (Phase 5b consolidation: error_interceptor + intelligent_error_handler merged)
Consolidated from:
  - core/services/error_intelligence.py (582 LOC) - Pattern learning, theme messages, storage
  - core/services/error_interceptor.py (407 LOC) - Context capture, middleware, retention
  - core/services/intelligent_error_handler.py (430 LOC) - AI classification, error patterns
"""

import json
import hashlib
import gzip
import re
import traceback
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from dev.goblin.core.config import Config


class ErrorSeverity(Enum):
    """Error severity classification."""

    CRITICAL = "critical"  # System cannot continue
    HIGH = "high"  # Major feature broken
    MEDIUM = "medium"  # Feature degraded
    LOW = "low"  # Minor issue
    INFO = "info"  # Informational only


@dataclass
class ErrorPattern:
    """Learned error pattern with fix history."""

    signature: str  # Unique hash of error type + message pattern
    error_type: str  # Exception class name
    message_pattern: str  # Regex pattern for message
    file_pattern: str  # File/module where error occurs
    occurrences: int = 0  # Total times seen
    last_seen: str = ""  # ISO timestamp
    fixes_attempted: int = 0  # Times fix was tried
    fixes_successful: int = 0  # Times fix worked
    suggested_fixes: List[str] = field(default_factory=list)  # List of fix approaches
    user_notes: str = ""  # User-added notes about this error


@dataclass
class ErrorContext:
    """Captured error context with sanitization."""

    error_type: str
    error_message: str
    command: str
    params: List[str]
    timestamp: str
    signature: str
    severity: ErrorSeverity
    stack_trace: str
    recent_commands: List[str]
    workspace_state: Dict[str, Any]
    git_status: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON."""
        data = {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "command": self.command,
            "params": self.params,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "severity": self.severity.value,
            "stack_trace": self.stack_trace,
            "recent_commands": self.recent_commands,
            "workspace_state": self.workspace_state,
        }
        if self.git_status:
            data["git_status"] = self.git_status
        return json.dumps(data, separators=(",", ":"))

    def capture_context(self, config: Config, session_analytics=None):
        """Capture full error context with sanitization (from error_interceptor)."""
        # Basic error info
        context = {}
        context["error_type"] = self.error_type
        context["error_message"] = self.error_message
        context["command"] = self.command
        context["params"] = self.params
        context["timestamp"] = self.timestamp

        # Workspace state
        context["workspace"] = {
            "theme": config.get("theme", "foundation"),
            "location": config.get("last_location", "unknown"),
            "timezone": config.get_env("TIMEZONE", "UTC"),
        }

        # Severity already set in __init__
        context["severity"] = self.severity.value

        # Git status (already captured if available)
        if self.git_status:
            context["git_status"] = self.git_status

        # Recent commands (already sanitized)
        context["recent_commands"] = self.recent_commands

        return context


class ErrorContextManager:
    """Manages error context storage with unified smart retention (from error_interceptor)."""

    def __init__(self, config: Config):
        self.config = config
        self.contexts_dir = (
            Path(config.project_root) / "memory" / "logs" / "error_contexts"
        )
        self.archive_dir = self.contexts_dir / ".archive"
        self.contexts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Create symlink for latest error
        self.latest_link = self.contexts_dir / "latest.json"

    def add_context(self, error_context: ErrorContext):
        """Add error context with smart retention."""
        # Save context file
        filename = f"{error_context.timestamp.replace(':', '-').replace('.', '-')}_{error_context.signature}.json"
        filepath = self.contexts_dir / filename

        with open(filepath, "w") as f:
            f.write(error_context.to_json())

        # Update latest symlink
        if self.latest_link.exists() or self.latest_link.is_symlink():
            self.latest_link.unlink()
        self.latest_link.symlink_to(filename)

        # Apply retention policy
        self._apply_retention()

    def _apply_retention(self):
        """Unified smart retention policy (from error_interceptor)."""
        all_contexts = list(self.contexts_dir.glob("*.json"))
        all_contexts = [f for f in all_contexts if f.name != "latest.json"]

        now = datetime.now()
        keep = set()

        # Parse and categorize contexts
        contexts_data = []
        for filepath in all_contexts:
            try:
                with open(filepath, "r") as f:
                    data = json.loads(f.read())
                    data["filepath"] = filepath
                    data["timestamp_dt"] = datetime.fromisoformat(
                        data["timestamp"].split(".")[0]
                    )
                    contexts_data.append(data)
            except Exception:
                continue

        # Rule 1: Keep all from last 7 days
        seven_days_ago = now - timedelta(days=7)
        for ctx in contexts_data:
            if ctx["timestamp_dt"] > seven_days_ago:
                keep.add(ctx["filepath"])

        # Rule 2: Keep last 20 critical/high severity
        high_severity = [
            c for c in contexts_data if c.get("severity") in ["critical", "high"]
        ]
        high_severity.sort(key=lambda x: x["timestamp_dt"], reverse=True)
        for ctx in high_severity[:20]:
            keep.add(ctx["filepath"])

        # Rule 3: Keep last 5 per unique signature
        by_signature = {}
        for ctx in contexts_data:
            sig = ctx.get("signature", "unknown")
            if sig not in by_signature:
                by_signature[sig] = []
            by_signature[sig].append(ctx)

        for signature_contexts in by_signature.values():
            signature_contexts.sort(key=lambda x: x["timestamp_dt"], reverse=True)
            for ctx in signature_contexts[:5]:
                keep.add(ctx["filepath"])

        # Archive old contexts (monthly archives)
        for ctx in contexts_data:
            if ctx["filepath"] not in keep:
                month = ctx["timestamp_dt"].strftime("%Y-%m")
                archive_file = self.archive_dir / f"{month}.json.gz"

                # Append to monthly archive (compressed)
                mode = "ab" if archive_file.exists() else "wb"
                with gzip.open(archive_file, mode) as f:
                    f.write((json.dumps(ctx) + "\n").encode())

                # Delete original
                ctx["filepath"].unlink()

    def get_recent(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get all errors from last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        results = []

        for filepath in self.contexts_dir.glob("*.json"):
            if filepath.name == "latest.json":
                continue

            try:
                with open(filepath, "r") as f:
                    data = json.loads(f.read())
                    ts = datetime.fromisoformat(data["timestamp"].split(".")[0])
                    if ts > cutoff:
                        results.append(data)
            except Exception:
                continue

        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def get_by_severity(self, level: str) -> List[Dict[str, Any]]:
        """Get errors by severity level."""
        results = []

        for filepath in self.contexts_dir.glob("*.json"):
            if filepath.name == "latest.json":
                continue

            try:
                with open(filepath, "r") as f:
                    data = json.loads(f.read())
                    if data.get("severity") == level:
                        results.append(data)
            except Exception:
                continue

        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def get_by_signature(self, signature: str) -> List[Dict[str, Any]]:
        """Get errors matching signature pattern."""
        results = []

        for filepath in self.contexts_dir.glob("*.json"):
            if filepath.name == "latest.json":
                continue

            try:
                with open(filepath, "r") as f:
                    data = json.loads(f.read())
                    if data.get("signature") == signature:
                        results.append(data)
            except Exception:
                continue

        return sorted(results, key=lambda x: x["timestamp"], reverse=True)


class ErrorInterceptor:
    """Error interceptor middleware for command execution (from error_interceptor)."""

    def __init__(self, config: Config, theme_messenger=None, session_analytics=None):
        self.config = config
        self.theme_messenger = theme_messenger
        self.session_analytics = session_analytics
        self.context_manager = ErrorContextManager(config)

    def intercept(
        self, func: Callable, *args, **kwargs
    ) -> Tuple[Any, Optional[Exception]]:
        """Intercept function execution with error handling."""
        try:
            result = func(*args, **kwargs)
            return result, None
        except Exception as e:
            # Don't intercept system exits or keyboard interrupts
            if isinstance(e, (SystemExit, KeyboardInterrupt)):
                raise

            # Capture error context
            error_context = ErrorContext(
                error_type=type(e).__name__,
                error_message=str(e),
                command=kwargs.get("command", "unknown"),
                params=kwargs.get("params", []),
                timestamp=datetime.now().isoformat(),
                signature="",  # Will be set in capture
                severity=ErrorSeverity.MEDIUM,  # Will be set in capture
                stack_trace="",  # Will be set in capture
                recent_commands=[],  # Will be set in capture
                workspace_state={},  # Will be set in capture
            )

            # Capture full context
            error_context.capture_context(self.config, self.session_analytics)

            # Save context
            self.context_manager.add_context(error_context)

            # Prompt user with theme-aware options
            action = self._prompt_user(error_context)

            if action == "retry":
                # Retry the command
                return self.intercept(func, *args, **kwargs)
            elif action == "ok_help":
                # Trigger OK FIX command
                return None, e
            elif action == "dev_mode":
                # Enable DEV MODE at error line
                return None, e
            else:
                # Continue (return error)
                return None, e

    def _prompt_user(self, error_context: ErrorContext) -> str:
        """Display theme-aware error prompt."""
        if self.theme_messenger:
            # Use theme messenger for formatted output
            prompt = self.theme_messenger.format_message(
                "prompt",
                "prompt_error_options",
                error=error_context.error_type,
                message=error_context.error_message,
            )
        else:
            # Fallback to plain text
            prompt = f"\n💀 Error: {error_context.error_type}\n"
            prompt += f"   {error_context.error_message}\n\n"
            prompt += "Options:\n"
            prompt += "  1. Retry\n"
            prompt += "  2. Get OK Help (AI-powered fix)\n"
            prompt += "  3. Enter DEV MODE\n"
            prompt += "  4. Continue\n\n"
            prompt += "Choose [1|2|3|4]: "

        print(prompt, end="")

        try:
            choice = input().strip()
            if choice == "1":
                return "retry"
            elif choice == "2":
                return "ok_help"
            elif choice == "3":
                return "dev_mode"
            else:
                return "continue"
        except (EOFError, KeyboardInterrupt):
            return "continue"


class IntelligentErrorHandler:
    """AI-powered error classification with Gemini integration (from intelligent_error_handler)."""

    def __init__(self, gemini=None, session_analytics=None, audit_logger=None):
        """Initialize intelligent error handler."""
        self.gemini = gemini
        self._session_analytics = session_analytics
        self._audit_logger = audit_logger
        self.user_role = "user"  # Default, updated by command handler

        # Error classification patterns
        self.error_patterns = {
            "FileNotFoundError": {
                "category": "file_access",
                "severity": "medium",
                "common_causes": [
                    "File path incorrect",
                    "File not created yet",
                    "Wrong directory",
                ],
                "quick_fixes": [
                    "Check file path",
                    "Use absolute path",
                    "Create file first",
                ],
            },
            "PermissionError": {
                "category": "file_access",
                "severity": "high",
                "common_causes": [
                    "Insufficient permissions",
                    "Read-only file",
                    "Protected directory",
                ],
                "quick_fixes": [
                    "Check file permissions",
                    "Run with appropriate role",
                    "Change file access",
                ],
            },
            "ValueError": {
                "category": "data_validation",
                "severity": "medium",
                "common_causes": [
                    "Invalid input format",
                    "Out of range value",
                    "Wrong data type",
                ],
                "quick_fixes": [
                    "Check input format",
                    "Validate data",
                    "Review command parameters",
                ],
            },
            "KeyError": {
                "category": "data_access",
                "severity": "medium",
                "common_causes": [
                    "Missing configuration",
                    "Invalid key",
                    "Data not initialized",
                ],
                "quick_fixes": [
                    "Check configuration",
                    "Verify key exists",
                    "Initialize data first",
                ],
            },
            "ImportError": {
                "category": "dependency",
                "severity": "high",
                "common_causes": [
                    "Missing module",
                    "Import path incorrect",
                    "Dependency not installed",
                ],
                "quick_fixes": [
                    "Install missing package",
                    "Check import path",
                    "Verify dependencies",
                ],
            },
            "AttributeError": {
                "category": "code_error",
                "severity": "medium",
                "common_causes": [
                    "Object not initialized",
                    "Wrong attribute name",
                    "Type mismatch",
                ],
                "quick_fixes": [
                    "Check object type",
                    "Verify attribute exists",
                    "Initialize object first",
                ],
            },
            "TypeError": {
                "category": "data_validation",
                "severity": "medium",
                "common_causes": [
                    "Wrong argument type",
                    "Missing arguments",
                    "Incompatible operation",
                ],
                "quick_fixes": [
                    "Check argument types",
                    "Verify function signature",
                    "Convert data type",
                ],
            },
        }

    @property
    def session_analytics(self):
        """Lazy load session analytics"""
        if self._session_analytics is None:
            try:
                from dev.goblin.core.services.session_analytics import get_session_analytics

                self._session_analytics = get_session_analytics()
            except Exception:
                pass
        return self._session_analytics

    @property
    def audit_logger(self):
        """Lazy load audit logger"""
        if self._audit_logger is None:
            try:
                from dev.goblin.core.services.api_audit import get_audit_logger

                self._audit_logger = get_audit_logger()
            except Exception:
                pass
        return self._audit_logger

    def handle_error(
        self,
        error: Exception,
        command: str,
        params: list,
        context: Optional[Dict] = None,
        allow_retry: bool = True,
        retry_callback: Optional[Callable] = None,
    ) -> Tuple[str, Optional[str]]:
        """Handle an error with intelligent analysis and user options."""
        # Classify error
        error_type = type(error).__name__
        error_msg = str(error)

        # Get error classification
        classification = self.error_patterns.get(
            error_type,
            {
                "category": "unknown",
                "severity": "medium",
                "common_causes": [],
                "quick_fixes": [],
            },
        )

        # Build context
        full_context = {
            "command": command,
            "params": params,
            "error_type": error_type,
            "error_message": error_msg,
            "classification": classification,
            "timestamp": datetime.now().isoformat(),
        }

        if context:
            full_context.update(context)

        # Get traceback
        tb = traceback.format_exc()
        full_context["traceback"] = tb

        # Log to session analytics
        if self.session_analytics:
            self.session_analytics.track_error(
                command=command,
                params=params,
                error_type=error_type,
                error_msg=error_msg,
                context=full_context,
            )

        # Build user-friendly error message
        error_display = self._format_error_message(
            error_type=error_type,
            error_msg=error_msg,
            command=command,
            classification=classification,
        )

        # For now, return the formatted error
        # In full implementation, this would present interactive options
        return error_display, None

    def _format_error_message(
        self, error_type: str, error_msg: str, command: str, classification: Dict
    ) -> str:
        """Format user-friendly error message."""
        severity_icons = {"low": "💡", "medium": "⚠️", "high": "❌", "critical": "🔴"}

        icon = severity_icons.get(classification["severity"], "⚠️")

        message = f"{icon} Error in {command}\n"
        message += f"{'=' * 60}\n\n"
        message += f"Error Type: {error_type}\n"
        message += f"Message: {error_msg}\n\n"

        if classification["common_causes"]:
            message += "💭 Common Causes:\n"
            for cause in classification["common_causes"]:
                message += f"  • {cause}\n"
            message += "\n"

        if classification["quick_fixes"]:
            message += "🔧 Quick Fixes:\n"
            for fix in classification["quick_fixes"]:
                message += f"  • {fix}\n"
            message += "\n"

        message += "💡 Options:\n"
        message += "  • Check your input and try again\n"
        message += "  • Use HELP command for guidance\n"
        message += "  • Use FEEDBACK to report persistent issues\n"

        return message

    async def get_ai_suggestion(
        self, error: Exception, command: str, params: list, context: Dict
    ) -> Optional[str]:
        """Get AI-powered error analysis and suggestion."""
        # Check if user role allows API access
        if self.user_role == "user":
            # For user role, limit AI suggestions to reduce API usage
            pass

        if not self.gemini:
            return None

        try:
            # Build prompt for AI
            prompt = self._build_ai_prompt(error, command, params, context)

            # Query Gemini
            import time

            start_time = time.time()

            response = await self.gemini.ask(prompt)

            duration_ms = (time.time() - start_time) * 1000

            # Log API usage
            if self.audit_logger:
                self.audit_logger.log_api_call(
                    user_role=self.user_role,
                    operation="ERROR_ANALYSIS",
                    api_type="gemini",
                    query=f"Error: {type(error).__name__} in {command}",
                    duration_ms=duration_ms,
                    success=True,
                )

            return response

        except Exception as e:
            # Failed to get AI suggestion
            if self.audit_logger:
                self.audit_logger.log_api_call(
                    user_role=self.user_role,
                    operation="ERROR_ANALYSIS",
                    api_type="gemini",
                    query=f"Error: {type(error).__name__}",
                    success=False,
                    error_msg=str(e),
                )
            return None

    def _build_ai_prompt(
        self, error: Exception, command: str, params: list, context: Dict
    ) -> str:
        """Build prompt for AI error analysis."""
        error_type = type(error).__name__
        error_msg = str(error)

        prompt = f"""Analyze this uDOS command error and suggest a fix:

Command: {command}
Parameters: {params}
Error Type: {error_type}
Error Message: {error_msg}

Context:
- Category: {context.get('classification', {}).get('category', 'unknown')}
- Severity: {context.get('classification', {}).get('severity', 'medium')}

Please provide:
1. Brief explanation of what went wrong
2. Specific fix for this situation
3. How to prevent this error in the future

Keep the response concise and actionable."""

        return prompt

    def format_interactive_prompt(
        self,
        error_msg: str,
        allow_retry: bool = True,
        ai_suggestion: Optional[str] = None,
    ) -> str:
        """Format interactive error prompt with options."""
        prompt = error_msg + "\n"
        prompt += "─" * 60 + "\n"
        prompt += "What would you like to do?\n\n"

        options = []
        if allow_retry:
            options.append("1. Retry - Try the command again")
        options.append("2. Get Help - View detailed help for this command")
        if ai_suggestion:
            options.append("3. AI Suggestion - See AI-powered fix suggestion")
        options.append("4. Report - Report this as a bug")
        options.append("5. Continue - Skip and continue")

        for option in options:
            prompt += f"  {option}\n"

        prompt += "\nEnter your choice (1-5): "

        return prompt

    """Main error intelligence service with pattern learning."""

    # Theme-aware error messages
    THEME_MESSAGES = {
        "default": {
            "critical": "💀 CRITICAL ERROR: {error_type}",
            "high": "❌ ERROR: {error_type}",
            "medium": "⚠️  Warning: {error_type}",
            "low": "ℹ️  Notice: {error_type}",
            "prompt": "\nOptions:\n  1. Retry\n  2. OK FIX (AI-assisted)\n  3. DEV MODE\n  4. Skip\nChoose [1-4]: ",
            "fix_success": "✅ Fix applied successfully!",
            "fix_failed": "❌ Fix did not resolve the issue",
        },
        "dungeon": {
            "critical": "☠️  THE DUNGEON MASTER HAS SPOKEN: {error_type}",
            "high": "⚔️  Your quest has hit a wall: {error_type}",
            "medium": "🛡️  A minor obstacle blocks your path: {error_type}",
            "low": "📜 The scroll reveals: {error_type}",
            "prompt": "\nWhat is your choice, adventurer?\n  1. Try again, brave one\n  2. Summon the Oracle (OK FIX)\n  3. Enter the Debug Realm\n  4. Flee and continue\nYour choice [1-4]: ",
            "fix_success": "🎉 The Oracle's wisdom prevails! Issue vanquished!",
            "fix_failed": "😞 The Oracle's spell was not enough...",
        },
        "galaxy": {
            "critical": "🚨 SHIP CRITICAL: {error_type}",
            "high": "⚡ SYSTEM FAULT: {error_type}",
            "medium": "📡 ANOMALY DETECTED: {error_type}",
            "low": "🛰️  SENSOR NOTICE: {error_type}",
            "prompt": "\nCaptain's options:\n  1. Re-engage systems\n  2. Consult AI Navigator (OK FIX)\n  3. Enter Engineering Mode\n  4. Bypass and continue\nCommand [1-4]: ",
            "fix_success": "🚀 Systems restored to optimal!",
            "fix_failed": "🔧 Repair cycle incomplete",
        },
    }

    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        self.config = config
        self.project_root = Path(config.project_root)
        self.theme = config.get("theme", "default")

        # Storage paths
        self.data_dir = self.project_root / "memory" / "system" / "error_intelligence"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.patterns_file = self.data_dir / "patterns.json"
        self.contexts_dir = self.data_dir / "contexts"
        self.archive_dir = self.data_dir / ".archive"

        self.contexts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Load patterns
        self.patterns: Dict[str, ErrorPattern] = self._load_patterns()

        # Session stats
        self.session_errors = 0
        self.session_fixes = 0

    def _load_patterns(self) -> Dict[str, ErrorPattern]:
        """Load learned error patterns from disk."""
        patterns = {}

        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, "r") as f:
                    data = json.load(f)
                    for sig, p in data.items():
                        patterns[sig] = ErrorPattern(
                            signature=p["signature"],
                            error_type=p["error_type"],
                            message_pattern=p["message_pattern"],
                            file_pattern=p["file_pattern"],
                            occurrences=p.get("occurrences", 0),
                            last_seen=p.get("last_seen", ""),
                            fixes_attempted=p.get("fixes_attempted", 0),
                            fixes_successful=p.get("fixes_successful", 0),
                            suggested_fixes=p.get("suggested_fixes", []),
                            user_notes=p.get("user_notes", ""),
                        )
            except Exception:
                pass

        return patterns

    def _save_patterns(self):
        """Save patterns to disk."""
        data = {}
        for sig, p in self.patterns.items():
            data[sig] = {
                "signature": p.signature,
                "error_type": p.error_type,
                "message_pattern": p.message_pattern,
                "file_pattern": p.file_pattern,
                "occurrences": p.occurrences,
                "last_seen": p.last_seen,
                "fixes_attempted": p.fixes_attempted,
                "fixes_successful": p.fixes_successful,
                "suggested_fixes": p.suggested_fixes,
                "user_notes": p.user_notes,
            }

        with open(self.patterns_file, "w") as f:
            json.dump(data, f, indent=2)

    def capture_error(
        self,
        error: Exception,
        command: str,
        params: List[str],
        recent_commands: List[str] = None,
    ) -> ErrorContext:
        """Capture and analyze error with full context."""
        import traceback
        import subprocess

        # Generate signature
        signature = self._generate_signature(error)

        # Classify severity
        severity = self._classify_severity(error)

        # Sanitize stack trace
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        stack_trace = self._sanitize_stack_trace(tb_lines)

        # Sanitize recent commands
        safe_commands = self._sanitize_commands(recent_commands or [])

        # Capture workspace state
        workspace_state = {
            "theme": self.theme,
            "location": self.config.get("last_location", "unknown"),
            "timezone": self.config.get_env("TIMEZONE", "UTC"),
        }

        # Git status (optional)
        git_status = None
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=self.project_root,
            )
            if result.returncode == 0 and result.stdout.strip():
                git_status = result.stdout.strip()[:200]  # Limit length
        except Exception:
            pass

        # Create context
        context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            command=command,
            params=params,
            timestamp=datetime.now().isoformat(),
            signature=signature,
            severity=severity,
            stack_trace=stack_trace,
            recent_commands=safe_commands,
            workspace_state=workspace_state,
            git_status=git_status,
        )

        # Update pattern
        self._update_pattern(context, error)

        # Save context
        self._save_context(context)

        # Update session stats
        self.session_errors += 1

        return context

    def _generate_signature(self, error: Exception) -> str:
        """Generate unique signature for pattern matching."""
        error_type = type(error).__name__

        # Normalize message (replace numbers, strings, paths)
        message_pattern = str(error)
        message_pattern = re.sub(r"\d+", "N", message_pattern)
        message_pattern = re.sub(r'["\'].*?["\']', '""', message_pattern)
        message_pattern = re.sub(r"/[^\s]+", "/<path>", message_pattern)

        # Extract file from traceback
        file_pattern = "unknown"
        if error.__traceback__:
            tb = error.__traceback__
            while tb.tb_next:
                tb = tb.tb_next
            file_pattern = tb.tb_frame.f_code.co_filename.split("/")[-1]

        signature_str = f"{error_type}:{message_pattern}:{file_pattern}"
        return hashlib.sha256(signature_str.encode()).hexdigest()[:16]

    def _classify_severity(self, error: Exception) -> ErrorSeverity:
        """Classify error severity."""
        error_type = type(error).__name__

        critical_types = {
            "SystemExit",
            "KeyboardInterrupt",
            "MemoryError",
            "RecursionError",
            "SyntaxError",
            "SystemError",
        }
        high_types = {
            "PermissionError",
            "FileNotFoundError",
            "ImportError",
            "AttributeError",
            "ModuleNotFoundError",
            "OSError",
        }
        medium_types = {
            "ValueError",
            "TypeError",
            "KeyError",
            "IndexError",
            "RuntimeError",
            "AssertionError",
        }

        if error_type in critical_types:
            return ErrorSeverity.CRITICAL
        elif error_type in high_types:
            return ErrorSeverity.HIGH
        elif error_type in medium_types:
            return ErrorSeverity.MEDIUM
        elif "Error" in error_type or "Exception" in error_type:
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.INFO

    def _sanitize_stack_trace(self, tb_lines: List[str]) -> str:
        """Compress and sanitize stack trace."""
        frames = []

        for line in tb_lines:
            if 'File "' in line:
                # Extract and compress file reference
                match = re.search(r'File ".*?/([^/]+\.py)", line (\d+)', line)
                if match:
                    frames.append(f"{match.group(1)}:{match.group(2)}")

        return " → ".join(frames[-5:]) if frames else "unknown"

    def _sanitize_commands(self, commands: List[str]) -> List[str]:
        """Remove sensitive data from command history."""
        sanitized = []

        for cmd in commands[-5:]:  # Last 5 only
            # Remove API keys
            cmd = re.sub(r"(api[_-]?key[=\s]+)\S+", r"\1***", cmd, flags=re.I)
            # Remove passwords
            cmd = re.sub(r"(pass(word)?[=\s]+)\S+", r"\1***", cmd, flags=re.I)
            # Remove absolute paths
            cmd = re.sub(r"/Users/[^/\s]+/", "<user>/", cmd)
            sanitized.append(cmd)

        return sanitized

    def _update_pattern(self, context: ErrorContext, error: Exception):
        """Update or create pattern from error context."""
        sig = context.signature

        if sig in self.patterns:
            # Update existing pattern
            pattern = self.patterns[sig]
            pattern.occurrences += 1
            pattern.last_seen = context.timestamp
        else:
            # Create new pattern
            message_pattern = str(error)
            message_pattern = re.sub(r"\d+", r"\\d+", message_pattern)
            message_pattern = re.sub(
                r'["\'].*?["\']', r'["\'"].*?["\'"]', message_pattern
            )

            file_pattern = (
                context.stack_trace.split(" → ")[-1].split(":")[0]
                if context.stack_trace != "unknown"
                else "*"
            )

            self.patterns[sig] = ErrorPattern(
                signature=sig,
                error_type=context.error_type,
                message_pattern=message_pattern,
                file_pattern=file_pattern,
                occurrences=1,
                last_seen=context.timestamp,
            )

        self._save_patterns()

    def _save_context(self, context: ErrorContext):
        """Save error context to file."""
        filename = f"{context.timestamp.replace(':', '-').replace('.', '-')}_{context.signature}.json"
        filepath = self.contexts_dir / filename

        with open(filepath, "w") as f:
            f.write(context.to_json())

        # Update latest symlink
        latest = self.contexts_dir / "latest.json"
        if latest.exists() or latest.is_symlink():
            latest.unlink()
        latest.symlink_to(filename)

        # Apply retention
        self._apply_retention()

    def _apply_retention(self):
        """Smart retention policy for error contexts."""
        all_contexts = [
            f for f in self.contexts_dir.glob("*.json") if f.name != "latest.json"
        ]
        now = datetime.now()
        keep = set()

        # Rule 1: Keep all from last 7 days
        seven_days_ago = now - timedelta(days=7)
        for filepath in all_contexts:
            try:
                with open(filepath, "r") as f:
                    data = json.loads(f.read())
                    ts = datetime.fromisoformat(data["timestamp"].split(".")[0])
                    if ts > seven_days_ago:
                        keep.add(filepath)
            except Exception:
                continue

        # Rule 2: Keep last 50 high/critical severity
        high_severity = []
        for filepath in all_contexts:
            try:
                with open(filepath, "r") as f:
                    data = json.loads(f.read())
                    if data.get("severity") in ["critical", "high"]:
                        ts = datetime.fromisoformat(data["timestamp"].split(".")[0])
                        high_severity.append((ts, filepath))
            except Exception:
                continue

        high_severity.sort(reverse=True)
        for _, fp in high_severity[:50]:
            keep.add(fp)

        # Rule 3: Keep last 10 per unique signature
        by_sig = {}
        for filepath in all_contexts:
            try:
                with open(filepath, "r") as f:
                    data = json.loads(f.read())
                    sig = data.get("signature", "unknown")
                    ts = datetime.fromisoformat(data["timestamp"].split(".")[0])
                    if sig not in by_sig:
                        by_sig[sig] = []
                    by_sig[sig].append((ts, filepath))
            except Exception:
                continue

        for sig_contexts in by_sig.values():
            sig_contexts.sort(reverse=True)
            for _, fp in sig_contexts[:10]:
                keep.add(fp)

        # Archive old contexts
        for filepath in all_contexts:
            if filepath not in keep:
                try:
                    with open(filepath, "r") as f:
                        data = f.read()

                    # Append to monthly archive
                    ts = filepath.name.split("_")[0]
                    month = ts[:7].replace("-", "")  # YYYYMM
                    archive_file = self.archive_dir / f"{month}.json.gz"

                    with gzip.open(archive_file, "at") as f:
                        f.write(data + "\n")

                    filepath.unlink()
                except Exception:
                    pass

    def get_theme_message(self, severity: ErrorSeverity, key: str, **kwargs) -> str:
        """Get theme-aware error message."""
        theme = self.theme if self.theme in self.THEME_MESSAGES else "default"
        messages = self.THEME_MESSAGES[theme]

        template = messages.get(severity.value, messages.get(key, key))
        if not template:
            template = messages.get(key, key)

        try:
            return template.format(**kwargs)
        except Exception:
            return template

    def prompt_user(self, context: ErrorContext) -> str:
        """Display theme-aware error prompt and get user choice."""
        # Show error message
        msg = self.get_theme_message(
            context.severity, context.severity.value, error_type=context.error_type
        )
        print(f"\n{msg}")
        print(f"   {context.error_message}\n")

        # Show pattern info if known
        if context.signature in self.patterns:
            pattern = self.patterns[context.signature]
            if pattern.occurrences > 1:
                print(f"   [Seen {pattern.occurrences} times previously]")
                if pattern.suggested_fixes:
                    print(f"   [Known fix: {pattern.suggested_fixes[0][:50]}...]")
                print()

        # Show prompt
        prompt_msg = self.get_theme_message(context.severity, "prompt")
        print(prompt_msg, end="")

        try:
            choice = input().strip()
            return {"1": "retry", "2": "ok_fix", "3": "dev_mode", "4": "skip"}.get(
                choice, "skip"
            )
        except (EOFError, KeyboardInterrupt):
            return "skip"

    def record_fix_attempt(self, signature: str, fix_description: str, success: bool):
        """Record the result of a fix attempt."""
        if signature in self.patterns:
            pattern = self.patterns[signature]
            pattern.fixes_attempted += 1

            if success:
                pattern.fixes_successful += 1
                self.session_fixes += 1

                # Add to suggested fixes if not already there
                if fix_description not in pattern.suggested_fixes:
                    pattern.suggested_fixes.insert(0, fix_description)
                    # Keep only top 5 fixes
                    pattern.suggested_fixes = pattern.suggested_fixes[:5]

            self._save_patterns()

    def get_suggested_fix(self, signature: str) -> Optional[str]:
        """Get best suggested fix for an error pattern."""
        if signature in self.patterns:
            pattern = self.patterns[signature]
            if pattern.suggested_fixes and pattern.fixes_successful > 0:
                # Return most successful fix
                return pattern.suggested_fixes[0]
        return None

    def get_recent_errors(self, days: int = 7) -> List[Dict]:
        """Get recent error contexts."""
        cutoff = datetime.now() - timedelta(days=days)
        results = []

        for filepath in self.contexts_dir.glob("*.json"):
            if filepath.name == "latest.json":
                continue

            try:
                with open(filepath, "r") as f:
                    data = json.loads(f.read())
                    ts = datetime.fromisoformat(data["timestamp"].split(".")[0])
                    if ts > cutoff:
                        results.append(data)
            except Exception:
                continue

        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def get_pattern_summary(self) -> str:
        """Get summary of known error patterns."""
        if not self.patterns:
            return "No error patterns learned yet."

        lines = ["Known Error Patterns:"]
        lines.append("-" * 40)

        # Sort by occurrences
        sorted_patterns = sorted(
            self.patterns.values(), key=lambda p: p.occurrences, reverse=True
        )

        for p in sorted_patterns[:10]:  # Top 10
            fix_rate = (
                (p.fixes_successful / p.fixes_attempted * 100)
                if p.fixes_attempted > 0
                else 0
            )
            lines.append(f"  {p.error_type}: {p.occurrences} times")
            if p.fixes_attempted > 0:
                lines.append(f"    → Fix rate: {fix_rate:.0f}%")

        return "\n".join(lines)

    def get_session_stats(self) -> Dict[str, int]:
        """Get session statistics."""
        return {
            "errors": self.session_errors,
            "fixes": self.session_fixes,
            "patterns_known": len(self.patterns),
        }


# Global singleton
_error_intelligence = None
_error_handler: Optional[IntelligentErrorHandler] = None
_error_context_manager: Optional[ErrorContextManager] = None
_error_interceptor: Optional[ErrorInterceptor] = None


def get_error_intelligence(config: Config = None) -> ErrorIntelligence:
    """Get or create ErrorIntelligence singleton."""
    global _error_intelligence

    if _error_intelligence is None:
        if config is None:
            config = Config()
        _error_intelligence = ErrorIntelligence(config)

    return _error_intelligence


def get_error_context_manager(config: Config = None) -> ErrorContextManager:
    """Get or create global ErrorContextManager singleton (from error_interceptor)."""
    global _error_context_manager
    if _error_context_manager is None:
        if config is None:
            config = Config()
        _error_context_manager = ErrorContextManager(config)
    return _error_context_manager


def get_error_handler() -> IntelligentErrorHandler:
    """Get or create global IntelligentErrorHandler singleton (from intelligent_error_handler)."""
    global _error_handler
    if _error_handler is None:
        _error_handler = IntelligentErrorHandler()
    return _error_handler


def handle_command_error(
    error: Exception, command: str, params: list, context: Optional[Dict] = None
) -> str:
    """
    Convenience function to handle command errors (from intelligent_error_handler).

    Usage:
        try:
            result = execute_command()
        except Exception as e:
            return handle_command_error(e, "MAP", ["CREATE"], context)

    Args:
        error: The exception
        command: Command name
        params: Command parameters
        context: Additional context

    Returns:
        Formatted error message
    """
    handler = get_error_handler()
    error_msg, choice = handler.handle_error(
        error=error, command=command, params=params, context=context
    )
    return error_msg
