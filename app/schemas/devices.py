from pydantic import BaseModel, Field

class DeviceDiagnosisRequest(BaseModel):
    device_id: str = Field(..., examples=["device-001"])
    question: str = Field(..., examples=["设备持续温度过高，应该如何处理？"])
