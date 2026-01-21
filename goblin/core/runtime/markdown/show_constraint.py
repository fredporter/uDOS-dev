#!/usr/bin/env python3
"""
Map Tile Constraint Helper

Shows 120x40 character grid for designing map tiles.
"""


def show_grid():
    """Display 120x40 character grid."""
    print("\n" + "=" * 120)
    print("120-CHARACTER WIDTH CONSTRAINT".center(120))
    print("=" * 120)
    print()

    # Top ruler
    ruler_top = ""
    for i in range(0, 120, 10):
        ruler_top += f"{i:<10}"
    print(ruler_top)

    # Box template (120 wide)
    border = "┌" + "─" * 118 + "┐"
    empty = "│" + " " * 118 + "│"
    bottom = "└" + "─" * 118 + "┘"

    print(border)
    for row in range(1, 39):  # 38 content rows (2 for borders = 40 total)
        if row == 1:
            title = "TITLE HERE".center(118)
            print(f"│{title}│")
        elif row == 37:
            info = "Info line".center(118)
            print(f"│{info}│")
        else:
            print(empty)
    print(bottom)

    print()
    print(f"Total width: 120 chars")
    print(f"Total height: 40 lines")
    print(f"Content area: 118 × 38 chars (borders excluded)")


if __name__ == "__main__":
    show_grid()
