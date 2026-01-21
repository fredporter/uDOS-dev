"""
GitHub Integration Routes for Goblin Dev Server
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/v0/github", tags=["github"])

# Lazy initialization - only create when needed
_gh_instance = None


def get_gh():
    """Lazy-load GitHub integration (check auth on first use)."""
    global _gh_instance
    if _gh_instance is None:
        from ..services.github_integration import GitHubIntegration
        _gh_instance = GitHubIntegration()
    return _gh_instance


class IssueCreate(BaseModel):
    """Issue creation request."""
    title: str
    body: str
    labels: Optional[List[str]] = None


@router.get("/health")
async def health_check():
    """Check GitHub CLI availability."""
    try:
        gh = get_gh()
        info = gh.get_repo_info()
        return {
            "status": "ok",
            "cli_authenticated": True,
            "repo": info.get("name"),
            "owner": info.get("owner", {}).get("login")
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/sync")
async def sync_repository():
    """Sync local repository with remote."""
    try:
        gh = get_gh()
        result = gh.sync_repo()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues")
async def get_issues(state: str = "open"):
    """Get repository issues.
    
    Args:
        state: Issue state (open, closed, all)
    """
    try:
        gh = get_gh()
        issues = gh.get_issues(state)
        return {"issues": issues, "count": len(issues)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/issues")
async def create_issue(issue: IssueCreate):
    """Create a new issue."""
    try:
        gh = get_gh()
        result = gh.create_issue(
            title=issue.title,
            body=issue.body,
            labels=issue.labels
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pulls")
async def get_pull_requests(state: str = "open"):
    """Get pull requests.
    
    Args:
        state: PR state (open, closed, merged, all)
    """
    try:
        gh = get_gh()
        prs = gh.get_pull_requests(state)
        return {"pull_requests": prs, "count": len(prs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/devlog")
async def get_devlog(month: Optional[str] = None):
    """Get devlog content.
    
    Args:
        month: Month in YYYY-MM format (default: current month)
    """
    try:
        gh = get_gh()
        content = gh.get_devlog(month)
        return {"month": month, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/roadmap")
async def get_roadmap():
    """Get current roadmap."""
    try:
        gh = get_gh()
        content = gh.get_roadmap()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/agents")
async def get_agents_doc():
    """Get AGENTS.md content."""
    try:
        gh = get_gh()
        content = gh.get_agents_doc()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/copilot")
async def get_copilot_instructions():
    """Get Copilot instructions."""
    try:
        gh = get_gh()
        content = gh.get_copilot_instructions()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{log_type}")
async def get_logs(log_type: str, lines: int = 50):
    """Get recent log entries.
    
    Args:
        log_type: Log type (debug, error, session-commands)
        lines: Number of lines to return
    """
    try:
        gh = get_gh()
        content = gh.search_logs(log_type, lines)
        return {"log_type": log_type, "lines": lines, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
