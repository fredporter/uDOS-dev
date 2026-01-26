"""
uDOS Knowledge Package - Consolidated Knowledge Management
Handles markdown indexing, 4-tier memory system, and file picking

Consolidates:
- base_manager.py (v1.0.8 - markdown indexing, FTS search)
- service.py (v1.0.18 - XP integration, skill unlocks)
- tier_manager.py (v1.0.20 - 4-tier privacy system)
- types.py (v1.0.20 - data structures, enums)
- file_picker.py (v1.0.30 - StandardizedInput integration)
- bank.py (unified knowledge bank interface)
- memory.py (memory tier system)

Version: 1.1.0
"""

# Core knowledge types and enums
from .types import (
    KnowledgeTier,
    KnowledgeType,
    KnowledgeItem,
    PrivacySettings,
    KnowledgeTransaction,
    TIER_DESCRIPTIONS,
)

# Knowledge managers
from .bank import KnowledgeManager, get_knowledge_manager
from .base_manager import KnowledgeManager as BaseKnowledgeManager
from .tier_manager import TierKnowledgeManager
from .service import KnowledgeService

# Memory and file picking
from .memory import MemoryManager, MemoryTier
from .file_picker import KnowledgeFilePicker

__all__ = [
    # Types
    "KnowledgeTier",
    "KnowledgeType",
    "KnowledgeItem",
    "PrivacySettings",
    "KnowledgeTransaction",
    "TIER_DESCRIPTIONS",
    # Managers
    "KnowledgeManager",
    "get_knowledge_manager",
    "BaseKnowledgeManager",
    "TierKnowledgeManager",
    "KnowledgeService",
    # Memory & Pickers
    "MemoryManager",
    "MemoryTier",
    "KnowledgeFilePicker",
]

import json
from pathlib import Path


def _get_knowledge_version():
    """Get version from knowledge/version.json."""
    # knowledge module is at core/knowledge/, version.json is at knowledge/
    version_file = Path(__file__).parent.parent.parent / "knowledge" / "version.json"
    if version_file.exists():
        with open(version_file, "r") as f:
            return json.load(f).get("version", "1.0.0.0")
    return "1.0.0.0"


__version__ = _get_knowledge_version()
