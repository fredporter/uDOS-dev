"""
AI Generation Service
=====================

Unified AI generation service for uDOS that:
1. Integrates with Gemini (primary) and Mistral/Devstral (secondary)
2. Uses layer-themed prompts from template system
3. Supports MAKE/REDO/UNDO command workflows
4. Handles offline fallbacks gracefully

Version: 1.0.0
Alpha: v1.0.0.62+
"""

import asyncio
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from dev.goblin.core.services.logging_manager import get_logger
from dev.goblin.core.services.template_loader import (
    get_template_loader,
    get_template_for_layer,
    get_ai_prompt,
    LayerTheme,
)

logger = get_logger("ai-generation")

# Lazy import flags for providers
_gemini_available = None
_devstral_available = None


def _check_gemini():
    """Check if Gemini is available."""
    global _gemini_available
    if _gemini_available is None:
        try:
            # Try different import paths
            try:
                from wizard.providers.gemini_client import GeminiClient
            except ImportError:
                from extensions.wizard_server.providers.gemini_client import (
                    GeminiClient,
                )
            _gemini_available = True
        except ImportError:
            _gemini_available = False
    return _gemini_available


def _check_devstral():
    """Check if Devstral is available."""
    global _devstral_available
    if _devstral_available is None:
        try:
            try:
                from wizard.providers.devstral_client import DevstralClient
            except ImportError:
                from extensions.wizard_server.providers.devstral_client import (
                    DevstralClient,
                )
            _devstral_available = True
        except ImportError:
            _devstral_available = False
    return _devstral_available


def _get_gemini_client():
    """Get Gemini client with fallback import paths."""
    try:
        from wizard.providers.gemini_client import GeminiClient

        return GeminiClient()
    except ImportError:
        pass
    try:
        from extensions.wizard_server.providers.gemini_client import GeminiClient

        return GeminiClient()
    except ImportError:
        pass
    return None


def _get_devstral_client():
    """Get Devstral client with fallback import paths."""
    try:
        from wizard.providers.devstral_client import DevstralClient

        return DevstralClient()
    except ImportError:
        pass
    try:
        from extensions.wizard_server.providers.devstral_client import DevstralClient

        return DevstralClient()
    except ImportError:
        pass
    return None


class AIProvider(Enum):
    """Available AI providers."""

    GEMINI = "gemini"
    MISTRAL = "mistral"
    DEVSTRAL = "devstral"
    VIBE_CLI = "vibe"  # Mistral vibe CLI
    OFFLINE = "offline"


class GenerationType(Enum):
    """Types of generation requests."""

    MAKE_GUIDE = auto()  # Survival/knowledge guide
    MAKE_DO = auto()  # Practical task help
    SUGGEST = auto()  # Workflow suggestions
    ENCOUNTER = auto()  # Layer-specific encounter
    ENCYCLOPEDIA = auto()  # Encyclopedia entry
    CUSTOM = auto()  # Custom prompt


@dataclass
class GenerationRequest:
    """AI generation request."""

    prompt: str
    gen_type: GenerationType = GenerationType.CUSTOM
    layer_id: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 2000
    temperature: float = 0.7
    provider: Optional[AIProvider] = None  # Auto-select if None


@dataclass
class GenerationResponse:
    """AI generation response."""

    success: bool
    content: str = ""
    provider: Optional[AIProvider] = None
    model: str = ""
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: Optional[str] = None
    fallback_used: bool = False
    layer_theme: Optional[LayerTheme] = None


