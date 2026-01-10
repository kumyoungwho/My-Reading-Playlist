import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

# =================================================
# 페이지 설정
# =================================================
st.set_page_config(
    page_title="My Reading Playlist",
    layout="centered"
)

# =================================================
# 🎨 CSS — 초기 디자인 100% 유지
# =================================================
css_code = '''
<style>
/* 1. 전체 핑크색 배경 */
.stApp {
    background-color: #FFC0CB !important;
    background-image: none;
}

/* 2. 제목 스타일 */
h1 {
    color: #C2185B;
    text-align: center;
    font-family: sans-serif;
    font-weight: 800;
    margin-bottom: 20px;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
}

/* 3. 카드 디자인 */
.book-card {
    background: #FFFFFF;
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    text-align: center;
    border: 2px solid #F8BBD0;
    margin-bottom: 40px !important;
}

/* 4. 슬라이더 스타일 */
div[data-baseweb="slider"] {
    padding-top: 10px !important;
    padding-bottom: 0px !important;
}

div[data-baseweb="slider"] > div > div:first-child {
    background-color: #9E9E9E !important;
    height: 4px !important;
}

div[data-baseweb="slider"] > div > div:nth-child(2) {
    background-color: #212121 !important;
    height: 4px !important;
}

div[data-baseweb="slider"] div[role="slider"] {
    background-color: #212121 !important;
    box-shadow: none !important;
    width: 18px !important;
    height: 18px !important;
    top: -3px !important;
}

/* 숫자 팝업 숨김 */
div[data-testid="stSliderTickBarMin"],
div[data-testid="stSliderTickBarMax"],
div[data-baseweb="tooltip"] {
    display: none !important;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.6);
    border-radius: 12px;
    border: none;
    margin-right: 10px;
    padding: 10px 20px !important;
    font-size: 1.1rem;
}

.stTabs [aria-selected="true"] {
    background: #EC407A !important;
    color: white !important;
    font-weight: bold;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* 버튼 스타일 */
.stButton > button {
    border: none;
    background: white;
    color: #000;
    border-radius: 50%;
    width: 45px;
    height: 45px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    transition: 0.2s;
}
.stButton > button:hover {
    background: #F8BBD0;
    transform: scale(1.1);
}

/* 버튼 정렬 */
div[data-testid="stHorizontalBlock"] {
    justify-content: center !important;
}
div[data-testid="column"] {
    display: flex !important;
    justify-content: center !important;
}

/* 퍼센트 오버레이 */
.slider-wrapper {
    position: relative;
    width: 100%;
}
.percent-overlay {
    position: absolute;
    top: -34px;
    left: 50%;
    transform: translateX(-50%);
    font-weight: 800;
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
</style>
'''
st.markdown(css_code, unsafe_allow_html=True)

# =================================================
# Google Sheets 인증 (Secrets)
# =================================================
@st.cache_resource
def get_ws():
    json_content = st.secrets["gcp_json"]
    if isinstance(json_content, str):
        json_content = json.loads(json_content)

    creds = Credentials.from_service_account_info(
        json_content,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8/edit"
    )
    return sheet.sheet1

ws = get_ws()

# =================================================
# 데이터 로드
# =================================================
df = pd.DataFrame(ws.get_all_records())

def safe_int(x):
    try:
        return int(x)
    except:
        return 0

df["progress"] = df["progress"].apply(safe_int)
df["total"] = df["total"].apply(safe_int)

reading = df[df["status"] == "reading"].reset_index(drop=True)

st.title("🎧 My Reading Playlist")

if reading.empty:
    st.info("읽고 있는 책이 없습니다.")
    st.stop()

book = reading.iloc[0]
row_idx = reading.index[0] + 2

if "progress" not in st.session_state:
    st.session_state.progress = book["progress"]

def save():
    val = int(st.session_state.progress)
    ws.update_cell(row_idx, 3, val)
    if val >= 100:
        ws.update_cell(row_idx, 5, "done")
        ws.update_cell(row_idx, 6, datetime.now().strftime("%Y-%m-%d"))

# 카드
st.markdown(f"""
<div class="book-card">
    <h3>🎵 {book['title']}</h3>
    <p>{book['author']}</p>
</div>
""", unsafe_allow_html=True)

# 퍼센트
st.markdown(f"""
<div class="slider-wrapper">
    <div class="percent-overlay">{st.session_state.progress}%</div>
</div>
""", unsafe_allow_html=True)

st.slider(
    "",
    0, 100,
    key="progress",
    on_change=save,
    label_visibility="collapsed"
)

read_pages = int(book["total"] * st.session_state.progress / 100)
st.caption(f"📄 {read_pages} / {book['total']}p")

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("⏮"):
        st.session_state.progress = max(0, st.session_state.progress - 5)
        save()
        st.rerun()
with c2:
    if st.button("■"):
        st.session_state.progress = 100
        save()
        st.balloons()
        st.rerun()
with c3:
    if st.button("⏭"):
        st.session_state.progress = min(100, st.session_state.progress + 5)
        save()
        st.rerun()
with c4:
    if st.button("💾"):
        save()
        st.success("저장 완료")
