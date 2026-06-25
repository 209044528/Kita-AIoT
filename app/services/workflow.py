from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.serializers import model_to_dict
from app.models import Alarm, Device, WorkflowExecution, WorkOrder
from app.services.agent import analyze_alarm, resolve_platform
from app.services.diagnosis import build_diagnosis
from app.services.rag import retrieve


def _should_create_order(
    alarm: Alarm,
    recent: list[Alarm],
    platform_analysis: dict[str, Any],
) -> tuple[bool, str]:
    if alarm.level == "critical":
        return True, "P1"
    analysis = platform_analysis.get("analysis", {})
    if isinstance(analysis, dict) and analysis.get("should_create_work_order") is True:
        return True, str(analysis.get("priority") or "P2")
    same_warning_count = sum(
        1
        for item in recent
        if item.alarm_type == alarm.alarm_type and item.level == "warning"
    )
    if same_warning_count >= 3:
        return True, "P2"
    return False, "P2"


def _work_order_text(
    diagnosis: dict[str, Any],
    platform_analysis: dict[str, Any],
) -> tuple[str, str]:
    analysis = platform_analysis.get("analysis", {})
    if not isinstance(analysis, dict):
        return diagnosis["analysis"], "；".join(diagnosis["suggestion"])
    causes = analysis.get("possible_causes")
    actions = analysis.get("actions")
    reason = analysis.get("summary") or diagnosis["analysis"]
    if causes:
        reason = f"{reason}；可能原因：{'；'.join(map(str, causes))}"
    suggestion = "；".join(map(str, actions)) if actions else "；".join(diagnosis["suggestion"])
    return str(reason), suggestion


def run_alarm_workflow(db: Session, payload: dict[str, Any], trigger_type: str) -> WorkflowExecution:
    requested_platform = str(payload.get("platform") or "auto")
    selected_platform = resolve_platform(requested_platform)
    execution = WorkflowExecution(
        trigger_type=trigger_type,
        platform=selected_platform,
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
                .limit(10)
            )
        )
        diagnosis = build_diagnosis(device, recent, alarm.message)
        references = retrieve(f"{alarm.alarm_type} {alarm.message} {device.name}")
        platform_result = analyze_alarm(
            selected_platform,
            model_to_dict(device),
            [model_to_dict(item) for item in recent],
            model_to_dict(alarm),
            diagnosis,
            references,
        )

        create_order, priority = _should_create_order(alarm, recent, platform_result)
        work_order_id = None
        if create_order:
            reason, suggestion = _work_order_text(diagnosis, platform_result)
            order = WorkOrder(
                device_id=device.device_id,
                alarm_id=alarm.alarm_id,
                title=f"{device.name} {alarm.message}",
                reason=reason,
                suggestion=suggestion,
                priority=priority,
                status="created",
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            work_order_id = order.work_order_id

        execution.trigger_ref = alarm.alarm_id
        execution.platform = platform_result["platform"]
        execution.status = "succeeded"
        execution.output_payload = {
            "alarm_id": alarm.alarm_id,
            "diagnosis": diagnosis,
            "rag_references": references,
            "agent": platform_result,
            "work_order_id": work_order_id,
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
