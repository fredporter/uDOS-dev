"""
uDOS Unified Predictor Service (v1.2.30)

Shared command prediction/autocomplete logic for CLI, TUI, and GUI interfaces.

Consolidates functionality from:
- core/ui/command_predictor.py (Smart predictor with confidence)
- core/utils/autocomplete.py (Autocomplete service)

Provides:
- Command suggestions from commands.json
- Fuzzy matching for typo tolerance
- History-based learning
- Confidence scoring
- Syntax highlighting tokens
- Option/subcommand completion

Author: uDOS Development Team
Version: 1.2.30
"""

import difflib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Prediction:
    """
    A single command prediction.
    
    Attributes:
        text: Predicted command/text
        confidence: Score 0.0 - 1.0
        source: Origin ("schema", "history", "fuzzy", "option")
        description: Help text
        syntax: Usage syntax
        category: Command category
        is_partial: Whether this completes partial input
    """
    text: str
    confidence: float
    source: str
    description: str = ""
    syntax: str = ""
    category: str = "general"
    is_partial: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'source': self.source,
            'description': self.description,
            'syntax': self.syntax,
            'category': self.category,
            'is_partial': self.is_partial,
        }


@dataclass
class Token:
    """
    Highlighted token in command input.
    
    Attributes:
        text: Token text
        token_type: Type for styling
        start: Start position
        end: End position
        color: Suggested color
    """
    text: str
    token_type: str  # "command", "subcommand", "arg", "path", "flag", "value", "unknown"
    start: int
    end: int
    color: str = "white"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'type': self.token_type,
            'start': self.start,
            'end': self.end,
            'color': self.color,
        }


# Token colors by type
TOKEN_COLORS = {
    'command': 'green',
    'subcommand': 'cyan',
    'arg': 'white',
    'path': 'magenta',
    'flag': 'cyan',
    'value': 'yellow',
    'unknown': 'red',
    'string': 'yellow',
}


