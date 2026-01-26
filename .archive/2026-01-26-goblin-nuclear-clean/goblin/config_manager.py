"""
Configuration Management for Goblin Dev Server

Handles environment variables, setup, and configuration validation.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

# Load .env file if it exists
ENV_FILE = Path(__file__).parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class GoblinConfig(BaseModel):
    """Goblin server configuration from environment variables."""
    
    model_config = ConfigDict(case_sensitive=False, extra="allow")
    
    # Server
    goblin_host: str = Field(default="127.0.0.1")
    goblin_port: int = Field(default=8767)
    goblin_env: str = Field(default="development")
    goblin_log_level: str = Field(default="INFO")
    
    # GitHub
    github_token: Optional[str] = Field(default=None)
    github_repo_owner: str = Field(default="fredporter")
    github_repo_name: str = Field(default="uDOS")
    
    # Notion
    notion_api_key: Optional[str] = Field(default=None)
    notion_database_id: Optional[str] = Field(default=None)
    
    # Mistral/Vibe
    mistral_api_key: Optional[str] = Field(default=None)
    mistral_api_url: str = Field(default="https://api.mistral.ai/v1")
    
    # HubSpot
    hubspot_api_key: Optional[str] = Field(default=None)
    hubspot_access_token: Optional[str] = Field(default=None)
    
    # Database paths (relative to uDOS root)
    db_workflow: str = Field(default="memory/goblin/workflow.db")
    db_contacts: str = Field(default="memory/bank/user/contacts.db")
    db_tasks: str = Field(default="memory/goblin/tasks.db")
    db_sync_log: str = Field(default="memory/goblin/notion_sync.db")
    
    # Logging
    log_dir: str = Field(default="memory/logs")
    log_file_pattern: str = Field(default="goblin-{datetime}.log")
    debug_mode: bool = Field(default=False)
    
    # ngrok
    ngrok_authtoken: Optional[str] = Field(default=None)
    ngrok_domain: Optional[str] = Field(default=None)
    
    # Security
    webhook_secret_key: Optional[str] = Field(default=None)
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    )
    
    # Feature flags
    enable_notion_sync: bool = Field(default=True)
    enable_github_integration: bool = Field(default=True)
    enable_ai_features: bool = Field(default=True)
    enable_workflow_manager: bool = Field(default=True)
    enable_public_url: bool = Field(default=True)
    
    # Development
    auto_reload: bool = Field(default=True)
    include_swagger_ui: bool = Field(default=True)
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables."""
        return cls(
            goblin_host=os.getenv("GOBLIN_HOST", "127.0.0.1"),
            goblin_port=int(os.getenv("GOBLIN_PORT", "8767")),
            goblin_env=os.getenv("GOBLIN_ENV", "development"),
            goblin_log_level=os.getenv("GOBLIN_LOG_LEVEL", "INFO"),
            github_token=os.getenv("GITHUB_TOKEN"),
            github_repo_owner=os.getenv("GITHUB_REPO_OWNER", "fredporter"),
            github_repo_name=os.getenv("GITHUB_REPO_NAME", "uDOS"),
            notion_api_key=os.getenv("NOTION_API_KEY"),
            notion_database_id=os.getenv("NOTION_DATABASE_ID"),
            mistral_api_key=os.getenv("MISTRAL_API_KEY"),
            mistral_api_url=os.getenv("MISTRAL_API_URL", "https://api.mistral.ai/v1"),
            hubspot_api_key=os.getenv("HUBSPOT_API_KEY"),
            hubspot_access_token=os.getenv("HUBSPOT_ACCESS_TOKEN"),
            db_workflow=os.getenv("DB_WORKFLOW", "memory/goblin/workflow.db"),
            db_contacts=os.getenv("DB_CONTACTS", "memory/bank/user/contacts.db"),
            db_tasks=os.getenv("DB_TASKS", "memory/goblin/tasks.db"),
            db_sync_log=os.getenv("DB_SYNC_LOG", "memory/goblin/notion_sync.db"),
            log_dir=os.getenv("LOG_DIR", "memory/logs"),
            log_file_pattern=os.getenv("LOG_FILE_PATTERN", "goblin-{datetime}.log"),
            debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
            ngrok_authtoken=os.getenv("NGROK_AUTHTOKEN"),
            ngrok_domain=os.getenv("NGROK_DOMAIN"),
            webhook_secret_key=os.getenv("WEBHOOK_SECRET_KEY"),
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"),
            enable_notion_sync=os.getenv("ENABLE_NOTION_SYNC", "true").lower() == "true",
            enable_github_integration=os.getenv("ENABLE_GITHUB_INTEGRATION", "true").lower() == "true",
            enable_ai_features=os.getenv("ENABLE_AI_FEATURES", "true").lower() == "true",
            enable_workflow_manager=os.getenv("ENABLE_WORKFLOW_MANAGER", "true").lower() == "true",
            enable_public_url=os.getenv("ENABLE_PUBLIC_URL", "true").lower() == "true",
            auto_reload=os.getenv("AUTO_RELOAD", "true").lower() == "true",
            include_swagger_ui=os.getenv("INCLUDE_SWAGGER_UI", "true").lower() == "true",
        )


