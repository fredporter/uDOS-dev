"""
AI Test Command Handler for uDOS TUI.

Commands to test AI API connections and view configuration:
- AI TEST - Test all configured providers
- AI TEST <provider> - Test specific provider
- AI STATUS - Show provider status and quotas
- AI PROMPTS - Show available prompt templates
- AI KEYS - Check which API keys are configured
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from dev.goblin.core.ui.content_grid import ContentGrid


def handle_ai_test_command(
    params: str, grid: Optional["ContentGrid"] = None, parser: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Handle AI TEST commands.

    Args:
        params: Command parameters
        grid: Content grid for display
        parser: Smart prompt parser

    Returns:
        Command result dict
    """
    parts = params.strip().split(maxsplit=1)
    subcommand = parts[0].upper() if parts else ""

    if not subcommand or subcommand == "TEST":
        provider = parts[1].lower() if len(parts) > 1 else None
        return _test_providers(provider, grid)
    elif subcommand == "STATUS":
        return _show_status(grid)
    elif subcommand == "PROMPTS":
        return _show_prompts(grid)
    elif subcommand == "KEYS":
        return _show_keys(grid)
    elif subcommand == "HELP":
        return _show_help(grid)
    else:
        # Assume it's a provider name for testing
        return _test_providers(subcommand.lower(), grid)


def _test_providers(
    provider: Optional[str] = None, grid: Optional["ContentGrid"] = None
) -> Dict[str, Any]:
    """Test AI provider connections."""
    lines = [
        "╔════════════════════════════════════════╗",
        "║         🤖 AI CONNECTION TEST          ║",
        "╚════════════════════════════════════════╝",
        "",
    ]

    results = {}
    providers_to_test = []

    if provider:
        providers_to_test = [provider]
    else:
        providers_to_test = ["gemini", "anthropic", "openai", "devstral"]

    for prov in providers_to_test:
        result = _test_single_provider(prov)
        results[prov] = result

        if result["configured"]:
            if result["success"]:
                status = "✅ Connected"
                model = result.get("model", "unknown")
                lines.append(f"  {prov.upper():12} {status} ({model})")
                if result.get("response_preview"):
                    lines.append(
                        f"                 Response: {result['response_preview'][:40]}..."
                    )
            else:
                lines.append(
                    f"  {prov.upper():12} ❌ Error: {result.get('error', 'Unknown')}"
                )
        else:
            lines.append(f"  {prov.upper():12} ⚠️  Not configured (no API key)")

    lines.append("")

    # Summary
    configured = sum(1 for r in results.values() if r["configured"])
    working = sum(1 for r in results.values() if r["success"])

    lines.extend(
        [
            "────────────────────────────────────────",
            f"  {configured}/{len(providers_to_test)} configured, {working}/{len(providers_to_test)} working",
            "",
        ]
    )

    if working == 0 and configured == 0:
        lines.extend(
            [
                "  💡 To configure API keys:",
                "     1. Copy wizard/config/ai_keys.template.json",
                "        to wizard/config/ai_keys.json",
                "     2. Add your API keys",
                "     3. Run AI TEST again",
                "",
            ]
        )

    if grid:
        grid.set_content("\n".join(lines), wrap=False)

    return {
        "success": working > 0,
        "message": f"{working}/{len(providers_to_test)} providers working",
        "results": results,
        "content": "\n".join(lines),
    }


def _test_single_provider(provider: str) -> Dict[str, Any]:
    """Test a single AI provider."""
    result = {
        "provider": provider,
        "configured": False,
        "success": False,
        "model": None,
        "response_preview": None,
        "error": None,
        "latency_ms": 0,
    }

    try:
        if provider == "gemini":
            return _test_gemini()
        elif provider == "anthropic":
            return _test_anthropic()
        elif provider == "openai":
            return _test_openai()
        elif provider == "devstral":
            return _test_devstral()
        else:
            result["error"] = f"Unknown provider: {provider}"
            return result
    except Exception as e:
        result["error"] = str(e)
        return result


