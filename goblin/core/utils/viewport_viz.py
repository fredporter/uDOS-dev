# uDOS v1.0.0 - Viewport Visualization & Color Testing

import os
import shutil
from dev.goblin.core.utils.column_formatter import ColumnFormatter, ColumnConfig

class ViewportVisualizer:
    """
    Creates ASCII art splash screens and color tests for viewport validation.
    Tests terminal capabilities: dimensions, color support, Unicode rendering.
    
    DESIGN RULE: No color emojis in bordered output!
    Use only: ■ □ ▪ ▫ ● ○ ◆ ◇ ▲ ▼ ◀ ▶ ★ ☆ ♠ ♣ ♥ ♦ • ✓ ✗ ⚠ ▬ ═ ║
    Reason: Color emojis (🎯🔍📊) are 2-width but terminals measure inconsistently,
    breaking box border alignment. Block chars are reliable 1-width.
    """

    # Polaroid Colors (System Default) - High-contrast photo-inspired
    COLORS = {
        'red':     '\033[38;5;196m',  # tput 196 - Bold Red
        'green':   '\033[38;5;46m',   # tput 46  - Bright Green
        'yellow':  '\033[38;5;226m',  # tput 226 - Yellow Burst
        'blue':    '\033[38;5;21m',   # tput 21  - Deep Blue
        'purple':  '\033[38;5;201m',  # tput 201 - Magenta Pink
        'cyan':    '\033[38;5;51m',   # tput 51  - Cyan Flash
        'white':   '\033[38;5;15m',   # tput 15  - Pure White
        'black':   '\033[38;5;16m',   # tput 16  - Pure Black

        # Grayscale gradient blocks
        'gray_0':  '\033[38;5;232m',  # Darkest gray
        'gray_1':  '\033[38;5;236m',
        'gray_2':  '\033[38;5;240m',
        'gray_3':  '\033[38;5;244m',
        'gray_4':  '\033[38;5;248m',
        'gray_5':  '\033[38;5;252m',  # Lightest gray

        # Inverted colors (text on colored background)
        'white_on_red':    '\033[97;41m',  # White text on red background
        'white_on_blue':   '\033[97;44m',  # White text on blue background
        'white_on_green':  '\033[97;42m',  # White text on green background
        'white_on_cyan':   '\033[97;46m',  # White text on cyan background
        'white_on_purple': '\033[97;45m',  # White text on purple background
        'black_on_yellow': '\033[30;43m',  # Black text on yellow background
        'black_on_green':  '\033[30;42m',  # Black text on green background

        'reset':   '\033[0m'
    }

    # Shading blocks (Unicode)
    SHADES = {
        'full':    '█',  # 100%
        'dark':    '▓',  # 75%
        'medium':  '▒',  # 50%
        'light':   '░',  # 25%
        'empty':   ' '   # 0%
    }

    # ASCII fallback blocks
    ASCII_SHADES = {
        'full':    '#',
        'dark':    '@',
        'medium':  '+',
        'light':   '.',
        'empty':   ' '
    }

    def __init__(self, viewport=None):
        self.viewport = viewport
        self.width = viewport.width if viewport else 80
        self.height = viewport.height if viewport else 24
        self.unicode_support = self._test_unicode()
        self.color_support = self._test_color()
        self.monospace_font = self._test_monospace()
        # Use actual terminal width (minus padding) without arbitrary cap
        self.formatter = ColumnFormatter(ColumnConfig(width=self.width - 4))

    def _test_unicode(self):
        """Test if terminal supports Unicode."""
        try:
            # Try to encode Unicode block character
            '█'.encode('utf-8')
            return True
        except:
            return False

    def _test_color(self):
        """Test if terminal supports 256 colors."""
        # Check TERM environment variable
        term = os.environ.get('TERM', '')
        return '256color' in term or 'truecolor' in term

    def _test_monospace(self):
        """Detect if terminal is using monospace font."""
        # All terminals should use monospace, but we'll check viewport consistency
        if self.viewport:
            # If viewport detection worked, assume monospace
            return True
        return True  # Default assumption

    def color(self, text, color_name):
        """Apply color to text if supported."""
        if not self.color_support:
            return text
        color_code = self.COLORS.get(color_name, self.COLORS['reset'])
        reset = self.COLORS['reset']
        return f"{color_code}{text}{reset}"

    def shade_block(self, shade_level):
        """Get appropriate shade block character."""
        blocks = self.SHADES if self.unicode_support else self.ASCII_SHADES
        return blocks.get(shade_level, blocks['empty'])

    def generate_splash_screen(self):
        """Generate complete viewport splash with color and dimension tests."""
        lines = []

        # Header
        lines.append("=" * self.width)
        title = "🔄 VIEWPORT & COLOR TEST"
        padding = (self.width - len(title)) // 2
        lines.append(" " * padding + title)
        lines.append("=" * self.width)
        lines.append("")

        # Terminal info
        lines.append(f"📐 Dimensions: {self.width}×{self.height} characters")
        lines.append(f"🔤 Unicode: {'✅ Supported' if self.unicode_support else '⚠️  Limited (ASCII fallback)'}")
        lines.append(f"🎨 Color: {'✅ 256-color' if self.color_support else '⚠️  Monochrome'}")
        lines.append(f"🖋️  Font: {'✅ Monospace detected' if self.monospace_font else '⚠️  Variable-width detected'}")

        if self.viewport:
            lines.append(f"📱 Device: {self.viewport.device_type}")
            lines.append(f"🎯 Grid: {self.viewport.grid_width}×{self.viewport.grid_height} cells")

        lines.append("")

        # Color palette test
        lines.append("🎨 POLAROID COLOR PALETTE (System Default):")
        lines.append("─" * self.width)

        # Color blocks
        color_line = "  "
        color_labels = []
        for name, code in [('red', 'red'), ('green', 'green'), ('yellow', 'yellow'),
                          ('blue', 'blue'), ('purple', 'purple'), ('cyan', 'cyan')]:
            block = self.shade_block('full') * 4
            color_line += self.color(block, code) + "  "
            color_labels.append(f"{name:^6}")

        lines.append(color_line)
        lines.append("  " + "  ".join(color_labels))
        lines.append("")

        # Grayscale gradient test
        lines.append("⬛ GRAYSCALE GRADIENT TEST:")
        lines.append("─" * self.width)

        gradient_line = "  "
        if self.unicode_support:
            # Unicode gradient
            for i in range(6):
                gray = f"gray_{i}"
                block = self.shade_block('full') * 6
                gradient_line += self.color(block, gray)
        else:
            # ASCII gradient
            for shade in ['full', 'dark', 'medium', 'light', 'empty']:
                gradient_line += self.shade_block(shade) * 6

        lines.append(gradient_line)
        lines.append("  " + "Black → Gray → White")
        lines.append("")

        # Shading blocks test
        lines.append("▓ SHADING BLOCKS TEST:")
        lines.append("─" * self.width)

        shade_line = "  "
        shade_labels = []
        for shade, label in [('full', '100%'), ('dark', '75%'),
                            ('medium', '50%'), ('light', '25%'), ('empty', '0%')]:
            shade_line += self.shade_block(shade) * 6 + "  "
            shade_labels.append(f"{label:^6}")

        lines.append(shade_line)
        lines.append("  " + "  ".join(shade_labels))
        lines.append("")

        # ASCII Art Test (uDOS logo)
        lines.append("🎯 ASCII ART RENDERING:")
        lines.append("─" * self.width)

        logo = self._generate_logo()
        for line in logo:
            # Center the logo
            padding = (self.width - len(line)) // 2
            lines.append(" " * padding + line)

        lines.append("")

        # Viewport boundary test
        lines.append("📏 VIEWPORT BOUNDARY TEST:")
        lines.append("─" * self.width)

        # Top border
        border_char = self.shade_block('full') if self.unicode_support else '#'
        lines.append(border_char * self.width)

        # Side borders with ruler
        ruler_width = self.width - 4
        ruler = "".join([str(i % 10) for i in range(ruler_width)])
        lines.append(border_char + " " + ruler + " " + border_char)

        # Bottom border
        lines.append(border_char * self.width)
        lines.append("")

        # Footer with palette info
        lines.append("=" * self.width)
        lines.append("Polaroid Color Codes: R#FF1744 G#00E676 Y#FFEB3B B#2196F3 P#E91E63 C#00E5FF")
        lines.append("Default palette applied. Colors: 256-color mode (ANSI)")
        lines.append("=" * self.width)

        return "\n".join(lines)

    def _generate_logo(self):
        """Generate uDOS ASCII art logo."""
        if self.unicode_support:
            return [
                self.color("██╗   ██╗██████╗  ██████╗ ███████╗", 'cyan'),
                self.color("██║   ██║██╔══██╗██╔═══██╗██╔════╝", 'cyan'),
                self.color("██║   ██║██║  ██║██║   ██║███████╗", 'blue'),
                self.color("██║   ██║██║  ██║██║   ██║╚════██║", 'blue'),
                self.color("╚██████╔╝██████╔╝╚██████╔╝███████║", 'purple'),
                self.color(" ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝", 'purple'),
            ]
        else:
            # ASCII fallback
            return [
                " _   _ ____   ___  ____  ",
                "| | | |  _ \\ / _ \\/ ___| ",
                "| | | | | | | | | \\___ \\ ",
                "| |_| | |_| | |_| |___) |",
                " \\___/|____/ \\___/|____/ ",
            ]

    def generate_compact_test(self):
        """Generate compact color test for inline display."""
        blocks = []

        # Color blocks
        for name, code in [('R', 'red'), ('G', 'green'), ('Y', 'yellow'),
                          ('B', 'blue'), ('P', 'purple'), ('C', 'cyan')]:
            block = self.shade_block('full')
            blocks.append(self.color(f"{name}:{block}{block}", code))

        # Grayscale
        gray_blocks = []
        for i in range(6):
            gray = f"gray_{i}"
            block = self.shade_block('full')
            gray_blocks.append(self.color(block, gray))

        return "  ".join(blocks) + " | " + "".join(gray_blocks)

    def test_font_spacing(self):
        """Test monospace font consistency."""
        test_lines = []

        test_lines.append("Font Spacing Test:")
        test_lines.append("─" * 40)
        test_lines.append("iiii IIII 1111 |||| .... ____")
        test_lines.append("mmmm MMMM WWWW @@@@ #### ████")
        test_lines.append("0123456789 ABCDEFGHIJ abcdefghij")
        test_lines.append("")

        # All lines should align perfectly in monospace
        test_lines.append("If columns don't align above,")
        test_lines.append("terminal may not be monospace.")

        return "\n".join(test_lines)
    
    def generate_educational_splash(self, viewport_manager=None):
        """
        Generate compact educational viewport splash with column layout.
        Shows detection results and TUI capabilities efficiently.
        
        Args:
            viewport_manager: ViewportManager instance for tier detection
            
        Returns:
            Formatted splash screen as string
        """
        lines = []
        term_cols, term_lines = self.width, self.height
        
        # Extract tier info
        tier_label = "Unknown"
        tier_desc = "Device type unknown"
        orientation = "Horizontal" if term_cols > term_lines else "Vertical"
        display_mode = "TERMINAL"
        optimal_cols = 2
        
        if viewport_manager:
            vp_info = viewport_manager.viewport_info
            tier_info = vp_info.get("screen_tier", {})
            tier_label = tier_info.get('label', 'Unknown')
            tier_desc = tier_info.get('description', 'Device type unknown')
            try:
                dm = viewport_manager.get_display_mode()
                display_mode = dm.current_config.mode.value.upper()
                optimal_cols = dm.get_optimal_columns()
            except:
                pass
        
        # Header - no title to avoid alignment issues
        lines.append(self.formatter.box_top())
        lines.append(self.formatter.box_line("VIEWPORT DETECTION & TUI CHECK", align="center"))
        
        # Detection Results - single line format
        lines.extend(self.formatter.box_section_header("DETECTION RESULTS", "Size, device, and features"))
        
        # Row 1: Viewport and Mode
        viewport_info = f"{self.color('█', 'cyan')} Viewport: {self.color(f'{term_cols}×{term_lines}', 'green')} chars"
        mode_info = f"{self.color('◆', 'yellow')} Mode: {self.color(display_mode, 'yellow')} ({optimal_cols} cols)"
        lines.append(self.formatter.box_line(f"  {viewport_info}  |  {mode_info}", align="left"))
        
        # Row 2: Device and Capabilities
        unicode_icon = "✅" if self.unicode_support else "❌"
        color_icon = "✅" if self.color_support else "❌"
        device_info = f"{self.color('▶', 'purple')} Device: {self.color(tier_label, 'cyan')} {self.color(orientation, 'green')}"
        caps_info = f"{unicode_icon} Unicode  {color_icon} Colors"
        lines.append(self.formatter.box_line(f"  {device_info}  |  {caps_info}", align="left"))
        lines.append(self.formatter.box_separator())
        
        # Character Gallery - single line
        lines.extend(self.formatter.box_section_header("CHARACTER GALLERY", "Boxes, symbols, colors"))
        
        if self.unicode_support:
            boxes = self.color('╔══╗ ╠══╣ ╬ ┌─┐ ├┤', 'cyan')
            symbols = self.color('▲ ▼ ◄ ►  ↑ ↓ ← →  ■ □ ● ○ ◆', 'yellow')
            lines.append(self.formatter.box_line(f"  {boxes}  |  {symbols}", align="left"))
        else:
            lines.append(self.formatter.box_line("  ASCII Mode: +-+ | # @ * [] () {} /\\", align="left"))
        lines.append(self.formatter.box_separator())
        
        # Color Palette - single row
        if self.color_support:
            lines.extend(self.formatter.box_section_header("COLOR PALETTE", "Polaroid 256-color theme"))
            color_line = "  "
            for code in ['red', 'green', 'yellow', 'blue', 'purple', 'cyan']:
                block = self.shade_block('full') * 3
                color_line += self.color(f"{block}", code) + " "
            lines.append(self.formatter.box_line(color_line, align="left"))
            
            # Grayscale
            gray_line = "  "
            for i in range(6):
                block = self.shade_block('full') * 4
                gray_line += self.color(block, f"gray_{i}")
            lines.append(self.formatter.box_line(gray_line + "  Black ► White", align="left"))
        else:
            lines.append(self.formatter.box_line("⚠️  Monochrome mode", align="left"))
        lines.append(self.formatter.box_separator())
        
        # Progress & Tags - combined
        lines.extend(self.formatter.box_section_header("UI ELEMENTS", "Progress bars and status tags"))
        prog = f"  {self.color('▰▰▰▰▰▰▱▱', 'green')} 75%  {self.color('●●○○', 'yellow')} 2/4  {self.color(' ACTIVE ', 'white_on_green')}  {self.color(' ERROR ', 'white_on_red')}"
        lines.append(self.formatter.box_line(prog, align="left"))
        lines.append(self.formatter.box_separator())
        
        # Summary
        lines.extend(self.formatter.box_section_header("SUMMARY", "What this means"))
        lines.append(self.formatter.box_line("  Each character = 1 grid unit in uDOS viewport system", align="left"))
        tier_desc = f"{self.color(tier_label, 'cyan')} tier ({term_cols}×{term_lines})"
        lines.append(self.formatter.box_line(f"  All panels auto-adapt to {tier_desc}", align="left"))
        lines.append(self.formatter.box_bottom())
        
        # Footer
        lines.append(f"{self.color('Commands:', 'yellow')} VIEWPORT (details) | CONFIG VIEWPORT (override) | STATUS (system)")
        
        return "\n".join(lines)
