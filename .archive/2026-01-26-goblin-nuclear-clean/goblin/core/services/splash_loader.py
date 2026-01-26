"""
Modular Splash Loader Service
Version: 2.4.0

Programmable terminal loader with animated effects, configurable via uPY commands.
Supports Tauri extension integration for rich visual effects.

Features:
- U block graphic animation
- Scrolling background stripe effects
- Info box slider with messages
- Scrolling text
- NES-style pointer/glove cursor
- Multiple animation presets
- User.json integration for splash preferences
"""

import time
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class SplashLoader:
    """Modular splash loader with programmable effects"""
    
    # NES-style cursor/pointer characters
    NES_POINTER = "👉"  # Pointing hand/glove
    NES_CURSOR = "▶"    # Triangle cursor
    NES_SELECT = "☞"    # Index pointing right
    
    # Block graphic characters for U logo
    BLOCK_FULL = "█"
    BLOCK_UPPER = "▀"
    BLOCK_LOWER = "▄"
    BLOCK_LEFT = "▌"
    BLOCK_RIGHT = "▐"
    BLOCK_LIGHT = "░"
    BLOCK_MEDIUM = "▒"
    BLOCK_DARK = "▓"
    
    # Stripe effects
    STRIPE_CHARS = ["═", "─", "━", "▬", "▭"]
    RAINBOW_COLORS = [
        "\033[91m",  # Red
        "\033[93m",  # Yellow
        "\033[92m",  # Green
        "\033[96m",  # Cyan
        "\033[94m",  # Blue
        "\033[95m",  # Magenta
    ]
    RESET = "\033[0m"
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize splash loader with optional configuration"""
        self.config = config or self._load_default_config()
        self.animation_running = False
        
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            'background_effect': 'rainbow-stripe',
            'show_info_box': True,
            'info_box_message': 'LOADING SYSTEM',
            'scroll_text': 'uDOS v2.4.0 - Offline-First Survival OS',
            'logo_block': 'U',
            'duration': 5000,
            'show_nes_pointer': True,
            'animation_speed': 0.1,
            'stripe_density': 3
        }
    
    def load_user_config(self, user_json_path: Path) -> bool:
        """Load splash configuration from user.json"""
        try:
            import json
            if user_json_path.exists():
                with open(user_json_path, 'r') as f:
                    user_data = json.load(f)
                    
                # Check for splash settings in system_settings
                if 'system_settings' in user_data:
                    ui_settings = user_data['system_settings'].get('ui', {})
                    if 'show_splash' in ui_settings:
                        self.config['enabled'] = ui_settings['show_splash']
                    if 'splash_config' in ui_settings:
                        self.config.update(ui_settings['splash_config'])
                return True
        except Exception as e:
            print(f"Warning: Could not load user splash config: {e}")
        return False
    
    def render_u_block_logo(self, animate: bool = False) -> List[str]:
        """
        Render the U block graphic logo
        
        Args:
            animate: If True, returns frames for animation
            
        Returns:
            List of logo lines (or frames if animated)
        """
        # U block graphic (7x5 character grid)
        logo_lines = [
            f"{self.BLOCK_FULL}     {self.BLOCK_FULL}",
            f"{self.BLOCK_FULL}     {self.BLOCK_FULL}",
            f"{self.BLOCK_FULL}     {self.BLOCK_FULL}",
            f"{self.BLOCK_FULL}     {self.BLOCK_FULL}",
            f" {self.BLOCK_FULL}{self.BLOCK_FULL}{self.BLOCK_FULL}{self.BLOCK_FULL}{self.BLOCK_FULL} "
        ]
        
        if not animate:
            return logo_lines
        
        # Animation frames: build-up effect
        frames = []
        for i in range(1, 6):
            frame = logo_lines[:i]
            frames.append(frame)
        return frames
    
    def render_stripe_background(self, width: int, height: int, effect: str = 'rainbow-stripe') -> List[str]:
        """
        Render scrolling background stripe effect
        
        Args:
            width: Terminal width
            height: Number of lines
            effect: Effect type (rainbow-stripe, matrix, grid, wave, pulse)
            
        Returns:
            List of background lines
        """
        lines = []
        
        if effect == 'rainbow-stripe':
            for i in range(height):
                color = self.RAINBOW_COLORS[i % len(self.RAINBOW_COLORS)]
                stripe_char = self.STRIPE_CHARS[i % len(self.STRIPE_CHARS)]
                line = color + (stripe_char * width) + self.RESET
                lines.append(line)
                
        elif effect == 'matrix':
            import random
            chars = "01"
            for i in range(height):
                line = self.RAINBOW_COLORS[2] + ''.join(random.choice(chars) for _ in range(width)) + self.RESET
                lines.append(line)
                
        elif effect == 'grid':
            for i in range(height):
                if i % 2 == 0:
                    line = "┼" + "─" * (width - 2) + "┼"
                else:
                    line = "│" + " " * (width - 2) + "│"
                lines.append(line)
                
        elif effect == 'wave':
            for i in range(height):
                wave_pos = int((i / height) * len(self.STRIPE_CHARS))
                char = self.STRIPE_CHARS[wave_pos]
                line = char * width
                lines.append(line)
                
        elif effect == 'pulse':
            density_chars = [self.BLOCK_LIGHT, self.BLOCK_MEDIUM, self.BLOCK_DARK, self.BLOCK_FULL]
            for i in range(height):
                char = density_chars[i % len(density_chars)]
                line = char * width
                lines.append(line)
        
        return lines
    
    def render_info_box(self, message: str, width: int = 40) -> List[str]:
        """
        Render info box with message
        
        Args:
            message: Message to display
            width: Box width
            
        Returns:
            List of box lines
        """
        # Box with double-line border (no gaps)
        top = "╔" + "═" * (width - 2) + "╗"
        mid = "║" + message.center(width - 2) + "║"
        bot = "╚" + "═" * (width - 2) + "╝"
        
        return [top, mid, bot]
    
    def render_scroll_text(self, text: str, width: int, offset: int = 0) -> str:
        """
        Render scrolling text with offset
        
        Args:
            text: Text to scroll
            width: Display width
            offset: Scroll offset position
            
        Returns:
            Visible portion of scrolling text
        """
        # Pad text to create seamless loop
        padded_text = text + "    " + text
        visible_start = offset % len(padded_text)
        visible_text = padded_text[visible_start:visible_start + width]
        
        # Pad if too short
        if len(visible_text) < width:
            visible_text = visible_text + " " * (width - len(visible_text))
        
        return visible_text
    
    def render_nes_pointer(self, selected_option: int = 0, options: List[str] = None) -> List[str]:
        """
        Render NES-style pointer next to menu options
        
        Args:
            selected_option: Index of selected option
            options: List of menu options
            
        Returns:
            List of lines with pointer and options
        """
        if options is None:
            options = ["START", "OPTIONS", "EXIT"]
        
        lines = []
        for i, option in enumerate(options):
            if i == selected_option:
                line = f"{self.NES_POINTER} {option}"
            else:
                line = f"  {option}"
            lines.append(line)
        
        return lines
    
    def animate_splash(self, duration_ms: int = 5000) -> None:
        """
        Run full splash animation sequence
        
        Args:
            duration_ms: Animation duration in milliseconds
        """
        self.animation_running = True
        frames = 60  # Target 60 frames
        frame_time = duration_ms / 1000 / frames
        
        try:
            # Get terminal dimensions
            try:
                import shutil
                term_size = shutil.get_terminal_size((80, 24))
                width, height = term_size.columns, term_size.lines
            except:
                width, height = 80, 24
            
            # Animation loop
            for frame in range(frames):
                if not self.animation_running:
                    break
                
                # Clear screen
                print("\033[2J\033[H", end='')
                
                # Render background
                bg_effect = self.config.get('background_effect', 'rainbow-stripe')
                bg_lines = self.render_stripe_background(width, height, bg_effect)
                
                # Calculate positions
                logo_height = 5
                info_height = 3
                vertical_center = (height - logo_height - info_height) // 2
                
                # Render background with overlay space
                for i, line in enumerate(bg_lines[:vertical_center]):
                    print(line)
                
                # Render U block logo (centered)
                logo_frames = self.render_u_block_logo(animate=True)
                current_logo = logo_frames[min(frame // 10, len(logo_frames) - 1)]
                for logo_line in current_logo:
                    print(logo_line.center(width))
                
                # Skip background lines where logo is
                for i in range(logo_height):
                    if vertical_center + i < len(bg_lines):
                        pass  # Logo overlay
                
                # Render info box (if enabled)
                if self.config.get('show_info_box', True):
                    info_msg = self.config.get('info_box_message', 'LOADING')
                    info_box = self.render_info_box(info_msg, width=40)
                    for box_line in info_box:
                        print(box_line.center(width))
                
                # Render scrolling text
                scroll_text = self.config.get('scroll_text', '')
                if scroll_text:
                    visible_text = self.render_scroll_text(scroll_text, width - 10, frame * 2)
                    print()
                    print(visible_text.center(width))
                
                # Render NES pointer (if enabled)
                if self.config.get('show_nes_pointer', False):
                    print()
                    pointer_lines = self.render_nes_pointer()
                    for pointer_line in pointer_lines:
                        print(pointer_line.center(width))
                
                # Frame delay
                sys.stdout.flush()
                time.sleep(frame_time)
                
        except KeyboardInterrupt:
            self.animation_running = False
        finally:
            # Clear and reset
            print("\033[2J\033[H", end='')
            self.animation_running = False
    
    def render_static_splash(self) -> str:
        """
        Render static splash screen (no animation)
        
        Returns:
            Complete splash screen as string
        """
        lines = []
        
        # Get terminal width
        try:
            import shutil
            width = shutil.get_terminal_size((80, 24)).columns
        except:
            width = 80
        
        # Header
        lines.append("=" * width)
        lines.append("")
        
        # U block logo
        logo = self.render_u_block_logo()
        for logo_line in logo:
            lines.append(logo_line.center(width))
        
        lines.append("")
        
        # Info box
        if self.config.get('show_info_box', True):
            info_msg = self.config.get('info_box_message', 'SYSTEM READY')
            info_box = self.render_info_box(info_msg, width=min(40, width - 10))
            for box_line in info_box:
                lines.append(box_line.center(width))
        
        lines.append("")
        
        # Scroll text (static)
        scroll_text = self.config.get('scroll_text', '')
        if scroll_text:
            lines.append(scroll_text.center(width))
        
        lines.append("")
        lines.append("=" * width)
        
        return "\n".join(lines)
    
    def stop_animation(self):
        """Stop any running animation"""
        self.animation_running = False


# Global loader instance
_splash_loader = None


def get_splash_loader(config: Optional[Dict] = None) -> SplashLoader:
    """Get or create global splash loader instance"""
    global _splash_loader
    if _splash_loader is None:
        _splash_loader = SplashLoader(config)
    return _splash_loader


def render_nes_toast(message: str, width: int = 40, style: str = "info") -> str:
    """
    Render NES-styled toast notification
    
    Args:
        message: Toast message
        width: Toast width
        style: Toast style (info, success, error, warning)
        
    Returns:
        Formatted toast notification
    """
    # NES-style icons
    icons = {
        'info': '📘',
        'success': '✓',
        'error': '✗',
        'warning': '⚠'
    }
    
    icon = icons.get(style, '•')
    
    # Box characters (no gaps)
    top = "╔" + "═" * (width - 2) + "╗"
    mid = "║" + f" {icon} {message}".ljust(width - 2) + "║"
    bot = "╚" + "═" * (width - 2) + "╝"
    
    return "\n".join([top, mid, bot])
