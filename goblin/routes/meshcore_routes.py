"""
MeshCore Routes - Device Manager + Pairing API Scaffolding

All endpoints prefixed with /api/dev/meshcore/*
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from extensions.transport.meshcore.device_registry import (
    DeviceRegistry,
    DeviceStatus,
    DeviceType,
)

router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "memory" / "sandbox" / "meshcore"
PAIRING_PATH = DATA_ROOT / "pairings.json"
SCHEMA_PATH = REPO_ROOT / "dev" / "goblin" / "schemas" / "meshcore_pairing.schema.json"

registry = DeviceRegistry(DATA_ROOT / "devices")


class DeviceCreateRequest(BaseModel):
    device_id: str = Field(..., min_length=1)
    device_type: str = Field("end_device")


class DeviceStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)


class PairingCreateRequest(BaseModel):
    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    method: str = Field("pin")
    expires_in_seconds: int = Field(900, ge=60, le=86400)
    metadata: Optional[Dict[str, object]] = None


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _load_pairings() -> Dict[str, object]:
    if not PAIRING_PATH.exists():
        return {"pairings": [], "updated_at": _now_iso()}
    try:
        return json.loads(PAIRING_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"pairings": [], "updated_at": _now_iso()}


def _save_pairings(data: Dict[str, object]) -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    PAIRING_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _generate_pin() -> str:
    return f"{random.randint(100000, 999999)}"


def _parse_device_type(value: str) -> DeviceType:
    mapping = {
        "node": DeviceType.NODE,
        "gateway": DeviceType.GATEWAY,
        "sensor": DeviceType.SENSOR,
        "repeater": DeviceType.REPEATER,
        "end_device": DeviceType.END_DEVICE,
    }
    if value not in mapping:
        raise HTTPException(status_code=400, detail="Invalid device_type")
    return mapping[value]


def _parse_device_status(value: str) -> DeviceStatus:
    mapping = {
        "online": DeviceStatus.ONLINE,
        "offline": DeviceStatus.OFFLINE,
        "connecting": DeviceStatus.CONNECTING,
        "error": DeviceStatus.ERROR,
    }
    if value not in mapping:
        raise HTTPException(status_code=400, detail="Invalid status")
    return mapping[value]


def _ensure_device(device_id: str, device_type: DeviceType) -> None:
    if not registry.get_device(device_id):
        registry.register_device(device_id, device_type)


@router.get("/")
async def meshcore_index():
    return {
        "status": "ok",
        "feature": "meshcore",
        "version": "0.1",
        "endpoints": [
            "/api/dev/meshcore/status",
            "/api/dev/meshcore/devices",
            "/api/dev/meshcore/devices/{device_id}",
            "/api/dev/meshcore/devices/{device_id}/status",
            "/api/dev/meshcore/pairings",
            "/api/dev/meshcore/pairings/{pairing_id}",
            "/api/dev/meshcore/pairings/{pairing_id}/confirm",
            "/api/dev/meshcore/pairings/{pairing_id}/cancel",
            "/api/dev/meshcore/schema",
        ],
    }


@router.get("/schema")
async def meshcore_schema():
    if not SCHEMA_PATH.exists():
        raise HTTPException(status_code=404, detail="Schema file not found")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@router.get("/status")
async def meshcore_status():
    return {
        "status": "ready",
        "devices": len(registry.list_devices()),
        "pairings": len(_load_pairings().get("pairings", [])),
    }


@router.get("/devices")
async def list_devices():
    devices = [d.to_dict() for d in registry.list_devices()]
    return {"count": len(devices), "devices": devices}


@router.post("/devices")
async def create_device(payload: DeviceCreateRequest):
    device_type = _parse_device_type(payload.device_type)
    _ensure_device(payload.device_id, device_type)
    device = registry.get_device(payload.device_id)
    return {"status": "registered", "device": device.to_dict() if device else None}


@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    device = registry.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device.to_dict()


@router.post("/devices/{device_id}/status")
async def update_device_status(device_id: str, payload: DeviceStatusRequest):
    status = _parse_device_status(payload.status)
    registry.update_status(device_id, status)
    device = registry.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "updated", "device": device.to_dict()}


@router.get("/pairings")
async def list_pairings():
    data = _load_pairings()
    return {"count": len(data.get("pairings", [])), "pairings": data.get("pairings", [])}


@router.post("/pairings")
async def create_pairing(payload: PairingCreateRequest):
    method = payload.method
    if method not in {"pin", "qr", "manual"}:
        raise HTTPException(status_code=400, detail="Invalid method")

    _ensure_device(payload.source_id, DeviceType.NODE)
    _ensure_device(payload.target_id, DeviceType.END_DEVICE)

    pairing_id = f"pair-{uuid.uuid4().hex[:8]}"
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(seconds=payload.expires_in_seconds)
    pairing_code = _generate_pin() if method in {"pin", "qr"} else None

    record = {
        "pairing_id": pairing_id,
        "source_id": payload.source_id,
        "target_id": payload.target_id,
        "method": method,
        "status": "pending",
        "pairing_code": pairing_code,
        "created_at": created_at.isoformat() + "Z",
        "expires_at": expires_at.isoformat() + "Z",
        "metadata": payload.metadata or {},
    }

    data = _load_pairings()
    data["pairings"] = data.get("pairings", [])
    data["pairings"].append(record)
    data["updated_at"] = _now_iso()
    _save_pairings(data)

    return {"status": "created", "pairing": record}


@router.get("/pairings/{pairing_id}")
async def get_pairing(pairing_id: str):
    data = _load_pairings()
    for record in data.get("pairings", []):
        if record.get("pairing_id") == pairing_id:
            return record
    raise HTTPException(status_code=404, detail="Pairing not found")


@router.post("/pairings/{pairing_id}/confirm")
async def confirm_pairing(pairing_id: str):
    data = _load_pairings()
    for record in data.get("pairings", []):
        if record.get("pairing_id") == pairing_id:
            record["status"] = "confirmed"
            data["updated_at"] = _now_iso()
            _save_pairings(data)
            return {"status": "confirmed", "pairing": record}
    raise HTTPException(status_code=404, detail="Pairing not found")


@router.post("/pairings/{pairing_id}/cancel")
async def cancel_pairing(pairing_id: str):
    data = _load_pairings()
    for record in data.get("pairings", []):
        if record.get("pairing_id") == pairing_id:
            record["status"] = "canceled"
            data["updated_at"] = _now_iso()
            _save_pairings(data)
            return {"status": "canceled", "pairing": record}
    raise HTTPException(status_code=404, detail="Pairing not found")
