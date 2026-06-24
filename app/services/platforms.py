from typing import Any
from time import perf_counter
from uuid import uuid4

import httpx

from app.core.config import settings


def _write_call_log(
    source: str,
    path: str,
    status_code: int,
    started: float,
    error_message: str | None = None,
) -> None:
    try:
        from app.core.database import SessionLocal
        from app.models import CallLog

        with SessionLocal() as db:
            db.add(
                CallLog(
                    request_id=uuid4().hex,
                    source=source,
                    method="POST",
                    path=path,
                    status_code=status_code,
                    duration_ms=round((perf_counter() - started) * 1000, 2),
                    error_message=error_message,
                )
            )
            db.commit()
    except Exception:
        pass


def call_dify_workflow(inputs: dict[str, Any], user: str = "kita-aiot") -> dict[str, Any]:
    if not settings.DIFY_API_BASE_URL or not settings.DIFY_API_KEY:
        raise RuntimeError("Dify API 未配置")

    url = f"{settings.DIFY_API_BASE_URL.rstrip('/')}/workflows/run"
    started = perf_counter()
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {settings.DIFY_API_KEY}"},
            json={"inputs": inputs, "response_mode": "blocking", "user": user},
            timeout=60,
        )
        response.raise_for_status()
        _write_call_log("dify", url, response.status_code, started)
        return response.json()
    except Exception as exc:
        status_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else 502
        _write_call_log("dify", url, status_code, started, str(exc))
        raise


def call_bailian(message: str) -> dict[str, Any]:
    if not settings.BAILIAN_API_KEY:
        raise RuntimeError("阿里百炼 API Key 未配置")

    url = f"{settings.BAILIAN_API_BASE_URL.rstrip('/')}/chat/completions"
    started = perf_counter()
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {settings.BAILIAN_API_KEY}"},
            json={
                "model": settings.BAILIAN_MODEL,
                "messages": [{"role": "user", "content": message}],
            },
            timeout=60,
        )
        response.raise_for_status()
        _write_call_log("bailian", url, response.status_code, started)
        return response.json()
    except Exception as exc:
        status_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else 502
        _write_call_log("bailian", url, status_code, started, str(exc))
        raise
