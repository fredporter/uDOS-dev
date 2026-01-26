"""
uPY v0.2 Interpreter - Sandboxed Python Execution

Main interpreter class with:
- AST validation
- Safe execution environment
- Resource limits
- Command injection
- Timeout protection
"""

import ast
import signal
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

from .validator import ASTValidator, SecurityError
from .safe_builtins import get_safe_builtins, get_safe_modules
from .commands import CommandInterface


class UPYError(Exception):
    """Base exception for uPY errors."""

    pass


class UPYSecurityError(UPYError):
    """Security violation in uPY script."""

    pass


class UPYTimeoutError(UPYError):
    """Script execution timeout."""

    pass


class UPYInterpreter:
    """
    Sandboxed Python interpreter for uPY v0.2 scripts.

    Features:
    - AST validation before execution
    - Limited built-in functions
    - Command injection (FILE.*, MESH.*, etc.)
    - Execution timeout
    - Output capture

    Example:
        interp = UPYInterpreter()
        result = interp.execute('''
            FILE.NEW(name="test.txt", content="Hello")
            print("File created")
        ''')
    """

    def __init__(
        self,
        command_executor: Optional[Callable] = None,
        timeout: int = 30,
        max_output_lines: int = 1000,
    ):
        """
        Initialize uPY interpreter.

        Args:
            command_executor: Function to execute uDOS commands
            timeout: Execution timeout in seconds
            max_output_lines: Maximum output lines to capture
        """
        self.validator = ASTValidator()
        self.command_interface = CommandInterface(command_executor)
        self.timeout = timeout
        self.max_output_lines = max_output_lines

        # Output capture
        self.output_lines: list = []
        self.output_truncated = False

    def execute(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute uPY script with sandboxing.

        Args:
            code: Python code to execute
            globals_dict: Optional global variables
            locals_dict: Optional local variables

        Returns:
            Execution result dict with:
                - success: bool
                - output: list of output lines
                - result: script return value (if any)
                - error: error message (if failed)
                - locals: final local variables

        Raises:
            UPYSecurityError: If security violations detected
            UPYTimeoutError: If execution exceeds timeout
        """
        # Validate AST
        try:
            self.validator.validate(code)
        except SecurityError as e:
            raise UPYSecurityError(str(e))
        except SyntaxError as e:
            return {
                "success": False,
                "output": [],
                "error": f"Syntax error: {e}",
                "locals": {},
            }

        # Prepare execution environment
        safe_globals = self._build_globals(globals_dict)
        safe_locals = locals_dict or {}

        # Reset output
        self.output_lines = []
        self.output_truncated = False

        # Execute with timeout
        try:
            with self._timeout_context(self.timeout):
                compiled = compile(code, "<upy>", "exec")
                exec(compiled, safe_globals, safe_locals)

            return {
                "success": True,
                "output": self.output_lines,
                "result": safe_locals.get("__result__"),
                "locals": safe_locals,
                "truncated": self.output_truncated,
            }

        except TimeoutError:
            raise UPYTimeoutError(f"Script execution exceeded {self.timeout}s timeout")

        except Exception as e:
            return {
                "success": False,
                "output": self.output_lines,
                "error": f"{type(e).__name__}: {str(e)}",
                "locals": safe_locals,
            }

    def _build_globals(
        self, user_globals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build safe globals dictionary."""
        safe_globals = {
            "__builtins__": get_safe_builtins(),
            "__name__": "__main__",
            "__doc__": None,
        }

        # Add safe modules
        safe_globals.update(get_safe_modules())

        # Add command interface
        safe_globals.update(self.command_interface.get_globals())

        # Add user globals (if provided)
        if user_globals:
            safe_globals.update(user_globals)

        # Override print to capture output
        safe_globals["__builtins__"]["print"] = self._captured_print

        return safe_globals

    def _captured_print(self, *args, **kwargs):
        """Capture print output."""
        line = " ".join(str(arg) for arg in args)

        if len(self.output_lines) < self.max_output_lines:
            self.output_lines.append(line)
        else:
            self.output_truncated = True

    @contextmanager
    def _timeout_context(self, seconds: int):
        """Context manager for execution timeout."""

        def timeout_handler(signum, frame):
            raise TimeoutError("Execution timeout")

        # Set alarm (Unix only)
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        except AttributeError:
            # Windows doesn't have SIGALRM, just execute without timeout
            yield

    def validate_only(self, code: str) -> Dict[str, Any]:
        """
        Validate script without executing.

        Args:
            code: Python code to validate

        Returns:
            Validation result dict
        """
        try:
            self.validator.validate(code)
            return {
                "valid": True,
                "errors": [],
                "warnings": self.validator.warnings,
            }
        except SecurityError as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": self.validator.warnings,
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "errors": [f"Syntax error: {e}"],
                "warnings": [],
            }
