from time import perf_counter
from typing import Any
from uuid import uuid4
import json

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
    normalized_inputs = inputs
    if settings.DIFY_SERIALIZE_COMPLEX_INPUTS:
        normalized_inputs = {
            key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
            for key, value in inputs.items()
        }
    started = perf_counter()
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {settings.DIFY_API_KEY}"},
            json={"inputs": normalized_inputs, "response_mode": "blocking", "user": user},
            timeout=settings.DIFY_TIMEOUT_SECONDS,
        )
        if (
            response.status_code == 400
            and not settings.DIFY_SERIALIZE_COMPLEX_INPUTS
            and "must be a string" in response.text
        ):
            _write_call_log("dify", url, response.status_code, started, response.text[:1000])
            normalized_inputs = {
                key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                for key, value in inputs.items()
            }
            started = perf_counter()
            response = httpx.post(
                url,
                headers={"Authorization": f"Bearer {settings.DIFY_API_KEY}"},
                json={"inputs": normalized_inputs, "response_mode": "blocking", "user": user},
                timeout=settings.DIFY_TIMEOUT_SECONDS,
            )
        if response.is_error:
            raise RuntimeError(f"Dify API {response.status_code}: {response.text[:1000]}")
        _write_call_log("dify", url, response.status_code, started)
        return response.json()
    except Exception as exc:
        status_code = response.status_code if "response" in locals() else 502
        _write_call_log("dify", url, status_code, started, str(exc))
        raise


def call_bailian_chat(
    messages: list[dict[str, str]],
    response_format: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not settings.BAILIAN_API_KEY:
        raise RuntimeError("阿里百炼 API Key 未配置")

    url = f"{settings.BAILIAN_API_BASE_URL.rstrip('/')}/chat/completions"
    started = perf_counter()
    payload: dict[str, Any] = {
        "model": settings.BAILIAN_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    if response_format:
        payload["response_format"] = response_format
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {settings.BAILIAN_API_KEY}"},
            json=payload,
            timeout=settings.BAILIAN_TIMEOUT_SECONDS,
        )
        if response.is_error:
            raise RuntimeError(f"百炼 API {response.status_code}: {response.text[:1000]}")
        _write_call_log("bailian", url, response.status_code, started)
        return response.json()
    except Exception as exc:
        status_code = response.status_code if "response" in locals() else 502
        _write_call_log("bailian", url, status_code, started, str(exc))
        raise


def call_bailian(message: str) -> dict[str, Any]:
    return call_bailian_chat([{"role": "user", "content": message}])
