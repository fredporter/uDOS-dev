"""
Tests for Unified Progress Bar
"""

from dev.goblin.core.ui.components.progress_bar import ProgressBar, FULL_BLOCK, EMPTY_BLOCK


def test_progress_bar_basic():
    pb = ProgressBar(total=100, width=10)
    out = pb.render(0)
    assert out.startswith("[" + (EMPTY_BLOCK * 10))
    assert out.endswith("0%")


def test_progress_bar_half():
    pb = ProgressBar(total=100, width=10)
    out = pb.render(50)
    assert out.startswith("[" + (FULL_BLOCK * 5))
    assert out.endswith("50%")


def test_progress_bar_full():
    pb = ProgressBar(total=10, width=10)
    out = pb.render(10)
    assert out.startswith("[" + (FULL_BLOCK * 10))
    assert out.endswith("100%")


def test_progress_bar_clamps():
    pb = ProgressBar(total=100, width=10)
    assert pb.render(-10).endswith("0%")
    assert pb.render(1000).endswith("100%")
