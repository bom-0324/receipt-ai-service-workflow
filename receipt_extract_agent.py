"""1번 워크플로우: 영수증 파싱·추출 (사용일자/상호명/결제금액/통화)."""

import config
from agent_client import run_agent, run_agent_mock
from normalize import normalize_extract


def run_receipt_extract_agent(file_id: str, file_name: str) -> tuple[dict, str]:
    """반환: (정규화된 추출 결과, 원본 output_text)"""
    if config.USE_MOCK:
        data, raw = run_agent_mock(config.RECEIPT_EXTRACT_AGENT_ID, file_name)
    else:
        data, raw = run_agent(
            config.RECEIPT_EXTRACT_AGENT_ID, file_id, config.RECEIPT_EXTRACT_CONFIG_ID
        )
    return normalize_extract(data), raw