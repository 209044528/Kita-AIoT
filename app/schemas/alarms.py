from pydantic import BaseModel, Field
from typing import Optional

class AlarmReport(BaseModel):
    device_id: str = Field(..., examples=["device-001"])
    alarm_type: str = Field(..., examples=["temperature_high"])
    level: str = Field(..., examples=["warning"])
    message: str = Field(..., examples=["设备温度超过 80 摄氏度阈值"])
    temperature: Optional[float] = Field(default=None, examples=[82.6])
    timestamp: Optional[str] = Field(default=None, examples=["2026-06-23T10:20:00+08:00"])
