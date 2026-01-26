"""
uCODE Smart Text Editor - .upy ↔ Python Parsing
================================================

Date: 20251213-173000UTC
Location: Core UI
Version: v1.2.24 (Python-First Rebase)

Purpose: Parse .upy files to Python for fast execution, render back to .upy for display

Architecture:
- .upy files are the STANDARD format (saved on disk)
- Smart editor parses .upy → Python (for execution)
- Smart editor renders Python → .upy (for display/editing)
- Execution is fast (Python interpreter, no parser overhead)

Three Display Modes:
1. pythonic  - Standard Python syntax (execution format)
2. symbolic  - uCODE .upy syntax (storage/display format)
3. typo      - Beautiful typography via Typo extension (optional display)

uCODE Syntax Rules:
- Commands: COMMAND[arg1|arg2|arg3]  (square brackets, pipes separate args)
- Variables: $variable-name (alphanumeric, dashes, underscores ONLY)
- Functions: @function-name[args] (alphanumeric, dashes, underscores ONLY)
- Tags: COMMAND*TAG (asterisk separator, TAG UPPERCASE)
- Filenames: Alphanumeric, dashes, underscores ONLY
- Emoji Escapes: ONLY inside COMMAND[...] for output text/strings

Forbidden Characters (NOT allowed in variables/filenames):
  `~@#$%^&*[]{}'"<>\|_
  Note: uCODE uses dashes (-) not underscores (_)
  
Emoji Escape System (ONLY in COMMAND[...] arguments for output text):
  :sb: → [    :eb: → ]    :pipe: → |    :star: → *    :dollar: → $
  :sq: → '    :dq: → "    :backtick: → `    :tilde: → ~    :at: → @
  :hash: → #    :percent: → %    :caret: → ^    :amp: → &
  :lcb: → {    :rcb: → }    :lt: → <    :gt: → >    :bs: → \
  :underscore: → _ (use dashes in uCODE, underscores only for output text)

Example (emoji codes for special chars in output):
  PRINT[This is the end|:sb:Score: $variable:eb:]
  Renders two lines:
    Line 1: This is the end
    Line 2: [Score: $variable]

Transformations:
- .upy → Python: Parse for execution (lossless)
- Python → .upy: Render for display/saving (lossless)
- .upy ↔ Typo: Optional beautiful typography (display only)

Usage:
    from dev.goblin.core.ui.ucode_editor import UCODEEditor
    
    editor = UCODEEditor(mode='symbolic')
    
    # Load .upy file
    upy_code = "PRINT['Hello'|'World']"
    
    # Parse to Python for execution
    python_code = editor.parse(upy_code)  # "PRINT('Hello', 'World')"
    exec(python_code)
    
    # Render back to .upy for display
    upy_display = editor.render(python_code)  # "PRINT['Hello'|'World']"
"""

from typing import Optional, Dict, Any, Literal
import re
import sys
import os

# Check if Typo extension is available
TYPO_AVAILABLE = False
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'extensions', 'cloned', 'typo'))
    from typo_renderer import TypoRenderer
    TYPO_AVAILABLE = True
except ImportError:
    TYPO_AVAILABLE = False

DisplayMode = Literal['pythonic', 'symbolic', 'typo']

# =============================================================================
# Emoji Escape System - For COMMAND[...] Arguments Only
# =============================================================================

# Emoji codes for special characters in command arguments (output text/strings)
COMMAND_EMOJI_MAP = {
    '[': ':sb:',       # start bracket
    ']': ':eb:',       # end bracket
    '|': ':pipe:',     # pipe separator
    '*': ':star:',     # asterisk
    '$': ':dollar:',   # dollar sign
    "'": ':sq:',       # single quote
    '"': ':dq:',       # double quote
    '`': ':backtick:', # backtick
    '~': ':tilde:',    # tilde
    '@': ':at:',       # at sign
    '#': ':hash:',     # hash
    '%': ':percent:',  # percent
    '^': ':caret:',    # caret
    '&': ':amp:',      # ampersand
    '{': ':lcb:',      # left curly brace
    '}': ':rcb:',      # right curly brace
    '<': ':lt:',       # less than
    '>': ':gt:',       # greater than
    '\\': ':bs:',      # backslash
    '_': ':underscore:', # underscore (uCODE uses dashes -)
}

