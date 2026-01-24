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
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add parent repo root to path for modular imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import modular utilities from wizard services
try:
    from wizard.services.path_utils import get_repo_root
except ImportError:
    # Fallback if wizard services not available
    def get_repo_root():
        current = Path(__file__).resolve()
        for parent in [current.parent] + list(current.parents):
            if (parent / "uDOS.py").exists():
                return parent
        raise RuntimeError("Could not find uDOS repository root")


# Setup logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("goblin-server")


# Version (use version.json when available)
def load_version():
    """Load version from version.json or fallback to hardcoded"""
    try:
        version_file = Path(__file__).parent / "version.json"
        if version_file.exists():
            import json

            with open(version_file) as f:
                data = json.load(f)
                return data.get("version", "0.1.0.0")
    except Exception as e:
        logger.warning(f"Could not load version.json: {e}")
    return "0.1.0.0"


VERSION = load_version()

# Config - use modular repo root
try:
    REPO_ROOT = get_repo_root()
    GOBLIN_DATA_PATH = REPO_ROOT / "memory" / "goblin"
    GOBLIN_DATA_PATH.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Could not determine repo root: {e}")
    REPO_ROOT = Path(__file__).parent.parent.parent
    GOBLIN_DATA_PATH = REPO_ROOT / "memory" / "goblin"
    GOBLIN_DATA_PATH.mkdir(parents=True, exist_ok=True)

# Config
GOBLIN_HOST = "127.0.0.1"
GOBLIN_PORT = 8767


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info(f"[GOBLIN] Starting Goblin Dev Server v{VERSION}")
    logger.info(f"[GOBLIN] Listening on http://{GOBLIN_HOST}:{GOBLIN_PORT}")
    logger.info("[GOBLIN] Experimental features active - expect breaking changes!")
    logger.info(f"[GOBLIN] Repo root: {REPO_ROOT}")
    logger.info(f"[GOBLIN] Data path: {GOBLIN_DATA_PATH}")

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
    lifespan=lifespan,
)

# CORS - localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets for Svelte dashboard
dashboard_assets_path = Path(__file__).parent / "dashboard" / "dist" / "assets"
if dashboard_assets_path.exists():
    app.mount("/assets", StaticFiles(directory=dashboard_assets_path), name="assets")
    logger.info(f"[GOBLIN] Mounted static assets from {dashboard_assets_path}")
else:
    logger.warning("[GOBLIN] Dashboard assets directory not found")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()

    logger.debug(f"[GOBLIN] {request.method} {request.url.path}")

    response = await call_next(request)

    duration = (datetime.now() - start_time).total_seconds()
    logger.debug(
        f"[GOBLIN] {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)"
    )

    return response


# Root endpoint - Serve Svelte dashboard
@app.get("/")
async def root():
    """Goblin Dev Server dashboard"""
    try:
        dashboard_path = Path(__file__).parent / "dashboard" / "dist" / "index.html"
        if dashboard_path.exists():
            with open(dashboard_path, "r") as f:
                return HTMLResponse(f.read())
    except Exception as e:
        logger.warning(f"[GOBLIN] Could not load Svelte dashboard: {e}")

    # Fallback to simple HTML
    return HTMLResponse(get_goblin_fallback_html())


# API info endpoint
@app.get("/api/v0/info")
async def api_info():
    """Goblin API server info (JSON)"""
    return {
        "server": "Goblin Dev Server",
        "version": VERSION,
        "status": "experimental",
        "port": GOBLIN_PORT,
        "scope": "local-only",
        "api_prefix": "/api/v0",
        "docs": f"http://{GOBLIN_HOST}:{GOBLIN_PORT}/docs",
        "warning": "Unstable API - expect breaking changes",
    }


