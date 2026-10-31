import pandas as pd

from app import run_receipt_workflow
from excel_builder import build_summary_df, dataframe_to_excel_bytes
from normalize import COLUMNS


def process_receipts(uploaded_files, on_progress=None):
    """
    Streamlit 업로드 파일 목록을 처리한다.
    반환: (결과 DataFrame, 집계 DataFrame, 엑셀 바이트, 파일별 상세)
    """
    files = [(f.name, f.getvalue()) for f in uploaded_files]
    rows, details = run_receipt_workflow(files, on_progress=on_progress)

    df = pd.DataFrame(rows, columns=COLUMNS)
    df["결제금액"] = pd.to_numeric(df["결제금액"], errors="coerce")
    summary_df = build_summary_df(df)
    excel_bytes = dataframe_to_excel_bytes(df)

    return df, summary_df, excel_bytes, details