def _test_gemini() -> Dict[str, Any]:
    """Test Gemini connection."""
    result = {
        "provider": "gemini",
        "configured": False,
        "success": False,
        "model": None,
        "response_preview": None,
        "error": None,
    }

    try:
        from wizard.providers.gemini_client import GeminiClient, GeminiRequest

        client = GeminiClient()

        if not client.api_key:
            result["error"] = "No API key"
            return result

        result["configured"] = True

        # Simple test prompt
        request = GeminiRequest(
            prompt="Reply with exactly: 'Gemini connected successfully'",
            max_tokens=50,
            temperature=0.0,
        )

        response = client.complete(request)

        if response.success:
            result["success"] = True
            result["model"] = response.model
            result["response_preview"] = response.content[:100]
            result["latency_ms"] = response.latency_ms
        else:
            result["error"] = response.error

        return result

    except ImportError:
        result["error"] = "google-generativeai package not installed"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def _test_anthropic() -> Dict[str, Any]:
    """Test Anthropic Claude connection."""
    result = {
        "provider": "anthropic",
        "configured": False,
        "success": False,
        "model": None,
        "response_preview": None,
        "error": None,
    }

    try:
        from wizard.providers.anthropic_client import AnthropicClient, AnthropicRequest

        client = AnthropicClient()

        if not client.api_key:
            result["error"] = "No API key"
            return result

        result["configured"] = True

        request = AnthropicRequest(
            prompt="Reply with exactly: 'Claude connected successfully'",
            max_tokens=50,
            temperature=0.0,
        )

        response = client.complete(request)

        if response.success:
            result["success"] = True
            result["model"] = response.model
            result["response_preview"] = response.content[:100]
            result["latency_ms"] = response.latency_ms
        else:
            result["error"] = response.error

        return result

    except ImportError:
        result["error"] = "anthropic package not installed"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def _test_openai() -> Dict[str, Any]:
    """Test OpenAI connection."""
    result = {
        "provider": "openai",
        "configured": False,
        "success": False,
        "model": None,
        "response_preview": None,
        "error": None,
    }

    try:
        from wizard.providers.openai_client import OpenAIClient, OpenAIRequest

        client = OpenAIClient()

        if not client.api_key:
            result["error"] = "No API key"
            return result

        result["configured"] = True

        request = OpenAIRequest(
            prompt="Reply with exactly: 'OpenAI connected successfully'",
            max_tokens=50,
            temperature=0.0,
        )

        response = client.complete(request)

        if response.success:
            result["success"] = True
            result["model"] = response.model
            result["response_preview"] = response.content[:100]
            result["latency_ms"] = response.latency_ms
        else:
            result["error"] = response.error

        return result

    except ImportError:
        result["error"] = "openai package not installed"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def _test_devstral() -> Dict[str, Any]:
    """Test Devstral/Mistral connection."""
    result = {
        "provider": "devstral",
        "configured": False,
        "success": False,
        "model": None,
        "response_preview": None,
        "error": None,
    }

    try:
        from wizard.providers.devstral_client import DevstralClient, DevstralRequest

        client = DevstralClient()

        if not client.api_key:
            result["error"] = "No API key"
            return result

        result["configured"] = True

        request = DevstralRequest(
            prompt="Reply with exactly: 'Devstral connected successfully'",
            max_tokens=50,
            temperature=0.0,
        )

        response = client.complete(request)

        if response.success:
            result["success"] = True
            result["model"] = response.model
            result["response_preview"] = response.content[:100]
            result["latency_ms"] = response.latency_ms
        else:
            result["error"] = response.error

        return result

    except ImportError:
        result["error"] = "mistralai package not installed"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def _show_status(grid: Optional["ContentGrid"] = None) -> Dict[str, Any]:
    """Show AI provider status with quotas."""
    lines = [
        "╔════════════════════════════════════════╗",
        "║         📊 AI PROVIDER STATUS          ║",
        "╚════════════════════════════════════════╝",
        "",
    ]

    # Try to get quota info
    try:
        from wizard.services.quota_tracker import QuotaTracker

        tracker = QuotaTracker()

        ai_providers = ["gemini", "anthropic", "openai", "mistral", "devstral"]

        for prov in ai_providers:
            try:
                status = tracker.get_quota_status(prov)
                if status:
                    cost = status.get("daily", {}).get("cost", 0)
                    budget = status.get("daily", {}).get("budget", 0)
                    requests = status.get("daily", {}).get("requests", 0)
                    limit = status.get("daily", {}).get("limit", 0)

                    status_icon = {
                        "ok": "✅",
                        "warning": "🟡",
                        "critical": "🔴",
                        "exceeded": "⛔",
                    }.get(status.get("status", ""), "❓")

                    lines.append(f"  {prov.upper():12} {status_icon}")
                    lines.append(f"               Cost: ${cost:.4f} / ${budget:.2f}")
                    lines.append(f"               Requests: {requests} / {limit}")
                    lines.append("")
            except Exception:
                pass

    except ImportError:
        lines.append("  Quota tracker not available")
        lines.append("")

    if grid:
        grid.set_content("\n".join(lines), wrap=False)

    return {
        "success": True,
        "message": "AI provider status",
        "content": "\n".join(lines),
    }


