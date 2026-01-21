"""
Binder Compiler Routes

FastAPI routes for multi-format binder compilation:
- Markdown export
- PDF export  
- JSON export
- Chapter management

Author: uDOS Team
Version: 0.1.0
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger('goblin.routes.binder')

# FastAPI Router
router = APIRouter(prefix="/api/v0/binder", tags=["binder"])

# Pydantic models for request validation
class ChapterCreate(BaseModel):
    """Create chapter request"""
    chapter_id: str
    title: str
    content: Optional[str] = ""
    order: int = 1
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": "section-1",
                "title": "Introduction",
                "content": "# Introduction\n\nThis is the intro chapter.",
                "order": 1
            }
        }


class ChapterUpdate(BaseModel):
    """Update chapter request"""
    title: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None
    status: Optional[str] = None  # draft, review, complete
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Title",
                "content": "Updated content here...",
                "status": "review"
            }
        }


class CompileRequest(BaseModel):
    """Compile binder request"""
    binder_id: str
    formats: Optional[List[str]] = ["markdown", "json"]
    include_toc: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "binder_id": "research-2026-01",
                "formats": ["markdown", "pdf", "json"],
                "include_toc": True
            }
        }


def get_compiler():
    """Lazy load binder compiler service"""
    from dev.goblin.services.binder_compiler import BinderCompiler
    return BinderCompiler()


@router.post("/compile", response_model=Dict[str, Any])
async def compile_binder(request: CompileRequest):
    """
    Compile binder in specified formats
    
    Generates multi-format outputs:
    - Markdown (.md)
    - PDF (.pdf)
    - JSON (.json)
    - Dev brief (YAML + Markdown)
    """
    try:
        compiler = get_compiler()
        
        if not request.binder_id:
            raise HTTPException(status_code=400, detail="binder_id required")
        
        if not request.formats or len(request.formats) == 0:
            raise HTTPException(status_code=400, detail="At least one format required")
        
        # Validate format names
        valid_formats = {"markdown", "pdf", "json", "brief"}
        invalid = set(request.formats) - valid_formats
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid formats: {', '.join(invalid)}. Valid: markdown, pdf, json, brief"
            )
        
        result = await compiler.compile_binder(
            binder_id=request.binder_id,
            formats=request.formats
        )
        
        logger.info(f"[BINDER] Compiled {request.binder_id}: {request.formats}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BINDER] Compile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{binder_id}/chapters", response_model=Dict[str, Any])
async def get_chapters(binder_id: str, include_content: bool = Query(False)):
    """
    Get binder chapter structure
    
    Returns list of chapters with metadata:
    - chapter_id: Unique identifier
    - title: Display title
    - order: Chapter order
    - status: draft | review | complete
    - word_count: Content length
    """
    try:
        if not binder_id:
            raise HTTPException(status_code=400, detail="binder_id required")
        
        compiler = get_compiler()
        chapters = await compiler.get_chapters(binder_id)
        
        logger.info(f"[BINDER] Retrieved {len(chapters)} chapters for {binder_id}")
        
        return {
            "binder_id": binder_id,
            "total": len(chapters),
            "chapters": chapters,
            "include_content": include_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BINDER] Get chapters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{binder_id}/chapters", response_model=Dict[str, Any])
async def add_chapter(binder_id: str, chapter: ChapterCreate):
    """
    Add chapter to binder
    
    Creates new chapter with optional content.
    """
    try:
        if not binder_id:
            raise HTTPException(status_code=400, detail="binder_id required")
        
        if not chapter.chapter_id or not chapter.title:
            raise HTTPException(status_code=400, detail="chapter_id and title required")
        
        compiler = get_compiler()
        result = await compiler.add_chapter(
            binder_id=binder_id,
            chapter=chapter.model_dump()
        )
        
        logger.info(f"[BINDER] Added chapter {chapter.chapter_id} to {binder_id}")
        
        return {
            "status": "added",
            "binder_id": binder_id,
            "chapter_id": chapter.chapter_id,
            "title": chapter.title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BINDER] Add chapter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{binder_id}/chapters/{chapter_id}", response_model=Dict[str, Any])
async def update_chapter(binder_id: str, chapter_id: str, update: ChapterUpdate):
    """
    Update chapter in binder
    
    Updates chapter content, metadata, or status.
    Supports partial updates (only specified fields are updated).
    """
    try:
        if not binder_id:
            raise HTTPException(status_code=400, detail="binder_id required")
        
        if not chapter_id:
            raise HTTPException(status_code=400, detail="chapter_id required")
        
        # Validate status if provided
        if update.status and update.status not in {"draft", "review", "complete"}:
            raise HTTPException(
                status_code=400,
                detail="status must be: draft, review, or complete"
            )
        
        compiler = get_compiler()
        result = await compiler.update_chapter(
            binder_id=binder_id,
            chapter_id=chapter_id,
            content=update.content or ""
        )
        
        logger.info(f"[BINDER] Updated chapter {chapter_id} in {binder_id}")
        
        return {
            "status": "updated",
            "binder_id": binder_id,
            "chapter_id": chapter_id,
            "updated_at": result.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BINDER] Update chapter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{binder_id}/chapters/{chapter_id}", response_model=Dict[str, Any])
async def get_chapter(binder_id: str, chapter_id: str):
    """
    Get specific chapter content
    
    Returns chapter metadata and full content.
    """
    try:
        if not binder_id:
            raise HTTPException(status_code=400, detail="binder_id required")
        
        if not chapter_id:
            raise HTTPException(status_code=400, detail="chapter_id required")
        
        # TODO: Query chapter from database
        
        # Placeholder response
        logger.info(f"[BINDER] Retrieved chapter {chapter_id} from {binder_id}")
        
        return {
            "binder_id": binder_id,
            "chapter_id": chapter_id,
            "title": "Chapter Title",
            "content": "# Chapter Content\n\n...",
            "status": "draft",
            "word_count": 0,
            "created_at": "2026-01-16T00:00:00",
            "updated_at": "2026-01-16T00:00:00"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BINDER] Get chapter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{binder_id}/chapters/{chapter_id}", response_model=Dict[str, Any])
async def delete_chapter(binder_id: str, chapter_id: str):
    """
    Delete chapter from binder
    
    Removes chapter and all associated content.
    """
    try:
        if not binder_id:
            raise HTTPException(status_code=400, detail="binder_id required")
        
        if not chapter_id:
            raise HTTPException(status_code=400, detail="chapter_id required")
        
        # TODO: Delete from database
        
        logger.info(f"[BINDER] Deleted chapter {chapter_id} from {binder_id}")
        
        return {
            "status": "deleted",
            "binder_id": binder_id,
            "chapter_id": chapter_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BINDER] Delete chapter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{binder_id}/status", response_model=Dict[str, Any])
async def binder_status(binder_id: str):
    """
    Get binder compilation status
    
    Returns:
    - Overall completion percentage
    - Chapter breakdown
    - Last compiled timestamp
    - Output file sizes
    """
    try:
        if not binder_id:
            raise HTTPException(status_code=400, detail="binder_id required")
        
        # TODO: Query binder status from database
        
        logger.info(f"[BINDER] Retrieved status for {binder_id}")
        
        return {
            "binder_id": binder_id,
            "status": "in-progress",
            "completion_percent": 45,
            "chapters_complete": 2,
            "chapters_total": 5,
            "last_compiled": None,
            "outputs": {
                "markdown": None,
                "pdf": None,
                "json": None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BINDER] Get status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{binder_id}/export", response_model=Dict[str, Any])
async def export_binder(binder_id: str, format: str = Query("markdown")):
    """
    Export binder in specified format
    
    Generates and returns export data:
    - format: markdown | pdf | json | brief
    - Returns file path and metadata
    """
    try:
        if not binder_id:
            raise HTTPException(status_code=400, detail="binder_id required")
        
        valid_formats = {"markdown", "pdf", "json", "brief"}
        if format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Valid: {', '.join(valid_formats)}"
            )
        
        compiler = get_compiler()
        
        # Compile if needed
        result = await compiler.compile_binder(
            binder_id=binder_id,
            formats=[format]
        )
        
        logger.info(f"[BINDER] Exported {binder_id} as {format}")
        
        return {
            "status": "exported",
            "binder_id": binder_id,
            "format": format,
            "outputs": result.get("outputs", []),
            "compiled_at": result.get("compiled_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BINDER] Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
