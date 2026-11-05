"""3번 워크플로우: 교차 검증 (사진을 한 번 더 읽어 사용일자/결제금액을 독립적으로 확인)."""

import config
from agent_client import run_agent, run_agent_mock
from normalize import normalize_extract


def verify_enabled() -> bool:
    return bool(config.VERIFY_AGENT_ID)


def run_verify_agent(file_id: str, file_name: str) -> tuple[dict, str]:
    """반환: (정규화된 재추출 결과, 원본 output_text)"""
    if config.USE_MOCK:
        data, raw = run_agent_mock(config.VERIFY_AGENT_ID, file_name)
    else:
        data, raw = run_agent(config.VERIFY_AGENT_ID, file_id, config.VERIFY_CONFIG_ID)
    return normalize_extract(data), raw