"""
Terminal Loader Command Handler
Version: 2.4.0

Provides uPY-programmable splash loader control for Tauri extension.
Integrated with modular SplashLoader service for rich terminal animations.

Commands:
    LOADER START [preset]       - Start terminal loader with optional preset
    LOADER STOP                 - Stop and hide loader
    LOADER ANIMATE              - Run animated splash sequence
    LOADER STATIC               - Show static splash screen
    LOADER BACKGROUND <effect>  - Set background effect (rainbow-stripe, matrix, grid, wave, pulse)
    LOADER MESSAGE "<text>"     - Set scrolling message text
    LOADER INFOBOX "<text>"     - Set info box message
    LOADER DURATION <ms>        - Set loading duration in milliseconds
    LOADER PRESET <name>        - Load preset configuration (default, matrix, retro, minimal, nes)
    LOADER POINTER <on|off>     - Toggle NES-style pointer/glove cursor
    LOADER CONFIG               - Show current configuration
    LOADER TOAST <message>      - Show NES-styled toast notification

Examples:
    LOADER START matrix
    LOADER ANIMATE
    LOADER BACKGROUND grid
    LOADER MESSAGE "Loading uDOS System..."
    LOADER INFOBOX "INITIALIZING"
    LOADER DURATION 3000
    LOADER PRESET nes
    LOADER POINTER on
    LOADER TOAST "System Ready!"
"""

from dev.goblin.core.commands.base_handler import BaseCommandHandler
from dev.goblin.core.services.splash_loader import get_splash_loader, render_nes_toast
from pathlib import Path


