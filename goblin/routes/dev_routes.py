"""
Dev Routes - Goblin Dev Server Endpoints

All endpoints prefixed with /api/dev/*
"""

from fastapi import APIRouter

router = APIRouter()


# ============================================================================
# DEV INDEX
# ============================================================================


@router.get("/")
async def dev_index():
    return {
        "status": "ok",
        "round": 7,
        "features": {
            "binders": "migrated-to-wizard",
            "screwdriver": "migrated-to-wizard",
            "meshcore": "planned",
        },
        "migrated": {
            "binder": "/api/binder/* (Wizard)",
            "screwdriver": "/api/sonic/screwdriver/* (Wizard)",
        },
    }
