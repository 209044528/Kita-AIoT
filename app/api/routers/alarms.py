from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.serializers import model_to_dict
from app.models import Alarm, Device
from app.schemas.alarms import AlarmReport
from app.services.workflow import run_alarm_workflow

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.post("/report", status_code=201)
def report_alarm(payload: AlarmReport, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Receive an alarm and run the same workflow used by the MQTT consumer."""
    if not db.get(Device, payload.device_id):
        raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")
    execution = run_alarm_workflow(db, payload.model_dump(mode="json"), trigger_type="http")
    if execution.status == "failed":
        raise HTTPException(status_code=500, detail=execution.error_message)
    return {
        "status": "received",
        "execution_id": execution.execution_id,
        "result": execution.output_payload,
    }


@router.get("/")
def get_all_alarms(db: Session = Depends(get_db)) -> dict[str, Any]:
    alarms = list(db.scalars(select(Alarm).order_by(Alarm.created_at.desc()).limit(100)))
    return {"count": len(alarms), "alarms": [model_to_dict(item) for item in alarms]}
