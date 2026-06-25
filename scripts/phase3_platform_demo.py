import argparse
import json

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a phase-3 platform and RAG demo.")
    parser.add_argument("--base-url", default="http://localhost:8001")
    parser.add_argument("--platform", choices=["dify", "bailian", "local"], required=True)
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=240) as client:
        qa = client.post(
            "/api/v1/knowledge/ask",
            json={
                "question": "温度超过 80 摄氏度时，SOP 要求如何处理？",
                "platform": args.platform,
                "device_id": "device-001",
            },
        )
        qa.raise_for_status()
        alarm = client.post(
            "/api/v1/alarms/report",
            json={
                "device_id": "device-003",
                "alarm_type": "device_offline",
                "level": "critical",
                "message": f" {args.platform} 平台完整链路演示",
                "temperature": 29.0,
                "platform": args.platform,
            },
        )
        alarm.raise_for_status()

    print(
        json.dumps(
            {
                "knowledge": qa.json(),
                "alarm_workflow": alarm.json(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
