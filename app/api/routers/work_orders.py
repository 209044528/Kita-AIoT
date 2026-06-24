from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.serializers import model_to_dict
from app.models import Alarm, Device, WorkOrder
from app.schemas.work_orders import WorkOrderCreate, WorkOrderResponse

router = APIRouter(prefix="/work-orders", tags=["work-orders"])


@router.post("/", response_model=WorkOrderResponse, status_code=201)
def create_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
) -> WorkOrderResponse:
    """Agent tool 4: create an operations work order."""
    if not db.get(Device, payload.device_id):
        raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")
    if payload.alarm_id and not db.get(Alarm, payload.alarm_id):
        raise HTTPException(status_code=404, detail=f"Alarm {payload.alarm_id} not found")

    work_order = WorkOrder(**payload.model_dump(), status="created")
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return WorkOrderResponse(
        work_order_id=work_order.work_order_id,
        status=work_order.status,
        created_at=work_order.created_at.isoformat(),
    )


@router.get("/")
def list_work_orders(
    device_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = select(WorkOrder).order_by(WorkOrder.created_at.desc())
    if device_id:
        statement = statement.where(WorkOrder.device_id == device_id)
    orders = list(db.scalars(statement.limit(100)))
    return {"count": len(orders), "work_orders": [model_to_dict(item) for item in orders]}
