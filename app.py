import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# =========================================================
# [설정] 구글 시트 주소
# =========================================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8/edit?usp=sharing"

# =========================================================
# [CSS] 모바일 오버레이 + 애니메이션
# =========================================================
css_code = """
<style>
.stApp {
    background-color: #FFC0CB !important;
}

/* 카드 */
.book-card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 16px;
}

/* 슬라이더 컨테이너 */
.slider-wrap {
    position: relative;
    margin-top: 10px;
}

/* 퍼센트 오버레이 */
.progress-overlay {
    position: absolute;
    top: -34px;
    left: 50%;
    transform: translateX(-50%) scale(1);
    font-size: 26px;
    font-weight: 800;
    color: #C2185B;
    transition: transform 0.15s ease, opacity 0.15s ease;
}

/* 버튼 */
.stButton > button {
    border-radius: 50%;
    width: 48px;
    height: 48px;
    font-size: 18px;
}

/* 모바일 전용 오버레이 활성화 */
@media (max-width: 768px) {
    .progress-overlay {
        opacity: 1;
    }
}

/* 데스크톱에서는 오버레이 숨김 */
@media (min-width: 769px) {
    .progress-overlay {
        display: none;
    }
}
</style>
"""

st.set_page_config(page_title="My Reading Playlist", layout="centered")
st.markdown(css_code, unsafe_allow_html=True)

# =========================================================
# [구글 시트 연결]
# =========================================================
@st.cache_resource
def get_worksheet():
    json_content = json.loads(st.secrets["gcp_json"], strict=False)
    creds = Credentials.from_service_account_info(
        json_content,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_url(SHEET_URL).sheet1

def load_data():
    sheet = get_worksheet()
    records = sheet.get_all_records()
    if not records:
        return [], []

    df = pd.DataFrame(records)
    df["row"] = df.index + 2

    reading = df[df["status"] == "reading"].to_dict("records")
    finished = df[df["status"] == "done"].to_dict("records")
    return reading, finished

# =========================================================
# [CRUD]
# =========================================================
def add_book(title, author, total):
    get_worksheet().append_row([title, author, 0, total, "reading", ""])

def update_progress(row, value):
    get_worksheet().update_cell(row, 3, value)

def mark_done(row):
    sheet = get_worksheet()
    sheet.update_cell(row, 3, 100)
    sheet.update_cell(row, 5, "done")
    sheet.update_cell(row, 6, datetime.now().strftime("%Y-%m-%d"))

def delete_book(row):
    get_worksheet().delete_rows(row)

# =========================================================
# [UI]
# =========================================================
st.title("🎧 My Reading Playlist")

if "prev_progress" not in st.session_state:
    st.session_state.prev_progress = {}

reading_list, finished_list = load_data()
tab1, tab2 = st.tabs(["Now Playing", "Done"])

# =========================================================
# [Now Playing]
# =========================================================
with tab1:
    with st.expander("➕ 책 추가하기"):
        with st.form("add"):
            t = st.text_input("제목")
            a = st.text_input("저자")
            p = st.number_input("총 페이지", 1, 5000, 300)
            if st.form_s_
