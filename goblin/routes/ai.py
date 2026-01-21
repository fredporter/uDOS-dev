"""
Mistral/Vibe CLI Integration Routes for Goblin Dev Server
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v0/ai", tags=["ai"])

# Lazy initialization - only create when needed
_ai_instance = None


def get_ai():
    """Lazy-load Mistral/Vibe integration (check availability on first use)."""
    global _ai_instance
    if _ai_instance is None:
        from ..services.mistral_vibe import MistralVibeIntegration
        _ai_instance = MistralVibeIntegration()
    return _ai_instance


class QueryRequest(BaseModel):
    """AI query request."""
    prompt: str
    include_context: bool = True
    model: str = "devstral-small"


class CodeExplainRequest(BaseModel):
    """Code explanation request."""
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None


@router.get("/health")
async def health_check():
    """Check Vibe CLI availability."""
    try:
        # Test by getting context files
        ai = get_ai()
        context = ai.get_context_files()
        return {
            "status": "ok",
            "vibe_cli_installed": True,
            "context_files_loaded": len(context)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/query")
async def query_ai(request: QueryRequest):
    """Query AI with project context.
    
    Uses Vibe CLI (Devstral) for local offline execution.
    """
    try:
        ai = get_ai()
        response = ai.query_vibe(
            prompt=request.prompt,
            include_context=request.include_context,
            model=request.model
        )
        return {"response": response, "model": request.model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context")
async def get_context():
    """Get all context files loaded for AI."""
    try:
        ai = get_ai()
        context = ai.get_context_files()
        return {
            "files": list(context.keys()),
            "total_files": len(context),
            "total_chars": sum(len(c) for c in context.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-logs")
async def analyze_logs(log_type: str = "error"):
    """Analyze recent logs with AI.
    
    Args:
        log_type: Type of log to analyze (error, debug, session-commands)
    """
    try:
        ai = get_ai()
        analysis = ai.analyze_logs(log_type)
        return {"log_type": log_type, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest-next")
async def suggest_next_steps():
    """Get AI suggestions for next development steps."""
    try:
        ai = get_ai()
        suggestions = ai.suggest_next_steps()
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-code")
async def explain_code(request: CodeExplainRequest):
    """Get AI explanation of code.
    
    Args:
        file_path: Path to file (relative to repo)
        line_start: Optional start line
        line_end: Optional end line
    """
    try:
        ai = get_ai()
        line_range = None
        if request.line_start and request.line_end:
            line_range = (request.line_start, request.line_end)
        
        explanation = ai.explain_code(request.file_path, line_range)
        return {
            "file_path": request.file_path,
            "line_range": line_range,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
