"""Tests for box_drawing.render_box helper"""

from dev.goblin.core.ui.components.box_drawing import (
    render_box,
    render_section,
    get_box_chars,
    BoxStyle,
)
from dev.goblin.core.ui.components.box_drawing import render_separator


def test_render_box_single_style_center_alignment():
    content = ["Title"]
    width = 20
    out = render_box(
        content, width=width, style=BoxStyle.SINGLE, padding=1, align="center"
    )
    lines = out.splitlines()
    chars = get_box_chars(BoxStyle.SINGLE)

    # top and bottom borders
    assert lines[0].startswith(chars.top_left)
    assert lines[0].endswith(chars.top_right)
    assert lines[-1].startswith(chars.bottom_left)
    assert lines[-1].endswith(chars.bottom_right)

    # content line length consistency
    assert len(lines[1]) == len(lines[0])
    assert len(lines[-1]) == len(lines[0])

    # vertical borders present
    assert lines[1][0] == chars.vertical
    assert lines[1][-1] == chars.vertical


def test_render_box_respects_width_and_padding():
    content = ["ABCDE"]
    width = 10
    out = render_box(
        content, width=width, style=BoxStyle.SINGLE, padding=2, align="left"
    )
    lines = out.splitlines()
    # total inner width = width + padding*2 + 2
    expected_inner = width + 2 * 2 + 2
    assert len(lines[0]) == expected_inner + 2  # add corners
    assert len(lines[1]) == expected_inner + 2


def test_render_separator_uses_horizontal_char():
    width = 25
    out = render_separator(width=width, style=BoxStyle.SINGLE)
    chars = get_box_chars(BoxStyle.SINGLE)
    assert len(out) == width
    assert set(out) == {chars.horizontal}


def test_render_section_composes_box_and_separator():
    width = 30
    title = "Section Title"
    subtitle = "Subtitle line"
    out = render_section(
        title, subtitle=subtitle, width=width, style=BoxStyle.SINGLE, align="center"
    )
    lines = out.splitlines()
    chars = get_box_chars(BoxStyle.SINGLE)
    # Expect: top border, title line, (optional subtitle), bottom of box, separator
    assert lines[0].startswith(chars.top_left) and lines[0].endswith(chars.top_right)
    # separator last line should be horizontal repeated
    assert set(lines[-1]) == {chars.horizontal}
