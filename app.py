import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# =========================================================
# 설정
# =========================================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8/edit?usp=sharing"

# =========================================================
# CSS
# =========================================================
css_code = """
<style>
.stApp { background-color: #FFC0CB !important; }

.book-card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 12px;
}

.slider-wrap {
    position: relative;
    margin-top: 12px;
}

.progress-overlay {
    position: absolute;
    top: -32px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 26px;
    font-weight: 800;
    color: #C2185B;
}

@media (min-width: 769px) {
    .progress-overlay { display: none; }
}

.stButton > button {
    border-radius: 50%;
    width: 48px;
    height: 48px;
}
</style>
"""

st.set_page_config(page_title="My Reading Playlist", layout="centered")
st.markdown(css_code, unsafe_allow_html=True)

# =========================================================
# Google Sheet
# =========================================================
@st.cache_resource
def get_worksheet():
    creds_json = json.loads(st.secrets["gcp_json"], strict=False)
    creds = Credentials.from_service_account_info(
        creds_json,
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
    return (
        df[df["status"] == "reading"].to_dict("records"),
        df[df["status"] == "done"].to_dict("records"),
    )

# =========================================================
# CRUD
# =========================================================
def add_book(title, author, total):
    get_worksheet().append_row([title, author, 0, total, "reading", ""])

def update_progress(row, val):
    get_worksheet().update_cell(row, 3, val)

def mark_done(row):
    sheet = get_worksheet()
    sheet.update_cell(row, 3, 100)
    sheet.update_cell(row, 5, "done")
    sheet.update_cell(row, 6, datetime.now().strftime("%Y-%m-%d"))

def delete_book(row):
    get_worksheet().delete_rows(row)

# =========================================================
# UI
# =========================================================
st.title("🎧 My Reading Playlist")

if "prev_progress" not in st.session_state:
    st.session_state.prev_progress = {}

reading_list, finished_list = load_data()
tab1, tab2 = st.tabs(["Now Playing", "Done"])

# =========================================================
# Now Playing
# =========================================================
with tab1:
    with st.expander("➕ 책 추가하기"):
        with st.form("add_form"):
            title = st.text_input("제목")
            author = st.text_input("저자")
            total = st.number_input("총 페이지", 1, 5000, 300)
            submitted = st.form_submit_button("추가")

        if submitted and title and author:
            add_book(title, author, total)
            st.rerun()

    for book in reading_list:
        st.markdown(f"""
        <div class="book-card">
            <h3>🎵 {book['title']}</h3>
            <p>{book['author']}</p>
        </div>
        """, unsafe_allow_html=True)

        key = str(book["row"])
        current = st.session_state.prev_progress.get(key, book["progress"])

        st.markdown('<div class="slider-wrap">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="progress-overlay">{current}%</div>',
            unsafe_allow_html=True
        )

        new_val = st.slider(
            "progress",
            0, 100,
            current,
            key=f"s_{key}",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.session_state.prev_progress[key] = new_val
        st.caption(f"📄 {int(book['total'] * new_val / 100)} / {book['total']}p")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button("⏮", key=f"prev_{key}"):
                update_progress(book["row"], max(0, new_val - 5))
                st.rerun()

        with c2:
            if st.button("■", key=f"done_{key}"):
                mark_done(book["row"])
                st.rerun()

        with c3:
            if st.button("⏭", key=f"next_{key}"):
                update_progress(book["row"], min(100, new_val + 5))
                st.rerun()

        with c4:
            if st.button("💾", key=f"save_{key}"):
                update_progress(book["row"], new_val)
                st.success("저장됨")
                time.sleep(0.3)
                st.rerun()

# =========================================================
# Done
# =========================================================
with tab2:
    for book in finished_list:
        c1, c2 = st.columns([5, 1])
        with c1:
            st.success(f"🏆 {book['title']} ({book['date']})")
        with c2:
            if st.button("❌", key=f"del_{book['row']}"):
                delete_book(book["row"])
                st.rerun()
