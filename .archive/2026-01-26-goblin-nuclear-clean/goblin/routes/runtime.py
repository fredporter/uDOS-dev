"""
Runtime API Routes for Goblin Dev Server

Endpoints for parsing and executing markdown runtime blocks (state, set, form, if, nav, panel).

Routes:
    POST /api/v0/runtime/parse         - Parse markdown and return blocks
    POST /api/v0/runtime/execute       - Execute single block
    POST /api/v0/runtime/execute-all   - Execute all blocks in markdown
    GET  /api/v0/runtime/state         - Get current runtime state
    POST /api/v0/runtime/state         - Set/update runtime state
    DELETE /api/v0/runtime/state       - Clear runtime state

Author: uDOS Team
Version: 0.1.0 (Experimental)
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from dev.goblin.services.runtime_executor import RuntimeExecutor

logger = logging.getLogger("goblin.runtime")

# Create router
router = APIRouter(prefix="/api/v0/runtime", tags=["runtime"])

# Global runtime executor instance (stateful)
_runtime_executor = None


def get_runtime_executor() -> RuntimeExecutor:
    """Get or create the global RuntimeExecutor instance."""
    global _runtime_executor
    if _runtime_executor is None:
        logger.info("[RUNTIME] Initializing RuntimeExecutor...")
        _runtime_executor = RuntimeExecutor(config={
            "max_state_size_bytes": 1024 * 1024,  # 1 MB
            "execution_timeout_ms": 5000          # 5 seconds
        })
    return _runtime_executor


# Request/Response Models
class ParseRequest(BaseModel):
    """Request to parse markdown content."""
    markdown: str = Field(..., description="Markdown content with runtime blocks")


class ParseResponse(BaseModel):
    """Response from parse operation."""
    blocks: List[Dict[str, Any]] = Field(..., description="Parsed runtime blocks")
    variables: List[str] = Field(default_factory=list, description="List of variable names")
    ast: Dict[str, Any] = Field(default_factory=dict, description="AST summary")


class ExecuteBlockRequest(BaseModel):
    """Request to execute a single block."""
    block_type: str = Field(..., description="Block type (state/set/form/if/nav/panel/map)")
    content: str = Field(..., description="Block content")
    line: Optional[int] = Field(None, description="Line number in source")


class ExecuteAllRequest(BaseModel):
    """Request to execute all blocks in markdown."""
    markdown: str = Field(..., description="Markdown content with runtime blocks")
    reset_state: bool = Field(False, description="Reset state before execution")


class ExecuteResponse(BaseModel):
    """Response from execution operation."""
    status: str = Field(..., description="Execution status (success/error)")
    output: Optional[Dict[str, Any]] = Field(None, description="Block output (if any)")
    state: Dict[str, Any] = Field(default_factory=dict, description="Current runtime state")
    error: Optional[str] = Field(None, description="Error message (if failed)")


class ExecuteAllResponse(BaseModel):
    """Response from execute-all operation."""
    blocks_executed: int = Field(..., description="Number of blocks executed")
    blocks_failed: int = Field(0, description="Number of blocks that failed")
    results: List[ExecuteResponse] = Field(default_factory=list, description="Individual block results")
    final_state: Dict[str, Any] = Field(default_factory=dict, description="Final runtime state")


class StateUpdateRequest(BaseModel):
    """Request to update runtime state."""
    variables: Dict[str, Any] = Field(..., description="Variables to set/update")


class StateResponse(BaseModel):
    """Response for state operations."""
    state: Dict[str, Any] = Field(default_factory=dict, description="Current runtime state")
    variable_count: int = Field(0, description="Number of variables in state")


# Routes
@router.post("/parse", response_model=ParseResponse)
async def parse_markdown(request: ParseRequest):
    """
    Parse markdown content and extract runtime blocks.
    
    Returns blocks array with type, content, and line number for each block.
    """
    try:
        executor = get_runtime_executor()
        result = executor.parse_markdown(request.markdown)
        
        logger.info(f"[RUNTIME] Parsed {len(result.get('blocks', []))} blocks")
        
        return ParseResponse(
            blocks=result.get("blocks", []),
            variables=result.get("variables", []),
            ast=result.get("ast", {})
        )
    except Exception as e:
        logger.error(f"[RUNTIME] Parse failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Parse failed: {str(e)}")


@router.post("/execute", response_model=ExecuteResponse)
async def execute_block(request: ExecuteBlockRequest):
    """
    Execute a single runtime block.
    
    Block types: state, set, form, if, nav, panel, map
    """
    try:
        executor = get_runtime_executor()
        
        result = executor.execute_block(
            block_type=request.block_type,
            content=request.content,
            state=None  # Use executor's internal state
        )
        
        logger.info(f"[RUNTIME] Executed {request.block_type} block - status: {result.get('status')}")
        
        return ExecuteResponse(
            status=result.get("status", "unknown"),
            output=result.get("output"),
            state=executor.get_state(),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"[RUNTIME] Execution failed: {e}", exc_info=True)
        return ExecuteResponse(
            status="error",
            output=None,
            state=executor.get_state() if executor else {},
            error=str(e)
        )


@router.post("/execute-all", response_model=ExecuteAllResponse)
async def execute_all_blocks(request: ExecuteAllRequest):
    """
    Parse and execute all runtime blocks in markdown content.
    
    Optionally reset state before execution.
    """
    try:
        executor = get_runtime_executor()
        
        # Reset state if requested
        if request.reset_state:
            executor.set_state({})
            logger.info("[RUNTIME] State reset before execution")
        
        # Parse markdown
        parse_result = executor.parse_markdown(request.markdown)
        blocks = parse_result.get("blocks", [])
        
        if not blocks:
            logger.warning("[RUNTIME] No runtime blocks found in markdown")
            return ExecuteAllResponse(
                blocks_executed=0,
                blocks_failed=0,
                results=[],
                final_state=executor.get_state()
            )
        
        # Execute each block
        results = []
        failed_count = 0
        
        for i, block in enumerate(blocks, 1):
            try:
                exec_result = executor.execute_block(
                    block_type=block["type"],
                    content=block["content"],
                    state=None  # Use executor's internal state
                )
                
                response = ExecuteResponse(
                    status=exec_result.get("status", "unknown"),
                    output=exec_result.get("output"),
                    state=executor.get_state(),
                    error=exec_result.get("error")
                )
                
                results.append(response)
                
                if response.status == "error":
                    failed_count += 1
                    logger.warning(f"[RUNTIME] Block {i}/{len(blocks)} failed: {response.error}")
                else:
                    logger.info(f"[RUNTIME] Block {i}/{len(blocks)} executed successfully")
                    
            except Exception as e:
                logger.error(f"[RUNTIME] Block {i}/{len(blocks)} exception: {e}", exc_info=True)
                results.append(ExecuteResponse(
                    status="error",
                    output=None,
                    state=executor.get_state(),
                    error=str(e)
                ))
                failed_count += 1
        
        logger.info(f"[RUNTIME] Executed {len(blocks)} blocks - {len(blocks) - failed_count} succeeded, {failed_count} failed")
        
        return ExecuteAllResponse(
            blocks_executed=len(blocks),
            blocks_failed=failed_count,
            results=results,
            final_state=executor.get_state()
        )
        
    except Exception as e:
        logger.error(f"[RUNTIME] Execute-all failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Execute-all failed: {str(e)}")


@router.get("/state", response_model=StateResponse)
async def get_state():
    """Get current runtime state (all variables)."""
    try:
        executor = get_runtime_executor()
        state = executor.get_state()
        
        return StateResponse(
            state=state,
            variable_count=len(state)
        )
    except Exception as e:
        logger.error(f"[RUNTIME] Get state failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Get state failed: {str(e)}")


@router.post("/state", response_model=StateResponse)
async def update_state(request: StateUpdateRequest):
    """Set or update runtime state variables."""
    try:
        executor = get_runtime_executor()
        
        # Update state
        current_state = executor.get_state()
        current_state.update(request.variables)
        executor.set_state(current_state)
        
        logger.info(f"[RUNTIME] Updated {len(request.variables)} variables")
        
        return StateResponse(
            state=executor.get_state(),
            variable_count=len(executor.get_state())
        )
    except Exception as e:
        logger.error(f"[RUNTIME] Update state failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Update state failed: {str(e)}")


@router.delete("/state", response_model=StateResponse)
async def clear_state():
    """Clear all runtime state variables."""
    try:
        executor = get_runtime_executor()
        executor.set_state({})
        
        logger.info("[RUNTIME] State cleared")
        
        return StateResponse(
            state={},
            variable_count=0
        )
    except Exception as e:
        logger.error(f"[RUNTIME] Clear state failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Clear state failed: {str(e)}")
