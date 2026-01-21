"""
Mistral API + Vibe CLI Integration for Goblin Dev Server

Provides AI assistance with access to:
- Devlogs (docs/devlog/)
- Roadmap (docs/roadmap.md)
- Debug/error logs (memory/logs/)
- Copilot instructions (.github/copilot-instructions.md)
- AGENTS.md

Supports:
- Local execution via Vibe CLI (Devstral offline)
- Cloud escalation via Mistral API (optional)
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


class MistralVibeIntegration:
    """Mistral API + Vibe CLI integration."""
    
    def __init__(
        self,
        repo_path: str = ".",
        vibe_config_path: Optional[str] = None,
        mistral_api_key: Optional[str] = None
    ):
        """Initialize Mistral/Vibe integration.
        
        Args:
            repo_path: Path to repository
            vibe_config_path: Path to .vibe/config.toml
            mistral_api_key: Optional Mistral API key for cloud
        """
        self.repo_path = Path(repo_path).absolute()
        self.vibe_config = Path(vibe_config_path) if vibe_config_path else None
        self.mistral_api_key = mistral_api_key
        self._check_vibe_cli()
    
    def _check_vibe_cli(self):
        """Verify Vibe CLI is installed."""
        try:
            subprocess.run(
                ["vibe", "--version"],
                capture_output=True,
                check=True
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Vibe CLI not installed. See: https://mistral.ai/news/vibe/"
            )
    
    def get_context_files(self) -> Dict[str, str]:
        """Gather all context files for AI assistance.
        
        Returns:
            Dictionary of filename -> content
        """
        context = {}
        
        # Core documentation
        files_to_read = [
            "AGENTS.md",
            "docs/roadmap.md",
            "docs/_index.md",
            ".github/copilot-instructions.md",
        ]
        
        for file_path in files_to_read:
            full_path = self.repo_path / file_path
            if full_path.exists():
                context[file_path] = full_path.read_text()
        
        # Recent devlog
        devlog_dir = self.repo_path / "docs" / "devlog"
        if devlog_dir.exists():
            current_month = datetime.now().strftime("%Y-%m")
            devlog_path = devlog_dir / f"{current_month}.md"
            if devlog_path.exists():
                context[f"docs/devlog/{current_month}.md"] = devlog_path.read_text()
        
        # Recent logs
        log_dir = self.repo_path / "memory" / "logs"
        if log_dir.exists():
            today = datetime.now().strftime("%Y-%m-%d")
            
            for log_type in ["debug", "error", "session-commands"]:
                log_path = log_dir / f"{log_type}-{today}.log"
                if log_path.exists():
                    # Get last 100 lines
                    result = subprocess.run(
                        ["tail", "-n", "100", str(log_path)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    context[f"logs/{log_type}-{today}.log"] = result.stdout
        
        return context
    
    def query_vibe(
        self,
        prompt: str,
        include_context: bool = True,
        model: str = "devstral-small"
    ) -> str:
        """Query Vibe CLI with project context.
        
        Args:
            prompt: User prompt
            include_context: Include project context files
            model: Model to use (devstral-small, devstral-large)
            
        Returns:
            AI response
        """
        # Build context string
        context_str = ""
        if include_context:
            context_files = self.get_context_files()
            context_str = "\n\n".join([
                f"=== {filename} ===\n{content}"
                for filename, content in context_files.items()
            ])
        
        # Build full prompt
        full_prompt = f"""You are helping with the uDOS project.

Here is the current project context:

{context_str}

User request: {prompt}
"""
        
        # Run vibe CLI
        result = subprocess.run(
            ["vibe", "chat", "--model", model],
            input=full_prompt,
            capture_output=True,
            text=True,
            check=True
        )
        
        return result.stdout
    
    def query_mistral_api(
        self,
        prompt: str,
        include_context: bool = True,
        model: str = "mistral-small-latest"
    ) -> str:
        """Query Mistral API (cloud) with project context.
        
        Args:
            prompt: User prompt
            include_context: Include project context files
            model: Model to use
            
        Returns:
            AI response
        """
        if not self.mistral_api_key:
            raise ValueError("Mistral API key not configured")
        
        # Build context
        context_files = self.get_context_files() if include_context else {}
        
        # Note: This would use the Mistral API client
        # For now, raise not implemented
        raise NotImplementedError(
            "Mistral API integration coming in v1.0.4.0. "
            "Use query_vibe() for local execution."
        )
    
    def analyze_logs(self, log_type: str = "error") -> str:
        """Analyze recent logs with AI.
        
        Args:
            log_type: Type of log to analyze
            
        Returns:
            AI analysis
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = self.repo_path / "memory" / "logs" / f"{log_type}-{today}.log"
        
        if not log_path.exists():
            return f"No {log_type} log found for {today}"
        
        # Get last 200 lines
        result = subprocess.run(
            ["tail", "-n", "200", str(log_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        log_content = result.stdout
        
        prompt = f"""Analyze these recent {log_type} log entries and identify:
1. Critical issues
2. Patterns or recurring problems
3. Suggested fixes

Log entries:
{log_content}
"""
        
        return self.query_vibe(prompt, include_context=False)
    
    def suggest_next_steps(self) -> str:
        """Suggest next development steps based on roadmap and logs.
        
        Returns:
            AI suggestions
        """
        prompt = """Based on the current roadmap, recent devlog entries, and any error logs,
suggest the next 3-5 development tasks that should be prioritized.
Consider:
1. Mission v1.0.4.0 goals
2. Recent errors or blockers
3. Logical sequencing of work
"""
        
        return self.query_vibe(prompt, include_context=True)
    
    def explain_code(self, file_path: str, line_range: Optional[tuple] = None) -> str:
        """Get AI explanation of code.
        
        Args:
            file_path: Path to file (relative to repo)
            line_range: Optional (start, end) line numbers
            
        Returns:
            AI explanation
        """
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            return f"File not found: {file_path}"
        
        content = full_path.read_text()
        
        if line_range:
            lines = content.split("\n")
            start, end = line_range
            content = "\n".join(lines[start-1:end])
        
        prompt = f"""Explain this code from {file_path}:

```
{content}
```

Provide:
1. High-level purpose
2. Key implementation details
3. Dependencies and integration points
"""
        
        return self.query_vibe(prompt, include_context=True)
