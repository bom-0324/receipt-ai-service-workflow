"""
agent_client.py

Upstage Studio Agent 공통 호출부.

흐름: 파일 업로드(Files API) → Job 생성(Responses API, model=agt_ID)
      → 상태 조회(polling) → output_text JSON 파싱

Upstage Studio API는 OpenAI 호환 형식이라 openai 패키지로 호출한다.
문서: https://console.upstage.ai/docs/studio-and-agents/agents/overview
"""

import json
import mimetypes
import re
import time

import config


class AgentError(Exception):
    """사용자에게 그대로 보여줄 수 있는 한국어 오류."""


##################################################
# Client
##################################################

_client = None


def get_client():
    global _client
    if _client is None:
        from openai import OpenAI  # 지연 import: mock 모드에서는 필요 없음

        _client = OpenAI(
            api_key=config.UPSTAGE_API_KEY,
            base_url=config.UPSTAGE_BASE_URL,
            timeout=60,
            max_retries=2,
        )
    return _client


def set_client(client):
    """테스트용: 가짜 클라이언트를 주입한다."""
    global _client
    _client = client


def _friendly_error(e: Exception, agent_id: str = "") -> AgentError:
    if isinstance(e, AgentError):
        return e
    status = getattr(e, "status_code", None)
    name = type(e).__name__
    if status == 401 or name == "AuthenticationError":
        return AgentError("API 키가 올바르지 않습니다(401). UPSTAGE_API_KEY를 확인하세요.")
    if status == 403:
        return AgentError("이 API 키로 해당 Agent를 쓸 권한이 없습니다(403).")
    if status == 404 or name == "NotFoundError":
        return AgentError(f"Agent를 찾을 수 없습니다(404). Agent ID({agent_id})를 다시 복사하세요.")
    if status == 415:
        return AgentError("지원하지 않는 파일 형식입니다(415).")
    if status == 429 or name == "RateLimitError":
        return AgentError("요청이 너무 많습니다(429). 잠시 후 다시 시도하세요.")
    if name in ("APIConnectionError", "APITimeoutError"):
        return AgentError("Upstage 서버에 연결하지 못했습니다. 네트워크를 확인하세요.")
    return AgentError(f"API 호출 오류: {name}: {e}")


##################################################
# Files API
##################################################

def upload_file(file_name: str, data: bytes) -> str:
    """영수증 파일을 업로드하고 file_id를 돌려준다."""
    mime = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    try:
        uploaded = get_client().files.create(
            file=(file_name, data, mime),
            purpose="user_data",
        )
    except Exception as e:  # noqa: BLE001
        raise _friendly_error(e) from e
    return uploaded.id


def delete_file(file_id: str) -> None:
    """업로드한 파일 정리(실패해도 무시)."""
    try:
        get_client().files.delete(file_id)
    except Exception:  # noqa: BLE001
        pass


##################################################
# Responses API (Job)
##################################################

def _create_job(agent_id: str, file_id: str, config_id: str = ""):
    kwargs = {
        "model": agent_id,
        "include": ["last"],
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_file", "file_id": file_id}],
            }
        ],
    }
    if config_id:
        kwargs["extra_body"] = {"config_id": config_id}

    # 업로드 직후에는 파일 변환이 끝나지 않아 409가 올 수 있어 몇 번 재시도한다.
    for attempt in range(6):
        try:
            return get_client().responses.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            if getattr(e, "status_code", None) == 409 and attempt < 5:
                time.sleep(2 + attempt)
                continue
            raise _friendly_error(e, agent_id) from e


