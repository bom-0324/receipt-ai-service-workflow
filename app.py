"""
app.py

처리 순서 제어 및 결과 병합.

영수증 1장마다:
  1) 파일 업로드 (1번 업로드한 file_id를 두 Agent가 같이 쓴다)
  2) 1번 Agent: 파싱·추출
  3) 2번 Agent: 분류·검토
  4) 3번 Agent: 교차 검증 (사진을 다시 읽어 금액·날짜 비교)
  5) 업로드 파일 정리 (삭제 확인)
  6) 결과를 1행으로 병합 + 검산
여러 장은 MAX_WORKERS 만큼 동시에 처리하고, 업로드 순서대로 돌려준다.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from agent_client import AgentError, delete_file, upload_file
from expense_review_agent import run_expense_review_agent
from normalize import merge_row
from receipt_extract_agent import run_receipt_extract_agent
from verify_agent import run_verify_agent, verify_enabled


def _process_one(file_name: str, data: bytes) -> tuple[dict, dict]:
    detail = {"파일명": file_name, "extract_raw": "", "review_raw": "", "verify_raw": "",
              "errors": [], "notes": []}
    extract = review = verify = None
    file_id = ""

    try:
        if not config.USE_MOCK:
            file_id = upload_file(file_name, data)

        try:
            extract, detail["extract_raw"] = run_receipt_extract_agent(file_id, file_name)
        except AgentError as e:
            detail["errors"].append(f"추출 실패: {e}")

        try:
            review, detail["review_raw"] = run_expense_review_agent(file_id, file_name)
        except AgentError as e:
            detail["errors"].append(f"검토 실패: {e}")

        # 3번 검증은 보조 장치라서, 실패해도 행 전체를 '검토 필요'로 만들지 않고 메모만 남긴다.
        if verify_enabled():
            try:
                verify, detail["verify_raw"] = run_verify_agent(file_id, file_name)
            except AgentError as e:
                detail["notes"].append(f"교차검증 건너뜀: {e}")

    except AgentError as e:
        detail["errors"].append(f"업로드 실패: {e}")
    except Exception as e:  # noqa: BLE001  예상 못한 오류도 행 단위로 기록
        detail["errors"].append(f"처리 오류: {type(e).__name__}: {e}")
    finally:
        if file_id and not delete_file(file_id):
            detail["notes"].append(f"Upstage 파일 삭제를 확인하지 못함 (file_id={file_id})")

    row = merge_row(file_name, extract, review, detail["errors"], verify)
    return row, detail


def run_receipt_workflow(files: list[tuple[str, bytes]], on_progress=None):
    """
    files: [(파일명, 바이트), ...]
    on_progress: 완료될 때마다 호출되는 콜백 (완료 수, 전체 수, 파일명)
    반환: (행 목록, 파일별 상세)
    """
    total = len(files)
    results = [None] * total
    done = 0

    with ThreadPoolExecutor(max_workers=max(1, config.MAX_WORKERS)) as pool:
        futures = {
            pool.submit(_process_one, name, data): i for i, (name, data) in enumerate(files)
        }
        for future in as_completed(futures):
            i = futures[future]
            results[i] = future.result()
            done += 1
            if on_progress:
                on_progress(done, total, files[i][0])

    rows = [r for r, _ in results]
    details = [d for _, d in results]
    return rows, details