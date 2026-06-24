from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alarm, Device


DEVICES = [
    {
        "device_id": "device-001",
        "name": "冷链温控网关 A-01",
        "type": "temperature_gateway",
        "status": "online",
        "location": "上海仓-冷库一区",
        "battery_level": 78,
        "temperature": 82.6,
        "signal_strength": -62,
        "last_seen_at": datetime.fromisoformat("2026-06-23T10:30:00+08:00"),
    },
    {
        "device_id": "device-002",
        "name": "产线振动传感器 B-12",
        "type": "vibration_sensor",
        "status": "online",
        "location": "苏州工厂-三号产线",
        "battery_level": 91,
        "temperature": 38.4,
        "signal_strength": -55,
        "last_seen_at": datetime.fromisoformat("2026-06-23T10:28:00+08:00"),
    },
    {
        "device_id": "device-003",
        "name": "边缘采集器 C-07",
        "type": "edge_collector",
        "status": "offline",
        "location": "杭州园区-配电房",
        "battery_level": 12,
        "temperature": 29.1,
        "signal_strength": None,
        "last_seen_at": datetime.fromisoformat("2026-06-23T09:41:00+08:00"),
    },
]

ALARMS = [
    {
        "alarm_id": "alarm-001",
        "device_id": "device-001",
        "alarm_type": "temperature_high",
        "level": "warning",
        "message": "设备温度超过 80 摄氏度阈值",
        "temperature": 82.6,
        "source": "seed",
        "created_at": datetime.fromisoformat("2026-06-23T10:20:00+08:00"),
        "raw_payload": {"source": "seed"},
    },
    {
        "alarm_id": "alarm-002",
        "device_id": "device-003",
        "alarm_type": "device_offline",
        "level": "critical",
        "message": "设备超过 30 分钟未上报心跳",
        "temperature": 29.1,
        "source": "seed",
        "created_at": datetime.fromisoformat("2026-06-23T09:45:00+08:00"),
        "raw_payload": {"source": "seed"},
    },
    {
        "alarm_id": "alarm-003",
        "device_id": "device-002",
        "alarm_type": "vibration_high",
        "level": "warning",
        "message": "振动 RMS 值连续三次超过阈值",
        "temperature": 38.4,
        "source": "seed",
        "created_at": datetime.fromisoformat("2026-06-23T10:05:00+08:00"),
        "raw_payload": {"source": "seed"},
    },
]


def seed_database(db: Session) -> None:
    if db.scalar(select(Device.device_id).limit(1)) is None:
        db.add_all(Device(**item) for item in DEVICES)
        db.commit()

    if db.scalar(select(Alarm.alarm_id).limit(1)) is None:
        db.add_all(Alarm(**item) for item in ALARMS)
        db.commit()
