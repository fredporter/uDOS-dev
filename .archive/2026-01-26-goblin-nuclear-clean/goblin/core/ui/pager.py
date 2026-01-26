"""
Compatibility shim for old pager imports (v1.2.30)

Redirects to unified pager at core/utils/pager.py
Keep this file for backwards compatibility.

DEPRECATED: Use `from dev.goblin.core.utils.pager import ...` instead
"""

# Re-export all from unified pager
from dev.goblin.core.utils.pager import (
    UnifiedPager,
    UnifiedPager as Pager,        # Alias
    UnifiedPager as EnhancedPager,  # Legacy alias
    PagerState,
    ScrollDirection,
    page_output,
    page_lines,
)

__all__ = [
    'Pager',
    'EnhancedPager', 
    'UnifiedPager',
    'PagerState',
    'ScrollDirection',
    'page_output',
    'page_lines',
]
