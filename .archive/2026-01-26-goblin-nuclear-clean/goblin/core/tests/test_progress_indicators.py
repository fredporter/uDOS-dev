"""Tests for unified progress indicators"""

import time
from dev.goblin.core.ui.progress_indicators import (
    ProgressIndicators,
    ProgressBar,
    MultiStageProgress,
)
from dev.goblin.core.ui.components.progress_bar import FULL_BLOCK, EMPTY_BLOCK
from dev.goblin.core.ui.components.box_drawing import get_box_chars, BoxStyle


def test_progress_bar_uses_canonical_blocks():
    bar = ProgressBar(total=10, width=10, title="Test")
    # halfway
    bar.current = 5
    rendered = bar.render()
    assert "[" in rendered and "]" in rendered
    # Extract the bracketed bar segment (split only on first title delimiter)
    segment = rendered.split(": ", 1)[1].split(" (")[0]
    # segment like "[█████░░░░░] 50%"
    bar_part = segment.split("]")[0].strip("[")
    # ensure only canonical blocks are used
    assert set(bar_part).issubset({FULL_BLOCK, EMPTY_BLOCK})
    assert "50%" in segment


def test_multi_stage_progress_uses_box_chars():
    stages = ["Stage A", "Stage B"]
    progress = MultiStageProgress(stages)
    # start and complete one stage to populate
    progress.start_stage(0)
    time.sleep(0.01)
    progress.complete_stage(0)
    rendered = progress.render()
    chars = get_box_chars(BoxStyle.SINGLE)
    lines = rendered.splitlines()
    assert lines[0].startswith(chars.top_left)
    assert lines[0].endswith(chars.top_right)
    assert lines[-1].startswith(chars.bottom_left)
    assert lines[-1].endswith(chars.bottom_right)
