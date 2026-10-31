import streamlit as st

import config
from service import process_receipts

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
        progress.empty()

##################################################
# 결과
##################################################

result = st.session_state.get("result")
if result:
    df, summary_df, excel_bytes, details = result

    need_review = int((df["검토여부"] == "검토 필요").sum())
    failed = [d for d in details if d["errors"]]

    c1, c2, c3 = st.columns(3)
    c1.metric("영수증", f"{len(df)}장")
    c2.metric("검토 필요", f"{need_review}건")
    krw = df.loc[df["통화"] == "KRW", "결제금액"].sum()
    c3.metric("KRW 합계", f"{krw:,.0f}원")

    if failed:
        st.warning(f"{len(failed)}개 파일에서 오류가 있었습니다. 아래 '분석 상세'를 확인하세요.")

    st.subheader("분석 결과")
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={"결제금액": st.column_config.NumberColumn(format="localized")},
    )

    st.subheader("집계")
    st.dataframe(summary_df[summary_df["건수"] > 0], hide_index=True)

    st.download_button(
        label="엑셀 다운로드",
        data=excel_bytes,
        file_name="expense_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

    with st.expander("분석 상세 (Agent 원본 응답·오류)"):
        for d in details:
            st.markdown(f"**{d['파일명']}**")
            for err in d["errors"]:
                st.error(err)
            col_a, col_b = st.columns(2)
            col_a.caption("1번 추출 Agent 응답")
            col_a.code(d["extract_raw"] or "(없음)", language="json")
            col_b.caption("2번 검토 Agent 응답")
            col_b.code(d["review_raw"] or "(없음)", language="json")