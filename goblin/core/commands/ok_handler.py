"""
OK Command Handler - AI-Assisted Workflow Generation & Code Fixing
Handles OK MAKE commands for workflow, SVG, documentation, test generation
and OK FIX commands for AI-powered code fixing

Commands:
- OK MAKE WORKFLOW <description> - Generate uPY workflow script
- OK MAKE SVG <description> - Generate SVG graphic
- OK MAKE DOC <topic> - Generate documentation
- OK MAKE TEST <file> - Generate unit tests
- OK MAKE MISSION <category> <tile> - Generate mission script
- OK ASK <question> - Ask AI assistant
- OK FIX <file> - Fix code issues with Mistral AI
- OK CLEAR - Clear conversation history
- OK STATUS - Show usage statistics

Integration:
- Gemini API for all MAKE commands (user content generation)
- Mistral AI for OK FIX commands (code analysis and fixing)
- Vibe CLI for Dev Mode (core/extensions code modifications)
- Context-aware via ok_context_manager
- Prompt augmentation via context_builder
- Settings via ok_config

Version: 1.2.0 (Phase 4: okfix_handler merged)
Author: Fred Porter
"""

import sys
import random
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass

from .base_handler import BaseCommandHandler
from dev.goblin.core.services.ok_context_manager import get_ok_context_manager
from dev.goblin.core.services.ok_config import get_ok_config
from dev.goblin.core.services.ok_context_builder import get_context_builder
from dev.goblin.core.utils.filename_generator import FilenameGenerator
from dev.goblin.core.services.logging_manager import get_logger

# Logger for OK handler (covers both MAKE and FIX)
logger = get_logger("command-ok")


@dataclass
class FixResult:
    """Result of a code fix operation (Phase 4: Merged from okfix_handler)."""

    success: bool
    file_path: Optional[str] = None
    original_code: Optional[str] = None
    fixed_code: Optional[str] = None
    explanation: str = ""
    changes_made: list = None
    errors_fixed: int = 0
    warnings_fixed: int = 0

    def __post_init__(self):
        if self.changes_made is None:
            self.changes_made = []


