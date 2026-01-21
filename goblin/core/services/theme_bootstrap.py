"""
Theme Bootstrap
===============

Initialize the active theme overlay from configuration.
Keeps debugging pure; only affects display layer via ThemeOverlay.
"""

from typing import Optional
from dev.goblin.core.config import Config
from dev.goblin.core.services.theme_overlay import set_active_theme, get_available_themes
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("theme-bootstrap")


def init_theme_from_config(config: Optional[Config] = None) -> str:
    """
    Initialize theme overlay based on configuration.

    Priority:
    1. .env `THEME_OVERLAY` (explicit overlay id)
    2. .env `THEME` (fallback; may be color theme but reused if matches overlay)
    3. default (no overlay)

    Returns:
    - Active theme id set (or 'default')
    """
    try:
        cfg = config or Config()
        overlay_id = cfg.get_env("THEME_OVERLAY", "")
        if not overlay_id:
            overlay_id = cfg.get_env("THEME", "")

        available = set(get_available_themes())

        if overlay_id and overlay_id in available:
            ok = set_active_theme(overlay_id)
            if ok:
                logger.info(f"[LOCAL] Theme overlay initialized: '{overlay_id}'")
                return overlay_id

        # Default overlay
        set_active_theme("default")
        logger.info("[LOCAL] Theme overlay disabled (default)")
        return "default"
    except Exception as e:
        logger.warning(f"[LOCAL] Theme bootstrap error: {e}")
        set_active_theme("default")
        return "default"