class AIGenerationService:
    """
    Unified AI generation service with template theming.

    Provider priority:
    1. Gemini (if configured) - fast, cost-effective
    2. Mistral/Devstral (if configured) - good for coding
    3. Vibe CLI (if installed) - local Mistral CLI
    4. Offline fallback - template-based responses

    Integrations:
    - QuotaTracker for usage limits and cost tracking
    - RequestWorkflowService for task/mission linkage
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize AI generation service."""
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Provider clients (lazy-loaded)
        self._gemini_client = None
        self._devstral_client = None

        # Vibe CLI path (if installed)
        self._vibe_cli = shutil.which("vibe")

        # Template loader
        self._template_loader = get_template_loader()

        # Quota tracker (lazy import to avoid circular deps)
        self._quota_tracker = None

        # Check available providers
        self._available_providers = self._detect_providers()

        logger.info(
            f"[LOCAL] AIGenerationService: providers={list(self._available_providers)}"
        )

    def _detect_providers(self) -> List[AIProvider]:
        """Detect available AI providers."""
        providers = []

        # Check Gemini
        if _check_gemini():
            client = _get_gemini_client()
            if client and client.api_key:
                providers.append(AIProvider.GEMINI)

        # Check Mistral/Devstral
        if _check_devstral():
            client = _get_devstral_client()
            if client and client.config.api_key:
                providers.append(AIProvider.DEVSTRAL)
                providers.append(AIProvider.MISTRAL)

        # Check Vibe CLI
        if self._vibe_cli:
            providers.append(AIProvider.VIBE_CLI)

        # Offline always available
        providers.append(AIProvider.OFFLINE)

        return providers

    def _get_quota_tracker(self):
        """Get quota tracker with lazy loading."""
        if self._quota_tracker is None:
            try:
                from wizard.services.quota_tracker import (
                    get_quota_tracker,
                    APIProvider as QuotaProvider,
                )

                self._quota_tracker = get_quota_tracker()
            except ImportError:
                logger.debug("[LOCAL] QuotaTracker not available")
        return self._quota_tracker

    def _check_quota(self, provider: AIProvider, estimated_tokens: int = 1000) -> bool:
        """Check if request is allowed by quota."""
        tracker = self._get_quota_tracker()
        if not tracker:
            return True  # No tracker, allow

        try:
            from wizard.services.quota_tracker import APIProvider as QuotaProvider

            # Map AI provider to quota provider
            provider_map = {
                AIProvider.GEMINI: QuotaProvider.GEMINI,
                AIProvider.MISTRAL: QuotaProvider.MISTRAL,
                AIProvider.DEVSTRAL: QuotaProvider.DEVSTRAL,
                AIProvider.VIBE_CLI: QuotaProvider.OFFLINE,
                AIProvider.OFFLINE: QuotaProvider.OFFLINE,
            }
            quota_provider = provider_map.get(provider, QuotaProvider.OFFLINE)
            return tracker.can_request(quota_provider, estimated_tokens)
        except Exception:
            return True

    def _record_usage(
        self,
        provider: AIProvider,
        input_tokens: int,
        output_tokens: int,
        cost: float = None,
    ):
        """Record API usage to quota tracker."""
        tracker = self._get_quota_tracker()
        if not tracker:
            return

        try:
            from wizard.services.quota_tracker import APIProvider as QuotaProvider

            provider_map = {
                AIProvider.GEMINI: QuotaProvider.GEMINI,
                AIProvider.MISTRAL: QuotaProvider.MISTRAL,
                AIProvider.DEVSTRAL: QuotaProvider.DEVSTRAL,
                AIProvider.VIBE_CLI: QuotaProvider.VIBE_CLI,
                AIProvider.OFFLINE: QuotaProvider.OFFLINE,
            }
            quota_provider = provider_map.get(provider, QuotaProvider.OFFLINE)
            tracker.record_request(quota_provider, input_tokens, output_tokens, cost)
        except Exception as e:
            logger.debug(f"[LOCAL] Failed to record usage: {e}")

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate content using available AI providers.

        Args:
            request: Generation request with prompt and parameters

        Returns:
            GenerationResponse with content or fallback
        """
        # Get themed prompt
        template = self._template_loader.get_for_layer(request.layer_id)
        layer_theme = template.layer_theme

        # Build system prompt from template
        system_prompt = self._build_system_prompt(request, template)

        # Select provider
        provider = request.provider or self._select_provider(request)

        # Check quota before making request
        estimated_tokens = request.max_tokens + len(request.prompt.split()) * 2
        if not self._check_quota(provider, estimated_tokens):
            logger.warning(f"[LOCAL] Quota exceeded for {provider.value}, falling back")
            # Try next provider or go offline
            if provider != AIProvider.OFFLINE:
                fallback_providers = [
                    p for p in self._available_providers if p != provider
                ]
                for fallback in fallback_providers:
                    if self._check_quota(fallback, estimated_tokens):
                        provider = fallback
                        break
                else:
                    provider = AIProvider.OFFLINE

        # Try generation with fallback chain
        response = await self._try_generation(request, provider, system_prompt)
        response.layer_theme = layer_theme

        # Record usage if successful
        if response.success and response.tokens_used > 0:
            input_tokens = len(request.prompt.split()) * 2  # Rough estimate
            output_tokens = response.tokens_used - input_tokens
            self._record_usage(
                response.provider,
                input_tokens,
                max(0, output_tokens),
                response.cost_usd,
            )

        return response

    def _build_system_prompt(self, request: GenerationRequest, template) -> str:
        """Build system prompt from template and request type."""
        # Map generation type to template prompt name
        prompt_names = {
            GenerationType.MAKE_GUIDE: "make_guide",
            GenerationType.MAKE_DO: "make_do",
            GenerationType.SUGGEST: "suggest_workflow",
            GenerationType.ENCOUNTER: "encounter",
            GenerationType.ENCYCLOPEDIA: "encyclopedia_entry",
        }

        prompt_name = prompt_names.get(request.gen_type)

        if prompt_name and prompt_name in template.ai_prompts:
            return template.ai_prompts[prompt_name]

        # Default system prompt
        return f"""You are an assistant for uDOS, an offline-first knowledge system.