class LoaderHandler(BaseCommandHandler):
    """Handle terminal loader configuration and control"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.splash_loader = get_splash_loader()
        
        # Load user preferences from user.json
        user_json = Path("memory/bank/user/user.json")
        if user_json.exists():
            self.splash_loader.load_user_config(user_json)
        
        self.current_config = {
            'backgroundEffect': 'rainbow-stripe',
            'showInfoBox': True,
            'infoBoxMessage': 'LOADING SYSTEM',
            'scrollText': 'uDOS v2.4.0 - Offline-First Survival OS',
            'logoBlock': 'U',
            'duration': 5000,
            'showNesPointer': True
        }

    def handle(self, command: str, params: list, grid, parser) -> dict:
        """Route LOADER subcommands"""
        if not params:
            return self._show_help()

        subcommand = params[0].upper()

        if subcommand == "START":
            preset = params[1] if len(params) > 1 else None
            return self._start_loader(preset)
        elif subcommand == "STOP":
            return self._stop_loader()
        elif subcommand == "ANIMATE":
            return self._animate_loader()
        elif subcommand == "STATIC":
            return self._static_splash()
        elif subcommand == "BACKGROUND":
            if len(params) < 2:
                return {"output": "Error: LOADER BACKGROUND requires effect name", "error": True}
            return self._set_background(params[1])
        elif subcommand == "MESSAGE":
            if len(params) < 2:
                return {"output": "Error: LOADER MESSAGE requires text", "error": True}
            message = ' '.join(params[1:]).strip('"\'')
            return self._set_message(message)
        elif subcommand == "INFOBOX":
            if len(params) < 2:
                return {"output": "Error: LOADER INFOBOX requires text", "error": True}
            text = ' '.join(params[1:]).strip('"\'')
            return self._set_infobox(text)
        elif subcommand == "DURATION":
            if len(params) < 2:
                return {"output": "Error: LOADER DURATION requires milliseconds", "error": True}
            try:
                duration = int(params[1])
                return self._set_duration(duration)
            except ValueError:
                return {"output": "Error: Duration must be a number", "error": True}
        elif subcommand == "PRESET":
            if len(params) < 2:
                return {"output": "Error: LOADER PRESET requires preset name", "error": True}
            return self._load_preset(params[1])
        elif subcommand == "POINTER":
            if len(params) < 2:
                return {"output": "Error: LOADER POINTER requires on|off", "error": True}
            return self._toggle_pointer(params[1])
        elif subcommand == "TOAST":
            if len(params) < 2:
                return {"output": "Error: LOADER TOAST requires message", "error": True}
            message = ' '.join(params[1:]).strip('"\'')
            style = params[2] if len(params) > 2 else "info"
            return self._show_toast(message, style)
        elif subcommand == "CONFIG":
            return self._show_config()
        else:
            return self._show_help()

    def _start_loader(self, preset: str = None) -> dict:
        """Start terminal loader"""
        if preset:
            self._load_preset(preset)
        
        # Update splash loader config
        self.splash_loader.config.update({
            'background_effect': self.current_config.get('backgroundEffect', 'rainbow-stripe'),
            'show_info_box': self.current_config.get('showInfoBox', True),
            'info_box_message': self.current_config.get('infoBoxMessage', 'LOADING'),
            'scroll_text': self.current_config.get('scrollText', ''),
            'duration': self.current_config.get('duration', 5000),
            'show_nes_pointer': self.current_config.get('showNesPointer', False)
        })
        
        # Send command to Tauri extension
        command = {
            'type': 'loader_start',
            'config': self.current_config
        }
        
        return {
            "output": f"Terminal loader started{' with preset: ' + preset if preset else ''}",
            "tauri_command": command
        }

    def _stop_loader(self) -> dict:
        """Stop terminal loader"""
        self.splash_loader.stop_animation()
        return {
            "output": "Terminal loader stopped",
            "tauri_command": {'type': 'loader_stop'}
        }
    
    def _animate_loader(self) -> dict:
        """Run animated splash sequence"""
        try:
            duration = self.current_config.get('duration', 5000)
            self.splash_loader.animate_splash(duration)
            return {"output": "Animation complete"}
        except Exception as e:
            return {"output": f"Error running animation: {e}", "error": True}
    
    def _static_splash(self) -> dict:
        """Show static splash screen"""
        try:
            splash_output = self.splash_loader.render_static_splash()
            print(splash_output)
            return {"output": ""}
        except Exception as e:
            return {"output": f"Error rendering splash: {e}", "error": True}

    def _set_background(self, effect: str) -> dict:
        """Set background effect"""
        valid_effects = ['rainbow-stripe', 'matrix', 'grid', 'wave', 'pulse']
        if effect not in valid_effects:
            return {
                "output": f"Error: Invalid effect. Valid: {', '.join(valid_effects)}",
                "error": True
            }
        
        self.current_config['backgroundEffect'] = effect
        return {"output": f"Background effect set to: {effect}"}

    def _set_message(self, text: str) -> dict:
        """Set scrolling message text"""
        self.current_config['scrollText'] = text
        return {"output": f"Scroll message set to: {text}"}

    def _set_infobox(self, text: str) -> dict:
        """Set info box message"""
        self.current_config['infoBoxMessage'] = text
        return {"output": f"Info box message set to: {text}"}

    def _set_duration(self, duration: int) -> dict:
        """Set loading duration"""
        if duration < 500 or duration > 30000:
            return {
                "output": "Error: Duration must be between 500 and 30000ms",
                "error": True
            }
        
        self.current_config['duration'] = duration
        return {"output": f"Loading duration set to: {duration}ms"}

    def _load_preset(self, preset_name: str) -> dict:
        """Load preset configuration"""
        presets = {
            'default': {
                'backgroundEffect': 'rainbow-stripe',
                'infoBoxMessage': 'LOADING SYSTEM',
                'scrollText': 'uDOS v2.4.0 - Offline-First Survival OS',
                'showNesPointer': False
            },
            'matrix': {
                'backgroundEffect': 'matrix',
                'infoBoxMessage': 'INITIALIZING MATRIX',
                'scrollText': 'Wake up, Neo... The Matrix has you...',
                'showNesPointer': False
            },
            'retro': {
                'backgroundEffect': 'grid',
                'infoBoxMessage': 'BOOTING SYSTEM',
                'scrollText': 'uDOS - Your Offline Command Center',
                'showNesPointer': False
            },
            'minimal': {
                'backgroundEffect': 'pulse',
                'infoBoxMessage': 'LOADING',
                'scrollText': 'Please wait...',
                'showNesPointer': False
            },
            'nes': {
                'backgroundEffect': 'wave',
                'infoBoxMessage': '▶ START GAME',
                'scrollText': '☞ Press any button to continue ☜',
                'showNesPointer': True
            }
        }

        if preset_name not in presets:
            return {
                "output": f"Error: Unknown preset. Available: {', '.join(presets.keys())}",
                "error": True
            }

        self.current_config.update(presets[preset_name])
        return {"output": f"Loaded preset: {preset_name}"}

    def _toggle_pointer(self, state: str) -> dict:
        """Toggle NES-style pointer"""
        state_lower = state.lower()
        if state_lower not in ['on', 'off']:
            return {"output": "Error: State must be 'on' or 'off'", "error": True}
        
        enabled = state_lower == 'on'
        self.current_config['showNesPointer'] = enabled
        self.splash_loader.config['show_nes_pointer'] = enabled
        
        return {"output": f"NES pointer {'enabled' if enabled else 'disabled'}"}
    
    def _show_toast(self, message: str, style: str = "info") -> dict:
        """Show NES-styled toast notification"""
        try:
            toast = render_nes_toast(message, width=50, style=style)
            print(toast)
            return {"output": ""}
        except Exception as e:
            return {"output": f"Error showing toast: {e}", "error": True}

    def _show_config(self) -> dict:
        """Show current configuration"""
        output = [
            "╔═══════════════════════════════════════════════╗",
            "║       LOADER CONFIGURATION                    ║",
            "╠═══════════════════════════════════════════════╣",
            f"║ Background:    {self.current_config['backgroundEffect']:<28}║",
            f"║ Info Box:      {self.current_config['infoBoxMessage']:<28}║",
            f"║ Scroll Text:   {self.current_config['scrollText'][:25]:<28}║",
            f"║ Duration:      {self.current_config['duration']}ms{'':<23}║",
            f"║ Logo Block:    {self.current_config['logoBlock']:<28}║",
            f"║ NES Pointer:   {'ON' if self.current_config.get('showNesPointer') else 'OFF':<28}║",
            "╚═══════════════════════════════════════════════╝"
        ]
        return {"output": "\n".join(output)}

    def _show_help(self) -> dict:
        """Show loader command help"""
        help_text = """
