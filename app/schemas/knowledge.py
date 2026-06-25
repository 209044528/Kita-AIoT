from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeAskRequest(BaseModel):
    question: str = Field(..., min_length=2, examples=["温度超过 80 摄氏度时应该如何处理？"])
    platform: Literal["auto", "dify", "bailian", "local"] = "auto"
    device_id: str | None = Field(default=None, examples=["device-001"])


class PlatformAnalyzeRequest(BaseModel):
    device_id: str
    alarm_type: str
    alarm_level: str
    alarm_message: str
    platform: Literal["dify", "bailian", "local"]
