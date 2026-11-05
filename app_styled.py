"""스타일이 적용된 실행 진입점.

기존 streamlit_app.py를 한 줄도 수정하지 않고 그대로 실행하면서,
화면 스타일(ui_style.py)만 위에 덧씌웁니다.

실행:  streamlit run app_styled.py
"""

from pathlib import Path
import runpy

import streamlit as st

from ui_style import apply_style, render_steps

# Streamlit은 스크립트를 매 상호작용마다 다시 실행하므로, 원본 함수를 한 번만 저장해 둔다.
if not hasattr(st, "_orig_set_page_config"):
    st._orig_set_page_config = st.set_page_config
    st._orig_title = st.title


def _set_page_config(*args, **kwargs):
    st._orig_set_page_config(*args, **kwargs)
    apply_style()  # set_page_config 직후에 CSS 주입


def _title(*args, **kwargs):
    st._orig_title(*args, **kwargs)
    render_steps()  # 제목 바로 아래에 단계 안내 표시


st.set_page_config = _set_page_config
st.title = _title

try:
    runpy.run_path(str(Path(__file__).parent / "streamlit_app.py"), run_name="__main__")
finally:
    # 원본 복구 (다른 코드에 영향이 남지 않도록)
    st.set_page_config = st._orig_set_page_config
    st.title = st._orig_title
