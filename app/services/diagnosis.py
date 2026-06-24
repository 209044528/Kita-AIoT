from app.models import Alarm, Device


def build_diagnosis(device: Device, alarms: list[Alarm], question: str) -> dict:
    alarm_types = {alarm.alarm_type for alarm in alarms}
    suggestions = ["先确认设备在线状态、最近心跳时间和历史告警频率。"]
    references = [
        {"title": "AIoT 设备运维 SOP", "section": "工单内容要求"},
        {"title": "设备告警 FAQ", "section": "什么时候需要创建工单"},
    ]

    if "temperature_high" in alarm_types or "温度" in question:
        analysis = "设备存在高温风险，常见原因包括散热受阻、风扇异常或部署环境温度过高。"
        suggestions += [
            "检查设备散热口是否堵塞或被遮挡。",
            "检查风扇是否正常运行。",
            "确认设备周边是否靠近热源，必要时调整部署位置。",
            "若温度持续高于 80 摄氏度，建议创建 P2 工单安排现场处理。",
        ]
        references.append({"title": "故障排查手册", "section": "temperature_high"})
    elif "device_offline" in alarm_types or "离线" in question:
        analysis = "设备存在离线风险，应优先排查供电、电量和网络链路。"
        suggestions += [
            "检查设备电量和现场供电。",
            "检查网关网络、SIM 卡或以太网连接。",
            "确认 MQTT Broker 地址和认证配置是否正确。",
            "离线超过 30 分钟建议创建工单。",
        ]
        references.append({"title": "故障排查手册", "section": "device_offline"})
    elif "vibration_high" in alarm_types or "振动" in question:
        analysis = "设备存在振动异常风险，可能与传感器安装、轴承状态或负载变化有关。"
        suggestions += [
            "检查传感器固定螺栓和安装位置。",
            "对比产线负载和设备运行工况。",
            "连续告警时创建 P2 工单。",
        ]
        references.append({"title": "故障排查手册", "section": "vibration_high"})
    else:
        analysis = "当前问题需要结合设备状态、历史告警和知识库内容进一步判断。"

    return {"analysis": analysis, "suggestion": suggestions, "references": references}
