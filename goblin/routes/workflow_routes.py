"""
Workflow Routes - Dev workflow endpoints (containers/vibe/logs/sync)

All endpoints prefixed with /api/dev/*
"""

import json
import shutil
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from wizard.services.logging_manager import get_logger

logger = get_logger("goblin-dev-workflows")

router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARY_ROOT = REPO_ROOT / "library"
LOG_ROOT = REPO_ROOT / "memory" / "logs"
GOBLIN_DATA = REPO_ROOT / "memory" / "sandbox" / "goblin"
VIBE_DATA = GOBLIN_DATA / "vibe"
CONTAINER_DATA = GOBLIN_DATA / "containers"
VAULT_ROOT = REPO_ROOT / "vault"

DEFAULT_CONTEXT_FILES = [
    "AGENTS.md",
    "V1.3-PROGRESS-REPORT.md",
    "docs/ROADMAP-TODO.md",
]


class ContainerTestRequest(BaseModel):
    validate_only: bool = True


class VibeChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system: Optional[str] = None
    format: str = "text"
    with_context: bool = False


class VibeContextRequest(BaseModel):
    files: Optional[List[str]] = None
    notes: Optional[str] = None


class VaultSyncRequest(BaseModel):
    source: str = "memory/bank"
    target: str = "vault/notes"
    extensions: List[str] = [".md"]
    dry_run: bool = False


