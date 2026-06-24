from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.serializers import model_to_dict
from app.models import Alarm, Device, WorkflowExecution, WorkOrder
from app.services.diagnosis import build_diagnosis
from app.services.platforms import call_dify_workflow


def run_alarm_workflow(db: Session, payload: dict[str, Any], trigger_type: str) -> WorkflowExecution:
    execution = WorkflowExecution(
        trigger_type=trigger_type,
        platform="dify" if settings.DIFY_WORKFLOW_ENABLED else "local",
        status="running",
        input_payload=payload,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    try:
        device = db.get(Device, payload["device_id"])
        if not device:
            raise ValueError(f"Device {payload['device_id']} not found")

        created_at = payload.get("timestamp")
        alarm = Alarm(
            device_id=device.device_id,
            alarm_type=payload["alarm_type"],
            level=payload["level"],
            message=payload["message"],
            temperature=payload.get("temperature"),
            source=trigger_type,
            raw_payload=payload,
            created_at=datetime.fromisoformat(created_at) if created_at else datetime.now(timezone.utc),
        )
        db.add(alarm)
        if alarm.temperature is not None:
            device.temperature = alarm.temperature
        device.last_seen_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alarm)

        recent = list(
            db.scalars(
                select(Alarm)
                .where(Alarm.device_id == device.device_id)
                .order_by(Alarm.created_at.desc())
                .limit(5)
            )
        )
        diagnosis = build_diagnosis(device, recent, alarm.message)
        platform_output: dict[str, Any] | None = None

        if settings.DIFY_WORKFLOW_ENABLED:
            platform_output = call_dify_workflow(
                {
                    "device_id": device.device_id,
                    "alarm_id": alarm.alarm_id,
                    "alarm_type": alarm.alarm_type,
                    "alarm_level": alarm.level,
                    "alarm_message": alarm.message,
                    "device_status": model_to_dict(device),
                    "local_diagnosis": diagnosis,
                },
                user=f"mqtt:{device.device_id}",
            )

        work_order_id = None
        if alarm.level == "critical":
            order = WorkOrder(
                device_id=device.device_id,
                alarm_id=alarm.alarm_id,
                title=f"{device.name} {alarm.message}",
                reason=diagnosis["analysis"],
                suggestion="；".join(diagnosis["suggestion"]),
                priority="P1",
                status="created",
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            work_order_id = order.work_order_id

        execution.trigger_ref = alarm.alarm_id
        execution.status = "succeeded"
        execution.output_payload = {
            "alarm_id": alarm.alarm_id,
            "diagnosis": diagnosis,
            "work_order_id": work_order_id,
            "platform_output": platform_output,
        }
        execution.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(execution)
        return execution
    except Exception as exc:
        db.rollback()
        execution = db.get(WorkflowExecution, execution.execution_id)
        execution.status = "failed"
        execution.error_message = str(exc)
        execution.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(execution)
        return execution
