"""
Layer Theme Bridge
==================

Maps the existing map layer system (100-899) to themed templates.

Layer Ranges in uDOS:
- EARTH Realm (L100-399): Surface, caves, atmosphere
- VIRTUAL Realm (L400-699): Game worlds (NetHack dungeon, etc.)
- SPACE Realm (L700-899): Solar system, galactic

Template Layer Themes:
- Surface (Earth surface, layer 100)
- Dungeon (NetHack L401-455, fantasy RPG)
- Upside Down (Deep virtual L500+, horror)
- Space Humor (Solar system L700-749, Hitchhiker's)
- Space Serious (Galactic L750-899, Foundation)

This module bridges the two systems.

Version: 1.0.0
Alpha: v1.0.0.62+
"""

from typing import Optional, Tuple
from dataclasses import dataclass

from dev.goblin.core.services.template_loader import (
    LayerTheme,
    get_template_loader,
    TemplateData,
)


# Map existing layer ranges to themes
LAYER_TO_THEME = {
    # Earth Realm
    (100, 199): LayerTheme.SURFACE,  # Earth surface
    (200, 299): LayerTheme.DUNGEON,  # Caves/underwater (dungeon-like)
    (300, 399): LayerTheme.SURFACE,  # Sky/atmosphere
    # Virtual Realm
    (400, 450): LayerTheme.DUNGEON,  # NetHack dungeon (L401-455)
    (451, 499): LayerTheme.DUNGEON,  # Other fantasy games
    (500, 599): LayerTheme.UPSIDE_DOWN,  # Deep virtual/horror zones
    (600, 699): LayerTheme.UPSIDE_DOWN,  # Extended virtual nightmares
    # Space Realm
    (700, 749): LayerTheme.SPACE_HUMOR,  # Solar system (local, familiar)
    (750, 799): LayerTheme.SPACE_SERIOUS,  # Galactic (vast, serious)
    (800, 899): LayerTheme.SPACE_SERIOUS,  # Intergalactic
}


def get_theme_for_layer_number(layer_number: int) -> LayerTheme:
    """
    Get theme for an existing map layer number.

    Args:
        layer_number: uDOS map layer (100-899)

    Returns:
        Appropriate LayerTheme
    """
    for (low, high), theme in LAYER_TO_THEME.items():
        if low <= layer_number <= high:
            return theme

    # Default to surface for unknown layers
    return LayerTheme.SURFACE


def get_template_for_map_layer(layer_number: int) -> TemplateData:
    """
    Get the appropriate template for a map layer.

    Args:
        layer_number: uDOS map layer (100-899)

    Returns:
        TemplateData for the layer
    """
    theme = get_theme_for_layer_number(layer_number)
    loader = get_template_loader()
    return loader.get_layer_template(theme)


@dataclass
class LayerContext:
    """Context information for a layer with theming."""

    layer_number: int
    theme: LayerTheme
    realm: str
    template: TemplateData

    @property
    def realm_name(self) -> str:
        """Get human-readable realm name."""
        realms = {
            "EARTH": "Earth",
            "VIRTUAL": "Virtual World",
            "SPACE": "Deep Space",
        }
        return realms.get(self.realm, self.realm)

    @property
    def theme_description(self) -> str:
        """Get theme description."""
        descriptions = {
            LayerTheme.SURFACE: "The familiar world above ground",
            LayerTheme.DUNGEON: "Dark passages and ancient secrets",
            LayerTheme.UPSIDE_DOWN: "Where reality inverts and nightmares roam",
            LayerTheme.SPACE_HUMOR: "The improbable cosmos, mostly harmless",
            LayerTheme.SPACE_SERIOUS: "The vast archives of galactic civilization",
        }
        return descriptions.get(self.theme, "Unknown dimension")


def get_layer_context(layer_number: int, realm: str = "EARTH") -> LayerContext:
    """
    Get full context for a layer including theme and template.

    Args:
        layer_number: uDOS map layer (100-899)
        realm: Realm code ("EARTH", "VIRTUAL", "SPACE")

    Returns:
        LayerContext with all theming information
    """
    # Infer realm from layer number if not provided
    if layer_number < 400:
        realm = "EARTH"
    elif layer_number < 700:
        realm = "VIRTUAL"
    else:
        realm = "SPACE"

    theme = get_theme_for_layer_number(layer_number)
    template = get_template_for_map_layer(layer_number)

    return LayerContext(
        layer_number=layer_number,
        theme=theme,
        realm=realm,
        template=template,
    )


def format_layer_welcome(layer_number: int, realm: str = "EARTH") -> str:
    """
    Generate a themed welcome message when entering a layer.

    Args:
        layer_number: Layer being entered
        realm: Realm code

    Returns:
        Themed welcome string
    """
    context = get_layer_context(layer_number, realm)
    template = context.template

    # Try to get welcome message from template
    if hasattr(template, "messages") and "info" in template.messages:
        welcome_template = template.messages.get("info", {}).get("INFO_WELCOME", "")
        if welcome_template:
            return welcome_template.replace("{{layer}}", str(layer_number))

    # Fallback themed messages
    if context.theme == LayerTheme.SURFACE:
        return f"""🌍 Entering Earth Layer {layer_number}
   Realm: {context.realm_name}
   Status: Normal conditions"""

    elif context.theme == LayerTheme.DUNGEON:
        return f"""⚔️ Descending to Layer {layer_number}
   Dungeon Depth: {layer_number - 400}
   "Fortune favors the bold..."""

    elif context.theme == LayerTheme.UPSIDE_DOWN:
        return f"""🔻 BREACH DETECTED - Layer {layer_number}
   ⚠️ HOSTILE ENVIRONMENT
   ⚠️ Reality Stability: COMPROMISED
   
   Light is your anchor. Sound attracts attention."""

    elif context.theme == LayerTheme.SPACE_HUMOR:
        return f"""🌌 Arriving at Layer {layer_number}
   Location: Space Sector ZZ9 Plural Z Alpha (ish)
   Panic Level: Don't
   
   Remember: The ships hang in the sky in much the same way that bricks don't."""

    else:  # SPACE_SERIOUS
        return f"""📚 FOUNDATION TERMINAL - Layer {layer_number}
   Archive Depth: Galactic
   Seldon Crisis Status: Monitoring
   
   "Violence is the last refuge of the incompetent."
   — Salvor Hardin"""


# Special layer constants for common access
LAYER_EARTH_SURFACE = 100
LAYER_EARTH_CAVES = 200
LAYER_NETHACK_START = 401
LAYER_NETHACK_END = 455
LAYER_UPSIDE_DOWN_START = 500
LAYER_SOLAR_SYSTEM = 700
LAYER_GALACTIC = 750


def is_dungeon_layer(layer_number: int) -> bool:
    """Check if layer is a dungeon/fantasy layer."""
    return get_theme_for_layer_number(layer_number) == LayerTheme.DUNGEON


def is_hostile_layer(layer_number: int) -> bool:
    """Check if layer is hostile (Upside Down)."""
    return get_theme_for_layer_number(layer_number) == LayerTheme.UPSIDE_DOWN


def is_space_layer(layer_number: int) -> bool:
    """Check if layer is in space."""
    theme = get_theme_for_layer_number(layer_number)
    return theme in (LayerTheme.SPACE_HUMOR, LayerTheme.SPACE_SERIOUS)
