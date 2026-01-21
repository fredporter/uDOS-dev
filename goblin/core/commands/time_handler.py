"""
Time Command Handler

Handles all time-related commands: CLOCK, TIMER, EGG, STOPWATCH, CALENDAR

Part of v1.2.31 - Self-Healing System + Core Time & Date

EGG Timer: Science-based egg cooking with large ASCII countdown display.
Inspired by termdown (https://github.com/trehn/termdown) but built native for uDOS.
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from calendar import monthcalendar, month_name, day_name

from .base_handler import BaseCommandHandler
from dev.goblin.core.services.timedate_manager import get_timedate_manager


# Large ASCII digits (7 lines tall, 6 chars wide) - termdown-inspired
LARGE_DIGITS = {
    '0': [
        ' ████ ',
        '██  ██',
        '██  ██',
        '██  ██',
        '██  ██',
        '██  ██',
        ' ████ '
    ],
    '1': [
        '  ██  ',
        ' ███  ',
        '  ██  ',
        '  ██  ',
        '  ██  ',
        '  ██  ',
        '██████'
    ],
    '2': [
        ' ████ ',
        '██  ██',
        '    ██',
        '   ██ ',
        '  ██  ',
        ' ██   ',
        '██████'
    ],
    '3': [
        ' ████ ',
        '██  ██',
        '    ██',
        '  ███ ',
        '    ██',
        '██  ██',
        ' ████ '
    ],
    '4': [
        '██  ██',
        '██  ██',
        '██  ██',
        '██████',
        '    ██',
        '    ██',
        '    ██'
    ],
    '5': [
        '██████',
        '██    ',
        '█████ ',
        '    ██',
        '    ██',
        '██  ██',
        ' ████ '
    ],
    '6': [
        ' ████ ',
        '██  ██',
        '██    ',
        '█████ ',
        '██  ██',
        '██  ██',
        ' ████ '
    ],
    '7': [
        '██████',
        '    ██',
        '   ██ ',
        '  ██  ',
        ' ██   ',
        ' ██   ',
        ' ██   '
    ],
    '8': [
        ' ████ ',
        '██  ██',
        '██  ██',
        ' ████ ',
        '██  ██',
        '██  ██',
        ' ████ '
    ],
    '9': [
        ' ████ ',
        '██  ██',
        '██  ██',
        ' █████',
        '    ██',
        '██  ██',
        ' ████ '
    ],
    ':': [
        '      ',
        '  ██  ',
        '  ██  ',
        '      ',
        '  ██  ',
        '  ██  ',
        '      '
    ],
    ' ': [
        '      ',
        '      ',
        '      ',
        '      ',
        '      ',
        '      ',
        '      '
    ]
}

# Egg cooking science - based on research and culinary standards
# Time in seconds at sea level, room temperature eggs, rolling boil
EGG_SCIENCE = {
    'soft': {
        'base_time': 270,  # 4.5 minutes - very runny yolk, set white
        'description': 'Soft-boiled (runny yolk)',
        'tip': 'Perfect for toast soldiers! Serve immediately.',
        'yolk': 'Very liquid, warm throughout',
        'white': 'Fully set but tender'
    },
    'mollet': {
        'base_time': 330,  # 5.5 minutes - classic French
        'description': 'Mollet (creamy, jammy)',
        'tip': 'French bistro style. Peel carefully under cool water.',
        'yolk': 'Creamy and jammy throughout',
        'white': 'Fully set, silky'
    },
    'jammy': {
        'base_time': 390,  # 6.5 minutes - ramen style
        'description': 'Jammy (ramen-style)',
        'tip': 'Perfect for ramen! Marinate in soy + mirin for ajitsuke tamago.',
        'yolk': 'Jammy center, set outer ring',
        'white': 'Fully set'
    },
    'medium': {
        'base_time': 480,  # 8 minutes
        'description': 'Medium-boiled (translucent center)',
        'tip': 'Great for salads. Easy to peel when cooled properly.',
        'yolk': 'Mostly set with slight translucence',
        'white': 'Fully set'
    },
    'hard': {
        'base_time': 600,  # 10 minutes
        'description': 'Hard-boiled (fully set)',
        'tip': 'For deviled eggs, egg salad. Avoid overcooking to prevent green ring.',
        'yolk': 'Fully set, light yellow',
        'white': 'Fully set, firm'
    },
    'hardmax': {
        'base_time': 720,  # 12 minutes
        'description': 'Very hard-boiled (firm throughout)',
        'tip': 'For long storage. Transfer to ice bath immediately!',
        'yolk': 'Firm, may have slight grey-green ring',
        'white': 'Very firm'
    }
}


class TimeHandler(BaseCommandHandler):
    """Handler for time-related commands."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timedate_manager = get_timedate_manager()
        
        # Timer state
        self.active_timer = None
        self.timer_thread = None
        self.timer_label = None  # Description for active timer
        
        # Stopwatch state
        self.stopwatch_start = None
        self.stopwatch_laps = []
        self.stopwatch_running = False
    
    def handle(self, command: str, params: List[str], grid=None) -> str:
        """
        Handle TIME commands.
        
        Args:
            command: Command name
            params: Command parameters
            grid: Optional grid instance
            
        Returns:
            Command result
        """
        cmd = command.upper()
        
        if cmd == 'CLOCK':
            return self._handle_clock(params)
        elif cmd == 'TIMER':
            return self._handle_timer(params)
        elif cmd == 'EGG':
            # EGG is an alias for TIMER EGG
            return self._handle_timer(['EGG'] + params)
        elif cmd == 'STOPWATCH':
            return self._handle_stopwatch(params)
        elif cmd == 'CALENDAR':
            return self._handle_calendar(params)
        elif cmd == 'TIME':
            # General TIME command - show current time
            return self._handle_time(params)
        else:
            return f"Unknown time command: {cmd}"
    
    def _handle_time(self, params: List[str]) -> str:
        """Handle TIME command - show current time."""
        if not params:
            # Show current time in current timezone
            tz_info = self.timedate_manager.get_time_info()
            time_str = self.timedate_manager.get_current_time()
            
            output = [f"\n🕐 Current Time"]
            output.append(f"   {time_str}")
            output.append(f"   {tz_info.name} ({tz_info.abbreviation} {tz_info.offset})")
            
            if tz_info.city:
                output.append(f"   📍 {tz_info.city}")
            
            if tz_info.tile:
                output.append(f"   🗺️  TILE {tz_info.tile}")
            
            return "\n".join(output)
        
        subcommand = params[0].upper()
        
        if subcommand == 'SET':
            # Set timezone
            if len(params) < 2:
                return "Usage: TIME SET <timezone|city>"
            
            tz_name = ' '.join(params[1:])
            if self.timedate_manager.set_timezone(tz_name):
                tz_info = self.timedate_manager.get_time_info()
                return f"✅ Timezone set to: {tz_info.name} ({tz_info.abbreviation})"
            else:
                return f"❌ Unknown timezone or city: {tz_name}"
        
        elif subcommand == 'ADD':
            # Add tracked timezone
            if len(params) < 2:
                return "Usage: TIME ADD <timezone|city>"
            
            tz_name = ' '.join(params[1:])
            if self.timedate_manager.add_tracked_zone(tz_name):
                return f"✅ Added to tracked zones: {tz_name}"
            else:
                return f"❌ Failed to add timezone: {tz_name}"
        
        elif subcommand == 'REMOVE':
            # Remove tracked timezone
            if len(params) < 2:
                return "Usage: TIME REMOVE <timezone>"
            
            tz_name = ' '.join(params[1:])
            if self.timedate_manager.remove_tracked_zone(tz_name):
                return f"✅ Removed from tracked zones: {tz_name}"
            else:
                return f"❌ Timezone not in tracked list: {tz_name}"
        
        elif subcommand == 'LIST':
            # List tracked timezones
            times = self.timedate_manager.get_multiple_times()
            
            if not times:
                return "No tracked timezones"
            
            output = ["\n🌍 Tracked Timezones"]
            output.append("=" * 60)
            
            for tz_info, time_str in times:
                output.append(f"{time_str}  {tz_info.name} ({tz_info.abbreviation})")
                if tz_info.city:
                    output.append(f"         📍 {tz_info.city}")
            
            return "\n".join(output)
        
        else:
            return f"Unknown TIME subcommand: {subcommand}\nUse: TIME SET|ADD|REMOVE|LIST"
    
    def _handle_clock(self, params: List[str]) -> str:
        """Handle CLOCK command - ASCII 7-segment display."""
        # Get time to display
        if params and params[0].upper() != 'MULTI':
            # Specific timezone
            tz_name = ' '.join(params)
            time_str = self.timedate_manager.get_current_time(tz_name, "%H:%M:%S")
            tz_info = self.timedate_manager.get_time_info(tz_name)
        else:
            # Current timezone
            time_str = self.timedate_manager.get_current_time(None, "%H:%M:%S")
            tz_info = self.timedate_manager.get_time_info()
        
        # ASCII 7-segment display
        clock_display = self._render_7segment(time_str)
        
        output = ["\n" + clock_display]
        output.append(f"\n{tz_info.name} ({tz_info.abbreviation} {tz_info.offset})")
        
        if params and params[0].upper() == 'MULTI':
            # Show multiple timezones
            output.append("\n🌍 Other Timezones:")
            times = self.timedate_manager.get_multiple_times()
            for tz_info, time_str in times:
                output.append(f"  {time_str}  {tz_info.abbreviation}")
        
        return "\n".join(output)
    
    def _render_7segment(self, time_str: str, large: bool = False) -> str:
        """
        Render time in ASCII display.
        
        Args:
            time_str: Time string (e.g., "12:34:56" or "05:30")
            large: Use large 7-line digits (True) or small 5-line (False)
            
        Returns:
            Multi-line ASCII art string
        """
        if large:
            # Use large LARGE_DIGITS (7 lines tall)
            num_lines = 7
            char_width = 7  # 6 chars + 1 space
            
            lines = ['' for _ in range(num_lines)]
            for char in time_str:
                if char in LARGE_DIGITS:
                    digit_lines = LARGE_DIGITS[char]
                    for i in range(num_lines):
                        lines[i] += digit_lines[i] + ' '
                else:
                    # Unknown character - add spaces
                    for i in range(num_lines):
                        lines[i] += '      ' + ' '
            
            return '\n'.join(lines)
        
        else:
            # Original small 5-line digits
            digits = {
                '0': [' ▄▄▄ ', '█   █', '█   █', '█   █', ' ▀▀▀ '],
                '1': ['  █  ', ' ██  ', '  █  ', '  █  ', ' ███ '],
                '2': [' ▄▄▄ ', '    █', ' ▄▄▄ ', '█    ', ' ▀▀▀▀'],
                '3': [' ▄▄▄ ', '    █', '  ▄▄ ', '    █', ' ▀▀▀ '],
                '4': ['█   █', '█   █', ' ▀▀▀█', '    █', '    █'],
                '5': [' ▄▄▄▄', '█    ', ' ▀▀▀ ', '    █', ' ▀▀▀ '],
                '6': [' ▄▄▄ ', '█    ', '█▄▄▄ ', '█   █', ' ▀▀▀ '],
                '7': [' ▀▀▀▀', '    █', '   █ ', '  █  ', ' █   '],
                '8': [' ▄▄▄ ', '█   █', ' ▄▄▄ ', '█   █', ' ▀▀▀ '],
                '9': [' ▄▄▄ ', '█   █', ' ▀▀▀█', '    █', ' ▀▀▀ '],
                ':': ['     ', '  •  ', '     ', '  •  ', '     ']
            }
            
            # Build display line by line
            lines = ['', '', '', '', '']
            for char in time_str:
                if char in digits:
                    digit_lines = digits[char]
                    for i in range(5):
                        lines[i] += digit_lines[i] + ' '
            
            return '\n'.join(lines)
    
    def _render_large_countdown(self, seconds: int, label: str = "") -> str:
        """
        Render a large ASCII countdown display.
        
        Args:
            seconds: Remaining seconds
            label: Optional label to display above
            
        Returns:
            Multi-line ASCII art string with countdown
        """
        # Format as MM:SS or HH:MM:SS
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            minutes = seconds // 60
            secs = seconds % 60
            time_str = f"{minutes:02d}:{secs:02d}"
        
        # Build the display
        display = self._render_7segment(time_str, large=True)
        
        output = []
        if label:
            output.append(f"  {label}")
            output.append("")
        output.append(display)
        
        return '\n'.join(output)
    
    def _handle_timer(self, params: List[str]) -> str:
        """Handle TIMER command - countdown timer with EGG preset."""
        if not params:
            return ("Usage: TIMER <duration>|EGG [options]\n"
                   "Examples:\n"
                   "  TIMER 5m              - 5 minute timer\n"
                   "  TIMER 1h 30m          - 1 hour 30 minutes\n"
                   "  TIMER 2:30:00         - 2 hours 30 minutes (HH:MM:SS)\n"
                   "  TIMER EGG soft        - Soft-boiled egg timer\n"
                   "  TIMER EGG jammy       - Ramen-style jammy egg\n"
                   "  TIMER STOP            - Stop active timer\n"
                   "  TIMER STATUS          - Check timer status with ASCII display\n"
                   "  TIMER SHOW            - Show large ASCII countdown\n\n"
                   "Egg Types: soft|mollet|jammy|medium|hard|hardmax\n"
                   "Egg Options: --eggs N, --fridge, --cold, --altitude M")
        
        subcommand = params[0].upper()
        
        if subcommand == 'STOP':
            if self.active_timer:
                label = self.timer_label or ""
                self.active_timer = None
                self.timer_label = None
                return f"⏹️  Timer stopped{': ' + label if label else ''}"
            else:
                return "No active timer"
        
        elif subcommand == 'EGG':
            # Delegate to egg handler with remaining params
            return self._handle_egg(params[1:])
        
        elif subcommand in ['STATUS', 'SHOW']:
            if self.active_timer:
                remaining = self.active_timer - time.time()
                if remaining > 0:
                    # Show large countdown display
                    label = self.timer_label or "⏱️  Timer"
                    countdown_display = self._render_large_countdown(int(remaining), label)
                    duration_str = self.timedate_manager.format_duration(int(remaining))
                    
                    return f"\n{countdown_display}\n\n  {duration_str} remaining"
                else:
                    self.active_timer = None
                    return "⏰ Timer expired!"
            else:
                return "No active timer"
        
        else:
            # Start timer
            duration_str = ' '.join(params)
            seconds = self.timedate_manager.parse_duration(duration_str)
            
            if not seconds:
                return f"❌ Invalid duration: {duration_str}"
            
            # Start timer
            self.active_timer = time.time() + seconds
            duration_display = self.timedate_manager.format_duration(seconds)
            
            return (f"⏱️  Timer started: {duration_display}\n"
                   f"Use: TIMER STATUS to check\n"
                   f"Use: TIMER STOP to cancel")
    
    def _calculate_egg_time(self, egg_type: str, num_eggs: int = 1, 
                             cold_start: bool = False, fridge_cold: bool = False,
                             altitude_m: int = 0) -> Tuple[int, Dict]:
        """
        Calculate egg cooking time based on science.
        
        Args:
            egg_type: Type of egg (soft, mollet, jammy, medium, hard, hardmax)
            num_eggs: Number of eggs (affects water temp recovery)
            cold_start: Start with cold water (vs rolling boil)
            fridge_cold: Eggs from fridge (vs room temperature)
            altitude_m: Altitude in meters (affects boiling point)
            
        Returns:
            (total_seconds, info_dict)
        """
        if egg_type not in EGG_SCIENCE:
            return 0, {}
        
        base = EGG_SCIENCE[egg_type]['base_time']
        adjustments = []
        
        # 1. Fridge-cold eggs need longer (heat must penetrate cold egg)
        if fridge_cold:
            # Add ~1 minute for fridge-cold eggs
            base += 60
            adjustments.append("+1m (fridge-cold eggs)")
        
        # 2. Multiple eggs - water temp drops, recovery time needed
        if num_eggs > 4:
            # Add 30 seconds per 4 eggs over the first 4
            extra = ((num_eggs - 4) // 4 + 1) * 30
            base += extra
            adjustments.append(f"+{extra}s (batch size: {num_eggs} eggs)")
        
        # 3. Cold start - gradual heating vs sudden boil (gentler)
        if cold_start:
            # Cold start method: eggs go in cold water, bring to boil, cover, remove from heat
            # This is actually a different technique - timing from boil reached
            base += 180  # 3 extra minutes to account for heating
            adjustments.append("+3m (cold start method)")
        
        # 4. Altitude adjustment (boiling point drops ~1°C per 300m)
        if altitude_m > 500:
            # Lower boiling temp = longer cooking
            # Roughly +10% per 1000m above sea level
            altitude_factor = 1 + (altitude_m / 10000)
            adjustment = int(base * (altitude_factor - 1))
            base += adjustment
            adjustments.append(f"+{adjustment}s (altitude: {altitude_m}m)")
        
        return base, {
            'type': egg_type,
            'num_eggs': num_eggs,
            'cold_start': cold_start,
            'fridge_cold': fridge_cold,
            'altitude': altitude_m,
            'adjustments': adjustments,
            'info': EGG_SCIENCE[egg_type]
        }
    
    def _handle_egg(self, params: List[str]) -> str:
        """
        Handle EGG command - science-based egg timer with story.
        
        Supports options:
            EGG soft|mollet|jammy|medium|hard|hardmax
            EGG soft --eggs 6 --cold --fridge --altitude 1500
            EGG STORY  - Show the Perfect Egg story guide
        """
        if not params:
            return self._egg_help()
        
        # Check for STORY subcommand
        if params[0].upper() == 'STORY':
            return self._egg_story()
        
        # Parse parameters
        egg_type = params[0].lower()
        
        if egg_type not in EGG_SCIENCE and egg_type not in ['help', 'science', 'types']:
            return f"❌ Unknown egg type: {egg_type}\n\n" + self._egg_help()
        
        if egg_type in ['help', 'types']:
            return self._egg_help()
        
        if egg_type == 'science':
            return self._egg_science_info()
        
        # Parse options
        num_eggs = 1
        cold_start = False
        fridge_cold = False
        altitude_m = 0
        
        i = 1
        while i < len(params):
            param = params[i].lower()
            if param in ['--eggs', '-n'] and i + 1 < len(params):
                try:
                    num_eggs = int(params[i + 1])
                    i += 2
                except ValueError:
                    i += 1
            elif param in ['--cold', '-c']:
                cold_start = True
                i += 1
            elif param in ['--fridge', '-f']:
                fridge_cold = True
                i += 1
            elif param in ['--altitude', '-a'] and i + 1 < len(params):
                try:
                    altitude_m = int(params[i + 1])
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1
        
        # Calculate time
        seconds, info = self._calculate_egg_time(
            egg_type, num_eggs, cold_start, fridge_cold, altitude_m
        )
        
        if not seconds:
            return f"❌ Could not calculate time for: {egg_type}"
        
        # Start timer
        self.active_timer = time.time() + seconds
        self.timer_label = f"🥚 {info['info']['description']}"
        
        # Format duration
        minutes = seconds // 60
        secs = seconds % 60
        duration_str = f"{minutes}m {secs}s" if secs else f"{minutes}m"
        
        # Build output with ASCII countdown preview
        output = [
            "",
            "╔════════════════════════════════════════════════════════════╗",
            "║                    🥚 THE PERFECT EGG 🥚                    ║",
            "╠════════════════════════════════════════════════════════════╣",
        ]
        
        # Show settings
        output.append(f"║  Style: {info['info']['description']:<47} ║")
        output.append(f"║  Eggs:  {num_eggs} egg{'s' if num_eggs > 1 else '':<48} ║")
        output.append(f"║  Time:  {duration_str:<48} ║")
        output.append("╠════════════════════════════════════════════════════════════╣")
        
        # Show the yolk and white status
        output.append(f"║  Yolk:  {info['info']['yolk']:<48} ║")
        output.append(f"║  White: {info['info']['white']:<48} ║")
        output.append("╠════════════════════════════════════════════════════════════╣")
        
        # Show adjustments if any
        if info['adjustments']:
            output.append("║  Adjustments:                                              ║")
            for adj in info['adjustments']:
                output.append(f"║    • {adj:<52} ║")
            output.append("╠════════════════════════════════════════════════════════════╣")
        
        # Tip
        output.append(f"║  💡 {info['info']['tip']:<53} ║")
        output.append("╠════════════════════════════════════════════════════════════╣")
        
        # Important instructions
        output.append("║  📋 INSTRUCTIONS:                                          ║")
        if fridge_cold:
            output.append("║    1. Remove eggs from fridge (cold start OK)             ║")
        else:
            output.append("║    1. Bring eggs to room temperature (20 min ideal)      ║")
        
        if cold_start:
            output.append("║    2. Place eggs in cold water, bring to boil            ║")
            output.append("║    3. Once boiling, timer starts - cover & remove heat   ║")
        else:
            output.append("║    2. Bring water to rolling boil first                  ║")
            output.append("║    3. Gently lower eggs with slotted spoon               ║")
        
        output.append("║    4. Prepare ice bath while eggs cook                    ║")
        output.append("║    5. Transfer to ice bath immediately when done          ║")
        output.append("║    6. Cool for 5 minutes before peeling                   ║")
        output.append("╚════════════════════════════════════════════════════════════╝")
        
        output.append("")
        output.append("  ⏱️  TIMER STARTED!")
        output.append("  Use: TIMER STATUS - Show countdown with large display")
        output.append("  Use: TIMER STOP   - Cancel timer")
        
        return '\n'.join(output)
    
    def _egg_help(self) -> str:
        """Return egg timer help text."""
        return """
🥚 EGG TIMER - Science-Based Perfect Eggs

Usage: EGG <type> [options]

Types:
  soft     - 4.5 min  (runny yolk, set white - for toast soldiers!)
  mollet   - 5.5 min  (French style, creamy throughout)
  jammy    - 6.5 min  (ramen-style, jammy center)
  medium   - 8 min    (mostly set, slight translucence)
  hard     - 10 min   (fully set, light yellow yolk)
  hardmax  - 12 min   (very firm, for storage)

Options:
  --eggs N, -n N      Number of eggs (affects timing for batches)
  --cold, -c          Cold start method (eggs in cold water)
  --fridge, -f        Eggs are fridge-cold (not room temp)
  --altitude M, -a M  Altitude in meters (affects boiling point)

Examples:
  EGG soft                        - Basic soft-boiled
  EGG jammy --eggs 6 --fridge     - Batch of 6 ramen eggs
  EGG hard -n 12 -f -a 1600       - Dozen eggs at altitude

Commands:
  EGG STORY    - The story of the perfect egg (cooking science)
  EGG SCIENCE  - Detailed explanation of timing factors
  EGG TYPES    - List all egg types with details
"""
    
    def _egg_story(self) -> str:
        """Return the egg story - a narrative guide to perfect eggs."""
        return """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🥚 THE STORY OF THE PERFECT EGG 🥚                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

    "The egg is to cuisine what the article is to speech."
                                        — Anonymous French Chef

┌──────────────────────────────────────────────────────────────────────────────┐
│  CHAPTER 1: THE SCIENCE OF THE EGG                                           │
└──────────────────────────────────────────────────────────────────────────────┘

An egg is a marvel of nature's engineering. The white (albumen) sets at 
around 80°C (176°F), while the yolk begins to thicken at 65°C (149°F) and 
becomes fully solid around 70°C (158°F).

This temperature difference is your secret weapon. By controlling time and 
temperature, you can achieve any texture from liquid gold to firm bouncy.

┌──────────────────────────────────────────────────────────────────────────────┐
│  CHAPTER 2: PREPARATION IS EVERYTHING                                        │
└──────────────────────────────────────────────────────────────────────────────┘

🌡️  ROOM TEMPERATURE: The Great Equalizer
    Eggs straight from the fridge are around 4°C. Room temperature eggs 
    are about 20°C. This 16-degree difference matters!
    
    • Fridge-cold eggs take longer to cook (the math is in the timer)
    • Cold eggs dropped into boiling water may crack from thermal shock
    • Let eggs sit out 20-30 minutes, or run under warm water for 5 min

🥣  THE WATER: Your Cooking Medium  
    • Use enough water to cover eggs by at least 2cm (1 inch)
    • Add a splash of vinegar (helps seal cracks)
    • A pinch of salt raises the boiling point slightly
    • A rolling boil is 100°C at sea level

┌──────────────────────────────────────────────────────────────────────────────┐
│  CHAPTER 3: TWO METHODS, ONE GOAL                                            │
└──────────────────────────────────────────────────────────────────────────────┘

⚡ THE BOILING WATER METHOD (Recommended for precision)
    1. Bring water to a rolling boil
    2. Lower eggs gently with a slotted spoon or spider
    3. Start timer immediately
    4. Maintain a gentle boil
    5. Transfer to ice bath at the exact moment

❄️  THE COLD START METHOD (Gentler, but less precise)
    1. Place eggs in cold water
    2. Bring to a boil
    3. Cover, remove from heat
    4. Let sit for the required time
    5. Transfer to ice bath

┌──────────────────────────────────────────────────────────────────────────────┐
│  CHAPTER 4: THE ICE BATH - DON'T SKIP THIS!                                  │
└──────────────────────────────────────────────────────────────────────────────┘

The ice bath is NOT optional. Here's why:

🛑 CARRYOVER COOKING: Eggs continue cooking even after removal from water.
   The residual heat in the egg can push a perfect jammy yolk to hard-boiled.

🛑 THE GREEN RING: That grey-green ring around overcooked yolks? That's iron
   sulfide, formed when the iron in the yolk reacts with hydrogen sulfide
   from the overheated white. The ice bath stops this reaction.

💧 ICE BATH TECHNIQUE:
    • Use equal parts ice and water
    • Submerge eggs for at least 5 minutes
    • This also makes peeling MUCH easier

┌──────────────────────────────────────────────────────────────────────────────┐
│  CHAPTER 5: THE PERFECT PEEL                                                 │
└──────────────────────────────────────────────────────────────────────────────┘

Fresh eggs are notoriously hard to peel. The science:

• Fresh eggs have a lower pH (more acidic), causing the whites to stick
• Older eggs (1-2 weeks) have a higher pH, peeling cleanly
• The ice bath helps the egg contract away from the shell

PEELING TIPS:
    1. Tap the wider end first (that's where the air pocket is)
    2. Roll gently on the counter to crack all over
    3. Peel under running water
    4. Start from the wider end where the air pocket creates a gap

┌──────────────────────────────────────────────────────────────────────────────┐
│  CHAPTER 6: ALTITUDE & OTHER VARIABLES                                       │
└──────────────────────────────────────────────────────────────────────────────┘

🏔️  ALTITUDE: Water boils at lower temperatures at higher altitudes
    • Sea level: 100°C (212°F)
    • 1,500m (5,000ft): ~95°C (203°F)  
    • 3,000m (10,000ft): ~90°C (194°F)
    
    Lower boiling point = longer cooking time. The timer adjusts for this!

📊 EGG SIZE: These timings assume large eggs (~60g)
    • Medium eggs: subtract 30 seconds
    • Extra-large eggs: add 30 seconds

🔥 HEAT SOURCE: Gas vs electric vs induction all heat differently
    • Use a timer, not intuition
    • Maintain consistent heat (gentle boil, not rolling)

┌──────────────────────────────────────────────────────────────────────────────┐
│  EPILOGUE: MASTERY THROUGH PRACTICE                                          │
└──────────────────────────────────────────────────────────────────────────────┘

The perfect egg is a personal preference. Some love a completely liquid yolk 
for dipping; others prefer a yolk that holds its shape on a salad. 

Use these times as a starting point, then adjust to your taste. Keep notes. 
The perfect egg for YOU might be 6 minutes and 20 seconds—and that's valid.

    "An egg is always an adventure; the next one may be different."
                                        — Oscar Wilde (probably not, but it should be)

══════════════════════════════════════════════════════════════════════════════
  Use: EGG <type>       - Start a timer (soft|mollet|jammy|medium|hard)
  Use: EGG SCIENCE      - Detailed timing breakdown
  Use: TIMER STATUS     - Check your egg timer
══════════════════════════════════════════════════════════════════════════════
"""
    
    def _egg_science_info(self) -> str:
        """Return detailed egg cooking science."""
        output = [
            "",
            "🔬 EGG COOKING SCIENCE",
            "=" * 60,
            "",
            "BASE TIMES (room temperature eggs, rolling boil, sea level):",
            ""
        ]
        
        for egg_type, info in EGG_SCIENCE.items():
            minutes = info['base_time'] // 60
            secs = info['base_time'] % 60
            time_str = f"{minutes}:{secs:02d}"
            output.append(f"  {egg_type.upper():<8} {time_str:<6}  {info['description']}")
            output.append(f"           Yolk: {info['yolk']}")
            output.append(f"           White: {info['white']}")
            output.append("")
        
        output.extend([
            "ADJUSTMENT FACTORS:",
            "",
            "  Fridge-cold eggs:    +1 minute",
            "  Batch (5+ eggs):     +30 seconds per 4 eggs",
            "  Cold start method:   +3 minutes (from boil)",
            "  Altitude 1000m+:     +10% per 1000m",
            "",
            "TEMPERATURES:",
            "",
            "  White sets:          ~80°C (176°F)",
            "  Yolk thickens:       ~65°C (149°F)", 
            "  Yolk solid:          ~70°C (158°F)",
            "  Rolling boil:        100°C at sea level",
            ""
        ])
        
        return '\n'.join(output)
    
    def _handle_stopwatch(self, params: List[str]) -> str:
        """Handle STOPWATCH command - lap timer."""
        if not params:
            return ("Usage: STOPWATCH <start|stop|lap|reset>\n\n"
                   "Commands:\n"
                   "  start  - Start/resume stopwatch\n"
                   "  stop   - Stop stopwatch\n"
                   "  lap    - Record lap time\n"
                   "  reset  - Reset stopwatch")
        
        subcommand = params[0].upper()
        
        if subcommand == 'START':
            if not self.stopwatch_running:
                if self.stopwatch_start is None:
                    self.stopwatch_start = time.time()
                    self.stopwatch_laps = []
                else:
                    # Resume
                    pass
                self.stopwatch_running = True
                return "⏱️  Stopwatch started"
            else:
                return "⏱️  Stopwatch already running"
        
        elif subcommand == 'STOP':
            if self.stopwatch_running:
                self.stopwatch_running = False
                elapsed = time.time() - self.stopwatch_start
                duration_str = self.timedate_manager.format_duration(int(elapsed))
                return f"⏹️  Stopwatch stopped: {duration_str}"
            else:
                return "Stopwatch not running"
        
        elif subcommand == 'LAP':
            if self.stopwatch_running:
                elapsed = time.time() - self.stopwatch_start
                self.stopwatch_laps.append(elapsed)
                lap_num = len(self.stopwatch_laps)
                lap_time = self.timedate_manager.format_duration(int(elapsed))
                return f"🏁 Lap {lap_num}: {lap_time}"
            else:
                return "❌ Stopwatch not running"
        
        elif subcommand == 'RESET':
            self.stopwatch_start = None
            self.stopwatch_laps = []
            self.stopwatch_running = False
            return "✅ Stopwatch reset"
        
        else:
            # Show status
            if self.stopwatch_start:
                elapsed = time.time() - self.stopwatch_start
                duration_str = self.timedate_manager.format_duration(int(elapsed))
                
                output = [f"\n⏱️  Stopwatch: {duration_str}"]
                output.append(f"Status: {'Running' if self.stopwatch_running else 'Stopped'}")
                
                if self.stopwatch_laps:
                    output.append(f"\n🏁 Laps ({len(self.stopwatch_laps)}):")
                    for i, lap_time in enumerate(self.stopwatch_laps, 1):
                        lap_str = self.timedate_manager.format_duration(int(lap_time))
                        output.append(f"  {i}. {lap_str}")
                
                return "\n".join(output)
            else:
                return "Stopwatch not started"
    
    def _handle_calendar(self, params: List[str]) -> str:
        """Handle CALENDAR command - month/year view."""
        # Parse parameters
        if params:
            try:
                if len(params) == 1:
                    # Year only
                    year = int(params[0])
                    month = datetime.now().month
                elif len(params) >= 2:
                    # Month and year
                    month = int(params[0])
                    year = int(params[1])
                else:
                    month = datetime.now().month
                    year = datetime.now().year
            except ValueError:
                return "❌ Invalid date format\nUsage: CALENDAR [month] [year]"
        else:
            # Current month
            now = datetime.now()
            month = now.month
            year = now.year
        
        # Validate month
        if month < 1 or month > 12:
            return f"❌ Invalid month: {month} (must be 1-12)"
        
        # Generate calendar
        cal = monthcalendar(year, month)
        month_str = month_name[month]
        
        # Build output
        output = [f"\n╔═══════════════════════════════════════╗"]
        output.append(f"║  {month_str} {year}".ljust(40) + "║")
        output.append(f"╠═══════════════════════════════════════╣")
        
        # Day headers
        day_headers = "  " + "  ".join([d[:2] for d in day_name])
        output.append(f"║ {day_headers}  ║")
        output.append(f"╠═══════════════════════════════════════╣")
        
        # Calendar weeks
        today = datetime.now()
        for week in cal:
            week_str = ""
            for day in week:
                if day == 0:
                    week_str += "   "
                else:
                    # Highlight today
                    if year == today.year and month == today.month and day == today.day:
                        week_str += f"[{day:2d}]"[:-1] if day < 10 else f"[{day}]"
                    else:
                        week_str += f" {day:2d}"
            output.append(f"║ {week_str}  ║")
        
        output.append(f"╚═══════════════════════════════════════╝")
        
        # Add timezone info
        tz_info = self.timedate_manager.get_time_info()
        time_str = self.timedate_manager.get_current_time(None, "%H:%M:%S")
        output.append(f"\n🕐 {time_str} {tz_info.abbreviation}")
        
        return "\n".join(output)


# Factory function
def create_time_handler(**kwargs):
    """Create TimeHandler instance."""
    return TimeHandler(**kwargs)
