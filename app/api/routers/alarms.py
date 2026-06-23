from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from uuid import uuid4

from app.core.database import DEVICES, ALARMS
from app.schemas.alarms import AlarmReport
from app.core.utils import now_iso

router = APIRouter(prefix="/alarms", tags=["alarms"])

@router.post("/report", status_code=201)
def report_alarm(payload: AlarmReport) -> Dict[str, Any]:
    """Convenience endpoint for local MQTT-simulator demos without a subscriber."""
    if payload.device_id not in DEVICES:
        raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")

    alarm = {
        "alarm_id": f"alarm-{uuid4().hex[:8]}",
        "device_id": payload.device_id,
        "alarm_type": payload.alarm_type,
        "level": payload.level,
        "message": payload.message,
        "temperature": payload.temperature,
        "created_at": payload.timestamp or now_iso(),
        "raw_payload": payload.model_dump(),
    }
    ALARMS.insert(0, alarm)

    if payload.temperature is not None:
        DEVICES[payload.device_id]["temperature"] = payload.temperature
    DEVICES[payload.device_id]["last_seen_at"] = now_iso()

    return {"status": "received", "alarm": alarm}

@router.get("/")
def get_all_alarms() -> Dict[str, Any]:
    return {"count": len(ALARMS), "alarms": ALARMS}
