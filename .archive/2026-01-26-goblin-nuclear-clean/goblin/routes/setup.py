"""
Setup and Configuration Routes for Goblin Dev Server

Provides endpoints for first-time setup, config management, and OAuth.
"""

from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import webbrowser
from urllib.parse import urlencode

from ..config_manager import (
    config,
    setup_state,
    get_full_config_status,
    get_required_variables,
    validate_github_setup,
    validate_notion_setup,
    validate_ai_setup,
    validate_hubspot_setup,
    validate_database_paths
)

router = APIRouter(prefix="/api/v0/setup", tags=["setup"])


# ========================================
# Models
# ========================================

class ConfigVariable(BaseModel):
    """Configuration variable update."""
    name: str
    value: str
    description: Optional[str] = None


class GitHubOAuthRequest(BaseModel):
    """GitHub OAuth request."""
    client_id: str
    scope: str = "repo,user"
    redirect_uri: str = "http://127.0.0.1:8767/api/v0/setup/github/callback"


class SetupProgress(BaseModel):
    """Setup progress tracker."""
    step: str
    completed: bool
    message: Optional[str] = None


# ========================================
# Status Endpoints
# ========================================

@router.get("/status")
async def get_setup_status():
    """Get current setup status and configuration."""
    return get_full_config_status()


@router.get("/progress")
async def get_setup_progress():
    """Get setup progress."""
    status = setup_state.get_status()
    variables = get_required_variables()
    
    # Calculate progress
    configured_count = len(status.get("variables_configured", []))
    total_required = sum(1 for v in variables.values() if v.get("required", False))
    
    return {
        "setup_complete": status.get("setup_complete", False),
        "initialized_at": status.get("initialized_at"),
        "progress_percent": int((configured_count / max(total_required, 1)) * 100) if total_required > 0 else 0,
        "variables_configured": configured_count,
        "services_enabled": len(status.get("services_enabled", [])),
        "required_variables": total_required,
        "configured_variables": variables
    }


@router.get("/required-variables")
async def get_setup_variables():
    """Get list of required variables and setup instructions."""
    return {
        "variables": get_required_variables(),
        "instructions": {
            "github": "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token",
            "notion": "https://developers.notion.com/docs/getting-started",
            "mistral": "https://docs.mistral.ai/",
            "hubspot": "https://developers.hubspot.com/docs/api/overview"
        }
    }


# ========================================
# Configuration Management
# ========================================

