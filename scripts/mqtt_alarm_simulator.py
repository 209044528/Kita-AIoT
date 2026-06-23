import argparse
import json
import random
import time
from datetime import datetime, timezone
from urllib import request


ALARM_TEMPLATES = [
    {
        "device_id": "device-001",
        "alarm_type": "temperature_high",
        "level": "warning",
        "message": "设备温度超过 80 摄氏度阈值",
        "temperature_range": (80.0, 88.0),
    },
    {
        "device_id": "device-003",
        "alarm_type": "device_offline",
        "level": "critical",
        "message": "设备超过 30 分钟未上报心跳",
        "temperature_range": (25.0, 32.0),
    },
    {
        "device_id": "device-002",
        "alarm_type": "vibration_high",
        "level": "warning",
        "message": "振动 RMS 值连续三次超过阈值",
        "temperature_range": (36.0, 42.0),
    },
]


def build_payload() -> dict:
    template = random.choice(ALARM_TEMPLATES)
    low, high = template["temperature_range"]
    return {
        "device_id": template["device_id"],
        "alarm_type": template["alarm_type"],
        "level": template["level"],
        "message": template["message"],
        "temperature": round(random.uniform(low, high), 1),
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }


def publish_mqtt(host: str, port: int, topic: str, payload: dict) -> None:
    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:
        raise RuntimeError("缺少 paho-mqtt，请先运行 pip install -r requirements.txt") from exc

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(host, port, keepalive=60)
    client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1)
    client.disconnect()


def post_to_api(url: str, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate AIoT alarm reports over MQTT.")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", default="aiot/device/alarm", help="MQTT topic")
    parser.add_argument("--count", type=int, default=1, help="Number of alarm messages")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between messages")
    parser.add_argument("--dry-run", action="store_true", help="Print payload only")
    parser.add_argument(
        "--post-url",
        default="",
        help="Also POST payload to FastAPI, for example http://localhost:8000/api/v1/alarms/report",
    )
    args = parser.parse_args()

    for index in range(args.count):
        payload = build_payload()
        print(json.dumps({"topic": args.topic, "payload": payload}, ensure_ascii=False, indent=2))

        if not args.dry_run:
            publish_mqtt(args.host, args.port, args.topic, payload)

        if args.post_url:
            post_to_api(args.post_url, payload)

        if index < args.count - 1:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
