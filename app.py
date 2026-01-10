import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

# =================================================
# 기본 설정
# =================================================
st.set_page_config(
    page_title="My Reading Playlist",
    layout="centered"
)

# =================================================
# CSS (핑크 배경 + 모바일 오버레이 + 버튼 중앙)
# =================================================
st.markdown("""
<style>
/* 전체 배경색 (연한 핑크) */
.stApp {
    background-color: #FFC0CB !important;
}

/* 슬라이더 퍼센트 오버레이 */
.slider-wrapper {
    position: relative;
    width: 100%;
    margin-top: 12px;
}

.percent-overlay {
    position: absolute;
    top: -32px;
    left: 50%;
    transform: translateX(-50%);
    font-weight: 800;
    font-size: 18px;
}

/* 데스크톱에서는 일반 중앙 표시 */
@media (min-width: 768px) {
    .percent-overlay {
        position: static;
        transform: none;
        text-align: center;
        margin-bottom: 12px;
    }
}

/* 버튼 가로줄 전체 가운데 */
div[data-testid="stHorizontalBlock"] {
    justify-content: center !important;
}

/* 각 버튼 컬럼 중앙 */
div[data-testid="column"] {
    display: flex !important;
    justify-content: center !important;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# Google Sheets 인증 (Secrets ONLY)
# =================================================
@st.cache_resource
def get_worksheet():
    try:
        json_content = st.secrets["gcp_json"]
        if isinstance(json_content, str):
            json_content = json.loads(json_content)

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(json_content, scopes=scopes)
        client = gspread.authorize(creds)

        sheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8/edit"
        )
        return sheet.sheet1

    except Exception as e:
        st.error(f"🚨 Google Sheets 연결 실패: {e}")
        st.stop()

ws = get_worksheet()

# =================================================
# 데이터 로드 & 타입 강제
# =================================================
df = pd.DataFrame(ws.get_all_records())

def safe_int(x):
    try:
        return int(x)
    except:
        return 0

df["progress"] = df["progress"].apply(safe_int)
df["total"] = df["total"].apply(safe_int)

reading_df = df[df["status"] == "reading"].reset_index(drop=True)

# =================================================
# Session State
# =================================================
if "slider_val" not in st.session_state:
    st.session_state.slider_val = int(reading_df.iloc[0]["progress"])

# =================================================
# 실시간 저장 함수 (on_change)
# =================================================
def save_progress(row_index):
    val = int(st.session_state.slider_val)
    ws.update_cell(row_index, 3, val)

    if val >= 100:
        ws.update_cell(row_index, 5, "done")
        ws.update_cell(row_index, 6, datetime.now().strftime("%Y-%m-%d"))

# =================================================
# UI
# =================================================
st.title("🎧 My Reading Playlist")

if reading_df.empty:
    st.info("읽고 있는 책이 없습니다.")
    st.stop()

book = reading_df.iloc[0]
row_index = reading_df.index[0] + 2

# 카드
st.markdown(f"""
<div style="background:white; padding:24px; border-radius:16px; text-align:center;">
    <div style="font-size:22px; font-weight:700;">🎵 {book['title']}</div>
    <div style="margin-top:4px; color:#666;">{book['author']}</div>
</div>
""", unsafe_allow_html=True)

# 퍼센트 오버레이
st.markdown(f"""
<div class="slider-wrapper">
    <div class="percent-overlay">{st.session_state.slider_val}%</div>
</div>
""", unsafe_allow_html=True)

# 슬라이더 (실시간 저장)
st.slider(
    "",
    0,
    100,
    key="slider_val",
    on_change=save_progress,
    args=(row_index,),
    label_visibility="collapsed"
)

read_pages = int(book["total"] * st.session_state.slider_val / 100)
st.caption(f"📄 {read_pages} / {book['total']}p")

# 하단 버튼
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("⏮"):
        st.session_state.slider_val = max(0, st.session_state.slider_val - 5)
        save_progress(row_index)
        st.rerun()

with c2:
    if st.button("■"):
        st.session_state.slider_val = 100
        save_progress(row_index)
        st.balloons()
        st.rerun()

with c3:
    if st.button("⏭"):
        st.session_state.slider_val = min(100, st.session_state.slider_val + 5)
        save_progress(row_index)
        st.rerun()

with c4:
    if st.button("💾"):
        save_progress(row_index)
        st.success("저장 완료")
