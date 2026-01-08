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
# [디자인] CSS
# =========================================================
css_code = """
<style>
.stApp { background-color: #FFC0CB !important; }

h1 {
    color: #C2185B;
    text-align: center;
    font-weight: 800;
}

.book-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    border: 2px solid #F8BBD0;
    text-align: center;
    margin-bottom: 10px;
}

.stButton > button {
    border-radius: 50%;
    width: 50px;
    height: 50px;
    font-size: 20px;
    background: white;
}

.button-row {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-bottom: 20px;
}

.btn-center {
    display: flex;
    justify-content: center;
}
</style>
"""

st.set_page_config(page_title="Pink Player", layout="centered")
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
    df["row"] = df.index + 2  # 실제 시트 row 번호

    reading = df[df["status"] == "reading"].to_dict("records")
    finished = df[df["status"] == "done"].to_dict("records")
    return reading, finished

# =========================================================
# [CRUD 함수]
# =========================================================
def add_book(title, author, total):
    sheet = get_worksheet()
    sheet.append_row([title, author, 0, total, "reading", ""])

def update_progress(row, value):
    sheet = get_worksheet()
    sheet.update_cell(row, 3, value)

def mark_done(row):
    sheet = get_worksheet()
    sheet.update_cell(row, 3, 100)
    sheet.update_cell(row, 5, "done")
    sheet.update_cell(row, 6, datetime.now().strftime("%Y-%m-%d"))

def delete_book(row):
    sheet = get_worksheet()
    sheet.delete_rows(row)

# =========================================================
# [화면]
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
            if st.form_submit_button("추가"):
                add_book(t, a, p)
                st.rerun()

    for i, book in enumerate(reading_list):
        st.markdown(f"""
        <div class="book-card">
            <h3>🎵 {book['title']}</h3>
            <p>{book['author']}</p>
            <h2>{book['progress']}%</h2>
        </div>
        """, unsafe_allow_html=True)

        key = f"{book['row']}"
        val = st.slider(
            "progress",
            0, 100,
            st.session_state.prev_progress.get(key, book["progress"]),
            key=f"s_{key}",
            label_visibility="collapsed"
        )

        st.caption(f"📄 {int(book['total'] * val / 100)} / {book['total']}p")

        st.markdown('<div class="button-row">', unsafe_allow_html=True)
        cols = st.columns(4)

        with cols[0]:
            if st.button("⏮", key=f"prev_{key}"):
                new = max(0, val - int(10 * 100 / book["total"]))
                update_progress(book["row"], new)
                st.session_state.prev_progress[key] = new
                st.rerun()

        with cols[1]:
            if st.button("■", key=f"done_{key}"):
                mark_done(book["row"])
                st.session_state.prev_progress.pop(key, None)
                st.rerun()

        with cols[2]:
            if st.button("⏭", key=f"next_{key}"):
                new = min(100, val + int(10 * 100 / book["total"]))
                update_progress(book["row"], new)
                st.session_state.prev_progress[key] = new
                st.rerun()

        with cols[3]:
            if st.button("💾", key=f"save_{key}"):
                update_progress(book["row"], val)
                st.session_state.prev_progress[key] = val
                st.success("저장됨")
                time.sleep(0.3)
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# [Done]
# =========================================================
with tab2:
    for book in finished_list:
        c1, c2 = st.columns([5,1])
        with c1:
            st.success(f"🏆 {book['title']} ({book['date']})")
        with c2:
            if st.button("❌", key=f"del_{book['row']}"):
                delete_book(book["row"])
                st.rerun()
