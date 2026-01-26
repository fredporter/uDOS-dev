"""
Teletext MODE - Experimental Renderer

Test retro teletext patterns, ANSI art, and 80x30 grid rendering
"""

import sys
from pathlib import Path

# Import from production Wizard service
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from wizard.services.teletext_patterns import TeletextPatternService, PatternName


class TeletextRenderer:
    """Experimental teletext pattern renderer"""
    
    def __init__(self, width: int = 80, ascii_only: bool = False):
        self.service = TeletextPatternService(width=width, ascii_only=ascii_only)
    
    def list_patterns(self):
        """List available patterns"""
        return [
            {"name": "chevrons", "description": "Animated chevron pattern"},
            {"name": "scanlines", "description": "Classic scanline effect"},
            {"name": "mosaic", "description": "Random mosaic tiles"},
            {"name": "c64", "description": "Commodore 64 raster bars"},
            {"name": "raster", "description": "Rainbow raster bars"},
            {"name": "loader", "description": "Progress loader animation"},
        ]
    
    def render(self, pattern: str, width: int = 80, ascii_only: bool = False):
        """Render single frame"""
        try:
            pattern_name = PatternName(pattern.lower())
            frame = self.service.next_frame(pattern_name, width=width, ascii_only=ascii_only)
            return {
                "pattern": pattern,
                "width": frame.width,
                "lines": frame.lines,
                "raw": "\n".join(frame.lines),
            }
        except ValueError:
            return {"error": f"Unknown pattern: {pattern}"}
    
    def animate(self, pattern: str, frames: int = 10, width: int = 80):
        """Generate animation frames"""
        try:
            pattern_name = PatternName(pattern.lower())
            animation = []
            for _ in range(frames):
                frame = self.service.next_frame(pattern_name, width=width)
                animation.append("\n".join(frame.lines))
            return {
                "pattern": pattern,
                "frames": frames,
                "animation": animation,
            }
        except ValueError:
            return {"error": f"Unknown pattern: {pattern}"}
