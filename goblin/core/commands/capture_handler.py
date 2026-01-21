"""
uDOS CAPTURE Handler - Web Content Capture Pipeline

Captures external content and converts to .udos.md format.

Commands:
- CAPTURE <url>                 Capture URL to inbox
- CAPTURE <url> --to <bundle>   Capture to specific bundle
- CAPTURE <url> --type <type>   Use specific pipeline (news, docs, recipe)
- CAPTURE LINKS <page_url>      Extract and queue all links
- CAPTURE LIST                  Show capture queue
- CAPTURE PROCESS               Process pending captures
- CAPTURE CLEAR                 Clear completed queue

Version: 1.0.0
Created: 2026-01-07
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from dev.goblin.core.commands.base_handler import BaseCommandHandler
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("command-capture")


# Pipeline configurations
PIPELINE_TYPES = {
    "markdown": {
        "name": "Clean Markdown",
        "description": "Standard content extraction",
        "extractors": ["readability", "html2text"],
    },
    "news": {
        "name": "News Article",
        "description": "Optimized for news sites",
        "extractors": ["readability", "date_extractor", "author_extractor"],
    },
    "docs": {
        "name": "Documentation",
        "description": "Technical documentation",
        "extractors": ["readability", "code_block_preserver"],
    },
    "recipe": {
        "name": "Recipe Extraction",
        "description": "Recipe schema extraction",
        "extractors": ["json_ld", "schema_org"],
    },
    "teletext": {
        "name": "Teletext Format",
        "description": "40-column text conversion",
        "extractors": ["teletext_converter"],
    },
}


class CaptureHandler(BaseCommandHandler):
    """Handler for CAPTURE web content commands."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_path = Path(__file__).parent.parent.parent
        self.inbox_path = self.root_path / "memory" / "inbox"
        self.queue_file = self.inbox_path / "pending" / "urls.txt"
        self.state_file = self.inbox_path / ".capture.json"

        # Ensure directories exist
        (self.inbox_path / "pending").mkdir(parents=True, exist_ok=True)
        (self.inbox_path / "processing").mkdir(parents=True, exist_ok=True)
        (self.inbox_path / "completed").mkdir(parents=True, exist_ok=True)
        (self.inbox_path / "failed").mkdir(parents=True, exist_ok=True)

    def handle(self, command: str, params: list, grid=None, parser=None) -> dict:
        """Route CAPTURE commands to appropriate handlers."""

        if not params:
            return self._handle_status([], grid)

        subcommand = params[0].upper()
        sub_params = params[1:] if len(params) > 1 else []

        # Check for subcommands
        handlers = {
            "LIST": self._handle_list,
            "PROCESS": self._handle_process,
            "CLEAR": self._handle_clear,
            "LINKS": self._handle_links,
            "STATUS": self._handle_status,
            "QUEUE": self._handle_queue,
        }

        handler = handlers.get(subcommand)
        if handler:
            return handler(sub_params, grid)

        # Assume first param is URL
        return self._handle_capture(params, grid)

    def _handle_capture(self, params: list, grid=None) -> dict:
        """Capture a URL to inbox or bundle."""
        if not params:
            return {
                "status": "error",
                "message": "Usage: CAPTURE <url> [--to <bundle>] [--type <pipeline>]",
            }

        url = params[0]

        # Parse options
        target_bundle = None
        pipeline_type = "markdown"

        i = 1
        while i < len(params):
            if params[i] == "--to" and i + 1 < len(params):
                target_bundle = params[i + 1]
                i += 2
            elif params[i] == "--type" and i + 1 < len(params):
                pipeline_type = params[i + 1].lower()
                i += 2
            else:
                i += 1

        # Validate URL
        if not self._is_valid_url(url):
            return {"status": "error", "message": f"Invalid URL: {url}"}

        # Validate pipeline type
        if pipeline_type not in PIPELINE_TYPES:
            return {
                "status": "error",
                "message": f"Unknown pipeline: {pipeline_type}\n"
                f"Available: {', '.join(PIPELINE_TYPES.keys())}",
            }

        # Add to queue
        queue_entry = {
            "url": url,
            "pipeline": pipeline_type,
            "target_bundle": target_bundle,
            "queued_at": datetime.now().isoformat(),
            "status": "pending",
        }

        self._add_to_queue(queue_entry)

        logger.info(f"[LOCAL] Queued capture: {url} (pipeline: {pipeline_type})")

        pipeline_info = PIPELINE_TYPES[pipeline_type]
        return {
            "status": "success",
            "message": f"📥 Queued for capture:\n\n"
            f"URL: {url}\n"
            f"Pipeline: {pipeline_info['name']}\n"
            f"Target: {target_bundle or 'memory/inbox/'}\n\n"
            f"Run CAPTURE PROCESS to process queue.",
        }

    def _handle_list(self, params: list, grid=None) -> dict:
        """List capture queue."""
        state = self._load_state()
        queue = state.get("queue", [])

        if not queue:
            return {"status": "info", "message": "📭 Capture queue is empty."}

        lines = ["📥 CAPTURE QUEUE", ""]

        for i, entry in enumerate(queue, 1):
            status_icon = {
                "pending": "⏳",
                "processing": "🔄",
                "completed": "✅",
                "failed": "❌",
            }.get(entry.get("status", "pending"), "❓")

            domain = urlparse(entry["url"]).netloc
            pipeline = entry.get("pipeline", "markdown")

            lines.append(f"{status_icon} {i}. {domain}")
            lines.append(f"   URL: {entry['url'][:60]}...")
            lines.append(f"   Pipeline: {pipeline}")
            lines.append("")

        pending_count = len([e for e in queue if e.get("status") == "pending"])
        lines.append(f"Pending: {pending_count} | Total: {len(queue)}")

        return {
            "status": "success",
            "message": "\n".join(lines),
            "data": {"queue": queue},
        }

    def _handle_process(self, params: list, grid=None) -> dict:
        """Process pending captures."""
        state = self._load_state()
        queue = state.get("queue", [])

        pending = [e for e in queue if e.get("status") == "pending"]

        if not pending:
            return {"status": "info", "message": "📭 No pending captures."}

        # Check for limit
        limit = None
        if "--limit" in params:
            idx = params.index("--limit")
            if idx + 1 < len(params):
                try:
                    limit = int(params[idx + 1])
                except ValueError:
                    pass

        to_process = pending[:limit] if limit else pending
        results = []

        for entry in to_process:
            result = self._process_url(entry)
            results.append(result)

            # Update entry status
            entry["status"] = "completed" if result["success"] else "failed"
            entry["processed_at"] = datetime.now().isoformat()
            if result.get("output_file"):
                entry["output_file"] = result["output_file"]
            if result.get("error"):
                entry["error"] = result["error"]

        self._save_state(state)

        successful = len([r for r in results if r["success"]])
        failed = len(results) - successful

        lines = [
            "📥 CAPTURE RESULTS",
            "",
            f"Processed: {len(results)}",
            f"✅ Success: {successful}",
            f"❌ Failed: {failed}",
            "",
        ]

        for result in results:
            icon = "✅" if result["success"] else "❌"
            lines.append(f"{icon} {result['url'][:50]}...")
            if result.get("output_file"):
                lines.append(f"   → {result['output_file']}")
            if result.get("error"):
                lines.append(f"   Error: {result['error']}")

        return {"status": "success", "message": "\n".join(lines)}

    def _process_url(self, entry: dict) -> dict:
        """Process a single URL capture."""
        url = entry["url"]
        pipeline = entry.get("pipeline", "markdown")
        target_bundle = entry.get("target_bundle")

        try:
            # Try to use wizard web pipeline if available
            try:
                from wizard.web.pipeline import WebPipeline

                pipeline_obj = WebPipeline(pipeline)
                content = pipeline_obj.fetch_and_convert(url)
            except ImportError:
                # Fall back to basic fetch
                content = self._basic_fetch(url)

            # Generate output filename
            domain = urlparse(url).netloc.replace(".", "-")
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{domain}-{timestamp}.udos.md"

            # Determine output path
            if target_bundle:
                output_dir = self.root_path / target_bundle
            else:
                output_dir = self.inbox_path / "completed"

            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / filename

            # Add metadata
            metadata = f"""---
title: {self._extract_title(content)}
source:
  url: {url}
  captured: {datetime.now().isoformat()}
  pipeline: {pipeline}
type: web-capture
tags: [auto-captured]
status: needs-review
---

"""
            output_file.write_text(metadata + content)

            logger.info(f"[LOCAL] Captured: {url} → {output_file}")

            return {
                "success": True,
                "url": url,
                "output_file": str(output_file.relative_to(self.root_path)),
            }

        except Exception as e:
            logger.error(f"[LOCAL] Capture failed: {url} - {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e),
            }

    def _basic_fetch(self, url: str) -> str:
        """Basic URL fetch without wizard pipeline."""
        try:
            import urllib.request

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) uDOS/1.0"
            }
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode("utf-8", errors="ignore")

            # Basic HTML to text conversion
            # Remove script and style tags
            html = re.sub(
                r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
            )
            html = re.sub(
                r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
            )

            # Remove HTML tags
            text = re.sub(r"<[^>]+>", "\n", html)

            # Clean up whitespace
            text = re.sub(r"\n\s*\n", "\n\n", text)
            text = text.strip()

            return text

        except Exception as e:
            raise Exception(f"Fetch failed: {e}")

    def _extract_title(self, content: str) -> str:
        """Extract title from content."""
        # Look for first heading
        lines = content.split("\n")
        for line in lines[:20]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line and len(line) > 10 and len(line) < 200:
                return line
        return "Captured Content"

    def _handle_links(self, params: list, grid=None) -> dict:
        """Extract and queue links from a page."""
        if not params:
            return {"status": "error", "message": "Usage: CAPTURE LINKS <page_url>"}

        url = params[0]

        if not self._is_valid_url(url):
            return {"status": "error", "message": f"Invalid URL: {url}"}

        try:
            # Fetch page
            import urllib.request

            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 uDOS/1.0"}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode("utf-8", errors="ignore")

            # Extract links
            links = re.findall(r'href=["\']([^"\']+)["\']', html)

            # Filter to absolute URLs on same domain
            base_domain = urlparse(url).netloc
            valid_links = []

            for link in links:
                if link.startswith("http"):
                    link_domain = urlparse(link).netloc
                    if link_domain == base_domain and link not in valid_links:
                        valid_links.append(link)

            # Add to queue
            for link in valid_links[:50]:  # Limit to 50 links
                self._add_to_queue(
                    {
                        "url": link,
                        "pipeline": "markdown",
                        "queued_at": datetime.now().isoformat(),
                        "status": "pending",
                        "source_page": url,
                    }
                )

            logger.info(f"[LOCAL] Extracted {len(valid_links)} links from {url}")

            return {
                "status": "success",
                "message": f"🔗 Extracted {len(valid_links)} links from {base_domain}\n\n"
                f"Queued for capture. Run CAPTURE PROCESS to start.",
                "data": {"links": valid_links[:10]},  # Return first 10
            }

        except Exception as e:
            return {"status": "error", "message": f"Failed to extract links: {e}"}

    def _handle_clear(self, params: list, grid=None) -> dict:
        """Clear completed/failed items from queue."""
        state = self._load_state()
        queue = state.get("queue", [])

        original_count = len(queue)

        # Keep only pending items
        state["queue"] = [e for e in queue if e.get("status") == "pending"]

        removed = original_count - len(state["queue"])
        self._save_state(state)

        return {
            "status": "success",
            "message": f"🧹 Cleared {removed} completed/failed items from queue.",
        }

    def _handle_status(self, params: list, grid=None) -> dict:
        """Show capture system status."""
        state = self._load_state()
        queue = state.get("queue", [])

        pending = len([e for e in queue if e.get("status") == "pending"])
        processing = len([e for e in queue if e.get("status") == "processing"])
        completed = len([e for e in queue if e.get("status") == "completed"])
        failed = len([e for e in queue if e.get("status") == "failed"])

        # Count files in inbox
        inbox_files = list((self.inbox_path / "completed").glob("*.md"))

        lines = [
            "📥 CAPTURE STATUS",
            "",
            f"Queue: {len(queue)} items",
            f"  ⏳ Pending: {pending}",
            f"  🔄 Processing: {processing}",
            f"  ✅ Completed: {completed}",
            f"  ❌ Failed: {failed}",
            "",
            f"Inbox files: {len(inbox_files)}",
            "",
            "Available pipelines:",
        ]

        for key, info in PIPELINE_TYPES.items():
            lines.append(f"  • {key}: {info['description']}")

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_queue(self, params: list, grid=None) -> dict:
        """Add URL directly to queue (alias for CAPTURE <url>)."""
        return self._handle_capture(params, grid)

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme in ["http", "https"], result.netloc])
        except:
            return False

    def _load_state(self) -> dict:
        """Load capture state."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {"queue": [], "stats": {}}

    def _save_state(self, state: dict) -> None:
        """Save capture state."""
        state["updated"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(state, indent=2))

    def _add_to_queue(self, entry: dict) -> None:
        """Add entry to capture queue."""
        state = self._load_state()

        # Check for duplicate URL
        existing_urls = [e["url"] for e in state.get("queue", [])]
        if entry["url"] not in existing_urls:
            state.setdefault("queue", []).append(entry)
            self._save_state(state)
