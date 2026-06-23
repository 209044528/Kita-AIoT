from pydantic import BaseModel, Field
from typing import Optional

class WorkOrderCreate(BaseModel):
    device_id: str = Field(..., examples=["device-001"])
    alarm_id: Optional[str] = Field(default=None, examples=["alarm-001"])
    title: str = Field(..., examples=["冷链温控网关高温告警处理"])
    reason: str = Field(..., examples=["设备持续高温，可能存在散热受阻或环境温度异常。"])
    suggestion: str = Field(..., examples=["检查散热口、风扇状态和冷库环境温度。"])
    priority: str = Field(default="P2", examples=["P2"])

class WorkOrderResponse(BaseModel):
    work_order_id: str
    status: str
    created_at: str