class OKHandler(BaseCommandHandler):
    """OK command handler for AI-assisted generation and code fixing"""

    def __init__(self, **kwargs):
        """
        Initialize OK handler.

        Args:
            **kwargs: Standard handler dependencies
        """
        super().__init__(**kwargs)

        # Context and configuration
        self.context_manager = get_ok_context_manager()
        self.context_builder = get_context_builder()
        self.ok_config = get_ok_config()

        # v1.2.23: FilenameGenerator for AI-generated content
        config = kwargs.get("config")
        self.filename_gen = FilenameGenerator(config=config)

        # Gemini service (lazy load)
        self._gemini = None

        # Mistral client for OK FIX (Phase 4: merged from okfix_handler)
        self.mistral_client = None
        self._init_mistral()
        self._load_fix_prompts()

        # Output directories
        self.output_dirs = {
            "workflow": Path("memory/workflows/missions"),
            "svg": Path("memory/drafts/svg"),
            "doc": Path("memory/docs"),
            "test": Path("memory/ucode/tests"),
            "mission": Path("memory/workflows/missions"),
        }

        # Ensure directories exist
        for dir_path in self.output_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "total_requests": 0,
            "by_command": {},
            "total_tokens": 0,
            "session_start": datetime.now(),
        }

        # Vibe CLI colors for OK FIX output (Phase 4)
        self.COLORS = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "red": "\033[31m",
            "bg_green": "\033[42m",
            "bg_yellow": "\033[43m",
            "bg_blue": "\033[44m",
        }

        # Vibe messages for OK FIX (Phase 4)
        self.VIBE_INTROS = [
            "🎸 Let's vibe with this code...",
            "✨ Checking the vibes on this one...",
            "🔮 Reading the code tea leaves...",
            "🎯 Targeting the issues...",
            "🌊 Flowing through the code...",
        ]

        self.VIBE_FIXES = [
            "💫 Fixed that right up!",
            "🎉 Looking much better now!",
            "✅ Smooth sailing ahead!",
            "🚀 Ready for launch!",
            "💪 Stronger code achieved!",
        ]

    @property
    def gemini(self):
        """
        Lazy load Gemini API service.
        Used for all MAKE commands (user content generation).
        """
        if self._gemini is None:
            try:
                try:
                    from wizard.extensions.assistant.gemini_service import GeminiService
                except ImportError:
                    return (
                        "❌ Assistant extension not installed. AI features unavailable."
                    )
                from dev.goblin.core.config import Config

                config = Config()

                # Initialize Gemini service
                gemini = GeminiService(config_manager=config)

                if not gemini.is_available:
                    # Gemini not configured - prompt for setup
                    return self._prompt_ai_setup(config)

                self._gemini = gemini
            except ImportError:
                # Assistant extension not installed
                return None
            except Exception as e:
                # Other initialization error
                return None
        return self._gemini

    def _get_vibe_cli(self):
        """
        Get Vibe CLI service for dev mode operations.
        Only used for core/extensions code modifications.
        """
        try:
            from wizard.extensions.assistant.vibe_cli_service import VibeCliService
            from dev.goblin.core.config import Config

            config = Config()

            vibe = VibeCliService(config_manager=config)
            return vibe if vibe.is_available else None
        except ImportError:
            return None
        except Exception:
            return None

    def handle(self, command: str, params: List[str], grid=None) -> str:
        """
        Handle OK commands.

        Args:
            command: Command name (OK)
            params: Command parameters
            grid: Optional grid instance

        Returns:
            Command result message
        """
        if not params:
            return self._show_help()

        subcommand = params[0].upper()

        # Route to subcommand handlers
        if subcommand == "MAKE":
            return self._handle_make(params[1:])
        elif subcommand == "ASK":
            return self._handle_ask(params[1:])
        elif subcommand == "FIX":
            return self._handle_fix(params[1:])
        elif subcommand == "CLEAR":
            return self._handle_clear()
        elif subcommand == "STATUS":
            return self._handle_status(params[1:])
        else:
            return f"❌ Unknown OK command: {subcommand}\n\nUse: OK --help"

    def _handle_make(self, params: List[str]) -> str:
        """Handle OK MAKE subcommands."""
        if not params:
            return (
                "OK MAKE - AI-Assisted Generation\n\n"
                "Workflows:\n"
                "  OK MAKE WORKFLOW <desc>   - Generate uPY workflow script\n"
                "  OK MAKE MISSION <cat> <tile> - Generate mission script\n"
                "  OK MAKE TEST <file>       - Generate unit tests\n"
                "  OK MAKE DOC <topic>       - Generate documentation\n\n"
                "Graphics (Typora/GitHub standards):\n"
                "  OK MAKE SEQUENCE <desc>   - js-sequence diagram (interactions)\n"
                "  OK MAKE FLOWCHART <desc>  - flowchart.js diagram (processes)\n"
                "  OK MAKE SVG <desc>        - Custom vector graphics\n"
                "  OK MAKE ASCII <desc>      - Text-based art\n"
                "  OK MAKE TELETEXT <desc>   - Retro terminal graphics\n\n"
                "Examples:\n"
                '  OK MAKE SEQUENCE "user login process"\n'
                '  OK MAKE FLOWCHART "water purification steps"\n'
                '  OK MAKE SVG "water filter components"\n'
                "  OK MAKE TEST core/services/ok_config.py\n"
            )

        make_type = params[0].upper()
        make_params = params[1:]

        if make_type == "WORKFLOW":
            return self._make_workflow(make_params)
        elif make_type == "SEQUENCE":
            return self._make_diagram(make_params, "sequence")
        elif make_type == "FLOWCHART" or make_type == "FLOW":
            return self._make_diagram(make_params, "flowchart")
        elif make_type == "SVG":
            return self._make_svg(make_params)
        elif make_type == "ASCII":
            return self._make_diagram(make_params, "ascii")
        elif make_type == "TELETEXT":
            return self._make_diagram(make_params, "teletext")
        elif make_type == "DOC":
            return self._make_doc(make_params)
        elif make_type == "TEST":
            return self._make_test(make_params)
        elif make_type == "MISSION":
            return self._make_mission(make_params)
        else:
            return f"❌ Unknown MAKE type: {make_type}\n\nSupported: SEQUENCE, FLOWCHART, SVG, ASCII, TELETEXT, WORKFLOW, DOC, TEST, MISSION"

    def _make_workflow(self, params: List[str]) -> str:
        """Generate uPY workflow script."""
        if not params:
            return "❌ Usage: OK MAKE WORKFLOW <description>"

        description = " ".join(params)

        # Check Gemini availability
        if not self.gemini or not self.gemini.is_available:
            return "❌ Gemini API not available. Set GEMINI_API_KEY in .env"

        # Build context-aware prompt
        prompt = self.context_builder.build_workflow_prompt("automation", description)

        # Generate with Gemini (user operation)
        try:
            response = self.gemini.ask(prompt, operation_type="user")

            if response.get("success"):
                # Extract code from response
                code = self._extract_code(response["response"])

                # Save to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"workflow_{timestamp}.upy"
                filepath = self.output_dirs["workflow"] / filename

                with open(filepath, "w") as f:
                    f.write(code)

                # Update stats
                self._update_stats("workflow", response.get("tokens_used", 0))

                return (
                    f"✅ Workflow generated: {filepath}\n\n"
                    f"Preview:\n{code[:200]}...\n\n"
                    f"Run with: RUN {filepath}"
                )
            else:
                return f"❌ Generation failed: {response.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Error: {e}"

    def _make_diagram(self, params: List[str], diagram_type: str) -> str:
        """Generate Typora-compatible diagram code (sequence/flowchart/ascii/teletext)."""
        if not params:
            type_examples = {
                "sequence": "Alice->Bob: Hello Bob!",
                "flowchart": "st=>start: Start\\nop=>operation: Process",
                "ascii": "water filtration system",
                "teletext": "survival guide header",
            }
            example = type_examples.get(diagram_type, "description")
            return f'❌ Usage: OK MAKE {diagram_type.upper()} <description>\n\nExample: OK MAKE {diagram_type.upper()} "{example}"'

        description = " ".join(params)

        if not self.gemini or not self.gemini.is_available:
            return "❌ Gemini API not available. Set GEMINI_API_KEY in .env"

        # Build diagram-specific prompt
        prompt = self._build_diagram_prompt(description, diagram_type)

        try:
            response = self.gemini.ask(prompt, operation_type="user")

            if response.get("success"):
                diagram_code = self._extract_code(response["response"])

                # Save to appropriate directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{diagram_type}_{timestamp}.md"

                # Determine output directory
                if diagram_type in ["sequence", "flowchart"]:
                    output_dir = Path("memory/drafts/diagrams")
                elif diagram_type == "ascii":
                    output_dir = Path("memory/drafts/ascii")
                elif diagram_type == "teletext":
                    output_dir = Path("memory/drafts/teletext")
                else:
                    output_dir = Path("memory/drafts")

                output_dir.mkdir(parents=True, exist_ok=True)
                filepath = output_dir / filename

                # Wrap in Typora/GitHub markdown fence
                if diagram_type in ["sequence", "flowchart"]:
                    fence_type = "sequence" if diagram_type == "sequence" else "flow"
                    wrapped_code = f"```{fence_type}\n{diagram_code}\n```\n"
                else:
                    wrapped_code = diagram_code

                with open(filepath, "w") as f:
                    f.write(wrapped_code)

                self._update_stats(diagram_type, response.get("tokens_used", 0))

                return (
                    f"✅ {diagram_type.upper()} diagram generated: {filepath}\n\n"
                    f"Format: Typora/GitHub compatible\n"
                    f"Preview:\n{diagram_code[:150]}...\n\n"
                    f"View with: SHOW {filepath}"
                )
            else:
                return f"❌ Generation failed: {response.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Error: {e}"

    def _make_svg(self, params: List[str]) -> str:
        """Generate SVG graphic."""
        if not params:
            return "❌ Usage: OK MAKE SVG <description>"

        description = " ".join(params)

        if not self.gemini or not self.gemini.is_available:
            return "❌ Gemini API not available. Set GEMINI_API_KEY in .env"

        # Build SVG-specific prompt
        prompt = self.context_builder.build_svg_prompt(description)

        try:
            response = self.gemini.ask(prompt, operation_type="user")

            if response.get("success"):
                svg_code = self._extract_code(response["response"])

                # Save to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"graphic_{timestamp}.svg"
                filepath = self.output_dirs["svg"] / filename

                with open(filepath, "w") as f:
                    f.write(svg_code)

                self._update_stats("svg", response.get("tokens_used", 0))

                return (
                    f"✅ SVG generated: {filepath}\n\n"
                    f"Size: {len(svg_code)} bytes\n"
                    f"Preview in browser or: SHOW {filepath}"
                )
            else:
                return f"❌ Generation failed: {response.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Error: {e}"

    def _make_doc(self, params: List[str]) -> str:
        """Generate documentation."""
        if not params:
            return "❌ Usage: OK MAKE DOC <topic>"

        topic = " ".join(params)

        if not self.gemini or not self.gemini.is_available:
            return "❌ Gemini API not available. Set GEMINI_API_KEY in .env"

        prompt = self.context_builder.build_doc_prompt(topic)

        try:
            response = self.gemini.ask(prompt, operation_type="user")

            if response.get("success"):
                doc_content = response["response"]

                # Save to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_topic = topic.replace(" ", "_")[:30]
                filename = f"{safe_topic}_{timestamp}.md"
                filepath = self.output_dirs["doc"] / filename

                with open(filepath, "w") as f:
                    f.write(doc_content)

                self._update_stats("doc", response.get("tokens_used", 0))

                return (
                    f"✅ Documentation generated: {filepath}\n\n"
                    f"Length: {len(doc_content)} characters\n"
                    f"View with: SHOW {filepath}"
                )
            else:
                return f"❌ Generation failed: {response.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Error: {e}"

    def _make_test(self, params: List[str]) -> str:
        """Generate unit tests."""
        if not params:
            return "❌ Usage: OK MAKE TEST <file_path>"

        file_path = params[0]

        if not self.gemini or not self.gemini.is_available:
            return "❌ Gemini API not available. Set GEMINI_API_KEY in .env"

        prompt = self.context_builder.build_test_prompt(file_path)

        try:
            response = self.gemini.ask(prompt, operation_type="user")

            if response.get("success"):
                test_code = self._extract_code(response["response"])

                # Save to file
                base_name = Path(file_path).stem
                filename = f"test_{base_name}.py"
                filepath = self.output_dirs["test"] / filename

                with open(filepath, "w") as f:
                    f.write(test_code)

                self._update_stats("test", response.get("tokens_used", 0))

                return (
                    f"✅ Tests generated: {filepath}\n\n" f"Run with: pytest {filepath}"
                )
            else:
                return f"❌ Generation failed: {response.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Error: {e}"

    def _make_mission(self, params: List[str]) -> str:
        """Generate mission script."""
        if len(params) < 2:
            return "❌ Usage: OK MAKE MISSION <category> <tile>"

        category = params[0]
        tile = params[1]

        if not self.gemini or not self.gemini.is_available:
            return "❌ Gemini API not available. Set GEMINI_API_KEY in .env"

        prompt = (
            f"Generate a uPY mission script for category '{category}' at TILE {tile}"
        )

        try:
            response = self.gemini.ask(prompt, operation_type="user")

            if response.get("success"):
                mission_code = self._extract_code(response["response"])

                # Save to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mission_{category}_{tile}_{timestamp}.upy"
                filepath = self.output_dirs["mission"] / filename

                with open(filepath, "w") as f:
                    f.write(mission_code)

                self._update_stats("mission", response.get("tokens_used", 0))

                return (
                    f"✅ Mission generated: {filepath}\n\n" f"Run with: RUN {filepath}"
                )
            else:
                return f"❌ Generation failed: {response.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Error: {e}"

    def _handle_ask(self, params: List[str]) -> str:
        """Handle OK ASK command."""
        if not params:
            return "❌ Usage: OK ASK <question>"

        question = " ".join(params)

        if not self.gemini or not self.gemini.is_available:
            return "❌ Gemini API not available. Set GEMINI_API_KEY in .env"

        # Build context-aware prompt
        prompt = self.context_builder.build_prompt(question, context_type="general")

        try:
            response = self.gemini.ask(prompt, operation_type="user")

            if response.get("success"):
                self._update_stats("ask", response.get("tokens_used", 0))
                return response["response"]
            else:
                return f"❌ Error: {response.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Error: {e}"

    def _handle_fix(self, params: List[str]) -> str:
        """Handle OK FIX command - suggest fixes for errors using AI + learned patterns."""
        from dev.goblin.core.services.pattern_learner import get_pattern_learner
        from dev.goblin.core.services.error_intelligence import get_error_context_manager

        learner = get_pattern_learner()
        error_manager = get_error_context_manager()

        # Get error context (signature or latest)
        if params and params[0].startswith("#"):
            # Specific error by signature
            signature = params[0][1:]  # Remove # prefix
            error_ctx = error_manager.get_context(signature)
            if not error_ctx:
                return f"❌ Error not found: #{signature}\n\nUse: ERROR HISTORY to see available errors"
        else:
            # Use latest error
            error_ctx = error_manager.get_latest()
            if not error_ctx:
                return "❌ No recent errors found\n\nUse OK FIX after an error occurs"

        # Build output
        lines = []
        lines.append("╔══════════════════════════════════════════════════════════╗")
        lines.append("║               OK FIX - Error Analysis                    ║")
        lines.append("╚══════════════════════════════════════════════════════════╝")
        lines.append("")

        # Show error summary
        lines.append(f"🔍 Error: {error_ctx['error_type']}")
        lines.append(f"   Message: {error_ctx['message']}")
        lines.append(f"   Signature: #{error_ctx['signature']}")
        lines.append(f"   Timestamp: {error_ctx['timestamp']}")
        lines.append("")

        # Get learned patterns
        suggestions = learner.suggest_fix(
            error_ctx["error_type"],
            error_ctx["message"],
            error_ctx.get("stack_trace", ""),
        )

        if suggestions:
            lines.append("📚 Learned Fixes (from previous occurrences):")
            for i, sugg in enumerate(suggestions[:3], 1):  # Top 3
                success_rate = sugg.get("success_rate", 0)
                if success_rate > 0:
                    lines.append(
                        f"   {i}. {sugg['fix']} (✅ {success_rate:.0%} success rate)"
                    )
                else:
                    lines.append(f"   {i}. {sugg['fix']}")
            lines.append("")

        # Get AI analysis (if available)
        if self.gemini and self.gemini.is_available:
            lines.append("🤖 AI Analysis (via Gemini)...")
            lines.append("")

            try:
                # Build error analysis prompt
                prompt = self._build_error_analysis_prompt(error_ctx, suggestions)

                # Query Gemini (dev operation - debugging)
                # Dev mode: Use Vibe CLI for code modifications
                vibe = self._get_vibe_cli()
                if vibe and vibe.is_available:
                    response = vibe.ask(prompt, operation_type="dev")
                else:
                    return "❌ Vibe CLI not available. Required for dev mode code modifications."

                if response.get("success"):
                    lines.append(response["response"])
                    self._update_stats("fix", response.get("tokens_used", 0))
                else:
                    lines.append(
                        f"⚠️  AI analysis failed: {response.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                lines.append(f"⚠️  AI analysis error: {e}")
        else:
            lines.append("ℹ️  AI analysis unavailable (set GEMINI_API_KEY in .env)")

        lines.append("")
        lines.append("Next Steps:")
        lines.append("  • Try suggested fix and use: OK FIX WORKED (or FAILED)")
        lines.append("  • View full error: ERROR SHOW #{signature}")
        lines.append("  • Enter debug mode: DEV MODE")

        return "\n".join(lines)

    def _build_error_analysis_prompt(
        self, error_ctx: Dict[str, Any], learned_suggestions: List[Dict]
    ) -> str:
        """Build prompt for Gemini error analysis."""
        prompt_parts = []

        prompt_parts.append(
            "You are an expert debugging assistant for uDOS (an offline-first terminal OS)."
        )
        prompt_parts.append("")
        prompt_parts.append("Analyze this error and provide:")
        prompt_parts.append("1. Root cause analysis")
        prompt_parts.append("2. Step-by-step fix instructions")
        prompt_parts.append("3. Prevention tips")
        prompt_parts.append("")
        prompt_parts.append(f"ERROR TYPE: {error_ctx['error_type']}")
        prompt_parts.append(f"MESSAGE: {error_ctx['message']}")

        if error_ctx.get("command"):
            prompt_parts.append(f"COMMAND: {error_ctx['command']}")

        if error_ctx.get("stack_trace"):
            # Truncate stack trace to avoid token limits
            stack = error_ctx["stack_trace"][:1000]
            prompt_parts.append("")
            prompt_parts.append("STACK TRACE:")
            prompt_parts.append(stack)

        if learned_suggestions:
            prompt_parts.append("")
            prompt_parts.append("PREVIOUSLY SUCCESSFUL FIXES:")
            for sugg in learned_suggestions[:3]:
                success_rate = sugg.get("success_rate", 0)
                prompt_parts.append(
                    f"  • {sugg['fix']} ({success_rate:.0%} success rate)"
                )

        prompt_parts.append("")
        prompt_parts.append("Provide concise, actionable advice (max 200 words).")

        return "\n".join(prompt_parts)

    def _build_diagram_prompt(self, description: str, diagram_type: str) -> str:
        """Build AI prompt for diagram generation."""
        type_specs = {
            "sequence": {
                "format": "js-sequence-diagrams syntax",
                "example": "Alice->Bob: Hello\\nNote right of Bob: Bob thinks\\nBob-->Alice: Hi!",
                "rules": [
                    "Use -> for solid lines, --> for dashed lines",
                    "Format: Actor->Actor: Message",
                    'Use "Note left/right of Actor: text" for notes',
                    'Use "Title: text" for diagram title',
                ],
            },
            "flowchart": {
                "format": "flowchart.js syntax",
                "example": "st=>start: Start\\nop=>operation: Process\\ne=>end\\nst->op->e",
                "rules": [
                    "Define nodes: id=>type: label",
                    "Types: start, end, operation, condition, inputoutput, subroutine",
                    "Connect with arrows: node1->node2",
                    "Conditions: cond(yes)->node1, cond(no)->node2",
                ],
            },
            "ascii": {
                "format": "ASCII art",
                "example": "+---+\\n| A |\\n+---+",
                "rules": [
                    "Use box drawing: + - | for borders",
                    "Use arrows: -> <- => <= for connections",
                    "Keep it simple and readable in monospace",
                ],
            },
            "teletext": {
                "format": "Teletext/ANSI art",
                "example": "█▀▀▀█\\n█   █\\n█▄▄▄█",
                "rules": [
                    "Use block chars: █ ▀ ▄ ░ ▒ ▓",
                    "Create retro terminal aesthetic",
                    "Use simple geometric shapes",
                ],
            },
        }

        spec = type_specs.get(diagram_type, type_specs["sequence"])

        prompt = f"""Generate a {diagram_type} diagram for: {description}

OUTPUT FORMAT: {spec['format']}

EXAMPLE:
{spec['example']}

RULES:
"""
        for rule in spec["rules"]:
            prompt += f"  • {rule}\n"

        prompt += f"""
REQUIREMENTS:
  • Output ONLY the diagram code (no markdown fences, no explanations)
  • Follow {spec['format']} syntax exactly
  • Keep it concise and clear
  • Test the syntax mentally before outputting

Generate the diagram code now:"""

        return prompt

    def _handle_clear(self) -> str:
        """Clear conversation history."""
        if self.gemini and self.gemini.is_available:
            self.gemini.clear_conversation()
            return "✅ Conversation history cleared"
        else:
            return "⚠️  No active conversation to clear"

    def _handle_fix(self, params: List[str]) -> str:
        """
        Handle OK FIX commands - AI-powered code fixing with Mistral AI.

        Phase 4: Merged from okfix_handler.py into main OK handler.
        Uses Mistral AI to analyze and fix code issues with Vibe CLI styling.

        Supported formats:
          OK FIX <file>         - Fix specific file
          OK FIX .              - Fix current context
          OK FIX --explain      - Explain without fixing
          OK FIX --vibe         - Extra vibe output
          OK FIX <file> --context - Include recent logs for context

        Args:
            params: Parameters for FIX command

        Returns:
            Fix result message
        """
        if not params:
            return self._format_fix_help()

        # Parse flags
        explain_only = "--explain" in params
        vibe_mode = "--vibe" in params
        with_context = "--context" in params or "--logs" in params

        # Remove flags from params
        file_params = [p for p in params if not p.startswith("--")]

        if not file_params:
            return self._c("yellow", "🤔 What should I fix? Give me a file path!")

        target = file_params[0]

        # Expand path
        if target == ".":
            # Current context - would need context from TUI
            return self._c(
                "yellow", "📂 Context fixing coming soon! For now, specify a file."
            )

        file_path = Path(target)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path

        if not file_path.exists():
            return self._c("red", f"❌ File not found: {target}")

        # Do the fix
        return self._fix_file_impl(
            file_path,
            explain_only=explain_only,
            vibe_mode=vibe_mode,
            with_context=with_context,
        )

    def _handle_status(self, params: List[str] = None) -> str:
        """Show OK assistant status."""

        lines = []

        # Gemini API status (used for all MAKE commands)
        if self.gemini and self.gemini.is_available:
            lines.append("🤖 OK Assistant Status: ACTIVE")
            lines.append("")
            capabilities = self.gemini.get_capabilities()
            lines.append(f"Provider: Gemini API (for MAKE commands)")
            lines.append(f"Model: {capabilities.get('model', 'N/A')}")
            lines.append(f"Context Window: {capabilities['context_window']:,} tokens")
            lines.append(f"Temperature: {self.ok_config.get('temperature')}")
            lines.append(f"Max Tokens: {self.ok_config.get('max_tokens'):,}")
        else:
            lines.append("🤖 OK Assistant Status: INACTIVE")
            lines.append("")
            lines.append("⚠️  Gemini API not available")
            lines.append("Set GEMINI_API_KEY in .env to enable MAKE commands")
            lines.append("")
            return "\n".join(lines)

        # Dev mode status (Vibe CLI for core/extensions code)
        vibe = self._get_vibe_cli()
        lines.append("")
        if vibe and vibe.is_available:
            lines.append("🛠️ Dev Mode: Vibe CLI (for core/extensions code)")
        else:
            lines.append("🛠️ Dev Mode: Vibe CLI not configured")

        # Session statistics
        lines.append("")
        lines.append("📊 Session Statistics:")
        lines.append(f"Total Requests: {self.stats['total_requests']}")
        lines.append(f"Total Tokens: {self.stats['total_tokens']:,}")

        if self.stats["by_command"]:
            lines.append("")
            lines.append("By Command:")
            for cmd, count in self.stats["by_command"].items():
                lines.append(f"  {cmd}: {count}")

        # Context status
        context = self.context_manager.get_context()
        if context["workspace"]["tile_location"]:
            lines.append("")
            lines.append(f"📍 Location: {context['workspace']['tile_location']}")

        return "\n".join(lines)

    def _prompt_ai_setup(self, config) -> Optional[Any]:
        """
        Prompt user for AI provider setup on first use.

        Args:
            config: Config instance

        Returns:
            Initialized AI provider or None if setup failed/skipped
        """
        from pathlib import Path

        # Check if assistant extension is installed
        assistant_path = Path("extensions/assistant")
        if not assistant_path.exists():
            print("\n❌ AI assistant extension not installed")
            print("OK commands require the AI assistant extension")
            print("\nInstallation:")
            print("  1. Ensure extensions/assistant/ directory exists")
            print("  2. Run setup: python extensions/assistant/setup_ai_providers.py")
            print("  3. Restart uDOS")
            return None

        print("\n💡 First-time OK Assistant Setup")
        print("\nRequired: Gemini API (for MAKE commands)")
        print("  • Get free API key: https://aistudio.google.com/app/apikey")
        print("  • Add to .env: GEMINI_API_KEY=your_key_here")

        print("\nOptional: Vibe CLI (for dev mode - core/extensions code)")
        print("  • Requires: Local GPU, Ollama or similar")
        print("  • Used only for modifying core/ and extensions/ code")

        print("\nFeatures enabled with Gemini:")
        print("  • OK MAKE WORKFLOW/SVG/DOC/TEST/MISSION")
        print("  • OK ASK <question>")
        print("  • OK FIX (AI error analysis)")

        print("\n📝 Quick Setup:")
        print("  1. Get Gemini API key: https://aistudio.google.com/app/apikey")
        print("  2. Add to .env: GEMINI_API_KEY=your_key_here")
        print("  3. Restart uDOS")
        print("\n⚠️  Setup skipped - OK commands will not be available")
        print("Set GEMINI_API_KEY in .env and restart uDOS")
        return None

    def _prompt_gemini_setup(self, config) -> Optional[Any]:
        """
        Legacy method - redirects to _prompt_ai_setup.
        Kept for backwards compatibility.
        """
        return self._prompt_ai_setup(config)

    # ========================================================================
    # OK FIX Implementation (Phase 4: Merged from okfix_handler.py)
    # ========================================================================

    def _init_mistral(self) -> None:
        """Initialize Mistral client for code fixing."""
        try:
            from wizard.providers.devstral_client import DevstralClient

            self.mistral_client = DevstralClient()
            logger.info("[LOCAL] Mistral client initialized for OK FIX")
        except ImportError as e:
            logger.warning(f"[LOCAL] Could not import Mistral client: {e}")
        except Exception as e:
            logger.error(f"[LOCAL] Failed to initialize Mistral: {e}")

    def _load_fix_prompts(self) -> None:
        """Load prompt templates for OK FIX."""
        self.fix_prompts = {
            "vibe": self._load_prompt_template("vibe-cli"),
            "okfix": self._load_prompt_template("okfix"),
        }
        logger.debug("[LOCAL] Loaded OK FIX prompt templates")

    def _load_prompt_template(self, prompt_id: str) -> dict:
        """Load a prompt template from the ai prompts directory."""
        prompt_path = Path("core/data/prompts/ai") / f"{prompt_id}.md"
        if not prompt_path.exists():
            return {}

        try:
            content = prompt_path.read_text()
            result = {"content": content, "sections": {}}

            # Parse frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    result["frontmatter"] = parts[1].strip()
                    result["body"] = parts[2].strip()

            return result
        except Exception as e:
            logger.warning(f"[LOCAL] Could not load prompt template {prompt_id}: {e}")
            return {}

    def _read_recent_logs(self, category: str, lines: int = 30) -> str:
        """Read recent log entries for context."""
        log_dir = Path("memory/logs")
        log_file = log_dir / f"{category}-{date.today()}.log"

        if not log_file.exists():
            return ""

        try:
            with open(log_file, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            logger.warning(f"[LOCAL] Could not read logs: {e}")
            return ""

    def _read_error_logs(self, lines: int = 20) -> str:
        """Read recent error logs."""
        return self._read_recent_logs("error", lines)

    def _read_session_logs(self, lines: int = 30) -> str:
        """Read recent session command logs."""
        return self._read_recent_logs("session-commands", lines)

    def _read_debug_logs(self, lines: int = 20) -> str:
        """Read recent debug logs."""
        return self._read_recent_logs("debug", lines)

    def _fix_file_impl(
        self,
        file_path: Path,
        explain_only: bool = False,
        vibe_mode: bool = False,
        with_context: bool = False,
    ) -> str:
        """Fix issues in a single file."""
        output = []

        # Vibe intro
        if vibe_mode:
            output.append(self._c("cyan", random.choice(self.VIBE_INTROS)))
            output.append("")

        output.append(self._c("bold", f"📄 Analyzing: {file_path.name}"))
        output.append(self._c("dim", f"   {file_path}"))
        output.append("")

        # Read file
        try:
            code = file_path.read_text()
        except Exception as e:
            return self._c("red", f"❌ Could not read file: {e}")

        # Check if Mistral is available
        if not self.mistral_client:
            return self._c(
                "yellow", "⚠️ Mistral AI not available. Check your configuration."
            )

        # Build the fix prompt
        prompt = self._build_fix_prompt(code, file_path, include_context=with_context)

        if with_context:
            output.append(self._c("dim", "   📋 Including log context..."))

        output.append(self._c("blue", "🤖 Consulting Mistral AI..."))

        try:
            # Call Mistral
            response = self.mistral_client.generate(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3,  # Lower temp for more consistent fixes
            )

            if not response.get("success"):
                return self._c(
                    "red", f"❌ AI error: {response.get('error', 'Unknown')}"
                )

            ai_response = response.get("content", "")

            # Parse the response
            result = self._parse_fix_response(ai_response, code)

            if explain_only:
                output.append(self._format_fix_explanation(result, vibe_mode))
            else:
                # Apply fixes
                if result.fixed_code and result.fixed_code != code:
                    output.append(self._apply_fixes(file_path, result, vibe_mode))
                else:
                    output.append(
                        self._c("green", "✨ Code looks good! No changes needed.")
                    )

        except Exception as e:
            logger.error(f"[LOCAL] OK FIX failed: {e}", exc_info=True)
            return self._c("red", f"❌ Error: {e}")

        return "\n".join(output)

    def _build_fix_prompt(
        self, code: str, file_path: Path, include_context: bool = False
    ) -> str:
        """Build the prompt for Mistral to fix code."""
        language = self._detect_language(file_path)

        # Base prompt
        prompt = f"""You are a code fixer. Analyze this {language} code and fix any issues.

IMPORTANT: Respond in this exact format:
---ANALYSIS---
List each issue found, one per line, with line numbers if possible.
---FIXED_CODE---
The complete fixed code (not a diff).
---CHANGES---
List each change made, one per line.

If the code is fine, still include the sections but say "No issues found" for analysis.

"""

        # Add log context if requested
        if include_context:
            error_logs = self._read_error_logs(15)
            session_logs = self._read_session_logs(20)

            if error_logs or session_logs:
                prompt += "CONTEXT FROM SYSTEM LOGS:\n"
                if error_logs:
                    prompt += f"\nRecent Errors:\n{error_logs}\n"
                if session_logs:
                    prompt += f"\nRecent Commands:\n{session_logs}\n"
                prompt += "\nConsider this context when analyzing the code.\n\n"

        prompt += f"""CODE TO FIX:
```{language}
{code}
```

Focus on:
- Syntax errors
- Logic bugs
- Common mistakes
- Best practices
- Import issues
- Type hints (for Python)
"""
        return prompt

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".rs": "rust",
            ".go": "go",
            ".sh": "bash",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
        }
        return ext_map.get(file_path.suffix.lower(), "code")

    def _parse_fix_response(self, response: str, original_code: str) -> FixResult:
        """Parse Mistral's response into a structured result."""
        result = FixResult(success=True, original_code=original_code)

        # Extract sections
        sections = {}
        current_section = None
        current_content = []

        for line in response.split("\n"):
            if line.strip().startswith("---") and line.strip().endswith("---"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line.strip("- ").lower()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        # Extract analysis
        if "analysis" in sections:
            result.explanation = sections["analysis"]
            # Count issues
            for line in sections["analysis"].split("\n"):
                if "error" in line.lower():
                    result.errors_fixed += 1
                elif "warning" in line.lower() or "issue" in line.lower():
                    result.warnings_fixed += 1

        # Extract fixed code
        if "fixed_code" in sections:
            fixed = sections["fixed_code"]
            # Remove markdown code blocks if present
            if fixed.startswith("```"):
                lines = fixed.split("\n")
                fixed = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                )
            result.fixed_code = fixed.strip()

        # Extract changes
        if "changes" in sections:
            result.changes_made = [
                line.strip("- •").strip()
                for line in sections["changes"].split("\n")
                if line.strip() and not line.strip().lower().startswith("no ")
            ]

        return result

    def _format_fix_explanation(self, result: FixResult, vibe_mode: bool) -> str:
        """Format the explanation output."""
        output = []

        output.append(self._c("bold", "📋 Analysis:"))
        output.append("")

        if result.explanation:
            for line in result.explanation.split("\n"):
                if line.strip():
                    output.append(f"   {line}")
        else:
            output.append(self._c("green", "   No issues found!"))

        output.append("")

        if result.changes_made:
            output.append(self._c("bold", "🔧 Proposed Changes:"))
            for change in result.changes_made:
                output.append(self._c("yellow", f"   • {change}"))

        output.append("")
        output.append(self._c("dim", "Run without --explain to apply these fixes."))

        return "\n".join(output)

    def _apply_fixes(self, file_path: Path, result: FixResult, vibe_mode: bool) -> str:
        """Apply fixes to the file."""
        output = []

        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + ".okfix.bak")
        file_path.rename(backup_path)

        try:
            # Write fixed code
            file_path.write_text(result.fixed_code)

            output.append(
                self._c(
                    "green",
                    (
                        random.choice(self.VIBE_FIXES)
                        if vibe_mode
                        else "✅ Fixes applied!"
                    ),
                )
            )
            output.append("")

            if result.changes_made:
                output.append(self._c("bold", "📝 Changes made:"))
                for change in result.changes_made:
                    output.append(self._c("green", f"   ✓ {change}"))

            output.append("")
            output.append(self._c("dim", f"   Backup saved: {backup_path.name}"))

            # Log the fix
            logger.info(
                f"[LOCAL] OK FIX applied to {file_path}: {len(result.changes_made)} changes"
            )

        except Exception as e:
            # Restore backup on failure
            if backup_path.exists():
                backup_path.rename(file_path)
            raise e

        return "\n".join(output)

    def _c(self, color: str, text: str) -> str:
        """Apply color to text (Vibe CLI style)."""
        if color in self.COLORS:
            return f"{self.COLORS[color]}{text}{self.COLORS['reset']}"
        return text

    def _format_fix_help(self) -> str:
        """Format OK FIX help text."""
        return f"""{self._c('bold', '🎸 OK FIX - AI Code Fixer')}

{self._c('cyan', 'Usage:')}
  OK FIX <file>             Fix errors in file
  OK FIX <file> --explain   Show what would be fixed
  OK FIX <file> --vibe      Extra verbose vibe output
  OK FIX <file> --context   Include recent logs for context
  OK FIX <file> --logs      Alias for --context

{self._c('cyan', 'Examples:')}
  OK FIX core/commands/my_handler.py
  OK FIX ./script.py --explain
  OK FIX memory/ucode/test.py --vibe
  OK FIX broken.py --context      (include error logs)

{self._c('cyan', 'Prompt Files:')}
  core/data/prompts/ai/vibe-cli.md
  core/data/prompts/ai/okfix.md

{self._c('dim', 'Powered by Mistral AI (open-mistral-nemo)')}
"""

    def _extract_code(self, response: str) -> str:
        """Extract code block from response."""
        # Look for code blocks
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                # Get code between first ```
                code = parts[1]
                # Remove language identifier if present
                if "\n" in code:
                    lines = code.split("\n")
                    if lines[0].strip() in ["python", "upy", "svg", "xml"]:
                        code = "\n".join(lines[1:])
                return code.strip()

        # No code blocks - return full response
        return response.strip()

    def _update_stats(self, command: str, tokens: int) -> None:
        """Update usage statistics."""
        self.stats["total_requests"] += 1
        self.stats["total_tokens"] += tokens
        self.stats["by_command"][command] = self.stats["by_command"].get(command, 0) + 1

        # Update context manager
        self.context_manager.add_command(f"OK MAKE {command.upper()}", "success")

    def _show_help(self) -> str:
        """Show OK command help."""
        return (
            "╔══════════════════════════════════════════════════════════╗\n"
            "║               OK Assistant - AI Workflows                ║\n"
            "╚══════════════════════════════════════════════════════════╝\n\n"
            "Workflows:\n"
            "  OK MAKE WORKFLOW <desc>  - Generate uPY workflow script\n"
            "  OK MAKE MISSION <cat> <tile> - Generate mission script\n"
            "  OK MAKE TEST <file>      - Generate unit tests\n"
            "  OK MAKE DOC <topic>      - Generate documentation\n\n"
            "Graphics (Typora/GitHub standards):\n"
            "  OK MAKE SEQUENCE <desc>  - js-sequence diagram (interactions)\n"
            "  OK MAKE FLOWCHART <desc> - flowchart.js diagram (processes)\n"
            "  OK MAKE SVG <desc>       - Custom vector graphics\n"
            "  OK MAKE ASCII <desc>     - Text-based art\n"
            "  OK MAKE TELETEXT <desc>  - Retro terminal graphics\n\n"
            "Assistant:\n"
            "  OK ASK <question>        - Ask AI assistant\n"
            "  OK FIX [#signature]      - Analyze error and suggest fixes\n"
            "  OK CLEAR                 - Clear conversation history\n"
            "  OK STATUS                - Show usage statistics\n\n"
            "Examples:\n"
            '  OK MAKE SEQUENCE "user login process"\n'
            '  OK MAKE FLOWCHART "water purification steps"\n'
            '  OK MAKE SVG "fire triangle diagram"\n'
            '  OK ASK "How do I use the TILE system?"\n'
            "  OK FIX                   - Fix latest error\n\n"
            "TUI:\n"
            "  Press O-key to open OK assistant panel\n\n"
            "Configuration:\n"
            "  Gemini API (for MAKE commands):\n"
            "    • Free API: https://aistudio.google.com/app/apikey\n"
            "    • Set in .env: GEMINI_API_KEY=your_key_here\n\n"
            "  Vibe CLI (optional, for dev mode only):\n"
            "    • Used only for core/ and extensions/ code modifications\n"
            "    • Requires local GPU/Ollama\n\n"
            "  Configure via: CONFIG (C-key) → [OK] tab\n"
        )


# Factory function for handler creation
def create_ok_handler(**kwargs) -> OKHandler:
    """
    Create OK handler instance.

    Args:
        **kwargs: Handler dependencies

    Returns:
        OKHandler instance
    """
    return OKHandler(**kwargs)
