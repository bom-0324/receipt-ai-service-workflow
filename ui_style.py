"""화면 스타일만 담당하는 모듈.

비즈니스 로직과 완전히 분리되어 있어서, 이 파일을 지우거나
apply_style() 호출 한 줄만 빼면 원래 화면으로 돌아갑니다.
"""

import streamlit as st

_CSS = """
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');

:root {
  --accent: #2F6FED;
  --accent-hover: #1F57C7;
  --accent-soft: #EEF4FF;
  --bg: #F6F7F9;
  --surface: #FFFFFF;
  --line: #E3E7EC;
  --text: #17202B;
  --muted: #667085;
  --radius: 12px;
}

/* ---------- 기본 폰트 / 여백 ---------- */
.stApp,
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp p, .stApp label, .stApp li, .stApp input,
.stApp textarea, .stApp button {
  font-family: 'Pretendard Variable', Pretendard, -apple-system, 'Noto Sans KR',
               'Malgun Gothic', sans-serif !important;
}
.stApp { background: var(--bg); color: var(--text); }

.block-container {
  max-width: 1160px;
  padding-top: 2.4rem;
  padding-bottom: 5rem;
}

/* 불필요한 기본 크롬 정리 */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* ---------- 제목 계층 ---------- */
.stApp h1 {
  font-size: 1.85rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  padding-bottom: 0.2rem;
}
.stApp h2, .stApp h3 {
  font-weight: 700;
  letter-spacing: -0.015em;
  margin-top: 2.2rem;
}
.stApp [data-testid="stCaptionContainer"] { color: var(--muted); line-height: 1.55; }

/* ---------- 파일 업로드 ---------- */
[data-testid="stFileUploader"] > label p { font-weight: 600; font-size: 0.95rem; }
[data-testid="stFileUploaderDropzone"] {
  background: var(--surface);
  border: 1.5px dashed #C4CCD6;
  border-radius: var(--radius);
  padding: 1.4rem 1.2rem;
  transition: border-color .15s ease, background .15s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}
[data-testid="stFileUploaderFile"] { border-radius: 8px; }

/* ---------- 버튼 ---------- */
.stButton > button,
.stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button {
  border-radius: 10px;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--text);
  font-weight: 600;
  padding: 0.55rem 1.2rem;
  min-height: 2.7rem;
  transition: background .15s ease, border-color .15s ease, box-shadow .15s ease;
}
.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"],
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  color: #fff;
}
.stButton > button:disabled { opacity: .45; cursor: not-allowed; }
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible {
  outline: 3px solid rgba(47, 111, 237, .3);
  outline-offset: 2px;
}

/* ---------- 요약 지표 (metric) ---------- */
[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
}
[data-testid="stMetricLabel"] p {
  color: var(--muted);
  font-size: 0.85rem;
  font-weight: 600;
}
[data-testid="stMetricValue"] {
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

/* ---------- 탭 ---------- */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.25rem;
  border-bottom: 1px solid var(--line);
}
.stTabs [data-baseweb="tab"] {
  height: 2.8rem;
  padding: 0 1.1rem;
  color: var(--muted);
}
.stTabs [data-baseweb="tab"] p { font-weight: 600; font-size: 0.98rem; }
.stTabs [aria-selected="true"] { color: var(--accent); }
.stTabs [aria-selected="true"] p { color: var(--accent); }
.stTabs [data-baseweb="tab-highlight"] {
  background: var(--accent);
  height: 3px;
  border-radius: 3px 3px 0 0;
}
.stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

/* ---------- 입력 요소 ---------- */
[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div {
  border-radius: 10px;
  border-color: var(--line);
  background: var(--surface);
}
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(47, 111, 237, .15);
}
.stApp label p { font-weight: 600; font-size: 0.9rem; }

/* ---------- 검토 폼 ---------- */
[data-testid="stForm"] {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 1.3rem 1.3rem 1rem;
}

/* ---------- 알림 ---------- */
[data-testid="stAlert"] {
  border-radius: var(--radius);
  border: 1px solid transparent;
}

/* ---------- 표 / 이미지 ---------- */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
}
[data-testid="stImage"] img {
  border: 1px solid var(--line);
  border-radius: var(--radius);
}

/* ---------- 확장 영역 ---------- */
[data-testid="stExpander"] details {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}
[data-testid="stExpander"] summary { font-weight: 600; }

/* ---------- 본문 가독성 ---------- */
.stApp p, .stApp li { line-height: 1.65; }

/* ---------- 요약 지표: 검토 필요(주황) / 검토 완료(초록) 색 구분 ---------- */
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div:nth-child(2) [data-testid="stMetricValue"] {
  color: #C2410C;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div:nth-child(3) [data-testid="stMetricValue"] {
  color: #15803D;
}

/* ---------- 다운로드 버튼은 칸 너비에 맞춰 크게 ---------- */
.stDownloadButton > button { width: 100%; min-height: 3rem; }

/* ---------- 상단 단계 안내 ---------- */
.steps {
  display: flex;
  gap: 0.75rem;
  margin: 0.4rem 0 1.6rem;
  flex-wrap: wrap;
}
.steps .step {
  flex: 1 1 200px;
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 0.85rem 1rem;
}
.steps .num {
  flex: none;
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 800;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.steps .ttl { font-weight: 700; font-size: 0.95rem; color: var(--text); }
.steps .dsc { font-size: 0.82rem; color: var(--muted); margin-top: 0.1rem; line-height: 1.45; }

/* ---------- 태블릿 ---------- */
@media (max-width: 900px) {
  .block-container { padding-left: 1.5rem; padding-right: 1.5rem; }
}

/* ---------- 모바일 ---------- */
@media (max-width: 640px) {
  .stApp { font-size: 15px; }
  .block-container {
    padding: 1.2rem 0.9rem calc(3rem + env(safe-area-inset-bottom, 0px));
  }
  .stApp h1 { font-size: 1.45rem; line-height: 1.3; }
  .stApp h2, .stApp h3 { margin-top: 1.6rem; font-size: 1.2rem; }

  /* 단계 안내: 3칸을 한 줄로, 설명은 숨김 */
  .steps { gap: 0.4rem; margin: 0.2rem 0 1.1rem; flex-wrap: nowrap; }
  .steps .step {
    flex: 1 1 0;
    min-width: 0;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 0.35rem;
    padding: 0.65rem 0.4rem;
  }
  .steps .dsc { display: none; }
  .steps .ttl { font-size: 0.8rem; line-height: 1.3; }

  /* 요약 카드: 세로 4줄 대신 2 x 2 */
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
    flex-wrap: wrap !important;
    gap: 0.6rem !important;
  }
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div {
    flex: 1 1 calc(50% - 0.3rem) !important;
    min-width: calc(50% - 0.3rem) !important;
    width: calc(50% - 0.3rem) !important;
  }
  [data-testid="stMetric"] { padding: 0.75rem 0.9rem; }
  [data-testid="stMetricValue"] { font-size: 1.25rem; }
  [data-testid="stMetricLabel"] p { font-size: 0.78rem; }

  /* 버튼: 손가락으로 누르기 쉬운 크기, 가로 꽉 차게 */
  .stButton > button,
  .stDownloadButton > button,
  [data-testid="stFormSubmitButton"] > button {
    width: 100%;
    min-height: 3rem;
    font-size: 1rem;
  }

  /* 입력창: 16px 미만이면 iOS가 포커스 시 화면을 확대함 */
  input, textarea { font-size: 16px !important; }

  /* 탭: 좁으면 옆으로 스크롤 */
  .stTabs [data-baseweb="tab-list"] { overflow-x: auto; scrollbar-width: none; }
  .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
  .stTabs [data-baseweb="tab"] { height: 3rem; padding: 0 0.85rem; white-space: nowrap; }
  .stTabs [data-baseweb="tab"] p { font-size: 0.92rem; }

  /* 업로드 영역 */
  [data-testid="stFileUploaderDropzone"] {
    padding: 1rem 0.8rem;
    flex-wrap: wrap;
    gap: 0.6rem;
  }
  [data-testid="stFileUploaderDropzone"] button { width: 100%; }

  /* 폼, 알림, 이미지, 표 */
  [data-testid="stForm"] { padding: 1rem 0.9rem 0.8rem; }
  [data-testid="stAlert"] { font-size: 0.92rem; }
  [data-testid="stImage"] img { max-width: 100%; height: auto; }
  [data-testid="stDataFrame"],
  [data-testid="stDataEditor"] { max-width: 100%; }
}
"""


def apply_style() -> None:
    """st.set_page_config() 바로 다음에 한 번 호출하세요."""
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


def render_steps() -> None:
    """제목 아래에 진행 순서(업로드 → 분석·검토 → 내보내기)를 보여줍니다."""
    st.markdown(
        """
        <div class="steps">
          <div class="step"><div class="num">1</div><div>
            <div class="ttl">영수증 업로드</div>
            <div class="dsc">이미지·PDF·HEIC를 여러 장 올려요</div></div></div>
          <div class="step"><div class="num">2</div><div>
            <div class="ttl">분석 · 검토</div>
            <div class="dsc">검토 필요 건을 사진과 비교하며 고쳐요</div></div></div>
          <div class="step"><div class="num">3</div><div>
            <div class="ttl">엑셀 내보내기</div>
            <div class="dsc">분기·컬럼을 골라 파일로 받아요</div></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
