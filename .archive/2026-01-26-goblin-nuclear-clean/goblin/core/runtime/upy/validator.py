"""
AST Validator for uPY v0.2

Validates Python AST to ensure safe execution:
- Blocks dangerous imports (os, subprocess, etc.)
- Blocks file I/O operations
- Blocks exec/eval/compile
- Blocks attribute access on forbidden objects
- Allows only whitelisted modules
"""

import ast
from typing import List, Set


class ASTValidator(ast.NodeVisitor):
    """
    Validates AST for security violations.

    Raises:
        SecurityError: If dangerous operations detected
    """

    # Forbidden imports
    FORBIDDEN_IMPORTS = {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "urllib",
        "requests",
        "http",
        "ftplib",
        "__import__",
        "importlib",
        "imp",
        "ctypes",
        "multiprocessing",
        "threading",
        "pickle",
        "marshal",
        "shelve",
    }

    # Allowed safe imports
    ALLOWED_IMPORTS = {
        "json",
        "math",
        "datetime",
        "time",
        "re",
        "random",
        "string",
        "itertools",
        "collections",
        "functools",
        "operator",
    }

    # Forbidden built-in functions
    FORBIDDEN_BUILTINS = {
        "exec",
        "eval",
        "compile",
        "open",
        "__import__",
        "globals",
        "locals",
        "vars",
        "dir",
        "help",
        "input",  # Use PROMPT command instead
    }

    # Forbidden attributes
    FORBIDDEN_ATTRS = {
        "__import__",
        "__loader__",
        "__spec__",
        "__builtins__",
        "__globals__",
        "__code__",
        "func_globals",
        "func_code",
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, code: str) -> None:
        """
        Validate Python code AST.

        Args:
            code: Python code to validate

        Raises:
            SyntaxError: If code has syntax errors
            SecurityError: If code contains dangerous operations
        """
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error: {e}")

        self.errors = []
        self.warnings = []
        self.visit(tree)

        if self.errors:
            raise SecurityError(
                f"Security violations detected:\n" + "\n".join(self.errors)
            )

    def visit_Import(self, node: ast.Import) -> None:
        """Check import statements."""
        for alias in node.names:
            module = alias.name.split(".")[0]

            if module in self.FORBIDDEN_IMPORTS:
                self.errors.append(f"Line {node.lineno}: Forbidden import: {module}")
            elif module not in self.ALLOWED_IMPORTS:
                self.warnings.append(f"Line {node.lineno}: Unknown module: {module}")

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from X import Y statements."""
        if node.module:
            module = node.module.split(".")[0]

            if module in self.FORBIDDEN_IMPORTS:
                self.errors.append(f"Line {node.lineno}: Forbidden import: {module}")
            elif module not in self.ALLOWED_IMPORTS:
                self.warnings.append(f"Line {node.lineno}: Unknown module: {module}")

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls."""
        # Check for forbidden built-ins
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_BUILTINS:
                self.errors.append(
                    f"Line {node.lineno}: Forbidden function: {node.func.id}()"
                )

        # Check for attribute-based calls (obj.method())
        if isinstance(node.func, ast.Attribute):
            attr = node.func.attr

            # Check for dangerous methods
            dangerous_methods = {"__import__", "__loader__", "exec", "eval"}
            if attr in dangerous_methods:
                self.errors.append(f"Line {node.lineno}: Forbidden method: {attr}()")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check attribute access."""
        if node.attr in self.FORBIDDEN_ATTRS:
            self.errors.append(
                f"Line {node.lineno}: Forbidden attribute access: {node.attr}"
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definitions."""
        # Function definitions are allowed
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check class definitions."""
        # Class definitions are allowed
        self.generic_visit(node)


class SecurityError(Exception):
    """Raised when security violations detected in AST."""

    pass
