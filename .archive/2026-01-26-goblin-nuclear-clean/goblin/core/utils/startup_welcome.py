"""
uDOS v1.0.30 - Startup Welcome & Demo Helper

Shows welcome message and offers optional demo of new features.
Called after system health check during startup.

Version: 1.0.30
"""

import os
import sys
from dev.goblin.core.services.standardized_input import StandardizedInput


def show_v1_0_30_welcome(viewport_width: int = 70):
    """
    Display welcome message with active features.

    Args:
        viewport_width: Terminal width for formatting
    """
    from dev.goblin.core.utils.column_formatter import ColumnFormatter, ColumnConfig
    import os
    import sys
    
    # Get version from setup.py
    try:
        setup_path = os.path.join(os.path.dirname(__file__), '..', '..', 'setup.py')
        with open(setup_path, 'r') as f:
            for line in f:
                if 'version=' in line:
                    version = line.split('"')[1]
                    break
            else:
                version = "1.2.31"
    except:
        version = "1.2.31"
    
    # Use viewport width with sensible limits (min 38 for 40x40, max 78)
    # Subtract 2 for border characters
    width = max(38, min(viewport_width - 2, 78))
    formatter = ColumnFormatter(ColumnConfig(width=width))

    print()
    print(formatter.box_top())
    print(formatter.box_multi_column([f"uDOS v{version}", "TUI System", "Grid Engine"]))
    print(formatter.box_multi_column(["Knowledge Bank", "Workflow System", "Extension API"]))
    print(formatter.box_bottom())


def offer_demo(skip_prompt: bool = False) -> bool:
    """
    Offer to show the v1.0.30 demo.

    Args:
        skip_prompt: If True, don't ask (for scripted startup)

    Returns:
        True if user wants to see demo
    """
    if skip_prompt:
        return False

    # Check if we're in an interactive terminal
    if not sys.stdin.isatty():
        return False

    print("  💡 See new features in action?")
    print()

    try:
        input_service = StandardizedInput()
        response = input_service.select_option(
            title="Run v1.0.30 demo?",
            options=["Yes", "No"],
            default_index=1
        )
        return response == "Yes"
    except (KeyboardInterrupt, EOFError):
        print()
        return False


def run_demo():
    """
    Run the v1.0.30 interactive demo.
    """
    try:
        # Import and run the demo
        import subprocess
        demo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'dev', 'demo_v1_0_30.py')

        if os.path.exists(demo_path):
            # Run demo with Python
            result = subprocess.run(
                [sys.executable, demo_path],
                cwd=os.path.dirname(demo_path)
            )
            return result.returncode == 0
        else:
            print(f"  ⚠️  Demo not found at: {demo_path}")
            print(f"  💡 Run manually: python dev/demo_v1_0_30.py")
            return False

    except Exception as e:
        print(f"  ❌ Error running demo: {e}")
        return False


def startup_sequence(viewport_width: int = 70, auto_skip_demo: bool = False):
    """
    Complete v1.0.30 startup sequence.

    Args:
        viewport_width: Terminal width
        auto_skip_demo: If True, skip demo prompt
    """
    # Show welcome message
    show_v1_0_30_welcome(viewport_width)

    # Offer demo (unless auto-skipping)
    if not auto_skip_demo:
        if offer_demo():
            print()
            print("  🎬 Starting demo...")
            print()

            input_service = StandardizedInput()
            input_service.text_input("Press ENTER to begin", default="")
            print()

            if run_demo():
                print()
                print("  ✅ Demo complete!")
            else:
                print()
                print("  Demo ended.")

            print()
            input_service.text_input("Press ENTER to continue to uDOS prompt", default="")
            print()


# Quick test
if __name__ == '__main__':
    startup_sequence(auto_skip_demo=False)
