import argparse
import json

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Kita-AIoT phase-2 API smoke test.")
    parser.add_argument("--base-url", default="http://localhost:8001")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    with httpx.Client(base_url=base_url, timeout=20) as client:
        health = client.get("/health")
        health.raise_for_status()

        alarm = client.post(
            "/api/v1/alarms/report",
            json={
                "device_id": "device-003",
                "alarm_type": "device_offline",
                "level": "critical",
                "message": "自动验收：设备离线",
                "temperature": 29.0,
            },
        )
        alarm.raise_for_status()

        workflows = client.get("/api/v1/workflow-executions")
        workflows.raise_for_status()
        work_orders = client.get("/api/v1/work-orders/")
        work_orders.raise_for_status()
        call_logs = client.get("/api/v1/call-logs")
        call_logs.raise_for_status()
        platforms = client.get("/api/v1/platforms/status")
        platforms.raise_for_status()

    result = {
        "health": health.json(),
        "alarm_workflow": alarm.json(),
        "workflow_count": workflows.json()["count"],
        "work_order_count": work_orders.json()["count"],
        "call_log_count": call_logs.json()["count"],
        "platforms": platforms.json(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
