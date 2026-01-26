"""
MODE Routes - Experimental MODE API Endpoints

All endpoints prefixed with /api/v0/modes/*
"""

from fastapi import APIRouter, Query

from modes.teletext_mode import TeletextRenderer
from modes.terminal_mode import TerminalRenderer

router = APIRouter()

# Initialize renderers
teletext = TeletextRenderer()
terminal = TerminalRenderer()


# ============================================================================
# TELETEXT MODE
# ============================================================================

@router.get("/teletext/patterns")
async def list_teletext_patterns():
    """List available Teletext patterns"""
    return {"patterns": teletext.list_patterns()}


@router.get("/teletext/render")
async def render_teletext(
    pattern: str = Query("chevrons", description="Pattern name"),
    width: int = Query(80, ge=20, le=80, description="Width in characters"),
    ascii_only: bool = Query(False, description="ASCII-only output"),
):
    """Render single Teletext frame"""
    return teletext.render(pattern, width, ascii_only)


@router.get("/teletext/animate")
async def animate_teletext(
    pattern: str = Query("raster", description="Pattern name"),
    frames: int = Query(10, ge=1, le=30, description="Number of frames"),
    width: int = Query(80, ge=20, le=80, description="Width in characters"),
):
    """Generate Teletext animation frames"""
    return teletext.animate(pattern, frames, width)


# ============================================================================
# TERMINAL MODE
# ============================================================================

@router.get("/terminal/schemes")
async def list_terminal_schemes():
    """List available Terminal color schemes"""
    return {"schemes": terminal.list_schemes()}


@router.get("/terminal/render")
async def render_terminal(
    text: str = Query("Sample text", description="Text to render"),
    fg: str = Query("white", description="Foreground color"),
    bg: str = Query(None, description="Background color"),
    style: str = Query(None, description="Text style"),
):
    """Render text with ANSI codes"""
    return terminal.render(text, fg, bg, style)


@router.get("/terminal/test")
async def test_terminal():
    """Test terminal capabilities"""
    return terminal.test_capabilities()


@router.get("/terminal/scheme")
async def apply_terminal_scheme(
    text: str = Query("Sample text", description="Text to render"),
    scheme: str = Query("default", description="Color scheme"),
):
    """Apply color scheme to text"""
    return terminal.apply_scheme(text, scheme)


# ============================================================================
# MODE INFO
# ============================================================================

@router.get("/")
async def list_modes():
    """List all available MODEs"""
    return {
        "modes": [
            {
                "name": "teletext",
                "description": "Retro teletext patterns and ANSI art",
                "endpoints": [
                    "/api/v0/modes/teletext/patterns",
                    "/api/v0/modes/teletext/render",
                    "/api/v0/modes/teletext/animate",
                ],
            },
            {
                "name": "terminal",
                "description": "Terminal emulation and ANSI escape codes",
                "endpoints": [
                    "/api/v0/modes/terminal/schemes",
                    "/api/v0/modes/terminal/render",
                    "/api/v0/modes/terminal/test",
                    "/api/v0/modes/terminal/scheme",
                ],
            },
        ]
    }
