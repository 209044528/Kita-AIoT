import json
import re
from typing import Any

from app.core.config import settings
from app.services.platforms import call_bailian_chat, call_dify_workflow
from app.services.rag import build_context, local_answer


ALARM_SYSTEM_PROMPT = """你是 Kita-AIoT 设备运维智能体。
必须依据设备状态、历史告警和给定知识库上下文分析，禁止编造参数。
输出 JSON，字段必须包含：
summary, possible_causes, actions, should_create_work_order, priority, references。
critical 告警应创建 P1 工单；连续同类 warning 或持续高温应创建 P2 工单。
references 必须引用给定知识库中的标题和章节。"""

QA_SYSTEM_PROMPT = """你是 Kita-AIoT 运维知识库助手。
只根据给定知识库上下文回答。信息不足时明确说明，不得编造。
回答应简洁、可执行，并在末尾列出引用的文档标题和章节。"""


def resolve_platform(requested: str) -> str:
    if requested != "auto":
        return requested
    configured = settings.AGENT_PLATFORM.lower()
    if configured in {"dify", "bailian", "local"}:
        if configured == "dify" and settings.DIFY_WORKFLOW_ENABLED:
            return "dify"
        if configured == "bailian" and settings.BAILIAN_API_KEY:
            return "bailian"
        if configured == "local":
            return "local"
    if settings.DIFY_WORKFLOW_ENABLED and settings.DIFY_API_KEY:
        return "dify"
    if settings.BAILIAN_API_KEY:
        return "bailian"
    return "local"


def _json_from_text(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {"answer": text}
    except json.JSONDecodeError:
        return {"answer": text}


def _bailian_text(response: dict[str, Any]) -> str:
    return response["choices"][0]["message"]["content"]


def analyze_alarm(
    platform: str,
    device: dict[str, Any],
    alarms: list[dict[str, Any]],
    alarm: dict[str, Any],
    local_diagnosis: dict[str, Any],
    references: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = resolve_platform(platform)
    context = build_context(references)
    input_data = {
        "device": device,
        "current_alarm": alarm,
        "recent_alarms": alarms,
        "local_diagnosis": local_diagnosis,
        "knowledge_context": context,
    }

    if selected == "dify":
        raw = call_dify_workflow(
            {
                "device_id": device["device_id"],
                "alarm_id": alarm["alarm_id"],
                "alarm_type": alarm["alarm_type"],
                "alarm_level": alarm["level"],
                "alarm_message": alarm["message"],
                "device_status": device,
                "local_diagnosis": {
                    **local_diagnosis,
                    "recent_alarms": alarms,
                    "rag_references": references,
                },
            },
            user=f"alarm:{device['device_id']}",
        )
        outputs = raw.get("data", {}).get("outputs", {})
        return {
            "platform": "dify",
            "analysis": outputs,
            "raw": raw,
            "references": references,
        }

    if selected == "bailian":
        raw = call_bailian_chat(
            [
                {"role": "system", "content": ALARM_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(input_data, ensure_ascii=False, default=str),
                },
            ],
            response_format={"type": "json_object"},
        )
        analysis = _json_from_text(_bailian_text(raw))
        return {
            "platform": "bailian",
            "analysis": analysis,
            "raw": raw,
            "references": references,
        }

    return {
        "platform": "local",
        "analysis": {
            "summary": alarm["message"],
            "possible_causes": [local_diagnosis["analysis"]],
            "actions": local_diagnosis["suggestion"],
            "should_create_work_order": alarm["level"] == "critical",
            "priority": "P1" if alarm["level"] == "critical" else "P2",
            "references": [
                {"title": item["title"], "section": item["section"]} for item in references
            ],
        },
        "raw": {},
        "references": references,
    }


def answer_question(
    platform: str,
    question: str,
    references: list[dict[str, Any]],
    device_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = resolve_platform(platform)
    context = build_context(references)

    if selected == "bailian":
        raw = call_bailian_chat(
            [
                {"role": "system", "content": QA_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"问题：{question}\n设备上下文：{json.dumps(device_context, ensure_ascii=False, default=str)}\n知识库：\n{context}",
                },
            ]
        )
        return {"platform": "bailian", "answer": _bailian_text(raw), "raw": raw}

    if selected == "dify":
        raw = call_dify_workflow(
            {
                "device_id": (device_context or {}).get("device_id", "knowledge-query"),
                "alarm_id": "knowledge-query",
                "alarm_type": "knowledge_question",
                "alarm_level": "info",
                "alarm_message": question,
                "device_status": device_context or {"status": "unknown"},
                "local_diagnosis": {
                    "question": question,
                    "knowledge_context": context,
                    "references": references,
                },
            },
            user="knowledge-query",
        )
        outputs = raw.get("data", {}).get("outputs", {})
        answer = (
            outputs.get("answer")
            or outputs.get("analysis")
            or outputs.get("result")
            or local_answer(question, references)
        )
        return {"platform": "dify", "answer": str(answer), "raw": raw}

    return {"platform": "local", "answer": local_answer(question, references), "raw": {}}
