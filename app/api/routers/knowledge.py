from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.serializers import model_to_dict
from app.models import Device, KnowledgeQuery
from app.schemas.knowledge import KnowledgeAskRequest, PlatformAnalyzeRequest
from app.services.agent import analyze_alarm, answer_question
from app.services.diagnosis import build_diagnosis
from app.services.rag import retrieve

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search")
def search_knowledge(
    query: str = Query(..., min_length=2),
    top_k: int = Query(default=3, ge=1, le=10),
) -> dict[str, Any]:
    references = retrieve(query, top_k)
    return {"query": query, "count": len(references), "references": references}


@router.post("/ask")
def ask_knowledge(
    payload: KnowledgeAskRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    device_context = None
    if payload.device_id:
        device = db.get(Device, payload.device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")
        device_context = model_to_dict(device)

    references = retrieve(payload.question)
    try:
        result = answer_question(payload.platform, payload.question, references, device_context)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"知识问答平台调用失败: {exc}") from exc

    record = KnowledgeQuery(
        question=payload.question,
        platform=result["platform"],
        answer=result["answer"],
        references=references,
        raw_response=result["raw"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "query_id": record.query_id,
        "platform": record.platform,
        "answer": record.answer,
        "references": references,
        "created_at": record.created_at.isoformat(),
    }


@router.get("/queries")
def list_queries(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    queries = list(
        db.scalars(select(KnowledgeQuery).order_by(KnowledgeQuery.created_at.desc()).limit(limit))
    )
    return {"count": len(queries), "queries": [model_to_dict(item) for item in queries]}


@router.post("/platform-analyze")
def platform_analyze(
    payload: PlatformAnalyzeRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    device = db.get(Device, payload.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")
    diagnosis = build_diagnosis(device, [], payload.alarm_message)
    alarm = {
        "alarm_id": "manual-analysis",
        "device_id": payload.device_id,
        "alarm_type": payload.alarm_type,
        "level": payload.alarm_level,
        "message": payload.alarm_message,
    }
    references = retrieve(f"{payload.alarm_type} {payload.alarm_message}")
    try:
        return analyze_alarm(
            payload.platform,
            model_to_dict(device),
            [],
            alarm,
            diagnosis,
            references,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"平台分析失败: {exc}") from exc
