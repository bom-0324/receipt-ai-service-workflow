"""2번 워크플로우: 경비 분류·검토 (경비구분/검토여부/사유)."""

import config
from agent_client import run_agent, run_agent_mock
from normalize import normalize_review_result


def run_expense_review_agent(file_id: str, file_name: str) -> tuple[dict, str]:
    """반환: (정규화된 검토 결과, 원본 output_text)"""
    if config.USE_MOCK:
        data, raw = run_agent_mock(config.EXPENSE_REVIEW_AGENT_ID, file_name)
    else:
        data, raw = run_agent(
            config.EXPENSE_REVIEW_AGENT_ID, file_id, config.EXPENSE_REVIEW_CONFIG_ID
        )
    return normalize_review_result(data), raw