def _ensure_repo_path(rel_path: str) -> Path:
    path = (REPO_ROOT / rel_path).resolve()
    if not str(path).startswith(str(REPO_ROOT.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path outside repo")
    return path


def _load_manifest(container_dir: Path) -> Optional[Dict[str, object]]:
    for filename in ["container.json", "container.template.json"]:
        path = container_dir / filename
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
    return None


def _validate_manifest(data: Dict[str, object]) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(data, dict):
        return {"errors": ["Manifest is not a JSON object"], "warnings": []}

    if "container" not in data:
        errors.append("Missing container section")
    if "policy" not in data:
        errors.append("Missing policy section")

    container = data.get("container", {}) if isinstance(data.get("container"), dict) else {}
    for field in ["id", "name", "type", "source"]:
        if not container.get(field):
            errors.append(f"container.{field} missing")

    integration = data.get("integration", {}) if isinstance(data.get("integration"), dict) else {}
    for path_field in ["wrapper_path", "service_path", "handler_path", "install_script"]:
        rel = integration.get(path_field)
        if rel:
            try:
                abs_path = _ensure_repo_path(rel)
                if not abs_path.exists():
                    warnings.append(f"integration.{path_field} missing: {rel}")
            except HTTPException:
                warnings.append(f"integration.{path_field} invalid path: {rel}")

    return {"errors": errors, "warnings": warnings}


def _tail_file(path: Path, lines: int) -> List[str]:
    if not path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return list(deque(f, maxlen=lines))


def _latest_log_file() -> Optional[Path]:
    if not LOG_ROOT.exists():
        return None
    candidates = [p for p in LOG_ROOT.iterdir() if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _write_history(entry: Dict[str, object]) -> None:
    VIBE_DATA.mkdir(parents=True, exist_ok=True)
    history_path = VIBE_DATA / "history.jsonl"
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _load_history(limit: int) -> List[Dict[str, object]]:
    history_path = VIBE_DATA / "history.jsonl"
    if not history_path.exists():
        return []
    with history_path.open("r", encoding="utf-8", errors="ignore") as f:
        lines = deque(f, maxlen=limit)
    result = []
    for line in lines:
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return result


def _write_vault_sync_report(report: Dict[str, object]) -> Path:
    VAULT_ROOT.mkdir(parents=True, exist_ok=True)
    log_dir = VAULT_ROOT / "07_LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    path = log_dir / f"vault_sync_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


# Context helpers
def _build_context_bundle() -> Dict[str, str]:
    context: Dict[str, str] = {}
    for rel in DEFAULT_CONTEXT_FILES:
        path = REPO_ROOT / rel
        if path.exists() and path.is_file():
            context[rel] = path.read_text(encoding="utf-8")
    return context


# ============================================================================
# CONTAINER DEV ENDPOINTS
# ============================================================================


@router.get("/containers")
async def list_containers():
    if not LIBRARY_ROOT.exists():
        return {"count": 0, "containers": []}
    containers = []
    for entry in sorted(LIBRARY_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        manifest = _load_manifest(entry)
        if not manifest:
            continue
        info = {
            "name": entry.name,
            "path": str(entry),
            "manifest": manifest.get("container", {}),
        }
        containers.append(info)
    return {"count": len(containers), "containers": containers}


@router.post("/containers/test/{name}")
async def test_container(name: str, payload: ContainerTestRequest):
    container_dir = LIBRARY_ROOT / name
    if not container_dir.exists():
        raise HTTPException(status_code=404, detail="Container not found")

    manifest = _load_manifest(container_dir)
    if not manifest:
        raise HTTPException(status_code=400, detail="Manifest missing or invalid JSON")

    validation = _validate_manifest(manifest)
    status = "ok" if not validation["errors"] else "error"

    result = {
        "status": status,
        "container": name,
        "validated_at": datetime.utcnow().isoformat() + "Z",
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "manifest": manifest,
    }

    CONTAINER_DATA.mkdir(parents=True, exist_ok=True)
    out_dir = CONTAINER_DATA / name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "last_test.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result


@router.get("/containers/status/{name}")
async def container_status(name: str):
    status_path = CONTAINER_DATA / name / "last_test.json"
    if status_path.exists():
        return json.loads(status_path.read_text(encoding="utf-8"))
    return {"status": "unknown", "container": name}


# ============================================================================
# VIBE DEV ENDPOINTS
# ============================================================================


@router.post("/vibe/context-inject")
async def vibe_context_inject(payload: VibeContextRequest):
    context = _build_context_bundle()
    extra_files = payload.files or []
    for rel in extra_files:
        path = _ensure_repo_path(rel)
        if path.exists() and path.is_file():
            context[rel] = path.read_text(encoding="utf-8")

    if payload.notes:
        context["notes"] = payload.notes

    VIBE_DATA.mkdir(parents=True, exist_ok=True)
    json_path = VIBE_DATA / "context.json"
    md_path = VIBE_DATA / "context.md"
    json_path.write_text(json.dumps(context, indent=2), encoding="utf-8")
    md_path.write_text("\n\n".join([f"=== {k} ===\n{v}" for k, v in context.items()]))

    return {
        "status": "ok",
        "files": len(context),
        "path": str(json_path),
    }


@router.post("/vibe/chat")
async def vibe_chat(payload: VibeChatRequest):
    try:
        from wizard.services.vibe_service import VibeService
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vibe service unavailable: {exc}")

    system = payload.system or ""
    if payload.with_context:
        context_path = VIBE_DATA / "context.md"
        if context_path.exists():
            system = (system + "\n\n" + context_path.read_text(encoding="utf-8")).strip()

    vibe = VibeService()
    try:
        response = vibe.generate(prompt=payload.prompt, system=system, format=payload.format)
    except Exception as exc:
        logger.error(f"[GOBLIN] Vibe chat failed: {exc}")
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "prompt": payload.prompt,
            "status": "error",
            "error": str(exc),
        }
        _write_history(entry)
        raise HTTPException(status_code=500, detail="Vibe chat failed")

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "prompt": payload.prompt,
        "status": "ok",
    }
    _write_history(entry)

    return {"status": "ok", "response": response}


@router.get("/vibe/history")
async def vibe_history(limit: int = Query(10, ge=1, le=200)):
    return {"count": len(_load_history(limit)), "history": _load_history(limit)}


# ============================================================================
# LOGS + VAULT SYNC ENDPOINTS
# ============================================================================


@router.get("/logs/list")
async def list_logs():
    if not LOG_ROOT.exists():
        return {"count": 0, "logs": []}
    logs = []
    for path in sorted(LOG_ROOT.iterdir()):
        if path.is_file():
            logs.append(
                {
                    "name": path.name,
                    "size_bytes": path.stat().st_size,
                    "modified_at": datetime.utcfromtimestamp(path.stat().st_mtime).isoformat() + "Z",
                }
            )
    return {"count": len(logs), "logs": logs}


@router.get("/logs/tail")
async def tail_logs(
    file: Optional[str] = Query(None),
    lines: int = Query(200, ge=1, le=2000),
):
    log_file = _latest_log_file() if not file else (LOG_ROOT / file)
    if not log_file:
        raise HTTPException(status_code=404, detail="No log files found")
    if not str(log_file.resolve()).startswith(str(LOG_ROOT.resolve())):
        raise HTTPException(status_code=400, detail="Invalid log path")
    content = _tail_file(log_file, lines)
    return {"file": log_file.name, "lines": len(content), "content": content}


@router.post("/vault/sync")
async def vault_sync(payload: VaultSyncRequest):
    source = _ensure_repo_path(payload.source)
    target = _ensure_repo_path(payload.target)
    if not source.exists():
        raise HTTPException(status_code=404, detail="Source path not found")
    target.mkdir(parents=True, exist_ok=True)

    report = {
        "source": str(source),
        "target": str(target),
        "extensions": payload.extensions,
        "dry_run": payload.dry_run,
        "copied": 0,
        "skipped": 0,
        "errors": [],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    for path in source.rglob("*"):
        if not path.is_file():
            continue
        if payload.extensions and path.suffix not in payload.extensions:
            report["skipped"] += 1
            continue

        rel = path.relative_to(source)
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if payload.dry_run:
            report["copied"] += 1
            continue
        try:
            shutil.copy2(path, dest)
            report["copied"] += 1
        except Exception as exc:
            report["errors"].append(f"{path}: {exc}")

    report_path = _write_vault_sync_report(report)
    report["report_path"] = str(report_path)
    return report