Current theme: {template.name} ({template.layer_theme.value if template.layer_theme else 'default'})
Style: {template.style}

Provide helpful, accurate information in the style of this theme."""

    def _select_provider(self, request: GenerationRequest) -> AIProvider:
        """Select best available provider for request."""
        # Prefer Gemini for general content
        if AIProvider.GEMINI in self._available_providers:
            return AIProvider.GEMINI

        # Use Devstral for coding-related
        if request.gen_type == GenerationType.MAKE_DO:
            if AIProvider.DEVSTRAL in self._available_providers:
                return AIProvider.DEVSTRAL

        # Try Vibe CLI
        if AIProvider.VIBE_CLI in self._available_providers:
            return AIProvider.VIBE_CLI

        # Fallback to offline
        return AIProvider.OFFLINE

    async def _try_generation(
        self, request: GenerationRequest, provider: AIProvider, system_prompt: str
    ) -> GenerationResponse:
        """Try generation with provider, falling back if needed."""

        try:
            if provider == AIProvider.GEMINI:
                return await self._generate_gemini(request, system_prompt)

            elif provider in (AIProvider.DEVSTRAL, AIProvider.MISTRAL):
                return await self._generate_mistral(request, system_prompt)

            elif provider == AIProvider.VIBE_CLI:
                return await self._generate_vibe_cli(request, system_prompt)

            else:
                return self._generate_offline(request, system_prompt)

        except Exception as e:
            logger.warning(f"[LOCAL] Provider {provider.value} failed: {e}")

            # Try next provider in fallback chain
            if provider != AIProvider.OFFLINE:
                return self._generate_offline(request, system_prompt)

            return GenerationResponse(success=False, error=str(e))

    async def _generate_gemini(
        self, request: GenerationRequest, system_prompt: str
    ) -> GenerationResponse:
        """Generate using Gemini API."""
        try:
            if self._gemini_client is None:
                self._gemini_client = _get_gemini_client()

            if not self._gemini_client or not self._gemini_client.api_key:
                raise Exception("Gemini not configured")

            # Execute request
            result = await self._gemini_client.execute(
                {
                    "prompt": request.prompt,
                    "system_prompt": system_prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "model": "gemini-1.5-flash",
                }
            )

            return GenerationResponse(
                success=result.get("success", False),
                content=result.get("content", ""),
                provider=AIProvider.GEMINI,
                model=result.get("model", "gemini-1.5-flash"),
                tokens_used=result.get("total_tokens", 0),
                cost_usd=result.get("cost_usd", 0.0),
            )

        except Exception as e:
            raise Exception(f"Gemini generation failed: {e}")

    async def _generate_mistral(
        self, request: GenerationRequest, system_prompt: str
    ) -> GenerationResponse:
        """Generate using Mistral/Devstral API."""
        try:
            if self._devstral_client is None:
                self._devstral_client = _get_devstral_client()

            if not self._devstral_client:
                raise Exception("Mistral/Devstral not configured")

            # Execute request
            result = await self._devstral_client.execute(
                {
                    "prompt": request.prompt,
                    "system_prompt": system_prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                }
            )

            return GenerationResponse(
                success=result.get("success", False),
                content=result.get("content", ""),
                provider=AIProvider.DEVSTRAL,
                model=result.get("model", "devstral-small"),
                tokens_used=result.get("total_tokens", 0),
                cost_usd=result.get("cost_usd", 0.0),
            )

        except Exception as e:
            raise Exception(f"Mistral generation failed: {e}")

    async def _generate_vibe_cli(
        self, request: GenerationRequest, system_prompt: str
    ) -> GenerationResponse:
        """Generate using Vibe CLI (local Mistral)."""
        if not self._vibe_cli:
            raise Exception("Vibe CLI not installed")

        try:
            # Build combined prompt for CLI
            full_prompt = f"{system_prompt}\n\nUser request: {request.prompt}"

            # Run vibe CLI
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [self._vibe_cli, "chat", "--message", full_prompt],
                    capture_output=True,
                    text=True,
                    timeout=60,
                ),
            )

            if result.returncode == 0:
                return GenerationResponse(
                    success=True,
                    content=result.stdout.strip(),
                    provider=AIProvider.VIBE_CLI,
                    model="vibe-local",
                )
            else:
                raise Exception(f"Vibe CLI error: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise Exception("Vibe CLI timeout")
        except Exception as e:
            raise Exception(f"Vibe CLI failed: {e}")

    def _generate_offline(
        self, request: GenerationRequest, system_prompt: str
    ) -> GenerationResponse:
        """Generate offline response from templates."""
        template = self._template_loader.get_for_layer(request.layer_id)

        # Build themed offline response
        if request.gen_type == GenerationType.MAKE_GUIDE:
            content = self._offline_make_guide(request, template)
        elif request.gen_type == GenerationType.MAKE_DO:
            content = self._offline_make_do(request, template)
        elif request.gen_type == GenerationType.SUGGEST:
            content = self._offline_suggest(request, template)
        else:
            content = self._offline_generic(request, template)

        return GenerationResponse(
            success=True,
            content=content,
            provider=AIProvider.OFFLINE,
            model="template-fallback",
            fallback_used=True,
        )

    def _offline_make_guide(self, request: GenerationRequest, template) -> str:
        """Generate offline guide response."""
        icon = template.icon if hasattr(template, "icon") else "📖"
        return f"""{icon} OFFLINE MODE - Knowledge Guide