def _wait(agent_id: str, resp):
    deadline = time.monotonic() + config.JOB_TIMEOUT_SEC
    while getattr(resp, "status", None) in ("queued", "in_progress"):
        if time.monotonic() > deadline:
            raise AgentError(
                f"{config.JOB_TIMEOUT_SEC}초 안에 분석이 끝나지 않았습니다(job {resp.id})."
            )
        time.sleep(config.POLL_INTERVAL_SEC)
        try:
            resp = get_client().responses.retrieve(resp.id, include=["last"])
        except Exception as e:  # noqa: BLE001
            raise _friendly_error(e, agent_id) from e

    status = getattr(resp, "status", None)
    if status != "completed":
        err = getattr(resp, "error", None)
        msg = (
            getattr(err, "message", None)
            or (err.get("message") if isinstance(err, dict) else None)
            or getattr(resp, "failure_message", None)
            or "원인 미상"
        )
        raise AgentError(f"Studio Agent 실행 실패(status={status}): {msg}")
    return resp


def _output_text(resp) -> str:
    text = getattr(resp, "output_text", None)
    if text:
        return text
    # output_text가 비어 있으면 output 배열에서 직접 꺼낸다.
    parts = []
    for item in getattr(resp, "output", None) or []:
        for c in getattr(item, "content", None) or []:
            t = getattr(c, "text", None)
            if t:
                parts.append(t)
    if parts:
        return parts[-1]  # include=["last"] → 마지막 단계 결과
    raise AgentError("Agent 응답에 결과 텍스트가 없습니다.")


def parse_json_text(text: str):
    """output_text를 JSON으로 읽는다. ```json 코드블록이나 앞뒤 설명문도 허용."""
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise AgentError(f"Agent 결과가 JSON 형식이 아닙니다: {text[:200]}")


_CITATION = re.compile(r"【[^】]*】|\[\^?\d+\]|†\d*")


def parse_kv_text(text: str) -> dict:
    """
    "경비구분: 식비【†1】 | 검토여부: 검토 불필요 | 사유: ..." 같은
    '키: 값' 문장을 dict로 바꾼다. (Agent가 JSON 대신 문장으로 답할 때)
    """
    result = {}
    for part in re.split(r"\s*\|\s*|\n+", text):
        part = part.strip().strip("-•* ").strip()
        m = re.match(r"^\**([^:：]{1,30}?)\**\s*[:：]\s*(.*)$", part)
        if m:
            key = m.group(1).strip()
            value = _CITATION.sub("", m.group(2)).strip().strip('"').strip()
            if key and key not in result:
                result[key] = value
    return result


def to_dict(data, text: str) -> dict:
    """JSON 파싱 결과가 dict가 아니어도 최대한 dict로 바꾼다."""
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            return data[0]
        data = " | ".join(str(i) for i in data)
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:  # 문자열 안에 JSON이 또 들어 있는 경우
            inner = parse_json_text(data)
            if isinstance(inner, dict):
                return inner
        except AgentError:
            pass
        kv = parse_kv_text(data)
        if kv:
            return kv
    raise AgentError(f"예상하지 못한 결과 형식입니다: {text[:200]}")


def run_agent(agent_id: str, file_id: str, config_id: str = "") -> tuple[dict, str]:
    """
    업로드된 파일 하나로 Studio Agent를 실행한다.
    반환: (파싱된 dict, 원본 output_text)
    """
    resp = _create_job(agent_id, file_id, config_id)
    resp = _wait(agent_id, resp)
    text = _output_text(resp)
    try:
        data = parse_json_text(text)
    except AgentError:
        data = text  # JSON이 아니면 '키: 값' 문장으로 읽어 본다
    return to_dict(data, text), text

##################################################
# Mock (USE_MOCK=1 일 때 화면 테스트용)
##################################################

def run_agent_mock(agent_id: str, file_name: str) -> tuple[dict, str]:
    if agent_id == config.EXPENSE_REVIEW_AGENT_ID:
        data = {"경비구분": "식비", "검토여부": "검토 불필요", "사유": "[MOCK] 식음료 영수증"}
    else:
        data = {
            "사용일자": "2026-10-30",
            "상호명": f"[MOCK] {file_name}",
            "결제금액": "10,300원",
            "통화": "KRW",
        }
    return data, json.dumps(data, ensure_ascii=False)