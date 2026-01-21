"""
uDOS BUNDLE Handler - Content Package Management

Implements the BUNDLE system for managing collections of .udos.md documents.

Commands:
- BUNDLE LIST               List all bundles
- BUNDLE LIST --active      List in-progress bundles
- BUNDLE SHOW <path>        Show bundle details
- BUNDLE START <path>       Begin a bundle
- BUNDLE PAUSE <path>       Pause drip delivery
- BUNDLE RESUME <path>      Resume drip delivery
- BUNDLE NEXT               Show next drip item
- BUNDLE SKIP               Skip current item
- BUNDLE COMPLETE <path>    Mark bundle as finished
- BUNDLE REVIEW <path>      Check for updates needed
- BUNDLE PLAN <topic>       Generate bundle outline (Wizard)
- BUNDLE GENERATE <plan>    Create docs from plan (Wizard)

Version: 1.0.0
Created: 2026-01-07
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from dev.goblin.core.commands.base_handler import BaseCommandHandler
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("command-bundle")


class BundleHandler(BaseCommandHandler):
    """Handler for BUNDLE content package commands."""

    MANIFEST_FILENAME = ".bundle.udos.md"
    STATE_DIR = ".state"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_path = Path(__file__).parent.parent.parent
        self.knowledge_path = self.root_path / "knowledge"
        self.memory_path = self.root_path / "memory"

    def handle(self, command: str, params: list, grid=None, parser=None) -> dict:
        """Route BUNDLE commands to appropriate handlers."""

        if not params:
            return self._handle_list([], grid)

        subcommand = params[0].upper()
        sub_params = params[1:] if len(params) > 1 else []

        handlers = {
            "LIST": self._handle_list,
            "SHOW": self._handle_show,
            "START": self._handle_start,
            "PAUSE": self._handle_pause,
            "RESUME": self._handle_resume,
            "NEXT": self._handle_next,
            "SKIP": self._handle_skip,
            "COMPLETE": self._handle_complete,
            "REVIEW": self._handle_review,
            "PLAN": self._handle_plan,
            "GENERATE": self._handle_generate,
            "STATUS": self._handle_status,
        }

        handler = handlers.get(subcommand)
        if handler:
            return handler(sub_params, grid)
        else:
            # Assume first param is a path for SHOW
            return self._handle_show(params, grid)

    def _find_bundles(
        self, base_path: Path = None, active_only: bool = False
    ) -> List[Dict]:
        """Find all bundles in knowledge directory."""
        base = base_path or self.knowledge_path
        bundles = []

        for root, dirs, files in os.walk(base):
            if self.MANIFEST_FILENAME in files:
                bundle_path = Path(root)
                manifest = self._load_manifest(bundle_path)
                if manifest:
                    state = self._load_state(bundle_path)
                    bundle_info = {
                        "path": str(bundle_path.relative_to(self.root_path)),
                        "title": manifest.get("title", bundle_path.name),
                        "type": manifest.get("type", "knowledge-bundle"),
                        "documents": len(manifest.get("sequence", [])),
                        "state": state,
                        "active": (
                            state.get("status") == "in-progress" if state else False
                        ),
                    }

                    if active_only and not bundle_info["active"]:
                        continue

                    bundles.append(bundle_info)

        return bundles

    def _load_manifest(self, bundle_path: Path) -> Optional[Dict]:
        """Load bundle manifest from .bundle.udos.md."""
        manifest_file = bundle_path / self.MANIFEST_FILENAME
        if not manifest_file.exists():
            return None

        try:
            content = manifest_file.read_text()
            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import yaml

                    return yaml.safe_load(parts[1])
        except Exception as e:
            logger.error(f"[LOCAL] Error loading manifest {manifest_file}: {e}")

        return None

    def _load_state(self, bundle_path: Path) -> Optional[Dict]:
        """Load bundle progress state."""
        state_file = bundle_path / self.STATE_DIR / "progress.json"
        if not state_file.exists():
            return None

        try:
            return json.loads(state_file.read_text())
        except Exception as e:
            logger.error(f"[LOCAL] Error loading state {state_file}: {e}")

        return None

    def _save_state(self, bundle_path: Path, state: Dict) -> bool:
        """Save bundle progress state."""
        state_dir = bundle_path / self.STATE_DIR
        state_dir.mkdir(exist_ok=True)
        state_file = state_dir / "progress.json"

        try:
            state["updated"] = datetime.now().isoformat()
            state_file.write_text(json.dumps(state, indent=2))
            return True
        except Exception as e:
            logger.error(f"[LOCAL] Error saving state {state_file}: {e}")
            return False

    def _handle_list(self, params: list, grid=None) -> dict:
        """List all bundles."""
        active_only = "--active" in params or "-a" in params

        bundles = self._find_bundles(active_only=active_only)

        if not bundles:
            msg = "No active bundles found." if active_only else "No bundles found."
            return {"status": "info", "message": msg}

        lines = ["📦 BUNDLES", ""]

        for bundle in bundles:
            status = "🔄" if bundle["active"] else "⬜"
            progress = ""
            if bundle["state"]:
                completed = bundle["state"].get("completed_count", 0)
                total = bundle["documents"]
                progress = f" [{completed}/{total}]"

            lines.append(f"{status} {bundle['title']}{progress}")
            lines.append(f"   📁 {bundle['path']}")
            lines.append("")

        return {
            "status": "success",
            "message": "\n".join(lines),
            "data": {"bundles": bundles},
        }

    def _handle_show(self, params: list, grid=None) -> dict:
        """Show bundle details."""
        if not params:
            return {"status": "error", "message": "Usage: BUNDLE SHOW <path>"}

        bundle_path = self._resolve_bundle_path(params[0])
        if not bundle_path:
            return {"status": "error", "message": f"Bundle not found: {params[0]}"}

        manifest = self._load_manifest(bundle_path)
        state = self._load_state(bundle_path) or {}

        lines = [
            f"📦 {manifest.get('title', bundle_path.name)}",
            f"Type: {manifest.get('type', 'knowledge-bundle')}",
            f"Category: {manifest.get('category', 'general')}",
            "",
        ]

        # Drip settings
        drip = manifest.get("drip", {})
        if drip.get("enabled"):
            lines.append("⏰ Drip Schedule:")
            lines.append(f"   Interval: {drip.get('interval', 'daily')}")
            lines.append(f"   Items per session: {drip.get('items_per_session', 1)}")
            lines.append("")

        # Wellbeing settings
        wellbeing = manifest.get("wellbeing", {})
        if wellbeing:
            lines.append("🧘 Wellbeing:")
            lines.append(f"   Energy cost: {wellbeing.get('energy_cost', 'medium')}")
            lines.append(
                f"   Focus required: {wellbeing.get('focus_required', 'medium')}"
            )
            lines.append("")

        # Contents
        sequence = manifest.get("sequence", [])
        if sequence:
            lines.append("📄 Contents:")
            completed = state.get("completed", [])
            for i, doc in enumerate(sequence, 1):
                status = "✅" if doc in completed else "⬜"
                current = "👉 " if doc == state.get("current_item") else "   "
                lines.append(f"{current}{status} {i}. {doc}")
            lines.append("")

        # Progress
        if state:
            lines.append(
                f"📊 Progress: {len(state.get('completed', []))}/{len(sequence)}"
            )
            lines.append(f"Status: {state.get('status', 'not-started')}")
            if state.get("started"):
                lines.append(f"Started: {state.get('started')[:10]}")

        return {
            "status": "success",
            "message": "\n".join(lines),
            "data": {"manifest": manifest, "state": state},
        }

    def _handle_start(self, params: list, grid=None) -> dict:
        """Start a bundle."""
        if not params:
            return {"status": "error", "message": "Usage: BUNDLE START <path>"}

        bundle_path = self._resolve_bundle_path(params[0])
        if not bundle_path:
            return {"status": "error", "message": f"Bundle not found: {params[0]}"}

        manifest = self._load_manifest(bundle_path)
        sequence = manifest.get("sequence", [])

        if not sequence:
            return {"status": "error", "message": "Bundle has no content sequence"}

        state = {
            "status": "in-progress",
            "started": datetime.now().isoformat(),
            "current_item": sequence[0],
            "current_index": 0,
            "completed": [],
            "completed_count": 0,
            "skipped": [],
        }

        self._save_state(bundle_path, state)

        logger.info(f"[LOCAL] Started bundle: {bundle_path}")

        return {
            "status": "success",
            "message": f"📦 Started: {manifest.get('title', bundle_path.name)}\n\n"
            f"First item: {sequence[0]}\n"
            f"Use BUNDLE NEXT to see current item.",
            "data": {"bundle": str(bundle_path), "state": state},
        }

    def _handle_pause(self, params: list, grid=None) -> dict:
        """Pause bundle drip delivery."""
        if not params:
            return {"status": "error", "message": "Usage: BUNDLE PAUSE <path>"}

        bundle_path = self._resolve_bundle_path(params[0])
        if not bundle_path:
            return {"status": "error", "message": f"Bundle not found: {params[0]}"}

        state = self._load_state(bundle_path)
        if not state:
            return {"status": "error", "message": "Bundle not started"}

        state["status"] = "paused"
        state["paused_at"] = datetime.now().isoformat()
        self._save_state(bundle_path, state)

        return {"status": "success", "message": "⏸️ Bundle paused"}

    def _handle_resume(self, params: list, grid=None) -> dict:
        """Resume bundle drip delivery."""
        if not params:
            return {"status": "error", "message": "Usage: BUNDLE RESUME <path>"}

        bundle_path = self._resolve_bundle_path(params[0])
        if not bundle_path:
            return {"status": "error", "message": f"Bundle not found: {params[0]}"}

        state = self._load_state(bundle_path)
        if not state:
            return {"status": "error", "message": "Bundle not started"}

        state["status"] = "in-progress"
        state["resumed_at"] = datetime.now().isoformat()
        self._save_state(bundle_path, state)

        return {"status": "success", "message": "▶️ Bundle resumed"}

    def _handle_next(self, params: list, grid=None) -> dict:
        """Show next drip item from active bundle."""
        # Find first active bundle
        bundles = self._find_bundles(active_only=True)

        if not bundles:
            return {
                "status": "info",
                "message": "No active bundles. Use BUNDLE START <path>",
            }

        # Get first active bundle
        bundle_info = bundles[0]
        bundle_path = self.root_path / bundle_info["path"]
        manifest = self._load_manifest(bundle_path)
        state = self._load_state(bundle_path)

        current_item = state.get("current_item")
        if not current_item:
            return {
                "status": "info",
                "message": "Bundle completed! Use BUNDLE START to begin another.",
            }

        # Read the current document
        doc_path = bundle_path / current_item
        if doc_path.exists():
            content = doc_path.read_text()
            lines = [
                f"📄 {current_item}",
                f"Bundle: {manifest.get('title', bundle_path.name)}",
                f"Progress: {state.get('completed_count', 0) + 1}/{len(manifest.get('sequence', []))}",
                "",
                "---",
                "",
                content[:2000] + ("..." if len(content) > 2000 else ""),
                "",
                "---",
                "",
                "✅ Mark complete: BUNDLE COMPLETE",
                "⏭️ Skip this item: BUNDLE SKIP",
            ]
            return {"status": "success", "message": "\n".join(lines)}
        else:
            return {"status": "error", "message": f"Document not found: {current_item}"}

    def _handle_skip(self, params: list, grid=None) -> dict:
        """Skip current item in active bundle."""
        bundles = self._find_bundles(active_only=True)

        if not bundles:
            return {"status": "info", "message": "No active bundles."}

        bundle_info = bundles[0]
        bundle_path = self.root_path / bundle_info["path"]
        manifest = self._load_manifest(bundle_path)
        state = self._load_state(bundle_path)

        current_item = state.get("current_item")
        if current_item:
            state["skipped"].append(current_item)

        # Move to next item
        sequence = manifest.get("sequence", [])
        current_index = state.get("current_index", 0) + 1

        if current_index < len(sequence):
            state["current_item"] = sequence[current_index]
            state["current_index"] = current_index
        else:
            state["current_item"] = None
            state["status"] = "completed"

        self._save_state(bundle_path, state)

        if state["current_item"]:
            return {
                "status": "success",
                "message": f"⏭️ Skipped. Next: {state['current_item']}",
            }
        else:
            return {"status": "success", "message": "📦 Bundle completed!"}

    def _handle_complete(self, params: list, grid=None) -> dict:
        """Mark current item as complete or complete entire bundle."""
        bundles = self._find_bundles(active_only=True)

        if not bundles:
            return {"status": "info", "message": "No active bundles."}

        bundle_info = bundles[0]
        bundle_path = self.root_path / bundle_info["path"]
        manifest = self._load_manifest(bundle_path)
        state = self._load_state(bundle_path)

        current_item = state.get("current_item")
        if current_item and current_item not in state["completed"]:
            state["completed"].append(current_item)
            state["completed_count"] = len(state["completed"])

        # Move to next item
        sequence = manifest.get("sequence", [])
        current_index = state.get("current_index", 0) + 1

        if current_index < len(sequence):
            state["current_item"] = sequence[current_index]
            state["current_index"] = current_index
            self._save_state(bundle_path, state)
            return {
                "status": "success",
                "message": f"✅ Completed: {current_item}\n\nNext: {state['current_item']}",
            }
        else:
            state["current_item"] = None
            state["status"] = "completed"
            state["completed_at"] = datetime.now().isoformat()
            self._save_state(bundle_path, state)
            return {
                "status": "success",
                "message": f"🎉 Bundle completed!\n\n"
                f"{manifest.get('title')}\n"
                f"Items: {state['completed_count']}/{len(sequence)}",
            }

    def _handle_review(self, params: list, grid=None) -> dict:
        """Check bundle for updates needed."""
        if not params:
            return {"status": "error", "message": "Usage: BUNDLE REVIEW <path>"}

        bundle_path = self._resolve_bundle_path(params[0])
        if not bundle_path:
            return {"status": "error", "message": f"Bundle not found: {params[0]}"}

        manifest = self._load_manifest(bundle_path)
        review = manifest.get("review", {})
        freshness_days = review.get("freshness_days", 90)

        issues = []
        sequence = manifest.get("sequence", [])

        for doc in sequence:
            doc_path = bundle_path / doc
            if not doc_path.exists():
                issues.append(f"❌ Missing: {doc}")
            else:
                mtime = datetime.fromtimestamp(doc_path.stat().st_mtime)
                age_days = (datetime.now() - mtime).days
                if age_days > freshness_days:
                    issues.append(f"⚠️ Stale ({age_days}d): {doc}")

        if issues:
            return {
                "status": "warning",
                "message": f"📋 Review needed for {manifest.get('title')}:\n\n"
                + "\n".join(issues),
            }
        else:
            return {
                "status": "success",
                "message": f"✅ Bundle is up to date: {manifest.get('title')}",
            }

    def _handle_plan(self, params: list, grid=None) -> dict:
        """Generate bundle outline using AI (Wizard only)."""
        if not params:
            return {"status": "error", "message": "Usage: BUNDLE PLAN <topic>"}

        topic = " ".join(params)

        # Check if Wizard is available
        # This would integrate with Gemini for planning
        return {
            "status": "info",
            "message": f"🧙 Bundle planning for '{topic}' requires Wizard Server.\n\n"
            f"Use: WIZARD BUNDLE PLAN {topic}",
        }

    def _handle_generate(self, params: list, grid=None) -> dict:
        """Generate bundle from plan (Wizard only)."""
        if not params:
            return {"status": "error", "message": "Usage: BUNDLE GENERATE <plan.json>"}

        return {
            "status": "info",
            "message": "🧙 Bundle generation requires Wizard Server.\n\n"
            "Use: WIZARD BUNDLE GENERATE <plan.json>",
        }

    def _handle_status(self, params: list, grid=None) -> dict:
        """Show status of all bundles."""
        all_bundles = self._find_bundles()
        active = [b for b in all_bundles if b["active"]]

        lines = [
            "📦 BUNDLE STATUS",
            "",
            f"Total bundles: {len(all_bundles)}",
            f"Active: {len(active)}",
            "",
        ]

        if active:
            lines.append("🔄 Active Bundles:")
            for bundle in active:
                state = bundle["state"]
                progress = f"{state.get('completed_count', 0)}/{bundle['documents']}"
                lines.append(f"  • {bundle['title']} [{progress}]")

        return {"status": "success", "message": "\n".join(lines)}

    def _resolve_bundle_path(self, path_str: str) -> Optional[Path]:
        """Resolve bundle path from user input."""
        # Try direct path
        direct = self.root_path / path_str
        if (direct / self.MANIFEST_FILENAME).exists():
            return direct

        # Try knowledge/ prefix
        knowledge = self.knowledge_path / path_str
        if (knowledge / self.MANIFEST_FILENAME).exists():
            return knowledge

        # Try searching by name
        for bundle in self._find_bundles():
            if path_str.lower() in bundle["path"].lower():
                return self.root_path / bundle["path"]
            if path_str.lower() in bundle["title"].lower():
                return self.root_path / bundle["path"]

        return None
