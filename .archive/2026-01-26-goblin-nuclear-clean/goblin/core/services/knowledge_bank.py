"""
Knowledge Bank Service - AI Instruction Management
===================================================

Loads, validates, and executes AI instructions from the Knowledge Bank.
Enables offline replication of perfected AI tasks.

Usage:
    from dev.goblin.core.services.knowledge_bank import KnowledgeBank

    kb = KnowledgeBank()

    # List instructions
    instructions = kb.list_instructions("coding")

    # Load instruction
    instruction = kb.get_instruction("fix-python-errors")

    # Render with variables
    prompt = kb.render_instruction("fix-python-errors", {"code": "..."})
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("knowledge-bank")

# Knowledge Bank paths
KB_SYSTEM_PATH = Path(__file__).parent.parent.parent / "knowledge" / "ai"
KB_USER_PATH = Path(__file__).parent.parent.parent / "memory" / "knowledge" / "ai"


@dataclass
class Instruction:
    """Loaded AI instruction."""

    id: str
    title: str
    purpose: str
    category: str
    prompt: str
    system_prompt: Optional[str] = None
    variables: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    version: str = "1.0.0"
    created: str = ""
    author: str = ""
    source_provider: str = ""
    quality_score: float = 0.0
    tags: List[str] = field(default_factory=list)

    # Execution config
    offline_capable: bool = True
    recommended_model: str = ""
    fallback_models: List[str] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 2048

    # Source path
    _source_path: Optional[Path] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], source_path: Optional[Path] = None
    ) -> "Instruction":
        """Create Instruction from JSON data."""
        # Handle both old and new schema formats
        if "instruction" in data:
            # New schema format
            inst = data.get("instruction", {})
            meta = data.get("metadata", {})
            exec_config = data.get("execution", {})
        else:
            # Old flat format (backward compatibility)
            inst = data
            meta = data
            exec_config = data

        return cls(
            id=inst.get("id", ""),
            title=inst.get("title", ""),
            purpose=inst.get("purpose", ""),
            category=inst.get("category", ""),
            prompt=inst.get("prompt", ""),
            system_prompt=inst.get("system_prompt"),
            variables=inst.get("variables", []),
            examples=inst.get("examples", []),
            version=meta.get("version", "1.0.0"),
            created=meta.get("created", ""),
            author=meta.get("author", ""),
            source_provider=meta.get("source_provider", ""),
            quality_score=meta.get("quality_score", 0.0),
            tags=meta.get("tags", []),
            offline_capable=exec_config.get("offline_capable", True),
            recommended_model=exec_config.get("recommended_model", ""),
            fallback_models=exec_config.get("fallback_models", []),
            temperature=exec_config.get("temperature", 0.7),
            max_tokens=exec_config.get("max_tokens", 2048),
            _source_path=source_path,
        )

    def render(self, variables: Dict[str, str]) -> str:
        """Render prompt with variables."""
        rendered = self.prompt
        for var in self.variables:
            name = var["name"]
            placeholder = f"{{{{{name}}}}}"
            if name in variables:
                rendered = rendered.replace(placeholder, variables[name])
            elif var.get("default"):
                rendered = rendered.replace(placeholder, var["default"])
            elif var.get("required", True):
                raise ValueError(f"Missing required variable: {name}")
        return rendered


class KnowledgeBank:
    """
    Knowledge Bank for AI instructions.

    Manages perfected instructions that can be executed
    offline with local models.
    """

    CATEGORIES = [
        "coding",
        "writing",
        "image",
        "workflow",
        "analysis",
        "creative",
        "system",
    ]

    def __init__(self):
        """Initialize Knowledge Bank."""
        self.system_path = KB_SYSTEM_PATH
        self.user_path = KB_USER_PATH

        # Ensure directories exist
        self.system_path.mkdir(parents=True, exist_ok=True)
        self.user_path.mkdir(parents=True, exist_ok=True)

        # Cache loaded instructions
        self._cache: Dict[str, Instruction] = {}

        logger.info(f"[LOCAL] Knowledge Bank initialized: {self.system_path}")

    def list_categories(self) -> List[str]:
        """List available categories."""
        categories = []
        for cat in self.CATEGORIES:
            sys_path = self.system_path / cat
            user_path = self.user_path / cat
            if sys_path.exists() or user_path.exists():
                categories.append(cat)
        return categories

    def list_instructions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available instructions.

        Args:
            category: Filter by category (optional)

        Returns:
            List of instruction summaries
        """
        instructions = []

        # Determine paths to search
        if category:
            search_paths = [
                (self.system_path / category, "system"),
                (self.user_path / category, "user"),
            ]
        else:
            search_paths = []
            for cat in self.CATEGORIES:
                search_paths.append((self.system_path / cat, "system"))
                search_paths.append((self.user_path / cat, "user"))

        seen_ids = set()

        for path, source in search_paths:
            if not path.exists():
                continue

            for json_file in path.glob("*.json"):
                if json_file.name == "instruction.schema.json":
                    continue

                try:
                    data = json.loads(json_file.read_text())
                    inst = data.get("instruction", {})
                    meta = data.get("metadata", {})

                    inst_id = inst.get("id", json_file.stem)

                    # User instructions override system
                    if inst_id in seen_ids and source == "system":
                        continue

                    seen_ids.add(inst_id)

                    instructions.append(
                        {
                            "id": inst_id,
                            "title": inst.get("title", ""),
                            "purpose": inst.get("purpose", ""),
                            "category": inst.get("category", path.name),
                            "version": meta.get("version", ""),
                            "quality_score": meta.get("quality_score", 0),
                            "source": source,
                            "tags": meta.get("tags", []),
                        }
                    )
                except Exception as e:
                    logger.warning(f"[LOCAL] Failed to load {json_file}: {e}")

        # Sort by quality score descending
        instructions.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        return instructions

    def get_instruction(self, instruction_id: str) -> Optional[Instruction]:
        """
        Get instruction by ID.

        Args:
            instruction_id: Instruction identifier

        Returns:
            Instruction object or None
        """
        # Check cache
        if instruction_id in self._cache:
            return self._cache[instruction_id]

        # Search for instruction file
        for cat in self.CATEGORIES:
            # User path takes precedence
            for base_path in [self.user_path, self.system_path]:
                json_file = base_path / cat / f"{instruction_id}.json"
                if json_file.exists():
                    try:
                        data = json.loads(json_file.read_text())
                        instruction = Instruction.from_dict(data, json_file)
                        self._cache[instruction_id] = instruction
                        return instruction
                    except Exception as e:
                        logger.error(f"[LOCAL] Failed to load {json_file}: {e}")
                        return None

        return None

    def render_instruction(
        self, instruction_id: str, variables: Dict[str, str]
    ) -> Optional[str]:
        """
        Render instruction prompt with variables.

        Args:
            instruction_id: Instruction identifier
            variables: Variable values to substitute

        Returns:
            Rendered prompt or None
        """
        instruction = self.get_instruction(instruction_id)
        if not instruction:
            return None

        try:
            return instruction.render(variables)
        except ValueError as e:
            logger.error(f"[LOCAL] Failed to render {instruction_id}: {e}")
            return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search instructions by query.

        Args:
            query: Search string

        Returns:
            Matching instructions
        """
        query_lower = query.lower()
        results = []

        for inst in self.list_instructions():
            # Search in title, purpose, tags
            if (
                query_lower in inst["title"].lower()
                or query_lower in inst["purpose"].lower()
                or any(query_lower in tag.lower() for tag in inst.get("tags", []))
            ):
                results.append(inst)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get Knowledge Bank statistics."""
        all_instructions = self.list_instructions()

        by_category = {}
        by_quality = {"high": 0, "medium": 0, "low": 0}

        for inst in all_instructions:
            cat = inst.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1

            score = inst.get("quality_score", 0)
            if score >= 8:
                by_quality["high"] += 1
            elif score >= 5:
                by_quality["medium"] += 1
            else:
                by_quality["low"] += 1

        return {
            "total": len(all_instructions),
            "by_category": by_category,
            "by_quality": by_quality,
            "categories_available": list(by_category.keys()),
        }

    def reload(self):
        """Clear cache and reload instructions."""
        self._cache.clear()
        logger.info("[LOCAL] Knowledge Bank cache cleared")


# Singleton instance
_kb_instance: Optional[KnowledgeBank] = None


def get_knowledge_bank() -> KnowledgeBank:
    """Get Knowledge Bank singleton."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBank()
    return _kb_instance