def _show_prompts(grid: Optional["ContentGrid"] = None) -> Dict[str, Any]:
    """Show available prompt templates."""
    lines = [
        "╔════════════════════════════════════════╗",
        "║         📝 PROMPT TEMPLATES            ║",
        "╚════════════════════════════════════════╝",
        "",
    ]

    prompts_dir = Path(__file__).parent.parent / "data" / "prompts"

    if prompts_dir.exists():
        # Load main prompts config
        gemini_prompts = prompts_dir / "gemini_prompts.json"
        if gemini_prompts.exists():
            import json

            try:
                data = json.loads(gemini_prompts.read_text())
                prompts = data.get("prompts", {})

                lines.append("  📄 gemini_prompts.json:")
                for name, config in prompts.items():
                    desc = config.get("description", "")[:40]
                    lines.append(f"     • {name}")
                    if desc:
                        lines.append(f"       {desc}")
                lines.append("")
            except Exception:
                pass

        # Graphics prompts
        graphics_dir = prompts_dir / "graphics"
        if graphics_dir.exists():
            lines.append("  🎨 Graphics Prompts:")
            for subdir in graphics_dir.iterdir():
                if subdir.is_dir():
                    files = list(subdir.glob("*.md"))
                    lines.append(f"     • {subdir.name}/ ({len(files)} templates)")
            lines.append("")
    else:
        lines.append("  No prompts directory found")
        lines.append("")

    lines.extend(
        [
            "────────────────────────────────────────",
            "  Use MAKE <type> <topic> to generate content",
            "",
        ]
    )

    if grid:
        grid.set_content("\n".join(lines), wrap=False)

    return {
        "success": True,
        "message": "Available prompt templates",
        "content": "\n".join(lines),
    }


def _show_keys(grid: Optional["ContentGrid"] = None) -> Dict[str, Any]:
    """Show which API keys are configured (not the actual keys)."""
    lines = [
        "╔════════════════════════════════════════╗",
        "║         🔑 API KEY STATUS              ║",
        "╚════════════════════════════════════════╝",
        "",
    ]

    import os

    # Check environment variables
    env_keys = {
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY"),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "MISTRAL_API_KEY": os.environ.get("MISTRAL_API_KEY"),
    }

    lines.append("  Environment Variables:")
    for key, value in env_keys.items():
        if value:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
            lines.append(f"     ✅ {key} = {masked}")
        else:
            lines.append(f"     ⚠️  {key} = (not set)")
    lines.append("")

    # Check config file
    config_file = (
        Path(__file__).parent.parent.parent / "wizard" / "config" / "ai_keys.json"
    )
    template_file = config_file.with_suffix(".template.json")

    lines.append("  Config File:")
    if config_file.exists():
        lines.append(f"     ✅ {config_file.name} exists")
        try:
            import json

            data = json.loads(config_file.read_text())
            configured = [k for k, v in data.items() if v and not k.startswith("_")]
            if configured:
                lines.append(f"        Keys: {', '.join(configured)}")
        except Exception:
            pass
    else:
        lines.append(f"     ⚠️  {config_file.name} not found")
        if template_file.exists():
            lines.append(f"        Copy from {template_file.name}")
    lines.append("")

    lines.extend(
        [
            "────────────────────────────────────────",
            "  Run AI TEST to verify connections",
            "",
        ]
    )

    if grid:
        grid.set_content("\n".join(lines), wrap=False)

    return {"success": True, "message": "API key status", "content": "\n".join(lines)}


def _show_help(grid: Optional["ContentGrid"] = None) -> Dict[str, Any]:
    """Show AI test command help."""
    lines = [
        "╔════════════════════════════════════════╗",
        "║         🤖 AI COMMANDS                 ║",
        "╚════════════════════════════════════════╝",
        "",
        "  AI TEST              Test all AI providers",
        "  AI TEST <provider>   Test specific provider",
        "                       (gemini, anthropic, openai, devstral)",
        "  AI STATUS            Show quotas and usage",
        "  AI PROMPTS           List prompt templates",
        "  AI KEYS              Check API key config",
        "",
        "  Related Commands:",
        "    MAKE <type> <topic>  Generate content",
        "    QUOTA                View API quotas",
        "",
    ]

    if grid:
        grid.set_content("\n".join(lines), wrap=False)

    return {"success": True, "message": "AI command help", "content": "\n".join(lines)}
