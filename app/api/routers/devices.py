from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.serializers import model_to_dict
from app.models import Alarm, Device
from app.schemas.devices import DeviceDiagnosisRequest
from app.services.diagnosis import build_diagnosis

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/")
def list_devices(db: Session = Depends(get_db)) -> dict[str, Any]:
    devices = list(db.scalars(select(Device).order_by(Device.device_id)))
    return {"count": len(devices), "devices": [model_to_dict(item) for item in devices]}


@router.get("/{device_id}/status")
def get_device_status(device_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Agent tool 1: query current device status."""
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return model_to_dict(device)


@router.get("/{device_id}/alarms")
def get_recent_alarms(
    device_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Agent tool 2: query recent alarms."""
    if not db.get(Device, device_id):
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    alarms = list(
        db.scalars(
            select(Alarm)
            .where(Alarm.device_id == device_id)
            .order_by(Alarm.created_at.desc())
            .limit(limit)
        )
    )
    return {"device_id": device_id, "count": len(alarms), "alarms": [model_to_dict(a) for a in alarms]}


@router.post("/diagnosis")
def device_diagnosis(
    payload: DeviceDiagnosisRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Agent tool 3: combine status, alarms, and KB-style guidance."""
    device = db.get(Device, payload.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")
    alarms = list(
        db.scalars(
            select(Alarm)
            .where(Alarm.device_id == payload.device_id)
            .order_by(Alarm.created_at.desc())
            .limit(5)
        )
    )
    diagnosis = build_diagnosis(device, alarms, payload.question)
    return {
        "device_id": payload.device_id,
        "question": payload.question,
        "device_status": model_to_dict(device),
        "recent_alarms": [model_to_dict(item) for item in alarms],
        **diagnosis,
    }
