from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any

from app.core.database import DEVICES, ALARMS
from app.schemas.devices import DeviceDiagnosisRequest

router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("/{device_id}/status")
def get_device_status(device_id: str) -> Dict[str, Any]:
    """Tool 1: query current device status for an Agent workflow."""
    device = DEVICES.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device

@router.get("/{device_id}/alarms")
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

@router.post("/diagnosis")
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
