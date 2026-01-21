"""
uDOS Alpha v1.0.0.0+ - GUIDE AI Command Handler

AI Knowledge Bank commands for managing perfected AI instruction library.
Note: Separate from GUIDE (knowledge/markdown) - this is GUIDE AI (AI instructions).

Commands:
- GUIDE AI LIST [category] - List available AI instructions
- GUIDE AI SHOW <id> - Show instruction details
- GUIDE AI RUN <id> [vars...] - Execute instruction with optional variables
- GUIDE AI SEARCH <query> - Search instructions by keyword
- GUIDE AI STATS - Show knowledge bank statistics
- GUIDE AI BUILD - Launch interactive instruction builder (Wizard only)

Version: 1.0.0.0
"""

import json
from pathlib import Path
from typing import Optional, Dict, List
from .base_handler import BaseCommandHandler
from dev.goblin.core.services.knowledge_bank import KnowledgeBank, Instruction


class GuideAICommandHandler(BaseCommandHandler):
    """Handles GUIDE AI (AI Knowledge Bank) commands."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kb = KnowledgeBank()

        # Check if we're in wizard mode for build command
        import os

        self.is_wizard = os.getenv("UDOS_WIZARD_MODE", "").lower() == "true"

    def handle(self, command: str, params: List[str], grid=None, parser=None) -> str:
        """
        Route BANK commands to appropriate handlers.

        Args:
            command: The subcommand (LIST, SHOW, RUN, etc.)
            params: List of parameters
            grid: Grid context (optional)
            parser: Command parser (optional)

        Returns:
            Result message
        """
        if command == "LIST":
            return self._handle_list(params)
        elif command == "SHOW":
            return self._handle_show(params)
        elif command == "RUN":
            return self._handle_run(params)
        elif command == "SEARCH":
            return self._handle_search(params)
        elif command == "STATS":
            return self._handle_stats(params)
        elif command == "BUILD":
            return self._handle_build(params)
        else:
            return self._handle_help()

    def _handle_list(self, params: List[str]) -> str:
        """List available instructions."""
        category = params[0] if params else None

        try:
            instructions = self.kb.list_instructions(category=category)

            if not instructions:
                msg = f"No instructions found"
                if category:
                    msg += f" in category '{category}'"
                return msg

            # Group by category
            by_category = {}
            for inst in instructions:
                cat = inst.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(inst)

            # Format output
            lines = ["\n📚 Knowledge Bank Instructions\n"]
            lines.append("=" * 60)

            for cat in sorted(by_category.keys()):
                lines.append(f"\n{cat.upper()}:")
                for inst in sorted(
                    by_category[cat], key=lambda x: x.quality_score, reverse=True
                ):
                    # Quality indicator
                    if inst.quality_score >= 9.0:
                        quality_badge = "🌟"
                    elif inst.quality_score >= 7.0:
                        quality_badge = "✅"
                    elif inst.quality_score >= 5.0:
                        quality_badge = "⚡"
                    else:
                        quality_badge = "📝"

                    lines.append(
                        f"  {quality_badge} [{inst.quality_score:.1f}] {inst.id}"
                    )
                    lines.append(f"      {inst.title}")

                    # Show required variables if any
                    if inst.variables:
                        var_names = ", ".join(inst.variables.keys())
                        lines.append(f"      Variables: {var_names}")

            lines.append(f"\n{'=' * 60}")
            lines.append(f"Total: {len(instructions)} instructions")
            lines.append("\nUse: GUIDE AI SHOW <id> to view details")
            lines.append("     GUIDE AI RUN <id> to execute")

            return "\n".join(lines)

        except Exception as e:
            return f"❌ Failed to list instructions: {e}"

    def _handle_show(self, params: List[str]) -> str:
        """Show instruction details."""
        if not params:
            return "❌ Usage: GUIDE AI SHOW <instruction_id>"

        instruction_id = params[0]

        try:
            inst = self.kb.get_instruction(instruction_id)

            if not inst:
                return (
                    f"❌ Instruction '{instruction_id}' not found\n"
                    f"   Use: KNOWLEDGE LIST to see available instructions"
                )

            # Format detailed view
            lines = ["\n" + "=" * 60]
            lines.append(f"📋 {inst.title}")
            lines.append("=" * 60)

            # Metadata
            lines.append(f"\nID: {inst.id}")
            lines.append(f"Category: {inst.category}")
            if inst.subcategory:
                lines.append(f"Subcategory: {inst.subcategory}")
            lines.append(f"Quality: {inst.quality_score}/10")

            if inst.tags:
                lines.append(f"Tags: {', '.join(inst.tags)}")

            # Instruction text
            lines.append(f"\n{'─' * 60}")
            lines.append("INSTRUCTION:")
            lines.append("─" * 60)
            lines.append(inst.text)
            lines.append("─" * 60)

            # Variables
            if inst.variables:
                lines.append(f"\nVARIABLES:")
                for var_name, var_info in inst.variables.items():
                    required = (
                        " (required)" if var_info.get("required") else " (optional)"
                    )
                    lines.append(f"  {{{{{var_name}}}}}{required}")
                    lines.append(f"    {var_info.get('description', 'No description')}")

            # Execution config
            lines.append(f"\nEXECUTION:")
            lines.append(f"  Primary model: {inst.model['primary']}")
            if inst.model.get("fallback"):
                lines.append(
                    f"  Fallback models: {', '.join(inst.model['fallback'][:3])}"
                )
            lines.append(f"  Temperature: {inst.parameters.get('temperature', 0.7)}")
            lines.append(f"  Max tokens: {inst.parameters.get('max_tokens', 2048)}")

            # Lineage info
            if inst.lineage:
                gemini_iters = inst.lineage.get("gemini_iterations", [])
                if gemini_iters:
                    lines.append(f"\nLINEAGE:")
                    lines.append(
                        f"  Refined with Gemini: {len(gemini_iters)} iterations"
                    )

                test_results = inst.lineage.get("test_results", [])
                if test_results:
                    passed = sum(1 for t in test_results if t.get("success"))
                    lines.append(f"  Tested: {passed}/{len(test_results)} passed")

            # Usage
            lines.append(f"\nUSAGE:")
            if inst.variables:
                var_example = " ".join(
                    f"{name}=value" for name in inst.variables.keys()
                )
                lines.append(f"  KNOWLEDGE RUN {inst.id} {var_example}")
            else:
                lines.append(f"  KNOWLEDGE RUN {inst.id}")

            lines.append("=" * 60)

            return "\n".join(lines)

        except Exception as e:
            return f"❌ Failed to show instruction: {e}"

    def _handle_run(self, params: List[str]) -> str:
        """Execute an instruction."""
        if not params:
            return (
                "❌ Usage: KNOWLEDGE RUN <instruction_id> [var1=value1 var2=value2 ...]"
            )

        instruction_id = params[0]

        try:
            inst = self.kb.get_instruction(instruction_id)

            if not inst:
                return f"❌ Instruction '{instruction_id}' not found"

            # Parse variables from remaining params
            variables = {}
            for param in params[1:]:
                if "=" in param:
                    key, value = param.split("=", 1)
                    variables[key.strip()] = value.strip()

            # Check required variables
            missing = []
            for var_name, var_info in inst.variables.items():
                if var_info.get("required") and var_name not in variables:
                    missing.append(var_name)

            if missing:
                return (
                    f"❌ Missing required variables: {', '.join(missing)}\n"
                    f"   Use: KNOWLEDGE SHOW {instruction_id} to see variable details"
                )

            # Render instruction with variables
            rendered = self.kb.render_instruction(inst, variables)

            # Execute with appropriate AI service
            # For now, show the rendered instruction
            # TODO: Integrate with Ollama/Vibe CLI service

            lines = ["\n" + "=" * 60]
            lines.append(f"🤖 Executing: {inst.title}")
            lines.append("=" * 60)
            lines.append(f"\nModel: {inst.model['primary']}")

            if variables:
                lines.append(f"\nVariables:")
                for k, v in variables.items():
                    lines.append(f"  {k} = {v}")

            lines.append(f"\n{'─' * 60}")
            lines.append("RENDERED INSTRUCTION:")
            lines.append("─" * 60)
            lines.append(rendered)
            lines.append("─" * 60)

            # Try to execute with Ollama if available
            try:
                from wizard.extensions.assistant.ollama_service import OllamaService

                ollama = OllamaService()

                lines.append(f"\n🔄 Running with Ollama...")
                result = ollama.generate(rendered, model=inst.model["primary"])

                lines.append(f"\n{'═' * 60}")
                lines.append("RESULT:")
                lines.append("═" * 60)
                lines.append(result)
                lines.append("═" * 60)

            except ImportError:
                lines.append(
                    f"\n⚠️  Ollama not available - showing rendered instruction only"
                )
                lines.append(f"   Install: INSTALL OLLAMA")
            except Exception as e:
                lines.append(f"\n❌ Execution failed: {e}")

            return "\n".join(lines)

        except Exception as e:
            return f"❌ Failed to run instruction: {e}"

    def _handle_search(self, params: List[str]) -> str:
        """Search instructions by keyword."""
        if not params:
            return "❌ Usage: GUIDE AI SEARCH <query>"

        query = " ".join(params)

        try:
            results = self.kb.search(query)

            if not results:
                return f"No instructions found matching '{query}'"

            lines = [f"\n🔍 Search results for '{query}'\n"]
            lines.append("=" * 60)

            for inst in results[:20]:  # Show first 20
                quality_badge = (
                    "🌟"
                    if inst.quality_score >= 9.0
                    else "✅" if inst.quality_score >= 7.0 else "⚡"
                )
                lines.append(f"\n{quality_badge} [{inst.quality_score:.1f}] {inst.id}")
                lines.append(f"    {inst.title}")
                lines.append(f"    Category: {inst.category}")

            lines.append(f"\n{'=' * 60}")
            lines.append(f"Found: {len(results)} instructions")

            if len(results) > 20:
                lines.append(f"(Showing first 20)")

            return "\n".join(lines)

        except Exception as e:
            return f"❌ Search failed: {e}"

    def _handle_stats(self, params: List[str]) -> str:
        """Show knowledge bank statistics."""
        try:
            stats = self.kb.get_stats()

            lines = ["\n📊 Knowledge Bank Statistics\n"]
            lines.append("=" * 60)

            lines.append(f"\nTotal Instructions: {stats['total']}")
            lines.append(f"System Instructions: {stats['system_count']}")
            lines.append(f"User Instructions: {stats['user_count']}")

            if stats["by_category"]:
                lines.append(f"\nBy Category:")
                for cat, count in sorted(stats["by_category"].items()):
                    lines.append(f"  {cat}: {count}")

            if stats["by_quality"]:
                lines.append(f"\nBy Quality:")
                lines.append(
                    f"  Production (9-10): {stats['by_quality'].get('production', 0)}"
                )
                lines.append(f"  Good (7-8): {stats['by_quality'].get('good', 0)}")
                lines.append(f"  Usable (5-6): {stats['by_quality'].get('usable', 0)}")
                lines.append(
                    f"  Experimental (3-4): {stats['by_quality'].get('experimental', 0)}"
                )
                lines.append(f"  Draft (1-2): {stats['by_quality'].get('draft', 0)}")

            lines.append(f"\nAverage Quality: {stats['avg_quality']:.1f}/10")

            lines.append("=" * 60)

            return "\n".join(lines)

        except Exception as e:
            return f"❌ Failed to get stats: {e}"

    def _handle_build(self, params: List[str]) -> str:
        """Launch interactive instruction builder."""
        if not self.is_wizard:
            return (
                "❌ KNOWLEDGE BUILD requires Wizard Mode\n"
                "   This command uses Gemini API for instruction refinement\n"
                "   Run on Wizard Server or use: CONFIG ROLE wizard"
            )

        # Launch the uPY builder script
        try:
            import subprocess

            script_path = Path("memory/ucode/knowledge/build_instruction.upy")

            if not script_path.exists():
                return (
                    f"❌ Builder script not found: {script_path}\n"
                    f"   Expected location: memory/ucode/knowledge/build_instruction.upy"
                )

            return (
                f"🚀 Launching Knowledge Bank Builder...\n"
                f"\n   RUN {script_path}\n"
                f"\nOr run directly:\n"
                f"   ./start_udos.sh {script_path}"
            )

        except Exception as e:
            return f"❌ Failed to launch builder: {e}"

    def _handle_help(self) -> str:
        """Show KNOWLEDGE command help."""
        lines = ["\n📚 Knowledge Bank Commands\n"]
        lines.append("=" * 60)
        lines.append("\nKNOWLEDGE LIST [category]  (alias: KNOW LIST)")
        lines.append("  List available AI instructions")
        lines.append("  Optional: Filter by category")
        lines.append("\nKNOWLEDGE SHOW <instruction_id>  (alias: KNOW SHOW)")
        lines.append("  Show detailed instruction information")
        lines.append(
            "\nKNOWLEDGE RUN <instruction_id> [var1=value ...]  (alias: KNOW RUN)"
        )
        lines.append("  Execute instruction with optional variables")
        lines.append("\nKNOWLEDGE SEARCH <query>  (alias: KNOW SEARCH)")
        lines.append("  Search instructions by keyword")
        lines.append("\nKNOWLEDGE STATS  (alias: KNOW STATS)")
        lines.append("  Show knowledge bank statistics")
        lines.append("\nKNOWLEDGE BUILD  (alias: KNOW BUILD)")
        lines.append("  Launch interactive builder (Wizard only)")
        lines.append("\n" + "=" * 60)
        lines.append("\nCategories: coding, writing, image, workflow,")
        lines.append("           analysis, creative, system")
        lines.append("\nExamples:")
        lines.append("  KNOWLEDGE LIST coding")
        lines.append("  KNOW SHOW fix-python-errors")
        lines.append("  KNOW RUN fix-python-errors file=core/test.py")
        lines.append("=" * 60)

        return "\n".join(lines)
