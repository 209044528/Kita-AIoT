from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.serializers import model_to_dict
from app.models import CallLog, WorkflowExecution
from app.services.platforms import call_bailian

router = APIRouter(tags=["operations"])


class BailianTestRequest(BaseModel):
    message: str


@router.get("/workflow-executions")
def list_workflow_executions(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    executions = list(
        db.scalars(select(WorkflowExecution).order_by(WorkflowExecution.started_at.desc()).limit(limit))
    )
    return {"count": len(executions), "executions": [model_to_dict(item) for item in executions]}


@router.get("/call-logs")
def list_call_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    logs = list(db.scalars(select(CallLog).order_by(CallLog.created_at.desc()).limit(limit)))
    return {"count": len(logs), "logs": [model_to_dict(item) for item in logs]}


@router.get("/platforms/status")
def platform_status() -> dict[str, Any]:
    return {
        "dify": {
            "configured": bool(settings.DIFY_API_BASE_URL and settings.DIFY_API_KEY),
            "workflow_enabled": settings.DIFY_WORKFLOW_ENABLED,
        },
        "bailian": {
            "configured": bool(settings.BAILIAN_API_KEY),
            "model": settings.BAILIAN_MODEL,
        },
        "agent": {"default_platform": settings.AGENT_PLATFORM},
        "n8n": {"configured": bool(settings.N8N_WEBHOOK_URL), "webhook_url": settings.N8N_WEBHOOK_URL},
        "mqtt": {"enabled": settings.MQTT_ENABLED, "topic": settings.MQTT_TOPIC},
        "minio": {"enabled": settings.MINIO_ENABLED, "bucket": settings.MINIO_BUCKET},
        "database": {"backend": settings.DATABASE_URL.split(":", 1)[0]},
    }


@router.post("/platforms/bailian/test")
def test_bailian(payload: BailianTestRequest) -> dict[str, Any]:
    try:
        return call_bailian(payload.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"百炼调用失败: {exc}") from exc
