"""
Terminal MODE - Experimental ANSI/Escape Code Testing

Test terminal emulation, ANSI escape codes, and color schemes
"""

from typing import Dict, List


class TerminalRenderer:
    """Experimental terminal renderer"""
    
    # ANSI color codes
    COLORS = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
    }
    
    STYLES = {
        "bold": "1",
        "dim": "2",
        "italic": "3",
        "underline": "4",
        "blink": "5",
        "reverse": "7",
        "hidden": "8",
        "strikethrough": "9",
    }
    
    def list_schemes(self):
        """List available color schemes"""
        return [
            {"name": "default", "description": "Standard ANSI colors"},
            {"name": "solarized", "description": "Solarized Dark theme"},
            {"name": "nord", "description": "Nord theme"},
            {"name": "gruvbox", "description": "Gruvbox theme"},
            {"name": "dracula", "description": "Dracula theme"},
        ]
    
    def render(self, text: str, fg: str = "white", bg: str = None, style: str = None):
        """Render text with ANSI codes"""
        codes = []
        
        # Foreground color
        if fg in self.COLORS:
            codes.append(self.COLORS[fg])
        
        # Background color
        if bg and bg in self.COLORS:
            bg_code = str(int(self.COLORS[bg]) + 10)  # BG = FG + 10
            codes.append(bg_code)
        
        # Style
        if style and style in self.STYLES:
            codes.append(self.STYLES[style])
        
        if codes:
            ansi_text = f"\033[{';'.join(codes)}m{text}\033[0m"
        else:
            ansi_text = text
        
        return {
            "text": text,
            "ansi": ansi_text,
            "codes": codes,
            "fg": fg,
            "bg": bg,
            "style": style,
        }
    
    def test_capabilities(self):
        """Test terminal capabilities"""
        tests = []
        
        # Color test
        for color in self.COLORS:
            tests.append({
                "test": f"Color: {color}",
                "ansi": self.render(f"████ {color}", fg=color)["ansi"],
            })
        
        # Style test
        for style in self.STYLES:
            tests.append({
                "test": f"Style: {style}",
                "ansi": self.render(f"Sample {style} text", style=style)["ansi"],
            })
        
        return {"tests": tests, "total": len(tests)}
    
    def apply_scheme(self, text: str, scheme: str = "default"):
        """Apply color scheme to text"""
        schemes = {
            "solarized": {"fg": "cyan", "bg": "black"},
            "nord": {"fg": "blue", "bg": "black"},
            "gruvbox": {"fg": "yellow", "bg": "black"},
            "dracula": {"fg": "magenta", "bg": "black"},
            "default": {"fg": "white", "bg": None},
        }
        
        scheme_colors = schemes.get(scheme, schemes["default"])
        return self.render(text, **scheme_colors)
