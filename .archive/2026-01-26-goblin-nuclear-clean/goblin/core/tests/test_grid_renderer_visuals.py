"""Visual tests for GridRenderer borders and progress bar"""

from dev.goblin.core.ui.grid_renderer import GridRenderer, ViewportTier
from dev.goblin.core.ui.grid_renderer import COLUMN_WIDTH, GUTTER_WIDTH
from dev.goblin.core.ui.components.box_drawing import get_box_chars, BoxStyle
from dev.goblin.core.ui.components.progress_bar import FULL_BLOCK, EMPTY_BLOCK


def test_grid_borders_use_box_drawing():
    renderer = GridRenderer(ViewportTier.STANDARD)
    renderer.create_grid(2, 3)
    renderer.header = "Test Header"
    out = renderer.render(border=True)
    lines = out.splitlines()

    chars = get_box_chars(BoxStyle.SINGLE)
    # First non-header line should be top border; find line with corner
    border_top_line = None
    for line in lines:
        if line.startswith(chars.top_left) and line.endswith(chars.top_right):
            border_top_line = line
            break
    assert border_top_line is not None

    # Last line should be bottom border
    assert lines[-1].startswith(chars.bottom_left)
    assert lines[-1].endswith(chars.bottom_right)


def test_grid_row_borders_use_box_drawing():
    """Verify grid row borders use BoxStyle.SINGLE vertical character."""
    renderer = GridRenderer(ViewportTier.STANDARD)
    renderer.create_grid(2, 3)

    # Render with borders
    out = renderer.render(border=True)
    lines = out.splitlines()

    # Find grid row lines (not header, not top/bottom borders)
    chars = get_box_chars(BoxStyle.SINGLE)
    grid_rows = [
        l for l in lines if l.startswith(chars.vertical) and l.endswith(chars.vertical)
    ]

    assert len(grid_rows) >= 2, "Should have at least 2 grid rows with borders"

    # Each row should start and end with vertical char
    for row in grid_rows:
        assert row[0] == chars.vertical
        assert row[-1] == chars.vertical


def test_grid_progress_bar_uses_canonical_blocks():
    renderer = GridRenderer()
    bar = renderer.render_progress_bar(50, width=10)
    # bar string format: "[████░░░░░]"
    assert bar.startswith("[") and bar.endswith("]")
    inner = bar.strip()[1:-1]
    assert set(inner).issubset({FULL_BLOCK, EMPTY_BLOCK})
