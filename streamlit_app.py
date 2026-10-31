import re

import pandas as pd
import streamlit as st

import config
from excel_builder import build_summary_df, dataframe_to_excel_bytes, resolve_headers
from normalize import CATEGORIES, COLUMNS
from service import process_receipts

try:  # 드래그로 컬럼 순서를 바꾸는 컴포넌트 (pip install streamlit-sortables)
    from streamlit_sortables import sort_items
except ImportError:
    sort_items = None

st.set_page_config(page_title="영수증 경비 정리 서비스", layout="wide")

st.title("영수증 경비 정리 서비스")
st.write("영수증을 여러 장 올리면 1장당 1행으로 정리하고 엑셀로 내려받을 수 있습니다.")

##################################################
# 설정 확인
##################################################

missing = config.missing_settings()
if missing:
    st.error(
        "다음 환경변수가 비어 있어 분석을 실행할 수 없습니다: "
        + ", ".join(missing)
        + "\n\n로컬은 .env 파일, Railway는 Variables 탭에 넣은 뒤 다시 실행하세요."
    )
if config.USE_MOCK:
    st.info("USE_MOCK=1 상태입니다. Upstage API를 호출하지 않고 가짜 결과를 보여줍니다.")

##################################################
# 업로드
##################################################

uploaded_files = st.file_uploader(
    "영수증 이미지 또는 PDF를 업로드하세요.",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True,
)

# 업로드 목록이 바뀌면 이전 결과를 지운다.
upload_key = tuple((f.name, f.size) for f in uploaded_files or [])
if st.session_state.get("upload_key") != upload_key:
    st.session_state.upload_key = upload_key
    st.session_state.pop("result", None)

if st.button("분석 시작", type="primary", disabled=bool(missing)):
    if not uploaded_files:
        st.warning("먼저 영수증 파일을 업로드해주세요.")
    else:
        progress = st.progress(0.0, text="분석 준비 중...")

        def on_progress(done, total, name):
            progress.progress(done / total, text=f"{done}/{total} 완료 · {name}")

        with st.spinner("Upstage Studio에서 영수증을 분석하고 있습니다..."):
            st.session_state.result = process_receipts(uploaded_files, on_progress)
        # 새 분석이면 표 편집 상태도 새로 시작한다.
        st.session_state.run_id = st.session_state.get("run_id", 0) + 1
        progress.empty()

##################################################
# 결과
##################################################