# Global config instance
config = GoblinConfig.from_env()


# ========================================
# Setup State Management
# ========================================

class SetupState:
    """Tracks setup progress and required variables."""
    
    def __init__(self, state_file: str = "memory/goblin/setup-state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load setup state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except:
                return {}
        return {
            "setup_complete": False,
            "initialized_at": None,
            "variables_configured": [],
            "services_enabled": []
        }
    
    def _save_state(self):
        """Save setup state to file."""
        with open(self.state_file, "w") as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def mark_variable_configured(self, variable: str, value: str = "***"):
        """Mark a variable as configured."""
        if variable not in self.data.get("variables_configured", []):
            self.data.setdefault("variables_configured", []).append(variable)
        self._save_state()
    
    def mark_service_enabled(self, service: str):
        """Mark a service as enabled."""
        if service not in self.data.get("services_enabled", []):
            self.data.setdefault("services_enabled", []).append(service)
        self._save_state()
    
    def mark_setup_complete(self):
        """Mark initial setup as complete."""
        import datetime
        self.data["setup_complete"] = True
        self.data["initialized_at"] = datetime.datetime.now().isoformat()
        self._save_state()
    
    def is_setup_complete(self) -> bool:
        """Check if initial setup is complete."""
        return self.data.get("setup_complete", False)
    
    def get_status(self) -> Dict[str, Any]:
        """Get setup status."""
        return {
            "setup_complete": self.data.get("setup_complete", False),
            "initialized_at": self.data.get("initialized_at"),
            "variables_configured": self.data.get("variables_configured", []),
            "services_enabled": self.data.get("services_enabled", []),
            "total_variables": len(self.data.get("variables_configured", [])),
            "total_services": len(self.data.get("services_enabled", []))
        }


# Global setup state instance
setup_state = SetupState()


# ========================================
# Configuration Validation
# ========================================

def validate_github_setup() -> Dict[str, Any]:
    """Validate GitHub integration configuration."""
    return {
        "configured": bool(config.github_token),
        "method": "token" if config.github_token else "gh-cli",
        "token_present": bool(config.github_token),
        "repo": f"{config.github_repo_owner}/{config.github_repo_name}",
        "status": "ready" if (config.github_token or _check_gh_cli_installed()) else "not-configured"
    }


def validate_notion_setup() -> Dict[str, Any]:
    """Validate Notion integration configuration."""
    return {
        "configured": bool(config.notion_api_key),
        "has_api_key": bool(config.notion_api_key),
        "has_database_id": bool(config.notion_database_id),
        "status": "ready" if (config.notion_api_key and config.notion_database_id) else "not-configured"
    }


def validate_ai_setup() -> Dict[str, Any]:
    """Validate AI/Mistral integration configuration."""
    return {
        "configured": bool(config.mistral_api_key),
        "has_api_key": bool(config.mistral_api_key),
        "api_url": config.mistral_api_url,
        "vibe_cli_installed": _check_vibe_cli_installed(),
        "status": "ready" if (config.mistral_api_key or _check_vibe_cli_installed()) else "not-configured"
    }


def validate_hubspot_setup() -> Dict[str, Any]:
    """Validate HubSpot integration configuration."""
    return {
        "configured": bool(config.hubspot_api_key or config.hubspot_access_token),
        "has_api_key": bool(config.hubspot_api_key),
        "has_access_token": bool(config.hubspot_access_token),
        "status": "ready" if (config.hubspot_api_key or config.hubspot_access_token) else "not-configured"
    }


def validate_database_paths() -> Dict[str, Any]:
    """Validate database paths exist or are creatable."""
    from pathlib import Path
    
    paths = {
        "workflow": config.db_workflow,
        "contacts": config.db_contacts,
        "tasks": config.db_tasks,
        "sync_log": config.db_sync_log
    }
    
    results = {}
    for name, path in paths.items():
        full_path = Path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        results[name] = {
            "path": str(full_path),
            "exists": full_path.exists(),
            "writable": full_path.parent.is_dir() and os.access(full_path.parent, os.W_OK)
        }
    
    return results


def get_full_config_status() -> Dict[str, Any]:
    """Get complete configuration status."""
    return {
        "server": {
            "host": config.goblin_host,
            "port": config.goblin_port,
            "environment": config.goblin_env,
            "debug": config.debug_mode
        },
        "services": {
            "github": validate_github_setup(),
            "notion": validate_notion_setup(),
            "ai": validate_ai_setup(),
            "hubspot": validate_hubspot_setup()
        },
        "databases": validate_database_paths(),
        "setup": setup_state.get_status(),
        "features": {
            "notion_sync": config.enable_notion_sync,
            "github_integration": config.enable_github_integration,
            "ai_features": config.enable_ai_features,
            "workflow_manager": config.enable_workflow_manager,
            "public_url": config.enable_public_url
        },
        "logging": {
            "directory": config.log_dir,
            "level": config.goblin_log_level
        }
    }


# ========================================
# Helper Functions
# ========================================

def _check_gh_cli_installed() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    import subprocess
    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False


def _check_vibe_cli_installed() -> bool:
    """Check if Vibe CLI is installed."""
    import subprocess
    try:
        result = subprocess.run(["which", "vibe"], capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False


def get_required_variables() -> Dict[str, Dict[str, Any]]:
    """Get list of required variables and their status."""
    return {
        "github_token": {
            "name": "GitHub API Token",
            "description": "Personal access token for GitHub API access",
            "env_var": "GITHUB_TOKEN",
            "required": False,
            "status": "configured" if config.github_token else "optional",
            "documentation": "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
        },
        "notion_api_key": {
            "name": "Notion API Key",
            "description": "API key for Notion workspace access",
            "env_var": "NOTION_API_KEY",
            "required": config.enable_notion_sync,
            "status": "configured" if config.notion_api_key else "not-configured",
            "documentation": "https://developers.notion.com/docs/getting-started"
        },
        "notion_database_id": {
            "name": "Notion Database ID",
            "description": "ID of your main Notion database",
            "env_var": "NOTION_DATABASE_ID",
            "required": config.enable_notion_sync,
            "status": "configured" if config.notion_database_id else "not-configured",
            "documentation": "https://developers.notion.com/docs/working-with-databases"
        },
        "mistral_api_key": {
            "name": "Mistral API Key (Optional)",
            "description": "API key for cloud AI features via Mistral",
            "env_var": "MISTRAL_API_KEY",
            "required": False,
            "status": "configured" if config.mistral_api_key else "optional",
            "documentation": "https://docs.mistral.ai/"
        },
        "hubspot_api_key": {
            "name": "HubSpot API Key",
            "description": "API key for HubSpot CRM integration",
            "env_var": "HUBSPOT_API_KEY",
            "required": False,
            "status": "configured" if config.hubspot_api_key else "optional",
            "documentation": "https://developers.hubspot.com/docs/api/overview"
        }
    }


def export_config_template() -> str:
    """Export current config as .env template."""
    lines = [
        "# uDOS Goblin Dev Server Configuration",
        "# Generated from current environment",
        "",
    ]
    
    for key, value in config.dict().items():
        env_key = key.upper()
        if isinstance(value, bool):
            value = str(value).lower()
        lines.append(f"{env_key}={value or ''}")
    
    return "\n".join(lines)
