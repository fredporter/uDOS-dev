"""
TS Markdown Runtime Executor

Handles:
- Parse .md files for runtime blocks
- Execute blocks (state, set, form, if/else, nav)
- Maintain state store ($variables)
- Variable interpolation
- SQLite data binding
"""

import logging
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger('goblin-runtime')

class RuntimeExecutor:
    """TypeScript Markdown Runtime executor"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_state_size = config.get("max_state_size_bytes", 1048576)
        self.timeout = config.get("execution_timeout_ms", 5000)
        self.state: Dict[str, Any] = {}
        
        logger.info("[GOBLIN:RUNTIME] Initialized executor")
    
    def parse_markdown(self, markdown: str) -> Dict[str, Any]:
        """
        Parse markdown and extract runtime blocks
        
        Returns:
            {
                "blocks": [...],
                "variables": [...],
                "ast": {}
            }
        """
        logger.info(f"[GOBLIN:RUNTIME] Parsing {len(markdown)} bytes")
        
        blocks = []
        variables = set()
        
        # Extract fenced code blocks
        pattern = r'```(\w+)\n(.*?)\n```'
        matches = re.finditer(pattern, markdown, re.DOTALL)
        
        for match in matches:
            block_type = match.group(1)
            content = match.group(2)
            
            # Only runtime blocks
            if block_type in ['state', 'set', 'form', 'if', 'else', 'nav', 'panel', 'map']:
                blocks.append({
                    "type": block_type,
                    "content": content,
                    "line": markdown[:match.start()].count('\n') + 1
                })
                
                # Extract variable references
                var_refs = re.findall(r'\$[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*', content)
                variables.update(var_refs)
        
        return {
            "blocks": blocks,
            "variables": list(variables),
            "ast": {
                "total_blocks": len(blocks),
                "block_types": list(set(b["type"] for b in blocks))
            }
        }
    
    def execute_block(self, block_type: str, content: str, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a single runtime block
        
        Args:
            block_type: state | set | form | if | else | nav | panel | map
            content: Block content
            state: Current state (optional)
        
        Returns:
            {
                "status": "executed",
                "state": {...},
                "output": "..."
            }
        """
        if state:
            self.state = state
        
        logger.info(f"[GOBLIN:RUNTIME] Executing block: {block_type}")
        
        if block_type == "state":
            return self._execute_state(content)
        elif block_type == "set":
            return self._execute_set(content)
        elif block_type == "form":
            return self._execute_form(content)
        elif block_type == "if":
            return self._execute_if(content)
        elif block_type == "nav":
            return self._execute_nav(content)
        elif block_type == "panel":
            return self._execute_panel(content)
        else:
            return {
                "status": "unsupported",
                "block_type": block_type,
                "message": f"Block type '{block_type}' not implemented yet"
            }
    
    def _execute_state(self, content: str) -> Dict[str, Any]:
        """
        Execute state block
        
        Example:
            $name = "Fred"
            $coins = 10
            $has_key = false
        """
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse: $var = value
            match = re.match(r'\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)', line)
            if match:
                var_name = f"${match.group(1)}"
                value_str = match.group(2).strip()
                
                # Parse value
                value = self._parse_value(value_str)
                
                # Set in state (preserve existing if configured)
                if var_name not in self.state:  # preserve mode
                    self.state[var_name] = value
                    logger.debug(f"[GOBLIN:RUNTIME] Set {var_name} = {value}")
        
        return {
            "status": "executed",
            "state": self.state,
            "output": ""
        }
    
    def _execute_set(self, content: str) -> Dict[str, Any]:
        """
        Execute set block (state mutations)
        
        Commands:
            set $var value
            inc $var n
            dec $var n
            toggle $var
        """
        lines = content.strip().split('\n')
        
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            
            command = parts[0]
            
            if command == "set" and len(parts) >= 3:
                var = parts[1]
                # Handle 'set $var = value' or 'set $var value'
                value_parts = parts[2:]
                if value_parts[0] == '=':
                    value_parts = value_parts[1:]
                value = ' '.join(value_parts)
                self.state[var] = self._parse_value(value)
                logger.debug(f"[GOBLIN:RUNTIME] set {var} = {value}")
            
            elif command == "inc" and len(parts) >= 3:
                var = parts[1]
                amount = int(parts[2])
                current = self.state.get(var, 0)
                self.state[var] = current + amount
                logger.debug(f"[GOBLIN:RUNTIME] inc {var} by {amount}")
            
            elif command == "dec" and len(parts) >= 3:
                var = parts[1]
                amount = int(parts[2])
                current = self.state.get(var, 0)
                self.state[var] = current - amount
                logger.debug(f"[GOBLIN:RUNTIME] dec {var} by {amount}")
            
            elif command == "toggle" and len(parts) >= 2:
                var = parts[1]
                current = self.state.get(var, False)
                self.state[var] = not current
                logger.debug(f"[GOBLIN:RUNTIME] toggle {var}")
        
        return {
            "status": "executed",
            "state": self.state,
            "output": ""
        }
    
    def _execute_form(self, content: str) -> Dict[str, Any]:
        """Execute form block (parse YAML-style field definitions)"""
        fields = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse field: name: type label
            if ':' in line:
                parts = line.split(':', 1)
                field_name = parts[0].strip()
                field_def = parts[1].strip().split(' ', 1)
                
                field = {
                    "name": field_name,
                    "type": field_def[0] if field_def else "text",
                    "label": field_def[1] if len(field_def) > 1 else field_name
                }
                fields.append(field)
                logger.debug(f"[GOBLIN:RUNTIME] form field: {field_name} ({field['type']})")
        
        return {
            "status": "executed",
            "state": self.state,
            "output": "form",
            "fields": fields
        }
    
    def _execute_if(self, content: str) -> Dict[str, Any]:
        """Execute if block (evaluate basic conditionals)"""
        condition_result = False
        condition_text = content.strip()
        
        # Replace variables in condition
        for var, value in self.state.items():
            condition_text = condition_text.replace(var, repr(value))
        
        # Evaluate basic comparisons (safe - no eval())
        try:
            # Split by logical operators
            if ' and ' in condition_text:
                parts = condition_text.split(' and ')
                condition_result = all(self._evaluate_comparison(p.strip()) for p in parts)
            elif ' or ' in condition_text:
                parts = condition_text.split(' or ')
                condition_result = any(self._evaluate_comparison(p.strip()) for p in parts)
            else:
                condition_result = self._evaluate_comparison(condition_text)
                
            logger.debug(f"[GOBLIN:RUNTIME] if condition: {content} = {condition_result}")
        except Exception as e:
            logger.error(f"[GOBLIN:RUNTIME] if evaluation error: {e}")
            condition_result = False
        
        return {
            "status": "executed",
            "state": self.state,
            "output": "if",
            "condition": condition_result,
            "condition_text": content
        }
    
    def _evaluate_comparison(self, expr: str) -> bool:
        """Safely evaluate a comparison expression (no eval())"""
        operators = ['==', '!=', '<=', '>=', '<', '>']
        
        for op in operators:
            if op in expr:
                left, right = expr.split(op, 1)
                left_val = self._parse_value(left.strip())
                right_val = self._parse_value(right.strip())
                
                if op == '==':
                    return left_val == right_val
                elif op == '!=':
                    return left_val != right_val
                elif op == '<':
                    return left_val < right_val
                elif op == '>':
                    return left_val > right_val
                elif op == '<=':
                    return left_val <= right_val
                elif op == '>=':
                    return left_val >= right_val
        
        # Single boolean value
        return self._parse_value(expr.strip())
    
    def _execute_nav(self, content: str) -> Dict[str, Any]:
        """Execute nav block (parse navigation choices)"""
        choices = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse choice: label -> target
            if '->' in line:
                parts = line.split('->', 1)
                choice = {
                    "label": parts[0].strip(),
                    "target": parts[1].strip()
                }
            else:
                # Simple choice (label only)
                choice = {
                    "label": line,
                    "target": line.lower().replace(' ', '_')
                }
            
            choices.append(choice)
            logger.debug(f"[GOBLIN:RUNTIME] nav choice: {choice['label']} -> {choice['target']}")
        
        return {
            "status": "executed",
            "state": self.state,
            "output": "nav",
            "choices": choices
        }
    
    def _execute_panel(self, content: str) -> Dict[str, Any]:
        """Execute panel block (interpolate variables and render)"""
        # Interpolate variables
        rendered = content
        for var, value in self.state.items():
            rendered = rendered.replace(var, str(value))
        
        return {
            "status": "executed",
            "state": self.state,
            "output": rendered
        }
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse value literal (string, number, boolean, null)"""
        value_str = value_str.strip()
        
        # String
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        
        # Boolean
        if value_str == "true":
            return True
        if value_str == "false":
            return False
        
        # Null
        if value_str == "null":
            return None
        
        # Number
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            # Fallback to string
            return value_str
    
    def get_state(self) -> Dict[str, Any]:
        """Get current runtime state"""
        return self.state.copy()
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """Set runtime state"""
        self.state = state.copy()
        logger.debug(f"[GOBLIN:RUNTIME] State updated ({len(state)} variables)")
