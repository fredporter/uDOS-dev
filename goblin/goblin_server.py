"""
Goblin Server - MODE Experimental Playground

Version: v0.2.0.0 (Nuclear Clean)
Port: 8767
Scope: Local development only (localhost)

Purpose: Test experimental MODEs (Teletext, Terminal) before promoting to Core
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wizard.services.logging_manager import get_logger
from wizard.services.path_utils import get_repo_root

logger = get_logger("goblin-server")

# Global console instance
_console = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _console

    # Startup
    logger.info("[GOBLIN] 🧪 Goblin MODE Playground starting...")
    logger.info("[GOBLIN] Port: 8767 (localhost only)")
    logger.info("[GOBLIN] MODEs: Teletext, Terminal")
    logger.info("[GOBLIN] Dashboard: http://localhost:5174")

    # Start interactive console (optional)
    console_flag = os.getenv("GOBLIN_CONSOLE", "0").lower()
    if console_flag in {"1", "true", "yes", "on"}:
        if sys.stdin and sys.stdin.isatty():
            try:
                from services.goblin_console import create_goblin_console

                config = {"port": 8767, "host": "127.0.0.1"}
                _console = create_goblin_console(config)
                _console.start()
                logger.info("[GOBLIN] ✅ Interactive console started")
            except Exception as exc:
                logger.warning(f"[GOBLIN] ⚠️ Console failed to start: {exc}")
        else:
            logger.info("[GOBLIN] Console disabled (no TTY detected)")
    else:
        logger.info("[GOBLIN] Console disabled (set GOBLIN_CONSOLE=1 to enable)")

    yield

    # Shutdown
    if _console:
        _console.stop()

    logger.info("[GOBLIN] 🛑 Goblin MODE Playground shutting down...")


# Initialize FastAPI with lifespan
app = FastAPI(
    title="Goblin MODE Playground",
    version="0.2.0.0",
    description="Experimental MODE testing server (Teletext, Terminal)",
    lifespan=lifespan,
)

# CORS for local dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "server": "Goblin MODE Playground",
        "version": "0.2.0.0",
        "port": 8767,
        "modes": ["teletext", "terminal"],
        "status": "experimental",
        "dashboard": "http://localhost:5174",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "server": "goblin", "version": "0.2.0.0"}


# Import routes (add goblin to path for local imports)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from routes.mode_routes import router as mode_router
    app.include_router(mode_router, prefix="/api/v0/modes", tags=["modes"])
    logger.info("[GOBLIN] ✅ MODE routes loaded")
except ImportError as e:
    logger.warning(f"[GOBLIN] ⚠️ MODE routes not found: {e}")

# Dev workflow routes (Round 7 kickoff)
try:
    from routes.dev_routes import router as dev_router
    app.include_router(dev_router, prefix="/api/dev", tags=["dev"])
    logger.info("[GOBLIN] ✅ Dev routes loaded")
except ImportError as e:
    logger.warning(f"[GOBLIN] ⚠️ Dev routes not found: {e}")

# Screwdriver routes migrated to Wizard (/api/sonic/screwdriver/*)

# MeshCore device manager routes (Round 7 kickoff)
try:
    from routes.meshcore_routes import router as meshcore_router
    app.include_router(
        meshcore_router, prefix="/api/dev/meshcore", tags=["meshcore"]
    )
    logger.info("[GOBLIN] ✅ MeshCore routes loaded")
except ImportError as e:
    logger.warning(f"[GOBLIN] ⚠️ MeshCore routes not found: {e}")

# Workflow routes (containers/vibe/logs/vault sync)
try:
    from routes.workflow_routes import router as workflow_router
    app.include_router(workflow_router, prefix="/api/dev", tags=["workflow"])
    logger.info("[GOBLIN] ✅ Workflow routes loaded")
except ImportError as e:
    logger.warning(f"[GOBLIN] ⚠️ Workflow routes not found: {e}")


# Static files for built dashboard (production)
dashboard_dist = Path(__file__).parent / "dashboard" / "build"
if dashboard_dist.exists():
    app.mount("/", StaticFiles(directory=str(dashboard_dist), html=True), name="dashboard")
    logger.info("[GOBLIN] ✅ Dashboard mounted (production build)")


if __name__ == "__main__":
    logger.info("[GOBLIN] 🚀 Starting Goblin server on http://localhost:8767")
    uvicorn.run(
        "goblin_server:app",
        host="127.0.0.1",
        port=8767,
        reload=True,
        log_level="info",
    )
