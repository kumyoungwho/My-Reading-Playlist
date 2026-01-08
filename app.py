import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =============================
# 기본 설정
# =============================
st.set_page_config(
    page_title="My Reading Playlist",
    layout="centered"
)

# =============================
# CSS
# =============================
st.markdown("""
<style>
.slider-wrapper {
    position: relative;
    width: 100%;
    margin-top: 24px;
}

.percent-overlay {
    position: absolute;
    top: -32px;
    left: 50%;
    transform: translateX(-50%);
    font-weight: 700;
    font-size: 18px;
}

@media (min-width: 768px) {
    .percent-overlay {
        position: static;
        transform: none;
        text-align: center;
        margin-bottom: 12px;
    }
}

.control-buttons {
    display: flex;
    justify-content: center;
    gap: 28px;
    margin-top: 28px;
}
</style>
""", unsafe_allow_html=True)

# =============================
# Google Sheets 연결
# =============================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "service_account.json",
    scopes=SCOPE
)

client = gspread.authorize(creds)
sheet = client.open_by_key("1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8")
worksheet = sheet.sheet1

df = pd.DataFrame(worksheet.get_all_records())

# =============================
# 🔒 컬럼 타입 강제
# =============================
def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default

df["total"] = df["total"].apply(safe_int)
df["progress"] = df["progress"].apply(safe_int)

# =============================
# 첫 번째 책 (임시)
# =============================
ROW_INDEX = 2  # 실제 시트 기준 (헤더 다음 줄)

book = df.iloc[0]
total_pages = book["total"]

# =============================
# session_state 초기화
# =============================
if "progress_slider" not in st.session_state:
    st.session_state["progress_slider"] = book["progress"]

# =============================
# 🔄 실시간 저장 함수
# =============================
def save_progress():
    new_val = int(st.session_state["progress_slider"])
    col = worksheet.find("progress").col
    worksheet.update_cell(ROW_INDEX, col, new_val)

# =============================
# 헤더
# =============================
st.markdown("## 🎧 My Reading Playlist")

# =============================
# 카드
# =============================
st.markdown(
    """
    <div style="background:white; padding:24px; border-radius:16px; text-align:center;">
        <div style="font-size:22px; font-weight:700;">🎵 프로젝트 헤일메리</div>
        <div style="margin-top:4px; color:#666;">앤디 위어</div>
    </div>
    """,
    unsafe_allow_html=True
)

# =============================
# 슬라이더 (on_change 자동 저장)
# =============================
st.slider(
    "",
    min_value=0,
    max_value=100,
    key="progress_slider",
    on_change=save_progress
)

new_val = st.session_state["progress_slider"]
read_pages = int(total_pages * new_val / 100)

st.markdown(
    f"""
    <div class="slider-wrapper">
        <div class="percent-overlay">{new_val}%</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(f"📄 {read_pages} / {total_pages}p")

# =============================
# 하단 버튼
# =============================
st.markdown("""
<div class="control-buttons">
    <button>⏮</button>
    <button>⏸</button>
    <button>⏭</button>
    <button>📘</button>
</div>
""", unsafe_allow_html=True)
