from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from uuid import uuid4

from app.core.database import DEVICES, ALARMS, WORK_ORDERS
from app.schemas.work_orders import WorkOrderCreate, WorkOrderResponse
from app.core.utils import now_iso

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

@router.post("/", response_model=WorkOrderResponse, status_code=201)
def create_work_order(payload: WorkOrderCreate) -> WorkOrderResponse:
    """Tool 3: create an operations work order from Agent analysis."""
    if payload.device_id not in DEVICES:
        raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")

    if payload.alarm_id and not any(alarm["alarm_id"] == payload.alarm_id for alarm in ALARMS):
        raise HTTPException(status_code=404, detail=f"Alarm {payload.alarm_id} not found")

    work_order = payload.model_dump()
    work_order.update(
        {
            "work_order_id": f"wo-{uuid4().hex[:8]}",
            "status": "created",
            "created_at": now_iso(),
        }
    )
    WORK_ORDERS.insert(0, work_order)
    return WorkOrderResponse(
        work_order_id=work_order["work_order_id"],
        status=work_order["status"],
        created_at=work_order["created_at"],
    )

@router.get("/")
def list_work_orders(device_id: Optional[str] = None) -> Dict[str, Any]:
    orders = WORK_ORDERS
    if device_id:
        orders = [order for order in WORK_ORDERS if order["device_id"] == device_id]
    return {"count": len(orders), "work_orders": orders}
