"""
GitHub Integration Service for Goblin Dev Server

Provides GitHub CLI integration with access to:
- Repository management (clone, pull, push, sync)
- Webhooks (issue events, PR events, push events)
- Issue and PR management
- Access to project documentation (devlogs, roadmap, instructions)

Uses GitHub CLI (gh) for authentication and operations.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


class GitHubIntegration:
    """GitHub CLI integration for Goblin."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize GitHub integration.
        
        Args:
            repo_path: Path to local git repository
        """
        self.repo_path = Path(repo_path).absolute()
        self._check_gh_cli()
    
    def _check_gh_cli(self):
        """Verify GitHub CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "GitHub CLI not authenticated. Run: gh auth login"
                )
        except FileNotFoundError:
            raise RuntimeError(
                "GitHub CLI not installed. Install: brew install gh"
            )
    
    def _run_gh(self, args: List[str]) -> Dict[str, Any]:
        """Run GitHub CLI command.
        
        Args:
            args: Command arguments
            
        Returns:
            Parsed JSON output
        """
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            cwd=self.repo_path,
            check=True
        )
        return json.loads(result.stdout) if result.stdout else {}
    
    def sync_repo(self) -> Dict[str, str]:
        """Sync local repository with remote.
        
        Returns:
            Status dictionary
        """
        # Fetch latest
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )
        
        # Check status
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=self.repo_path,
            check=True
        )
        
        has_changes = bool(result.stdout.strip())
        
        return {
            "synced": not has_changes,
            "has_local_changes": has_changes,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_issues(self, state: str = "open") -> List[Dict[str, Any]]:
        """Get repository issues.
        
        Args:
            state: Issue state (open, closed, all)
            
        Returns:
            List of issues
        """
        return self._run_gh([
            "issue", "list",
            "--state", state,
            "--json", "number,title,state,labels,createdAt,updatedAt,author"
        ])
    
    def get_pull_requests(self, state: str = "open") -> List[Dict[str, Any]]:
        """Get pull requests.
        
        Args:
            state: PR state (open, closed, merged, all)
            
        Returns:
            List of pull requests
        """
        return self._run_gh([
            "pr", "list",
            "--state", state,
            "--json", "number,title,state,createdAt,updatedAt,author,mergeable"
        ])
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create a new issue.
        
        Args:
            title: Issue title
            body: Issue body
            labels: Optional labels
            
        Returns:
            Created issue data
        """
        args = ["issue", "create", "--title", title, "--body", body]
        if labels:
            args.extend(["--label", ",".join(labels)])
        
        return self._run_gh(args)
    
    def get_devlog(self, month: Optional[str] = None) -> str:
        """Get devlog content.
        
        Args:
            month: Month in YYYY-MM format (default: current month)
            
        Returns:
            Devlog markdown content
        """
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        devlog_path = self.repo_path / "docs" / "devlog" / f"{month}.md"
        
        if not devlog_path.exists():
            return f"# Devlog {month}\n\nNo entries yet."
        
        return devlog_path.read_text()
    
    def get_roadmap(self) -> str:
        """Get current roadmap.
        
        Returns:
            Roadmap markdown content
        """
        roadmap_path = self.repo_path / "docs" / "roadmap.md"
        return roadmap_path.read_text()
    
    def get_copilot_instructions(self) -> str:
        """Get Copilot instructions.
        
        Returns:
            Copilot instructions content
        """
        instructions_path = self.repo_path / ".github" / "copilot-instructions.md"
        return instructions_path.read_text()
    
    def get_agents_doc(self) -> str:
        """Get AGENTS.md content.
        
        Returns:
            AGENTS.md content
        """
        agents_path = self.repo_path / "AGENTS.md"
        return agents_path.read_text()
    
    def search_logs(self, log_type: str = "debug", lines: int = 50) -> str:
        """Search recent log entries.
        
        Args:
            log_type: Log type (debug, error, session-commands)
            lines: Number of lines to return
            
        Returns:
            Recent log entries
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.repo_path / "memory" / "logs" / f"{log_type}-{today}.log"
        
        if not log_file.exists():
            return f"No {log_type} log for {today}"
        
        # Get last N lines
        result = subprocess.run(
            ["tail", "-n", str(lines), str(log_file)],
            capture_output=True,
            text=True,
            check=True
        )
        
        return result.stdout
    
    def get_repo_info(self) -> Dict[str, Any]:
        """Get repository information.
        
        Returns:
            Repository metadata
        """
        return self._run_gh(["repo", "view", "--json", "name,owner,description,url,defaultBranchRef"])
    
    def setup_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """Setup repository webhook.
        
        Args:
            url: Webhook URL
            events: List of events (issues, pull_request, push, etc.)
            
        Returns:
            Webhook configuration
        """
        # Note: GitHub CLI doesn't support webhook creation directly
        # This would need to use the GitHub API via gh api command
        raise NotImplementedError(
            "Webhook setup requires GitHub API. "
            "Use: gh api repos/:owner/:repo/hooks -f config[url]=URL"
        )
