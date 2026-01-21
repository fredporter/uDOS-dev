"""
.udos.md Parser and Executor

Unified Markdown format with:
- YAML frontmatter (metadata)
- Markdown content
- Embedded uPY scripts (```upy blocks)
- JSON state blocks (```state blocks)
"""

from .parser import UDOSMarkdownParser, ParseError
from .executor import UDOSMarkdownExecutor, ExecutionError
from .document import UDOSDocument

__all__ = [
    "UDOSMarkdownParser",
    "ParseError",
    "UDOSMarkdownExecutor",
    "ExecutionError",
    "UDOSDocument",
]

__version__ = "0.1.0"
