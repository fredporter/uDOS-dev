"""
AI Prompt Loader Service

Loads and manages AI prompts from the core/data/prompts/ai/ directory.
Provides prompt templates for both TUI (Vibe CLI) and Tauri (Gemini) interfaces.

Part of uDOS Alpha v1.0.2.0+
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("service-prompts")


class PromptLoader:
    """
    Loads and manages AI prompts from markdown files.

    Prompts are stored as markdown files with YAML frontmatter:
    ---
    id: prompt-name
    provider: gemini|mistral|all
    version: 1.0.0
    tags: [tag1, tag2]
    ---

    # Prompt Title
    Content...
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize with optional custom prompts directory."""
        self.prompts_dir = prompts_dir or (
            PROJECT_ROOT / "core" / "data" / "prompts" / "ai"
        )
        self.user_prompts_dir = PROJECT_ROOT / "memory" / "prompts" / "ai"
        self._cache: Dict[str, dict] = {}
        self._load_all_prompts()

    def _load_all_prompts(self):
        """Load all prompts from both system and user directories."""
        # Load system prompts first
        if self.prompts_dir.exists():
            for prompt_file in self.prompts_dir.glob("*.md"):
                self._load_prompt_file(prompt_file, source="system")

        # Load user prompts (can override system)
        if self.user_prompts_dir.exists():
            for prompt_file in self.user_prompts_dir.glob("*.md"):
                self._load_prompt_file(prompt_file, source="user")

        logger.info(f"[LOCAL] Loaded {len(self._cache)} AI prompts")

    def _load_prompt_file(self, file_path: Path, source: str = "system"):
        """Load a single prompt file."""
        try:
            content = file_path.read_text()
            prompt_data = self._parse_prompt(content)

            if prompt_data:
                prompt_id = prompt_data.get("id", file_path.stem)
                prompt_data["source"] = source
                prompt_data["file_path"] = str(file_path)
                self._cache[prompt_id] = prompt_data
                logger.debug(f"[LOCAL] Loaded prompt: {prompt_id} from {source}")
        except Exception as e:
            logger.warning(f"[LOCAL] Failed to load prompt {file_path}: {e}")

    def _parse_prompt(self, content: str) -> Optional[dict]:
        """Parse markdown content with YAML frontmatter."""
        if not content.startswith("---"):
            return {"body": content, "frontmatter": {}}

        try:
            parts = content.split("---", 2)
            if len(parts) < 3:
                return {"body": content, "frontmatter": {}}

            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()

            return {**frontmatter, "body": body, "frontmatter": frontmatter}
        except yaml.YAMLError as e:
            logger.warning(f"[LOCAL] YAML parse error: {e}")
            return {"body": content, "frontmatter": {}}

    def get_prompt(self, prompt_id: str) -> Optional[dict]:
        """Get a prompt by ID."""
        return self._cache.get(prompt_id)

    def get_prompt_body(self, prompt_id: str) -> str:
        """Get just the body text of a prompt."""
        prompt = self.get_prompt(prompt_id)
        return prompt.get("body", "") if prompt else ""

    def list_prompts(
        self, provider: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[dict]:
        """List available prompts, optionally filtered by provider or tags."""
        prompts = []

        for prompt_id, prompt_data in self._cache.items():
            # Filter by provider
            if provider and prompt_data.get("provider") not in [provider, "all"]:
                continue

            # Filter by tags
            if tags:
                prompt_tags = prompt_data.get("tags", [])
                if not any(tag in prompt_tags for tag in tags):
                    continue

            prompts.append(
                {
                    "id": prompt_id,
                    "provider": prompt_data.get("provider", "all"),
                    "version": prompt_data.get("version", "1.0.0"),
                    "tags": prompt_data.get("tags", []),
                    "source": prompt_data.get("source", "system"),
                }
            )

        return prompts

    def get_system_prompt(self, prompt_id: str, section: str = "System Prompt") -> str:
        """Extract a specific section (like System Prompt) from a prompt."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return ""

        body = prompt.get("body", "")

        # Look for the section header
        lines = body.split("\n")
        in_section = False
        section_lines = []
        in_code_block = False

        for line in lines:
            # Check for section header
            if line.strip().startswith("##") and section.lower() in line.lower():
                in_section = True
                continue

            # Stop at next section
            if in_section and line.strip().startswith("##"):
                break

            if in_section:
                # Handle code blocks
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    if not in_code_block:  # End of code block
                        break
                    continue

                if in_code_block:
                    section_lines.append(line)

        return "\n".join(section_lines).strip()

    def reload(self):
        """Reload all prompts from disk."""
        self._cache.clear()
        self._load_all_prompts()


# Singleton instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance."""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def get_prompt(prompt_id: str) -> Optional[dict]:
    """Convenience function to get a prompt."""
    return get_prompt_loader().get_prompt(prompt_id)


def list_prompts(provider: Optional[str] = None) -> List[dict]:
    """Convenience function to list prompts."""
    return get_prompt_loader().list_prompts(provider=provider)


# Test entry point
if __name__ == "__main__":
    loader = PromptLoader()

    print("=== Available Prompts ===")
    for prompt in loader.list_prompts():
        print(f"  - {prompt['id']} ({prompt['provider']}) [{prompt['source']}]")

    print("\n=== Mistral Prompts ===")
    for prompt in loader.list_prompts(provider="mistral"):
        print(f"  - {prompt['id']}")

    print("\n=== Gemini Prompts ===")
    for prompt in loader.list_prompts(provider="gemini"):
        print(f"  - {prompt['id']}")

    # Test getting a system prompt
    print("\n=== OK FIX Primary Prompt ===")
    system_prompt = loader.get_system_prompt("okfix", "Primary Code Fix Prompt")
    print(system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt)
