"""2번 워크플로우: 경비 분류·검토 (경비구분/검토여부/사유)."""

import config
from agent_client import run_agent, run_agent_mock
from normalize import normalize_review_result


def run_expense_review_agent(file_id: str, file_name: str) -> tuple[dict, str]:
    """(예전 방식) 사진을 직접 읽고 분류한다. 반환: (정규화된 검토 결과, 원본 output_text)"""
    if config.USE_MOCK:
        data, raw = run_agent_mock(config.EXPENSE_REVIEW_AGENT_ID, file_name)
    else:
        data, raw = run_agent(
            config.EXPENSE_REVIEW_AGENT_ID, file_id, config.EXPENSE_REVIEW_CONFIG_ID
        )
    return normalize_review_result(data), raw


def run_expense_review_agent_text(extract_text: str, file_name: str) -> tuple[dict, str]:
    """1번이 읽어낸 결과(글)만 보고 분류한다. 사진을 다시 읽지 않아서 빠르다."""
    if config.USE_MOCK:
        data, raw = run_agent_mock(config.EXPENSE_REVIEW_AGENT_ID, file_name)
    else:
        text = "다음은 영수증 한 장에서 읽어낸 정보입니다.\n" + extract_text
        data, raw = run_agent(
            config.EXPENSE_REVIEW_AGENT_ID, "", config.EXPENSE_REVIEW_CONFIG_ID, text=text
        )
    return normalize_review_result(data), raw