def get_goblin_fallback_html() -> str:
    """Return simple fallback HTML when Svelte build unavailable"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Goblin Dev Server</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container { 
            max-width: 700px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 50px;
            text-align: center;
        }
        h1 { 
            font-size: 2.5em;
            color: #764ba2;
            margin-bottom: 10px;
        }
        .subtitle { 
            font-size: 1.1em;
            color: #666;
            margin-bottom: 30px;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 6px;
            color: #856404;
            margin-bottom: 30px;
            font-weight: 600;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 30px 0;
            text-align: left;
        }
        .info-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .info-item label {
            font-weight: 600;
            color: #333;
            display: block;
            font-size: 0.85em;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .info-item .value {
            color: #667eea;
            font-size: 1.1em;
            font-weight: 500;
        }
        .links {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 30px 0;
        }
        a {
            display: block;
            padding: 15px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .btn-docs {
            background: #667eea;
            color: white;
        }
        .btn-docs:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .btn-info {
            background: #e9ecef;
            color: #333;
        }
        .btn-info:hover {
            background: #dee2e6;
            transform: translateY(-2px);
        }
        .warning {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-top: 30px;
            font-size: 0.95em;
        }
        .footer {
            margin-top: 30px;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Goblin</h1>
        <p class="subtitle">Experimental Dev Server</p>
        
        <div class="status">⚠️ UNSTABLE API - EXPECT BREAKING CHANGES</div>
        
        <div class="info-grid">
            <div class="info-item">
                <label>Version</label>
                <div class="value">0.2.0</div>
            </div>
            <div class="info-item">
                <label>Status</label>
                <div class="value">Experimental</div>
            </div>
            <div class="info-item">
                <label>Port</label>
                <div class="value">8767</div>
            </div>
            <div class="info-item">
                <label>Scope</label>
                <div class="value">Local Only</div>
            </div>
            <div class="info-item">
                <label>API Prefix</label>
                <div class="value">/api/v0</div>
            </div>
            <div class="info-item">
                <label>Host</label>
                <div class="value">127.0.0.1</div>
            </div>
        </div>
        
        <div class="links">
            <a href="/docs" class="btn-docs">📚 API Docs (Swagger)</a>
            <a href="/api/v0/info" class="btn-info">📋 Server Info (JSON)</a>
        </div>
        
        <div class="warning">
            <strong>⚠️ Warning:</strong> This is an experimental development server. 
            The API at <code>/api/v0/*</code> is unstable and may change without notice. 
            Use for local development only.
        </div>
        
        <div class="footer">
            <p>uDOS Goblin Dev Server • Local Development Only</p>
        </div>
    </div>
</body>
</html>"""


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "goblin",
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
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
            "message": "Browser opened successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GOBLIN] Error opening browser: {e}")
        raise HTTPException(status_code=500, detail=f"Could not open browser: {str(e)}")


# ========================================
# Route Mounting
# ========================================

# REMOVED: Notion Sync - moved to Wizard Server (port 8765)
# Notion endpoints should be accessed via Wizard API

# REMOVED: Runtime - archived, use Core TypeScript Runtime instead
# Runtime execution now handled by Core, not Goblin

# REMOVED: Task Scheduler - moved to Wizard Server (port 8765)
# Task scheduling endpoints should be accessed via Wizard API

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
            "path": request.url.path,
        },
    )


# Main entry point
if __name__ == "__main__":
    import webbrowser
    import threading
    import time

    logger.info("=" * 60)
    logger.info("Goblin Dev Server")
    logger.info(f"   Version: {VERSION}")
    logger.info(f"   Port: {GOBLIN_PORT}")
    logger.info(f"   Dashboard: http://{GOBLIN_HOST}:{GOBLIN_PORT}")
    logger.info(f"   API Docs: http://{GOBLIN_HOST}:{GOBLIN_PORT}/docs")
    logger.info("   Status: EXPERIMENTAL - Expect breaking changes!")
    logger.info("=" * 60)

    # Open dashboard in browser after short delay
    def open_browser():
        time.sleep(1.5)  # Wait for server to start
        dashboard_url = f"http://{GOBLIN_HOST}:{GOBLIN_PORT}"
        logger.info(f"[GOBLIN] Opening dashboard in browser: {dashboard_url}")
        webbrowser.open(dashboard_url)

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host=GOBLIN_HOST, port=GOBLIN_PORT, log_level="debug")
