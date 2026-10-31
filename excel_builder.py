"""
excel_builder.py

결과 표를 .xlsx로 만든다. (3번 '엑셀 정리·집계' 역할을 Python이 담당)

시트 구성
  - 경비내역: 영수증 1장당 1행, 검토 필요 행은 노란색 표시
  - 집계: 통화·경비구분별 건수와 금액 합계 (SUMIFS 수식이라
          경비내역 시트에서 값을 고치면 집계도 같이 바뀐다)
"""

import io

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from normalize import CATEGORIES

DETAIL_SHEET = "경비내역"
SUMMARY_SHEET = "집계"

_HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_REVIEW_FILL = PatternFill("solid", fgColor="FFF2CC")
_TOTAL_FILL = PatternFill("solid", fgColor="DDEBF7")
_THIN = Side(style="thin", color="BFBFBF")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)

_WIDTHS = {"사용일자": 12, "상호명": 28, "결제금액": 14, "경비구분": 10,
           "통화": 8, "검토여부": 12, "사유": 50, "파일명": 28}


def build_summary_df(df: pd.DataFrame) -> pd.DataFrame:
    """화면에 보여줄 집계표 (엑셀 집계 시트와 같은 내용)."""
    if df.empty:
        return pd.DataFrame(columns=["통화", "경비구분", "건수", "금액합계"])
    amounts = pd.to_numeric(df["결제금액"], errors="coerce").fillna(0)
    rows = []
    for cur in sorted(c for c in df["통화"].fillna("").unique() if c):
        mask = df["통화"] == cur
        for cat in CATEGORIES:
            m = mask & (df["경비구분"] == cat)
            rows.append({"통화": cur, "경비구분": cat, "건수": int(m.sum()),
                         "금액합계": amounts[m].sum()})
        rows.append({"통화": cur, "경비구분": "합계", "건수": int(mask.sum()),
                     "금액합계": amounts[mask].sum()})
    return pd.DataFrame(rows)


def _style_header(ws, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _BORDER
    ws.freeze_panes = "A2"


def _write_detail(ws, df: pd.DataFrame):
    cols = list(df.columns)
    _style_header(ws, len(cols))
    review_col = cols.index("검토여부") + 1 if "검토여부" in cols else None
    amount_col = cols.index("결제금액") + 1 if "결제금액" in cols else None

    for r in range(2, len(df) + 2):
        needs_review = review_col and ws.cell(row=r, column=review_col).value == "검토 필요"
        for c in range(1, len(cols) + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = _BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=(cols[c - 1] == "사유"))
            if needs_review:
                cell.fill = _REVIEW_FILL
        if amount_col:
            ws.cell(row=r, column=amount_col).number_format = "#,##0.##"

    for i, name in enumerate(cols, start=1):
        ws.column_dimensions[get_column_letter(i)].width = _WIDTHS.get(name, 14)
    ws.auto_filter.ref = ws.dimensions


def _write_summary(ws, df: pd.DataFrame):
    cols = list(df.columns)
    n = len(df) + 1  # 마지막 데이터 행
    col = {name: get_column_letter(cols.index(name) + 1) for name in cols}
    rng = lambda name: f"'{DETAIL_SHEET}'!${col[name]}$2:${col[name]}${max(n, 2)}"  # noqa: E731

    headers = ["통화", "경비구분", "건수", "금액합계"]
    for c, h in enumerate(headers, start=1):
        ws.cell(row=1, column=c, value=h)
    _style_header(ws, len(headers))

    r = 2
    currencies = sorted(c for c in df["통화"].fillna("").unique() if c) or ["KRW"]
    for cur in currencies:
        first = r
        for cat in CATEGORIES:
            ws.cell(row=r, column=1, value=cur)
            ws.cell(row=r, column=2, value=cat)
            ws.cell(row=r, column=3,
                    value=f'=COUNTIFS({rng("통화")},A{r},{rng("경비구분")},B{r})')
            ws.cell(row=r, column=4,
                    value=f'=SUMIFS({rng("결제금액")},{rng("통화")},A{r},{rng("경비구분")},B{r})')
            r += 1
        ws.cell(row=r, column=1, value=cur)
        ws.cell(row=r, column=2, value="합계")
        ws.cell(row=r, column=3, value=f"=SUM(C{first}:C{r - 1})")
        ws.cell(row=r, column=4, value=f"=SUM(D{first}:D{r - 1})")
        for c in range(1, 5):
            ws.cell(row=r, column=c).fill = _TOTAL_FILL
            ws.cell(row=r, column=c).font = Font(bold=True)
        r += 1

    for row in ws.iter_rows(min_row=2, max_row=r - 1, max_col=4):
        for cell in row:
            cell.border = _BORDER
        row[3].number_format = "#,##0.##"

    r += 1
    ws.cell(row=r, column=1, value="검토 필요 건수").font = Font(bold=True)
    ws.cell(row=r, column=3, value=f'=COUNTIF({rng("검토여부")},"검토 필요")')
    ws.cell(row=r + 1, column=1, value="전체 영수증 수").font = Font(bold=True)
    ws.cell(row=r + 1, column=3, value=f"=COUNTA({rng('파일명')})")

    for letter, w in zip("ABCD", (10, 12, 10, 16)):
        ws.column_dimensions[letter].width = w


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=DETAIL_SHEET)
        _write_detail(writer.sheets[DETAIL_SHEET], df)
        if {"통화", "경비구분", "결제금액", "검토여부", "파일명"} <= set(df.columns):
            ws = writer.book.create_sheet(SUMMARY_SHEET)
            _write_summary(ws, df)
    output.seek(0)
    return output.getvalue()