╔═══════════════════════════════════════════════════════╗
║          TERMINAL LOADER COMMANDS                     ║
╠═══════════════════════════════════════════════════════╣
║ LOADER START [preset]       Start loader             ║
║ LOADER STOP                 Stop and hide loader     ║
║ LOADER ANIMATE              Run animated splash      ║
║ LOADER STATIC               Show static splash       ║
║ LOADER BACKGROUND <effect>  Set background effect    ║
║ LOADER MESSAGE "<text>"     Set scrolling message    ║
║ LOADER INFOBOX "<text>"     Set info box message     ║
║ LOADER DURATION <ms>        Set duration (500-30000) ║
║ LOADER PRESET <name>        Load preset              ║
║ LOADER POINTER <on|off>     Toggle NES pointer       ║
║ LOADER TOAST <message>      Show NES toast           ║
║ LOADER CONFIG               Show configuration       ║
╠═══════════════════════════════════════════════════════╣
║ Background Effects:                                   ║
║   • rainbow-stripe  Matrix style vertical stripes    ║
║   • matrix          Green falling characters         ║
║   • grid            Retro grid pattern               ║
║   • wave            Animated wave effect             ║
║   • pulse           Pulsing density blocks           ║
╠═══════════════════════════════════════════════════════╣
║ Presets:                                              ║
║   • default   Rainbow stripe with system info        ║
║   • matrix    Matrix-style loading screen            ║
║   • retro     Classic grid with boot message         ║
║   • minimal   Simple pulse animation                 ║
║   • nes       NES-style with pointer/glove cursor    ║
╠═══════════════════════════════════════════════════════╣
║ Examples:                                             ║
║   LOADER START nes                                    ║
║   LOADER ANIMATE                                      ║
║   LOADER BACKGROUND grid                              ║
║   LOADER MESSAGE "Loading uDOS System..."             ║
║   LOADER POINTER on                                   ║
║   LOADER TOAST "System Ready!"                        ║
╚═══════════════════════════════════════════════════════╝
"""
        return {"output": help_text.strip()}
