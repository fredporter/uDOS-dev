#!/usr/bin/env python3
"""
Box Drawing Unified Module
===========================

Consolidated box drawing characters and styles for TUI rendering.

This is the AUTHORITATIVE source for all box drawing in uDOS.
All other modules should import from here, not reimplement.

Version: 1.0.0
Date: 2026-01-14
Author: Fred Porter
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, List


class BoxStyle(Enum):
    """Box drawing character styles."""

    SINGLE = "single"  # ┌─┐│└┘
    DOUBLE = "double"  # ╔═╗║╚╝
    ROUNDED = "rounded"  # ╭─╮│╰╯
    HEAVY = "heavy"  # ┏━┓┃┗┛
    ASCII = "ascii"  # +-+|+-+
    TELETEXT = "teletext"  # Block characters for mosaic
    NONE = "none"  # No border


@dataclass
class BoxChars:
    """
    Box drawing characters for a style.

    Contains all Unicode box drawing characters needed for a specific style,
    including corners, edges, and junction points.
    """

    top_left: str
    top_right: str
    bottom_left: str
    bottom_right: str
    horizontal: str
    vertical: str
    # T-junctions
    t_down: str = "┬"  # ┬ (connects left, right, down)
    t_up: str = "┴"  # ┴ (connects left, right, up)
    t_right: str = "├"  # ├ (connects top, bottom, right)
    t_left: str = "┤"  # ┤ (connects top, bottom, left)
    cross: str = "┼"  # ┼ (connects all four directions)


# AUTHORITATIVE Box character sets
# All 7 styles defined here, nowhere else
BOX_CHARS: Dict[BoxStyle, BoxChars] = {
    BoxStyle.SINGLE: BoxChars(
        top_left="┌",
        top_right="┐",
        bottom_left="└",
        bottom_right="┘",
        horizontal="─",
        vertical="│",
        t_down="┬",
        t_up="┴",
        t_right="├",
        t_left="┤",
        cross="┼",
    ),
    BoxStyle.DOUBLE: BoxChars(
        top_left="╔",
        top_right="╗",
        bottom_left="╚",
        bottom_right="╝",
        horizontal="═",
        vertical="║",
        t_down="╦",
        t_up="╩",
        t_right="╠",
        t_left="╣",
        cross="╬",
    ),
    BoxStyle.ROUNDED: BoxChars(
        top_left="╭",
        top_right="╮",
        bottom_left="╰",
        bottom_right="╯",
        horizontal="─",
        vertical="│",
        t_down="┬",
        t_up="┴",
        t_right="├",
        t_left="┤",
        cross="┼",
    ),
    BoxStyle.HEAVY: BoxChars(
        top_left="┏",
        top_right="┓",
        bottom_left="┗",
        bottom_right="┛",
        horizontal="━",
        vertical="┃",
        t_down="┳",
        t_up="┻",
        t_right="┣",
        t_left="┫",
        cross="╋",
    ),
    BoxStyle.ASCII: BoxChars(
        top_left="+",
        top_right="+",
        bottom_left="+",
        bottom_right="+",
        horizontal="-",
        vertical="|",
        t_down="+",
        t_up="+",
        t_right="+",
        t_left="+",
        cross="+",
    ),
    BoxStyle.TELETEXT: BoxChars(
        top_left="▛",
        top_right="▜",
        bottom_left="▙",
        bottom_right="▟",
        horizontal="▀",
        vertical="▌",
        t_down="▀",
        t_up="▄",
        t_right="▌",
        t_left="▐",
        cross="█",
    ),
    BoxStyle.NONE: BoxChars(
        top_left=" ",
        top_right=" ",
        bottom_left=" ",
        bottom_right=" ",
        horizontal=" ",
        vertical=" ",
        t_down=" ",
        t_up=" ",
        t_right=" ",
        t_left=" ",
        cross=" ",
    ),
}


def get_box_chars(style: BoxStyle = BoxStyle.SINGLE) -> BoxChars:
    """
    Get box drawing characters for a specific style.

    Args:
        style: BoxStyle enum value (default: SINGLE)

    Returns:
        BoxChars dataclass with all characters for the style

    Example:
        chars = get_box_chars(BoxStyle.DOUBLE)
        print(chars.top_left)  # ╔
    """
    return BOX_CHARS[style]


def get_box_chars_by_name(style_name: str) -> Optional[BoxChars]:
    """
    Get box drawing characters by style name string.

    Args:
        style_name: Name of style ("single", "double", "rounded", etc)

    Returns:
        BoxChars if found, None otherwise

    Example:
        chars = get_box_chars_by_name("rounded")
    """
    try:
        style = BoxStyle(style_name)
        return BOX_CHARS[style]
    except ValueError:
        return None


__all__ = [
    "BoxStyle",
    "BoxChars",
    "BOX_CHARS",
    "get_box_chars",
    "get_box_chars_by_name",
    "render_box",
    "render_separator",
    "render_section",
]


def render_box(
    content_lines: List[str],
    width: int = 70,
    style: BoxStyle = BoxStyle.SINGLE,
    padding: int = 1,
    align: str = "left",
) -> str:
    """
    Render a boxed block using standardized box drawing characters.

    Args:
        content_lines: Lines of text to render inside the box
        width: Content width (excluding borders)
        style: BoxStyle to use for borders
        padding: Spaces on each side of content inside the box
        align: Text alignment for each content line: left|center|right

    Returns:
        A single string containing the rendered box with top/bottom borders.
    """
    chars = get_box_chars(style)

    # Top border: accounts for spaces between vertical border and content
    inner_total = width + (padding * 2) + 2  # one space on both sides
    top = f"{chars.top_left}{chars.horizontal * inner_total}{chars.top_right}"

    rendered_lines: List[str] = [top]

    for raw in content_lines:
        # Truncate content to width
        text = raw if len(raw) <= width else raw[:width]
        # Alignment
        if align == "center":
            left_pad = (width - len(text)) // 2
            right_pad = width - len(text) - left_pad
        elif align == "right":
            left_pad = width - len(text)
            right_pad = 0
        else:
            left_pad = 0
            right_pad = width - len(text)

        inner = (
            " "
            + (" " * padding)
            + (" " * left_pad)
            + text
            + (" " * right_pad)
            + (" " * padding)
            + " "
        )
        rendered_lines.append(f"{chars.vertical}{inner}{chars.vertical}")

    bottom = f"{chars.bottom_left}{chars.horizontal * inner_total}{chars.bottom_right}"
    rendered_lines.append(bottom)

    return "\n".join(rendered_lines)


def render_separator(width: int = 70, style: BoxStyle = BoxStyle.SINGLE) -> str:
    """
    Render a horizontal separator line using the style's horizontal character.

    Args:
        width: Length of the separator in characters
        style: BoxStyle to select the horizontal glyph

    Returns:
        A string of `width` repeated horizontal characters.
    """
    chars = get_box_chars(style)
    return chars.horizontal * width


def render_section(
    title: str,
    subtitle: Optional[str] = None,
    width: int = 70,
    style: BoxStyle = BoxStyle.SINGLE,
    align: str = "center",
) -> str:
    """
    Render a boxed title followed by a horizontal separator.

    Args:
        title: Section title text
        subtitle: Optional subtitle line below the title
        width: Content width (excluding borders)
        style: BoxStyle to use for borders
        align: Alignment for title/subtitle lines

    Returns:
        Multiline string with a header box and a separator line.
    """
    lines: List[str] = [title]
    if subtitle:
        lines.append(subtitle)
    header = render_box(lines, width=width, style=style, padding=1, align=align)
    sep = render_separator(width=width, style=style)
    return "\n".join([header, sep])