Topic: {request.prompt}

This system is currently offline. To get detailed AI-generated guides:
1. Configure Gemini API key in wizard/config/ai_keys.json
2. Or install Vibe CLI for local generation

For now, search the knowledge bank:
> SEARCH {request.prompt}
> CATALOG knowledge/

The knowledge bank contains extensive offline documentation."""

    def _offline_make_do(self, request: GenerationRequest, template) -> str:
        """Generate offline practical help."""
        return f"""📋 OFFLINE MODE - Practical Help

Request: {request.prompt}

AI generation is not available. Try:
1. SEARCH the knowledge bank for existing guides
2. CATALOG to browse available resources
3. HELP for command reference

Connect to internet and configure AI provider for enhanced assistance."""

    def _offline_suggest(self, request: GenerationRequest, template) -> str:
        """Generate offline workflow suggestion."""
        return f"""📊 OFFLINE MODE - Workflow Suggestion

Topic: {request.prompt}

Suggested offline workflow:
1. ✅ SEARCH "{request.prompt}" - Find related knowledge
2. ✅ CATALOG knowledge/ - Browse topic categories
3. ✅ LOAD [filename] - Open specific guides
4. ✅ MAP - Navigate to related areas

Configure AI provider for personalized learning paths."""

    def _offline_generic(self, request: GenerationRequest, template) -> str:
        """Generate generic offline response."""
        return f"""ℹ️ OFFLINE MODE

Request: {request.prompt}

AI generation requires an active provider. Configure one of:
- Gemini: Set GEMINI_API_KEY
- Mistral: Set MISTRAL_API_KEY  
- Vibe CLI: Install from mistral.ai

Use SEARCH and CATALOG commands for offline knowledge access."""

    # === Convenience Methods ===

    async def make_guide(
        self, topic: str, layer_id: int = 0, **kwargs
    ) -> GenerationResponse:
        """Generate a themed knowledge guide."""
        return await self.generate(
            GenerationRequest(
                prompt=topic,
                gen_type=GenerationType.MAKE_GUIDE,
                layer_id=layer_id,
                **kwargs,
            )
        )

    async def make_do(
        self, task: str, layer_id: int = 0, **kwargs
    ) -> GenerationResponse:
        """Generate practical task help."""
        return await self.generate(
            GenerationRequest(
                prompt=task,
                gen_type=GenerationType.MAKE_DO,
                layer_id=layer_id,
                **kwargs,
            )
        )

    async def suggest_workflow(
        self, topic: str, layer_id: int = 0, **kwargs
    ) -> GenerationResponse:
        """Generate workflow/learning path suggestion."""
        return await self.generate(
            GenerationRequest(
                prompt=topic,
                gen_type=GenerationType.SUGGEST,
                layer_id=layer_id,
                **kwargs,
            )
        )

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [p.value for p in self._available_providers]

    def is_online(self) -> bool:
        """Check if any online provider is available."""
        online_providers = {
            AIProvider.GEMINI,
            AIProvider.DEVSTRAL,
            AIProvider.MISTRAL,
            AIProvider.VIBE_CLI,
        }
        return bool(online_providers & set(self._available_providers))


# Singleton
_ai_service: Optional[AIGenerationService] = None


def get_ai_service() -> AIGenerationService:
    """Get or create AI generation service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIGenerationService()
    return _ai_service


# Convenience functions
async def make_guide(topic: str, layer_id: int = 0, **kwargs) -> GenerationResponse:
    """Generate a themed knowledge guide."""
    return await get_ai_service().make_guide(topic, layer_id, **kwargs)


async def make_do(task: str, layer_id: int = 0, **kwargs) -> GenerationResponse:
    """Generate practical task help."""
    return await get_ai_service().make_do(task, layer_id, **kwargs)


async def suggest_workflow(
    topic: str, layer_id: int = 0, **kwargs
) -> GenerationResponse:
    """Generate workflow suggestion."""
    return await get_ai_service().suggest_workflow(topic, layer_id, **kwargs)