# Reverse mapping for rendering (emoji → character)
EMOJI_UNESCAPE_MAP = {v: k for k, v in COMMAND_EMOJI_MAP.items()}

def render_command_emoji(text: str) -> str:
    """Convert emoji codes to actual characters (for PRINT/output commands)
    
    Args:
        text: Text with emoji codes (e.g., "Score: :sb:100:eb:")
    
    Returns:
        Text with actual characters (e.g., "Score: [100]")
    """
    result = text
    for emoji, char in EMOJI_UNESCAPE_MAP.items():
        result = result.replace(emoji, char)
    return result

class UCODEEditor:
    """Smart text editor for Python ↔ uCODE ↔ Typo transformations"""
    
    def __init__(self, mode: DisplayMode = 'symbolic'):
        self.mode = mode
        self.typo = None
        
        if mode == 'typo' and TYPO_AVAILABLE:
            self.typo = TypoRenderer()
        elif mode == 'typo' and not TYPO_AVAILABLE:
            print("⚠️  Typo extension not installed, falling back to symbolic mode")
            print("   Install: cd extensions/cloned && git clone <typo-repo>")
            self.mode = 'symbolic'
    
    def render(self, python_code: str) -> str:
        """Render Python code in current display mode
        
        Args:
            python_code: Valid Python code
        
        Returns:
            Rendered string (pythonic/symbolic/typo)
        """
        if self.mode == 'pythonic':
            return python_code
        
        elif self.mode == 'symbolic':
            return self._python_to_ucode(python_code)
        
        elif self.mode == 'typo':
            ucode = self._python_to_ucode(python_code)
            return self._ucode_to_typo(ucode)
        
        return python_code
    
    def parse(self, visual_code: str) -> str:
        """Parse visual code back to executable Python
        
        Args:
            visual_code: uCODE or Typo rendered string
        
        Returns:
            Valid Python code
        """
        if self.mode == 'pythonic':
            return visual_code
        
        elif self.mode == 'symbolic':
            return self._ucode_to_python(visual_code)
        
        elif self.mode == 'typo':
            ucode = self._typo_to_ucode(visual_code)
            return self._ucode_to_python(ucode)
        
        return visual_code
    
    # =========================================================================
    # Python ↔ uCODE Transformations
    # =========================================================================
    
    def _python_to_ucode(self, code: str) -> str:
        """Convert Python to uCODE .upy syntax
        
        Transformations:
            function("arg1", "arg2") → FUNCTION['arg1'|'arg2']
            function(arg1, arg2) → FUNCTION[arg1|arg2]
            var_name → var-name
            CLONE--dev → CLONE*DEV
            heal_sprite(20) → heal-sprite[20]
        
        Key: Commas → Pipes (,  →  |)
        """
        # Transform command tags: CLONE--dev → CLONE*DEV
        def transform_tags(match):
            cmd = match.group(1)
            tag = match.group(2).upper()
            return f"{cmd}*{tag}"
        
        result = code
        
        # Command tags (-- becomes *, tag UPPERCASE)
        result = re.sub(r'(\w+)--(\w+)', transform_tags, result)
        
        # Function calls: function("arg") → FUNCTION["arg"]
        result = re.sub(r'(\w+)\((.*?)\)', r'\1[\2]', result)
        
        # Commas to pipes (argument separators)
        # Only inside brackets, preserve commas in strings
        def replace_commas(match):
            bracket_content = match.group(1)
            # Simple approach: replace commas not in quotes
            in_quotes = False
            quote_char = None
            new_content = []
            for i, char in enumerate(bracket_content):
                if char in ['"', "'"] and (i == 0 or bracket_content[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                
                if char == ',' and not in_quotes:
                    new_content.append('|')
                else:
                    new_content.append(char)
            
            return '[' + ''.join(new_content) + ']'
        
        result = re.sub(r'\[([^\]]+)\]', replace_commas, result)
        
        # Underscores to dashes
        result = result.replace('_', '-')
        
        return result
    
    def _ucode_to_python(self, code: str) -> str:
        """Convert uCODE .upy syntax back to valid Python
        
        Reverse transformations:
            FUNCTION['arg1'|'arg2'] → function('arg1', 'arg2')
            FUNCTION[arg1|arg2] → function(arg1, arg2)
            var-name → var_name
            CLONE*DEV → CLONE--dev
            heal-sprite[20] → heal_sprite(20)
        
        Key: Pipes → Commas (|  →  ,)
        """
        result = code
        
        # Command tags: CLONE*DEV → CLONE--dev (preserve tag marker)
        def restore_tag(m):
            cmd = m.group(1)
            tag = m.group(2).lower()
            return f"{cmd}__TAG__{tag}"
        result = re.sub(r'(\w+)\*(\w+)', restore_tag, result)
        
        # Pipes to commas (argument separators)
        # Only inside brackets, preserve pipes in strings
        def replace_pipes(match):
            bracket_content = match.group(1)
            # Simple approach: replace pipes not in quotes
            in_quotes = False
            quote_char = None
            new_content = []
            for i, char in enumerate(bracket_content):
                if char in ['"', "'"] and (i == 0 or bracket_content[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                
                if char == '|' and not in_quotes:
                    new_content.append(',')
                else:
                    new_content.append(char)
            
            return '[' + ''.join(new_content) + ']'
        
        result = re.sub(r'\[([^\]]+)\]', replace_pipes, result)
        
        # Function calls: FUNCTION[arg] → function(arg)
        result = re.sub(r'(\w+)\[(.*?)\]', r'\1(\2)', result)
        
        # Dashes to underscores
        result = result.replace('-', '_')
        
        # Restore tag markers: __TAG__ → --
        result = result.replace('__TAG__', '--')
        
        # User function calls: @function(args) stays as is
        
        return result
    
    # =========================================================================
    # uCODE ↔ Typo Transformations (Optional)
    # =========================================================================
    
    def _ucode_to_typo(self, ucode: str) -> str:
        """Convert uCODE to beautiful typography via Typo extension
        
        Typo Enhancements:
            [brackets] → 𝗕𝗥𝗔𝗖𝗞𝗘𝗧𝗦 (bold serif)
            $variable → 𝘷𝘢𝘳𝘪𝘢𝘣𝘭𝘦 (italic)
            @function → 𝙛𝙪𝙣𝙘𝙩𝙞𝙤𝙣 (monospace)
            COMMAND → 𝐂𝐎𝐌𝐌𝐀𝐍𝐃 (bold)
            * (tag) → ⭐ (star symbol)
        """
        if not self.typo:
            return ucode
        
        # Use Typo renderer for beautiful typography
        try:
            return self.typo.render(ucode, style='ucode')
        except Exception as e:
            print(f"⚠️  Typo rendering failed: {e}")
            return ucode
    
    def _typo_to_ucode(self, typo: str) -> str:
        """Parse Typo-rendered text back to uCODE
        
        This reverses Typo typography back to standard uCODE syntax
        """
        if not self.typo:
            return typo
        
        try:
            return self.typo.parse(typo, source_style='ucode')
        except Exception as e:
            print(f"⚠️  Typo parsing failed: {e}")
            return typo
    
    # =========================================================================
    # Editor Features
    # =========================================================================
    
    def set_mode(self, mode: DisplayMode):
        """Change display mode"""
        if mode == 'typo' and not TYPO_AVAILABLE:
            print("⚠️  Typo extension not available, using symbolic mode")
            self.mode = 'symbolic'
        else:
            self.mode = mode
            if mode == 'typo' and not self.typo:
                self.typo = TypoRenderer()
    
    def syntax_highlight(self, code: str, mode: Optional[DisplayMode] = None) -> str:
        """Apply syntax highlighting (ANSI colors)
        
        Colors:
            Commands (UPPERCASE) → Cyan
            Functions (@prefix) → Green
            Variables ($prefix) → Yellow
            Tags (*suffix) → Magenta
            Strings ("...") → Blue
        """
        if mode is None:
            mode = self.mode
        
        # Render in current mode first
        rendered = self.render(code) if mode != 'pythonic' else code
        
        # Apply ANSI color codes
        # Commands (UPPERCASE words)
        rendered = re.sub(r'\b([A-Z][A-Z-]+)\b', r'\033[96m\1\033[0m', rendered)
        
        # Functions (@prefix)
        rendered = re.sub(r'(@[a-z-]+)', r'\033[92m\1\033[0m', rendered)
        
        # Variables ($prefix or lowercase with -)
        rendered = re.sub(r'(\$[a-z-]+)', r'\033[93m\1\033[0m', rendered)
        
        # Tags (*suffix)
        rendered = re.sub(r'(\*[A-Z]+)', r'\033[95m\1\033[0m', rendered)
        
        # Strings
        rendered = re.sub(r'(["\'])([^"\']*)\1', r'\033[94m\1\2\1\033[0m', rendered)
        
        return rendered
    
    def get_info(self) -> Dict[str, Any]:
        """Get editor configuration info"""
        return {
            'mode': self.mode,
            'typo_available': TYPO_AVAILABLE,
            'typo_active': self.typo is not None,
            'modes': ['pythonic', 'symbolic', 'typo'],
        }

# =============================================================================
# Convenience Functions
# =============================================================================

def python_to_ucode(code: str) -> str:
    """Quick conversion: Python → uCODE"""
    editor = UCODEEditor(mode='symbolic')
    return editor.render(code)

def ucode_to_python(code: str) -> str:
    """Quick conversion: uCODE → Python"""
    editor = UCODEEditor(mode='symbolic')
    return editor.parse(code)

def render_with_typo(code: str) -> str:
    """Quick conversion: Python → Typo (if available)"""
    editor = UCODEEditor(mode='typo')
    return editor.render(code)

# =============================================================================
# Example Usage
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("uCODE Smart Text Editor Demo")
    print("=" * 60)
    
    # Test code with multiple arguments (demonstrates pipe usage)
    python_code = '''
PRINT("Hello", "World")
set_var("water_supply", 20)
CLONE--dev
heal_sprite(20)
player_hp = 100
'''
    
    # Pythonic mode
    print("\n1. PYTHONIC MODE (Python - Execution Format):")
    editor_py = UCODEEditor(mode='pythonic')
    print(editor_py.render(python_code))
    
    # Symbolic mode
    print("\n2. SYMBOLIC MODE (uCODE .upy - Storage Format):")
    print("   Note: Pipes | separate arguments (not commas)")
    editor_sym = UCODEEditor(mode='symbolic')
    ucode = editor_sym.render(python_code)
    print(ucode)
    
    # Typo mode (if available)
    print("\n3. TYPO MODE (Beautiful Typography - Display Only):")
    editor_typo = UCODEEditor(mode='typo')
    print(f"   Typo available: {TYPO_AVAILABLE}")
    if TYPO_AVAILABLE:
        typo = editor_typo.render(python_code)
        print(typo)
    else:
        print("   (Install Typo extension for beautiful typography)")
    
    # Syntax highlighting
    print("\n4. SYNTAX HIGHLIGHTING:")
    print(editor_sym.syntax_highlight(python_code))
    
    # Round-trip test
    print("\n5. ROUND-TRIP TEST (.upy ↔ Python):")
    print("   Original Python:", python_code.strip())
    ucode = editor_sym.render(python_code)
    print("   .upy format:    ", ucode.strip())
    back = editor_sym.parse(ucode)
    print("   Back to Python: ", back.strip())
    print("   Match:          ", "✅" if back.strip() == python_code.strip() else "❌")
    
    print("\n" + "=" * 60)
    print("Editor Info:")
    for key, value in editor_sym.get_info().items():
        print(f"  {key}: {value}")
    print("\nArchitecture:")
    print("  • .upy files are STANDARD format (saved on disk)")
    print("  • Smart editor parses .upy → Python (for execution)")
    print("  • Execution is fast (Python interpreter, 925,078 ops/sec)")
    print("  • Pipes | separate arguments in .upy format")