result = st.session_state.get("result")
if result:
    df, details = result
    failed = [d for d in details if d["errors"]]
    if failed:
        st.warning(f"{len(failed)}개 파일에서 오류가 있었습니다. 아래 '분석 상세'를 확인하세요.")

    # ---------- 1. 결과 표 (직접 수정) ----------
    st.subheader("분석 결과")
    st.caption(
        "셀을 더블클릭해 값을 고칠 수 있습니다. 고친 내용은 집계와 엑셀에 바로 반영됩니다. "
        "맨 아래 빈 줄에서 행을 추가하고, 왼쪽 체크박스로 행을 골라 삭제할 수 있습니다."
    )

    currency_options = sorted({"KRW", "USD", "JPY", "EUR", "CNY", "GBP"}
                              | {c for c in df["통화"].dropna() if c})

    edited = st.data_editor(
        df,
        key=f"editor_{st.session_state.get('run_id', 0)}",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "사용일자": st.column_config.TextColumn(
                "사용일자", help="YYYY-MM-DD 형식", validate=r"^(\d{4}-\d{2}-\d{2})?$"
            ),
            "상호명": st.column_config.TextColumn("상호명"),
            "결제금액": st.column_config.NumberColumn(
                "결제금액", format="localized", min_value=0, step=1
            ),
            "경비구분": st.column_config.SelectboxColumn("경비구분", options=list(CATEGORIES)),
            "통화": st.column_config.SelectboxColumn("통화", options=currency_options),
            "검토여부": st.column_config.SelectboxColumn(
                "검토여부", options=["검토 필요", "검토 불필요"]
            ),
            "사유": st.column_config.TextColumn("사유", width="large"),
            "파일명": st.column_config.TextColumn("파일명", disabled=True),
        },
    )
    edited = edited.reset_index(drop=True)
    edited["결제금액"] = pd.to_numeric(edited["결제금액"], errors="coerce")

    # ---------- 2. 요약 (수정한 값 기준) ----------
    need_review = int((edited["검토여부"] == "검토 필요").sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("영수증", f"{len(edited)}장")
    c2.metric("검토 필요", f"{need_review}건")
    krw = edited.loc[edited["통화"] == "KRW", "결제금액"].sum()
    c3.metric("KRW 합계", f"{krw:,.0f}원")

    st.subheader("집계")
    summary_df = build_summary_df(edited)
    st.dataframe(summary_df[summary_df["건수"] > 0], hide_index=True)

    # ---------- 3. 엑셀 내보내기 ----------
    st.subheader("엑셀 내보내기")

    # (1) 컬럼 고르기·순서 바꾸기: 드래그
    if sort_items is not None:
        st.caption("컬럼을 끌어서 순서를 바꾸고, 엑셀에서 뺄 컬럼은 아래 '제외' 칸으로 옮기세요.")
        boxes = sort_items(
            [
                {"header": "엑셀에 넣을 컬럼 (왼쪽부터 순서대로)", "items": list(COLUMNS)},
                {"header": "제외", "items": []},
            ],
            multi_containers=True,
            key="column_sorter",
        )
        selected_cols = [c for c in boxes[0]["items"] if c in COLUMNS]
    else:  # 패키지가 없을 때 대체 화면
        selected_cols = st.multiselect(
            "엑셀에 넣을 컬럼 (고른 순서대로 들어갑니다)", options=COLUMNS, default=COLUMNS
        )

    # (2) 컬럼 이름 바꾸기
    with st.expander("엑셀 컬럼 이름 바꾸기"):
        st.caption("오른쪽 칸을 더블클릭해 고치세요. 비워두면 원래 이름을 씁니다.")
        rename_df = st.data_editor(
            pd.DataFrame({"원래 이름": COLUMNS, "엑셀에 표시할 이름": COLUMNS}),
            key="rename_editor",
            hide_index=True,
            width="stretch",
            column_config={"원래 이름": st.column_config.TextColumn(disabled=True)},
        )
    rename_map = dict(zip(rename_df["원래 이름"], rename_df["엑셀에 표시할 이름"]))
    headers, duplicated = resolve_headers(selected_cols, rename_map)

    if selected_cols:
        st.caption("엑셀 순서: " + "  →  ".join(headers[c] for c in selected_cols))

    # (3) 파일 이름·다운로드
    col_a, col_b = st.columns([2, 1])
    file_stem = col_a.text_input("파일 이름", value="expense_result")
    include_summary = col_b.checkbox("집계 시트 포함", value=True)

    if not selected_cols:
        st.info("엑셀에 넣을 컬럼을 하나 이상 남겨주세요.")
    elif duplicated:
        st.error("엑셀 컬럼 이름이 겹칩니다: " + ", ".join(duplicated))
    else:
        safe_stem = re.sub(r'[\\/:*?"<>|]', "_", file_stem.strip()) or "expense_result"
        excel_bytes = dataframe_to_excel_bytes(
            edited, columns=selected_cols, include_summary=include_summary, headers=headers
        )
        st.download_button(
            label=f"엑셀 다운로드 ({len(selected_cols)}개 컬럼)",
            data=excel_bytes,
            file_name=f"{safe_stem}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

    # ---------- 4. 분석 상세 ----------
    with st.expander("분석 상세 (Agent 원본 응답·오류)"):
        for d in details:
            st.markdown(f"**{d['파일명']}**")
            for err in d["errors"]:
                st.error(err)
            col_x, col_y = st.columns(2)
            col_x.caption("1번 추출 Agent 응답")
            col_x.code(d["extract_raw"] or "(없음)", language="json")
            col_y.caption("2번 검토 Agent 응답")
            col_y.code(d["review_raw"] or "(없음)", language="json")