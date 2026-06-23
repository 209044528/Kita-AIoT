from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


app = FastAPI(
    title="Kita-AIoT Phase 1 Tool API",
    description="AIoT device operations tool API for Dify workflow demos.",
    version="0.1.0",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


DEVICES: Dict[str, Dict[str, Any]] = {
    "device-001": {
        "device_id": "device-001",
        "name": "冷链温控网关 A-01",
        "type": "temperature_gateway",
        "status": "online",
        "location": "上海仓-冷库一区",
        "battery_level": 78,
        "temperature": 82.6,
        "signal_strength": -62,
        "last_seen_at": "2026-06-23T10:30:00+08:00",
    },
    "device-002": {
        "device_id": "device-002",
        "name": "产线振动传感器 B-12",
        "type": "vibration_sensor",
        "status": "online",
        "location": "苏州工厂-三号产线",
        "battery_level": 91,
        "temperature": 38.4,
        "signal_strength": -55,
        "last_seen_at": "2026-06-23T10:28:00+08:00",
    },
    "device-003": {
        "device_id": "device-003",
        "name": "边缘采集器 C-07",
        "type": "edge_collector",
        "status": "offline",
        "location": "杭州园区-配电房",
        "battery_level": 12,
        "temperature": 29.1,
        "signal_strength": None,
        "last_seen_at": "2026-06-23T09:41:00+08:00",
    },
}


ALARMS: List[Dict[str, Any]] = [
    {
        "alarm_id": "alarm-001",
        "device_id": "device-001",
        "alarm_type": "temperature_high",
        "level": "warning",
        "message": "设备温度超过 80 摄氏度阈值",
        "temperature": 82.6,
        "created_at": "2026-06-23T10:20:00+08:00",
        "raw_payload": {"source": "seed"},
    },
    {
        "alarm_id": "alarm-002",
        "device_id": "device-003",
        "alarm_type": "device_offline",
        "level": "critical",
        "message": "设备超过 30 分钟未上报心跳",
        "temperature": 29.1,
        "created_at": "2026-06-23T09:45:00+08:00",
        "raw_payload": {"source": "seed"},
    },
    {
        "alarm_id": "alarm-003",
        "device_id": "device-002",
        "alarm_type": "vibration_high",
        "level": "warning",
        "message": "振动 RMS 值连续三次超过阈值",
        "temperature": 38.4,
        "created_at": "2026-06-23T10:05:00+08:00",
        "raw_payload": {"source": "seed"},
    },
]


WORK_ORDERS: List[Dict[str, Any]] = []


class AlarmReport(BaseModel):
    device_id: str = Field(..., examples=["device-001"])
    alarm_type: str = Field(..., examples=["temperature_high"])
    level: str = Field(..., examples=["warning"])
    message: str = Field(..., examples=["设备温度超过 80 摄氏度阈值"])
    temperature: Optional[float] = Field(default=None, examples=[82.6])
    timestamp: Optional[str] = Field(default=None, examples=["2026-06-23T10:20:00+08:00"])


class WorkOrderCreate(BaseModel):
    device_id: str = Field(..., examples=["device-001"])
    alarm_id: Optional[str] = Field(default=None, examples=["alarm-001"])
    title: str = Field(..., examples=["冷链温控网关高温告警处理"])
    reason: str = Field(..., examples=["设备持续高温，可能存在散热受阻或环境温度异常。"])
    suggestion: str = Field(..., examples=["检查散热口、风扇状态和冷库环境温度。"])
    priority: str = Field(default="P2", examples=["P2"])


class DeviceDiagnosisRequest(BaseModel):
    device_id: str = Field(..., examples=["device-001"])
    question: str = Field(..., examples=["设备持续温度过高，应该如何处理？"])


class WorkOrderResponse(BaseModel):
    work_order_id: str
    status: str
    created_at: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "kita-aiot-phase1"}


@app.get("/api/v1/devices/{device_id}/status")
def get_device_status(device_id: str) -> Dict[str, Any]:
    """Tool 1: query current device status for an Agent workflow."""
    device = DEVICES.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device