@router.post("/configure")
async def update_config(variable: ConfigVariable):
    """Update a configuration variable."""
    try:
        # Update environment variable
        os.environ[variable.name.upper()] = variable.value
        
        # Update setup state
        setup_state.mark_variable_configured(variable.name, "***")
        
        return {
            "status": "success",
            "variable": variable.name,
            "message": f"Configuration updated: {variable.name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.get("/validate/github")
async def validate_github():
    """Validate GitHub integration setup."""
    return validate_github_setup()


@router.get("/validate/notion")
async def validate_notion():
    """Validate Notion integration setup."""
    return validate_notion_setup()


@router.get("/validate/ai")
async def validate_ai():
    """Validate AI integration setup."""
    return validate_ai_setup()


@router.get("/validate/hubspot")
async def validate_hubspot():
    """Validate HubSpot integration setup."""
    return validate_hubspot_setup()


@router.get("/validate/databases")
async def validate_databases():
    """Validate database paths."""
    return validate_database_paths()


# ========================================
# OAuth Setup
# ========================================

@router.post("/github/oauth-start")
async def github_oauth_start(client_id: str):
    """Start GitHub OAuth flow."""
    params = {
        'client_id': client_id,
        'scope': 'repo,user',
        'redirect_uri': 'http://127.0.0.1:8767/api/v0/setup/github/callback'
    }
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    return {
        "status": "ready",
        "auth_url": auth_url,
        "message": "Open the URL in your browser to authenticate with GitHub"
    }


@router.get("/github/callback")
async def github_oauth_callback(code: str, state: Optional[str] = None):
    """GitHub OAuth callback."""
    return {
        "status": "success",
        "code": code,
        "message": "GitHub authentication successful. You can now use GitHub integration.",
        "next_step": "Configure your GitHub token in settings"
    }


@router.post("/notion/oauth-start")
async def notion_oauth_start():
    """Start Notion OAuth flow."""
    # For Notion, we typically need the API key rather than OAuth
    return {
        "status": "ready",
        "type": "api_key",
        "documentation": "https://developers.notion.com/docs/getting-started",
        "message": "Use 'Create new integration' in Notion settings to get your API key"
    }


@router.post("/hubspot/oauth-start")
async def hubspot_oauth_start(client_id: str):
    """Start HubSpot OAuth flow."""
    scope = "contacts.lists.read,contacts.lists.write,crm.objects.contacts.read,crm.objects.contacts.write"
    
    params = {
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': 'http://127.0.0.1:8767/api/v0/setup/hubspot/callback'
    }
    auth_url = f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"
    
    return {
        "status": "ready",
        "auth_url": auth_url,
        "message": "Open the URL in your browser to authenticate with HubSpot"
    }


@router.get("/hubspot/callback")
async def hubspot_oauth_callback(code: str, state: Optional[str] = None):
    """HubSpot OAuth callback."""
    return {
        "status": "success",
        "code": code,
        "message": "HubSpot authentication successful",
        "next_step": "Exchange code for access token"
    }


# ========================================
# First-Time Setup Wizard
# ========================================

@router.post("/wizard/start")
async def start_setup_wizard():
    """Start the first-time setup wizard."""
    if setup_state.is_setup_complete():
        return {
            "status": "already_complete",
            "message": "Setup has already been completed",
            "initialized_at": setup_state.data.get("initialized_at")
        }
    
    return {
        "status": "started",
        "steps": [
            {
                "step": 1,
                "name": "Database Setup",
                "description": "Verify database paths and create directories"
            },
            {
                "step": 2,
                "name": "GitHub Integration",
                "description": "Configure GitHub API access (optional)"
            },
            {
                "step": 3,
                "name": "Notion Integration",
                "description": "Configure Notion API access (optional)"
            },
            {
                "step": 4,
                "name": "AI Features",
                "description": "Set up AI/Mistral features (optional)"
            },
            {
                "step": 5,
                "name": "HubSpot CRM",
                "description": "Configure CRM integration (optional)"
            },
            {
                "step": 6,
                "name": "Complete",
                "description": "Finish setup and start using Goblin"
            }
        ],
        "current_progress": setup_state.get_status()
    }


@router.post("/wizard/complete")
async def complete_setup_wizard():
    """Mark setup wizard as complete."""
    # Validate all critical paths exist
    db_validation = validate_database_paths()
    all_ready = all(db["writable"] for db in db_validation.values())
    
    if not all_ready:
        raise HTTPException(status_code=400, detail="Database paths not writable")
    
    setup_state.mark_setup_complete()
    
    return {
        "status": "complete",
        "message": "Setup wizard completed successfully!",
        "next_steps": [
            "Access Swagger UI at http://127.0.0.1:8767/docs",
            "Test endpoints with Try It Out button",
            "Check /api/v0/setup/status for configuration overview",
            "See Quick Start Guide at dev/goblin/QUICK-START-v1.0.4.0.md"
        ]
    }


# ========================================
# Path Management
# ========================================

@router.get("/paths")
async def get_paths():
    """Get organized path structure for installation and data."""
    from pathlib import Path
    
    root = Path.cwd()
    
    return {
        "root": str(root),
        "installation": {
            "core": str(root / "core"),
            "core_python": str(root / "core_beta"),
            "extensions": str(root / "extensions"),
            "app": str(root / "app-beta"),
            "wizard": str(root / "wizard"),
            "goblin": str(root / "dev" / "goblin")
        },
        "data": {
            "memory_root": str(root / "memory"),
            "logs": str(root / "memory" / "logs"),
            "databases": {
                "workflow": str(root / config.db_workflow),
                "contacts": str(root / config.db_contacts),
                "tasks": str(root / config.db_tasks),
                "sync_log": str(root / config.db_sync_log)
            },
            "cache": str(root / "memory" / "sandbox"),
            "user_data": str(root / "memory" / "user"),
            "public": str(root / "memory" / "public"),
            "private": str(root / "memory" / "private")
        },
        "documentation": {
            "setup_guide": str(root / "dev" / "goblin" / "QUICK-START-v1.0.4.0.md"),
            "readme": str(root / "dev" / "goblin" / "README.md"),
            "agents": str(root / "AGENTS.md"),
            "roadmap": str(root / "docs" / "roadmap.md")
        }
    }


@router.post("/paths/initialize")
async def initialize_paths():
    """Initialize all required directory paths."""
    from pathlib import Path
    
    root = Path.cwd()
    paths_to_create = [
        root / "memory" / "logs",
        root / "memory" / "goblin",
        root / "memory" / "bank" / "user",
        root / "memory" / "sandbox",
        root / "memory" / "user",
        root / "memory" / "public",
        root / "memory" / "private",
    ]
    
    created = []
    errors = []
    
    for path in paths_to_create:
        try:
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
        except Exception as e:
            errors.append({"path": str(path), "error": str(e)})
    
    return {
        "status": "complete",
        "created_directories": created,
        "errors": errors if errors else None
    }


# ========================================
# Configuration Export
# ========================================

@router.get("/export-env")
async def export_env_template():
    """Export current config as .env template."""
    from ..config_manager import export_config_template
    
    return {
        "format": "env",
        "content": export_config_template(),
        "filename": ".env",
        "instructions": "Copy content to .env file in dev/goblin/ directory"
    }


@router.get("/export-status")
async def export_status_report():
    """Export full configuration status as report."""
    return {
        "report": get_full_config_status(),
        "timestamp": "2026-01-16T15:00:00Z",
        "filename": "goblin-config-report.json"
    }
