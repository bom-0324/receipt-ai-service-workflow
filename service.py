import pandas as pd

from app import run_receipt_workflow
from normalize import COLUMNS


def process_receipts(uploaded_files, on_progress=None):
    """
    Streamlit 업로드 파일 목록을 처리한다.
    반환: (결과 DataFrame, 파일별 상세)
    집계와 엑셀은 화면에서 사용자가 수정한 표로 만든다.
    """
    files = [(f.name, f.getvalue()) for f in uploaded_files]
    rows, details = run_receipt_workflow(files, on_progress=on_progress)

    df = pd.DataFrame(rows, columns=COLUMNS)
    df["결제금액"] = pd.to_numeric(df["결제금액"], errors="coerce")
    return df, details