@app.get("/api/v1/devices/{device_id}/alarms")
def get_recent_alarms(
    device_id: str,
    limit: int = Query(default=10, ge=1, le=50),
) -> Dict[str, Any]:
    """Tool 2: query recent alarms for an Agent workflow."""
    if device_id not in DEVICES:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

    alarms = [alarm for alarm in ALARMS if alarm["device_id"] == device_id]
    alarms = sorted(alarms, key=lambda item: item["created_at"], reverse=True)[:limit]
    return {"device_id": device_id, "count": len(alarms), "alarms": alarms}


@app.post("/api/v1/work-orders", response_model=WorkOrderResponse, status_code=201)
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


@app.get("/api/v1/work-orders")
def list_work_orders(device_id: Optional[str] = None) -> Dict[str, Any]:
    orders = WORK_ORDERS
    if device_id:
        orders = [order for order in WORK_ORDERS if order["device_id"] == device_id]
    return {"count": len(orders), "work_orders": orders}


@app.post("/api/v1/tools/device-diagnosis")
def device_diagnosis(payload: DeviceDiagnosisRequest) -> Dict[str, Any]:
    """Optional Agent helper: combine device status, alarms, and KB-style guidance."""
    device = DEVICES.get(payload.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")

    recent_alarms = [
        alarm for alarm in ALARMS if alarm["device_id"] == payload.device_id
    ][:5]
    alarm_types = {alarm["alarm_type"] for alarm in recent_alarms}

    suggestions = ["先确认设备在线状态、最近心跳时间和历史告警频率。"]
    references = [
        {"title": "AIoT 设备运维 SOP", "section": "工单内容要求"},
        {"title": "设备告警 FAQ", "section": "什么时候需要创建工单"},
    ]

    if "temperature_high" in alarm_types or "温度" in payload.question:
        analysis = "设备存在高温风险，常见原因包括散热受阻、风扇异常或部署环境温度过高。"
        suggestions.extend(
            [
                "检查设备散热口是否堵塞或被遮挡。",
                "检查风扇是否正常运行。",
                "确认设备周边是否靠近热源，必要时调整部署位置。",
                "若温度持续高于 80 摄氏度，建议创建 P2 工单安排现场处理。",
            ]
        )
        references.append({"title": "故障排查手册", "section": "temperature_high"})
    elif "device_offline" in alarm_types or "离线" in payload.question:
        analysis = "设备存在离线风险，应优先排查供电、电量和网络链路。"
        suggestions.extend(
            [
                "检查设备电量和现场供电。",
                "检查网关网络、SIM 卡或以太网连接。",
                "确认 MQTT Broker 地址和认证配置是否正确。",
                "离线超过 30 分钟建议创建工单。",
            ]
        )
        references.append({"title": "故障排查手册", "section": "device_offline"})
    elif "vibration_high" in alarm_types or "振动" in payload.question:
        analysis = "设备存在振动异常风险，可能与传感器安装、轴承状态或负载变化有关。"
        suggestions.extend(
            [
                "检查传感器固定螺栓和安装位置。",
                "对比产线负载和设备运行工况。",
                "连续告警时创建 P2 工单。",
            ]
        )
        references.append({"title": "故障排查手册", "section": "vibration_high"})
    else:
        analysis = "当前问题需要结合设备状态、历史告警和知识库内容进一步判断。"

    return {
        "device_id": payload.device_id,
        "question": payload.question,
        "device_status": device,
        "recent_alarms": recent_alarms,
        "analysis": analysis,
        "suggestion": suggestions,
        "references": references,
    }


@app.post("/api/v1/alarms/report", status_code=201)
def report_alarm(payload: AlarmReport) -> Dict[str, Any]:
    """Convenience endpoint for local MQTT-simulator demos without a subscriber."""
    if payload.device_id not in DEVICES:
        raise HTTPException(status_code=404, detail=f"Device {payload.device_id} not found")

    alarm = {
        "alarm_id": f"alarm-{uuid4().hex[:8]}",
        "device_id": payload.device_id,
        "alarm_type": payload.alarm_type,
        "level": payload.level,
        "message": payload.message,
        "temperature": payload.temperature,
        "created_at": payload.timestamp or now_iso(),
        "raw_payload": payload.model_dump(),
    }
    ALARMS.insert(0, alarm)

    if payload.temperature is not None:
        DEVICES[payload.device_id]["temperature"] = payload.temperature
    DEVICES[payload.device_id]["last_seen_at"] = now_iso()

    return {"status": "received", "alarm": alarm}
