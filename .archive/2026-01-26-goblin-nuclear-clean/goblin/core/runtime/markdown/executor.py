"""
.udos.md Executor

Executes uPY scripts from .udos.md documents with permission validation.
"""

from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

from .document import UDOSDocument
from .parser import UDOSMarkdownParser
from ..upy import UPYInterpreter, UPYError


class ExecutionError(Exception):
    """Raised when script execution fails."""

    pass


class UDOSMarkdownExecutor:
    """
    Executes uPY scripts from .udos.md documents.

    Features:
    - Permission validation
    - Script execution with uPY interpreter
    - State management
    - Output capture
    """

    def __init__(
        self,
        command_executor: Optional[Callable] = None,
        permission_validator: Optional[Callable] = None,
    ):
        """
        Initialize executor.

        Args:
            command_executor: Function to execute uDOS commands
            permission_validator: Function to validate permissions
                                 Signature: validator(required: list, document: UDOSDocument) -> bool
        """
        self.parser = UDOSMarkdownParser()
        self.interpreter = UPYInterpreter(command_executor=command_executor)
        self.permission_validator = (
            permission_validator or self._default_permission_validator
        )

    def _default_permission_validator(
        self, required: List[str], document: UDOSDocument
    ) -> bool:
        """
        Default permission validator.

        Args:
            required: Required permissions
            document: Document to check

        Returns:
            True if all permissions granted
        """
        doc_perms = set(document.permissions)
        return all(perm in doc_perms for perm in required)

    def execute(
        self,
        content: str,
        globals_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Parse and execute .udos.md content.

        Args:
            content: .udos.md file content
            globals_dict: Optional global variables for scripts

        Returns:
            Execution result dict with:
                - document: Parsed UDOSDocument
                - scripts: List of script execution results
                - success: bool
                - error: error message (if failed)

        Raises:
            ExecutionError: If execution fails
        """
        # Parse document
        try:
            document = self.parser.parse(content)
        except Exception as e:
            return {
                "success": False,
                "error": f"Parse error: {e}",
                "document": None,
                "scripts": [],
            }

        # Validate permissions
        if not self.permission_validator(["execute"], document):
            return {
                "success": False,
                "error": "Insufficient permissions to execute scripts",
                "document": document,
                "scripts": [],
            }

        # Execute scripts
        script_results = []

        for i, script in enumerate(document.upy_scripts):
            # Build globals with state access
            script_globals = globals_dict or {}
            script_globals["STATE"] = StateAccessor(document)

            # Execute script
            try:
                result = self.interpreter.execute(
                    script["code"], globals_dict=script_globals
                )

                script_results.append(
                    {
                        "index": i,
                        "line": script["line"],
                        "success": result["success"],
                        "output": result["output"],
                        "error": result.get("error"),
                    }
                )

            except UPYError as e:
                script_results.append(
                    {
                        "index": i,
                        "line": script["line"],
                        "success": False,
                        "output": [],
                        "error": str(e),
                    }
                )

        # Determine overall success
        success = all(r["success"] for r in script_results)

        return {
            "success": success,
            "document": document,
            "scripts": script_results,
            "error": None if success else "One or more scripts failed",
        }

    def execute_file(
        self,
        filepath: str,
        globals_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute .udos.md file.

        Args:
            filepath: Path to .udos.md file
            globals_dict: Optional global variables

        Returns:
            Execution result dict

        Raises:
            ExecutionError: If file cannot be read or executed
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return self.execute(content, globals_dict)
        except IOError as e:
            raise ExecutionError(f"Cannot read file {filepath}: {e}")

    def validate_only(self, content: str) -> Dict[str, Any]:
        """
        Validate .udos.md content without executing.

        Args:
            content: .udos.md file content

        Returns:
            Validation result dict
        """
        # Parse document
        try:
            document = self.parser.parse(content)
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Parse error: {e}"],
                "warnings": [],
                "document": None,
            }

        errors = []
        warnings = []

        # Validate each script
        for i, script in enumerate(document.upy_scripts):
            validation = self.interpreter.validate_only(script["code"])

            if not validation["valid"]:
                errors.extend(
                    [
                        f"Script {i+1} (line {script['line']}): {err}"
                        for err in validation["errors"]
                    ]
                )

            warnings.extend(
                [
                    f"Script {i+1} (line {script['line']}): {warn}"
                    for warn in validation["warnings"]
                ]
            )

        # Validate state blocks (already validated during parse)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "document": document,
        }


class StateAccessor:
    """
    Provides STATE.GET/SET access to document state from scripts.

    Usage in uPY scripts:
        counter = STATE.GET(key="counter")
        STATE.SET(key="counter", value=counter + 1)
    """

    def __init__(self, document: UDOSDocument):
        self.document = document

    def GET(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        return self.document.get_state(key, default)

    def SET(self, key: str, value: Any) -> None:
        """Set state value."""
        self.document.set_state(key, value)

    def DELETE(self, key: str) -> None:
        """Delete state value."""
        for state_block in self.document.state_blocks:
            if key in state_block.get("data", {}):
                del state_block["data"][key]
                return