class PredictorService:
    """
    Unified command prediction service.
    
    Features:
    - Loads command schemas from commands.json
    - Tracks command frequency from history
    - Provides ranked predictions with confidence
    - Real-time syntax highlighting
    - Fuzzy matching for typo tolerance
    - Subcommand/option suggestions
    """
    
    def __init__(self, commands_file: Path = None):
        """
        Initialize predictor service.
        
        Args:
            commands_file: Path to commands.json (auto-detected if None)
        """
        self._init_commands_file(commands_file)
        
        # Command data
        self.commands: Dict[str, Dict] = {}
        self.command_list: List[str] = []
        
        # Learning data
        self.frequency_map: Dict[str, int] = {}
        self.recent_commands: List[str] = []
        self.max_recent = 100
        
        # Option cache for quick lookup
        self.option_cache: Dict[str, Dict] = {}
        
        # Load commands
        self._load_commands()
    
    def _init_commands_file(self, commands_file: Path = None):
        """Initialize commands file path"""
        if commands_file:
            self.commands_file = Path(commands_file)
        else:
            try:
                from dev.goblin.core.utils.paths import PATHS
                self.commands_file = PATHS.CORE_DATA / "commands.json"
            except ImportError:
                # Fallback
                current = Path(__file__).resolve()
                for parent in current.parents:
                    candidate = parent / "core" / "data" / "commands.json"
                    if candidate.exists():
                        self.commands_file = candidate
                        break
                else:
                    self.commands_file = Path("dev/goblin/core/data/commands.json")
    
    def _load_commands(self):
        """Load command schemas from commands.json"""
        if not self.commands_file.exists():
            return
        
        try:
            with open(self.commands_file) as f:
                data = json.load(f)
            
            # Handle new format: {"COMMANDS": [{NAME, SYNTAX, ...}]}
            if 'COMMANDS' in data and isinstance(data['COMMANDS'], list):
                for cmd in data['COMMANDS']:
                    name = cmd.get('NAME', '')
                    if name:
                        self.commands[name] = {
                            'syntax': cmd.get('SYNTAX', ''),
                            'description': cmd.get('DESCRIPTION', ''),
                            'category': cmd.get('CATEGORY', 'general'),
                            'subcommands': cmd.get('SUBCOMMANDS', {}),
                            'examples': cmd.get('EXAMPLES', []),
                        }
                        # Build option cache
                        self._build_option_cache(name, cmd)
            
            # Handle old format: {"commands": {NAME: {...}}}
            elif 'commands' in data:
                self.commands = data['commands']
            
            self.command_list = sorted(self.commands.keys())
            
        except Exception as e:
            print(f"[Predictor] Error loading commands: {e}")
    
    def _build_option_cache(self, cmd_name: str, cmd_data: dict):
        """Build option/subcommand cache for a command"""
        options = []
        option_details = {}
        
        # From SUBCOMMANDS
        subcommands = cmd_data.get('SUBCOMMANDS', {})
        for subcmd, desc in subcommands.items():
            clean = subcmd.strip('<>').split()[0].upper()
            if clean and clean not in ['NAME', 'DESC', 'TOPIC', 'QUESTION']:
                options.append(clean)
                option_details[clean] = str(desc) if desc else ''
        
        # From SYNTAX alternatives
        if not options and '|' in cmd_data.get('SYNTAX', ''):
            parts = cmd_data['SYNTAX'].split('|')
            for part in parts:
                words = part.strip().split()
                if len(words) > 1 and words[0].upper() == cmd_name:
                    opt = words[1].strip('<>"[]').upper()
                    if opt and opt not in ['<DESC>', '<TOPIC>', '<QUESTION>', '<NAME>']:
                        options.append(opt)
        
        self.option_cache[cmd_name] = {
            'options': list(set(options)),
            'option_details': option_details,
        }
    
    # ─── Prediction ─────────────────────────────────────────────────
    
    def predict(self, partial: str, max_results: int = 10) -> List[Prediction]:
        """
        Generate predictions for partial input.
        
        Args:
            partial: Current text being typed
            max_results: Maximum predictions
            
        Returns:
            List of predictions ranked by confidence
        """
        if not partial:
            return self._get_recent_predictions(max_results)
        
        predictions = []
        words = partial.split()
        cmd_partial = words[0] if words else ""
        cmd_partial_lower = cmd_partial.lower()
        
        # 1. Exact prefix matches (highest confidence)
        for cmd in self.command_list:
            if cmd.lower().startswith(cmd_partial_lower):
                confidence = 0.9
                # Boost from history
                if cmd in self.frequency_map:
                    confidence += min(0.1, self.frequency_map[cmd] / 100)
                
                schema = self.commands.get(cmd, {})
                predictions.append(Prediction(
                    text=cmd,
                    confidence=min(1.0, confidence),
                    source="schema",
                    description=schema.get('description', ''),
                    syntax=schema.get('syntax', ''),
                    category=schema.get('category', 'general'),
                ))
        
        # 2. History matches
        for recent in self.recent_commands[-50:]:
            recent_cmd = recent.split()[0] if recent.split() else recent
            if recent_cmd.lower().startswith(cmd_partial_lower):
                if not any(p.text == recent_cmd for p in predictions):
                    predictions.append(Prediction(
                        text=recent_cmd,
                        confidence=0.7,
                        source="history",
                        description=f"Recent: {recent}",
                    ))
        
        # 3. Fuzzy matches
        if len(cmd_partial) >= 3:
            for cmd in self.command_list:
                if cmd not in [p.text for p in predictions]:
                    similarity = self._fuzzy_score(cmd_partial_lower, cmd.lower())
                    if similarity > 0.6:
                        schema = self.commands.get(cmd, {})
                        predictions.append(Prediction(
                            text=cmd,
                            confidence=similarity * 0.6,
                            source="fuzzy",
                            description=schema.get('description', ''),
                            syntax=schema.get('syntax', ''),
                        ))
        
        # 4. Subcommand/option suggestions
        if len(words) > 1:
            cmd = words[0].upper()
            if cmd in self.commands:
                opt_predictions = self._predict_options(cmd, words[1:])
                predictions.extend(opt_predictions)
        
        # Sort by confidence
        predictions.sort(key=lambda p: p.confidence, reverse=True)
        return predictions[:max_results]
    
    def _get_recent_predictions(self, max_results: int) -> List[Prediction]:
        """Get predictions from history when input is empty"""
        predictions = []
        
        # Top frequent commands
        sorted_freq = sorted(self.frequency_map.items(), key=lambda x: x[1], reverse=True)
        for cmd, count in sorted_freq[:5]:
            schema = self.commands.get(cmd, {})
            predictions.append(Prediction(
                text=cmd,
                confidence=0.8,
                source="history",
                description=f"Used {count}x - {schema.get('description', '')}",
                syntax=schema.get('syntax', ''),
            ))
        
        # Recent unique commands
        seen = {p.text for p in predictions}
        for recent in reversed(self.recent_commands[-20:]):
            cmd = recent.split()[0] if recent.split() else recent
            if cmd not in seen:
                predictions.append(Prediction(
                    text=cmd,
                    confidence=0.6,
                    source="history",
                    description=f"Recent: {recent}",
                ))
                seen.add(cmd)
                if len(predictions) >= max_results:
                    break
        
        return predictions[:max_results]
    
    def _predict_options(self, command: str, current_args: List[str]) -> List[Prediction]:
        """Predict options/subcommands for a command"""
        predictions = []
        
        cache = self.option_cache.get(command, {})
        options = cache.get('options', [])
        details = cache.get('option_details', {})
        
        current_partial = current_args[-1].upper() if current_args else ""
        
        for opt in options:
            if not current_partial or opt.startswith(current_partial):
                predictions.append(Prediction(
                    text=f"{command} {opt}",
                    confidence=0.75,
                    source="option",
                    description=details.get(opt, ''),
                    is_partial=True,
                ))
        
        return predictions
    
    def _fuzzy_score(self, a: str, b: str) -> float:
        """Calculate fuzzy match score"""
        return difflib.SequenceMatcher(None, a, b).ratio()
    
    # ─── Syntax Highlighting ────────────────────────────────────────
    
    def tokenize(self, text: str) -> List[Token]:
        """
        Tokenize command text for syntax highlighting.
        
        Args:
            text: Command text
            
        Returns:
            List of tokens with type and color
        """
        if not text:
            return []
        
        tokens = []
        words = text.split()
        pos = 0
        
        for i, word in enumerate(words):
            # Find actual position in text
            start = text.find(word, pos)
            end = start + len(word)
            pos = end
            
            if i == 0:
                # First word is command
                if word.upper() in self.commands:
                    token_type = 'command'
                else:
                    token_type = 'unknown'
            else:
                # Subsequent words
                cmd = words[0].upper()
                cache = self.option_cache.get(cmd, {})
                options = cache.get('options', [])
                
                if word.upper() in options:
                    token_type = 'subcommand'
                elif word.startswith('-'):
                    token_type = 'flag'
                elif '/' in word or word.endswith(('.py', '.upy', '.json', '.md')):
                    token_type = 'path'
                elif word.startswith('"') or word.startswith("'"):
                    token_type = 'string'
                else:
                    token_type = 'arg'
            
            tokens.append(Token(
                text=word,
                token_type=token_type,
                start=start,
                end=end,
                color=TOKEN_COLORS.get(token_type, 'white'),
            ))
        
        return tokens
    
    def get_highlighted(self, text: str) -> str:
        """
        Get ANSI-highlighted text.
        
        Args:
            text: Command text
            
        Returns:
            Text with ANSI color codes
        """
        tokens = self.tokenize(text)
        if not tokens:
            return text
        
        # ANSI color codes
        COLORS = {
            'green': '\033[32m',
            'cyan': '\033[36m',
            'magenta': '\033[35m',
            'yellow': '\033[33m',
            'red': '\033[31m',
            'white': '\033[37m',
        }
        RESET = '\033[0m'
        
        result = []
        last_end = 0
        
        for token in tokens:
            # Add any text before token (spaces)
            if token.start > last_end:
                result.append(text[last_end:token.start])
            
            # Add colored token
            color = COLORS.get(token.color, '')
            result.append(f"{color}{token.text}{RESET}")
            last_end = token.end
        
        # Add remaining text
        if last_end < len(text):
            result.append(text[last_end:])
        
        return ''.join(result)
    
    # ─── Learning ───────────────────────────────────────────────────
    
    def record_command(self, command: str):
        """Record command execution for learning"""
        if not command:
            return
        
        # Extract command name
        cmd = command.split()[0].upper() if command.split() else command.upper()
        
        # Update frequency
        self.frequency_map[cmd] = self.frequency_map.get(cmd, 0) + 1
        
        # Add to recent
        self.recent_commands.append(command)
        if len(self.recent_commands) > self.max_recent:
            self.recent_commands = self.recent_commands[-self.max_recent:]
    
    def get_command_info(self, command: str) -> Optional[Dict]:
        """Get full info for a command"""
        return self.commands.get(command.upper())
    
    def get_options(self, command: str) -> List[str]:
        """Get available options for a command"""
        cache = self.option_cache.get(command.upper(), {})
        return cache.get('options', [])
    
    # ─── API Methods ────────────────────────────────────────────────
    
    def suggest(self, partial: str, max_results: int = 10) -> Dict:
        """
        API method for suggestions.
        
        Returns:
            Dict with 'predictions' and 'tokens' keys
        """
        predictions = self.predict(partial, max_results)
        tokens = self.tokenize(partial)
        
        return {
            'input': partial,
            'predictions': [p.to_dict() for p in predictions],
            'tokens': [t.to_dict() for t in tokens],
        }


# ─── Convenience Functions ──────────────────────────────────────────

_service_instance: PredictorService = None

def get_predictor_service(commands_file: Path = None) -> PredictorService:
    """Get singleton predictor service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = PredictorService(commands_file)
    return _service_instance


# ─── Backwards Compatibility ────────────────────────────────────────

# For code using CommandPredictor
CommandPredictor = PredictorService

# For code using AutocompleteService
AutocompleteService = PredictorService


# ─── Test ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    service = PredictorService()
    
    print(f"Loaded {len(service.command_list)} commands")
    print(f"First 10: {service.command_list[:10]}")
    
    # Test predictions
    print("\nPredictions for 'HE':")
    for p in service.predict('HE', max_results=5):
        print(f"  {p.text} ({p.confidence:.2f}) - {p.source}")
    
    # Test tokenization
    print("\nTokens for 'GUIDE WATER boiling':")
    for t in service.tokenize('GUIDE WATER boiling'):
        print(f"  {t.text}: {t.token_type} ({t.color})")
    
    # Test highlighting
    print("\nHighlighted:")
    print(service.get_highlighted('GUIDE WATER boiling'))
