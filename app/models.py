from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


class BaseModel(Base):
    __abstract__ = True


class Device(BaseModel):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    location: Mapped[str] = mapped_column(String(255))
    battery_level: Mapped[Optional[int]] = mapped_column(Integer)
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    signal_strength: Mapped[Optional[int]] = mapped_column(Integer)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Alarm(BaseModel):
    __tablename__ = "alarms"

    alarm_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("alarm"))
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), index=True)
    alarm_type: Mapped[str] = mapped_column(String(100), index=True)
    level: Mapped[str] = mapped_column(String(32), index=True)
    message: Mapped[str] = mapped_column(Text)
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), default="api")
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class WorkOrder(BaseModel):
    __tablename__ = "work_orders"

    work_order_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("wo"))
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), index=True)
    alarm_id: Mapped[Optional[str]] = mapped_column(ForeignKey("alarms.alarm_id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(16), default="P2")
    status: Mapped[str] = mapped_column(String(32), default="created", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CallLog(BaseModel):
    __tablename__ = "call_logs"

    call_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("call"))
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(32), default="http")
    method: Mapped[str] = mapped_column(String(16))
    path: Mapped[str] = mapped_column(String(500), index=True)
    status_code: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[float] = mapped_column(Float)
    client_host: Mapped[Optional[str]] = mapped_column(String(128))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class WorkflowExecution(BaseModel):
    __tablename__ = "workflow_executions"

    execution_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("wf"))
    trigger_type: Mapped[str] = mapped_column(String(32), index=True)
    trigger_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    platform: Mapped[str] = mapped_column(String(32), default="local")
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Document(BaseModel):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("doc"))
    device_id: Mapped[Optional[str]] = mapped_column(ForeignKey("devices.device_id"), nullable=True, index=True)
    object_name: Mapped[str] = mapped_column(String(500), unique=True)
    file_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(128))
    size: Mapped[int] = mapped_column(Integer)
    bucket: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KnowledgeQuery(BaseModel):
    __tablename__ = "knowledge_queries"

    query_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("qa"))
    question: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(32), default="local")
    answer: Mapped[str] = mapped_column(Text)
    references: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    raw_response: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
