"""
Command Interface for uPY v0.2

Provides uDOS command access from scripts via injected objects.

Example:
    FILE.NEW(name="test.txt", content="Hello World")
    MESH.SEND(device="node2", message="ping")
    PROMPT.ASK(text="Enter name:")
"""

from typing import Dict, Any, Callable, Optional


class CommandInterface:
    """
    Injects uDOS commands into uPY script execution context.

    Commands are accessed as objects with methods:
        FILE.NEW(name="test.txt")
        MESH.SEND(device="node2", message="hello")
    """

    def __init__(self, command_executor: Optional[Callable] = None):
        """
        Initialize command interface.

        Args:
            command_executor: Function to execute commands
                             Signature: executor(command: str, params: dict) -> Any
        """
        self.executor = command_executor or self._default_executor

        # Create command namespace objects
        self.FILE = self._create_namespace("FILE")
        self.MESH = self._create_namespace("MESH")
        self.PROMPT = self._create_namespace("PROMPT")
        self.STATE = self._create_namespace("STATE")
        self.LOG = self._create_namespace("LOG")

    def _default_executor(self, command: str, params: Dict[str, Any]) -> Any:
        """Default command executor (for testing)."""
        return {"command": command, "params": params, "status": "simulated"}

    def _create_namespace(self, prefix: str):
        """Create command namespace object."""
        return CommandNamespace(prefix, self.executor)

    def get_globals(self) -> Dict[str, Any]:
        """
        Get command objects for injection into script globals.

        Returns:
            Dictionary of command namespace objects
        """
        return {
            "FILE": self.FILE,
            "MESH": self.MESH,
            "PROMPT": self.PROMPT,
            "STATE": self.STATE,
            "LOG": self.LOG,
        }


class CommandNamespace:
    """
    Dynamic command namespace that converts method calls to command execution.

    Example:
        FILE.NEW(name="test.txt") -> executor('FILE.NEW', {'name': 'test.txt'})
    """

    def __init__(self, prefix: str, executor: Callable):
        self._prefix = prefix
        self._executor = executor

    def __getattr__(self, name: str):
        """Intercept attribute access to create command methods."""
        command = f"{self._prefix}.{name}"

        def command_method(**kwargs):
            """Execute command with parameters."""
            return self._executor(command, kwargs)

        return command_method

    def __repr__(self) -> str:
        return f"<CommandNamespace: {self._prefix}>"


# Command documentation for help system
COMMAND_DOCS = {
    "FILE": {
        "NEW": 'Create new file: FILE.NEW(name="file.txt", content="...")',
        "OPEN": 'Open file: FILE.OPEN(name="file.txt")',
        "SAVE": 'Save file: FILE.SAVE(name="file.txt", content="...")',
        "DELETE": 'Delete file: FILE.DELETE(name="file.txt")',
        "LIST": 'List files: FILE.LIST(directory=".")',
    },
    "MESH": {
        "SEND": 'Send message: MESH.SEND(device="node2", message="hello")',
        "BROADCAST": 'Broadcast: MESH.BROADCAST(message="hello")',
        "DEVICES": "List devices: MESH.DEVICES()",
        "PAIR": 'Pair device: MESH.PAIR(device="node2")',
    },
    "PROMPT": {
        "ASK": 'Ask user input: PROMPT.ASK(text="Enter name:")',
        "CONFIRM": 'Confirm yes/no: PROMPT.CONFIRM(text="Continue?")',
        "CHOOSE": 'Choose option: PROMPT.CHOOSE(options=["a", "b", "c"])',
    },
    "STATE": {
        "GET": 'Get state: STATE.GET(key="variable")',
        "SET": 'Set state: STATE.SET(key="variable", value=123)',
        "DELETE": 'Delete state: STATE.DELETE(key="variable")',
    },
    "LOG": {
        "INFO": 'Log info: LOG.INFO(message="Status update")',
        "WARN": 'Log warning: LOG.WARN(message="Warning")',
        "ERROR": 'Log error: LOG.ERROR(message="Error occurred")',
        "DEBUG": 'Log debug: LOG.DEBUG(message="Debug info")',
    },
}


def get_command_help(namespace: Optional[str] = None) -> str:
    """
    Get help text for commands.

    Args:
        namespace: Optional command namespace (FILE, MESH, etc.)

    Returns:
        Help text
    """
    if namespace:
        if namespace in COMMAND_DOCS:
            lines = [f"\n{namespace} Commands:"]
            for cmd, doc in COMMAND_DOCS[namespace].items():
                lines.append(f"  {doc}")
            return "\n".join(lines)
        else:
            return f"Unknown namespace: {namespace}"

    # Show all commands
    lines = ["\nuPY Command Reference:"]
    for ns, commands in COMMAND_DOCS.items():
        lines.append(f"\n{ns}:")
        for cmd, doc in commands.items():
            lines.append(f"  {doc}")

    return "\n".join(lines)
