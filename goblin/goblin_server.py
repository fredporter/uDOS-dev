"""
Goblin Dev Server - Experimental Development Server

Status: Development v0.1.0.0 (unstable, experimental)
Port: 8767
Scope: Local development only (localhost)

Purpose:
Feature development sandbox before promotion to:
- /core/ - Core runtime
- /extensions/ - Public extensions  
- /wizard/ - Production server
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('goblin-server')

# Version
VERSION = "0.1.0.0"

# Config
GOBLIN_HOST = "127.0.0.1"
GOBLIN_PORT = 8767

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info(f"[GOBLIN] Starting Goblin Dev Server v{VERSION}")
    logger.info(f"[GOBLIN] Listening on http://{GOBLIN_HOST}:{GOBLIN_PORT}")
    logger.info("[GOBLIN] Experimental features active - expect breaking changes!")
    
    # Load config (local-only, gitignored)
    config_path = Path(__file__).parent / "config" / "goblin.json"
    if config_path.exists():
        logger.info(f"[GOBLIN] Loaded config from {config_path}")
    else:
        logger.warning("[GOBLIN] No config found - using defaults")
    
    yield
    
    logger.info("[GOBLIN] Shutting down Goblin Dev Server")

# Create FastAPI app
app = FastAPI(
    title="Goblin Dev Server",
    description="Experimental development server for uDOS",
    version=VERSION,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    lifespan=lifespan
)

# CORS - localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    logger.debug(f"[GOBLIN] {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = (datetime.now() - start_time).total_seconds()
    logger.debug(f"[GOBLIN] {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
    
    return response

# Root endpoint
@app.get("/")
async def root():
    """Goblin Dev Server info"""
    return {
        "server": "Goblin Dev Server",
        "version": VERSION,
        "status": "experimental",
        "port": GOBLIN_PORT,
        "scope": "local-only",
        "api_prefix": "/api/v0",
        "docs": f"http://{GOBLIN_HOST}:{GOBLIN_PORT}/docs",
        "warning": "Unstable API - expect breaking changes"
    }

# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "goblin",
        "version": VERSION,
        "timestamp": datetime.now().isoformat()
    }

# Poke - Open URL in browser
@app.post("/api/v0/poke")
async def poke_url(request: Request):
    """
    Open a URL in the default browser.
    
    Body: {"url": "http://example.com"}
    """
    import webbrowser
    
    try:
        data = await request.json()
        url = data.get("url")
        
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        
        # Validate URL format
        if not url.startswith(("http://", "https://", "file://")):
            logger.warning(f"[GOBLIN] URL missing protocol: {url}")
        
        # Open in browser
        logger.info(f"[GOBLIN] Opening URL in browser: {url}")
        webbrowser.open(url)
        
        return {
            "status": "success",
            "url": url,
            "message": "Browser opened successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GOBLIN] Error opening browser: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not open browser: {str(e)}"
        )

# ========================================
# Notion Sync Endpoints (Phase B: Webhook)
# ========================================

# Mount Notion routes
try:
    from routes import notion as notion_routes
    app.include_router(notion_routes.router)
except ImportError:
    logger.warning("[GOBLIN] Could not load Notion routes")

# Mount Runtime routes
try:
    from routes import runtime as runtime_routes
    app.include_router(runtime_routes.router)
except ImportError:
    logger.warning("[GOBLIN] Could not load Runtime routes")

# Mount Task Scheduler routes
try:
    from routes import tasks as tasks_routes
    app.include_router(tasks_routes.router)
except ImportError:
    logger.warning("[GOBLIN] Could not load Tasks routes")

# Mount Binder Compiler routes
try:
    from routes import binder as binder_routes
    app.include_router(binder_routes.router)
except ImportError:
    logger.warning("[GOBLIN] Could not load Binder routes")

# ========================================
# GitHub Integration (v1.0.4.0)
# ========================================
try:
    from routes import github as github_routes
    app.include_router(github_routes.router)
except ImportError:
    logger.warning("[GOBLIN] Could not load GitHub routes")

# ========================================
# Mistral/Vibe CLI Integration (v1.0.4.0)
# ========================================
try:
    from routes import ai as ai_routes
    app.include_router(ai_routes.router)
except ImportError:
    logger.warning("[GOBLIN] Could not load AI routes")

# ========================================
# Workflow Manager (v1.0.4.0)
# ========================================
try:
    from routes import workflow as workflow_routes
    app.include_router(workflow_routes.router)
except ImportError:
    logger.warning("[GOBLIN] Could not load Workflow routes")

# ========================================
# Setup & Configuration
# ========================================
try:
    from routes import setup as setup_routes
    app.include_router(setup_routes.router)
except ImportError:
    logger.warning("[GOBLIN] Could not load Setup routes")

# ========================================
# Exception Handlers
# ========================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"[GOBLIN] Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": str(exc),
            "path": request.url.path
        }
    )

# Main entry point
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🧌 Goblin Dev Server")
    logger.info(f"   Version: {VERSION}")
    logger.info(f"   Port: {GOBLIN_PORT}")
    logger.info(f"   Docs: http://{GOBLIN_HOST}:{GOBLIN_PORT}/docs")
    logger.info("   Status: EXPERIMENTAL - Expect breaking changes!")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host=GOBLIN_HOST,
        port=GOBLIN_PORT,
        log_level="debug"
    )
