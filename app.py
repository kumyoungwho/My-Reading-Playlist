import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# ---------------------------------------------------------
# [설정 1] 구글 시트 주소를 여기에 붙여넣으세요! (따옴표 안에)
# ---------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8/edit?usp=sharing"

# ---------------- CSS 디자인 ----------------
css_code = '''
<style>
    .stApp { background-color: #FFC0CB !important; }
    h1 { color: #C2185B; text-align: center; font-family: sans-serif; font-weight: 800; margin-bottom: 20px; text-shadow: 1px 1px 2px rgba(255,255,255,0.5); }
    .book-card { background: #FFFFFF; padding: 25px; border-radius: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; border: 2px solid #F8BBD0; margin-bottom: 40px !important; }
    div[data-baseweb="slider"] { padding-top: 10px !important; padding-bottom: 0px !important; }
    div[data-baseweb="slider"] > div > div:first-child { background-color: #9E9E9E !important; height: 4px !important; }
    div[data-baseweb="slider"] > div > div:nth-child(2) { background-color: #212121 !important; height: 4px !important; }
    div[data-baseweb="slider"] div[role="slider"] { background-color: #212121 !important; width: 18px !important; height: 18px !important; top: -3px !important; }
    div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"], div[data-baseweb="tooltip"] { display: none !important; }
    .stButton > button { border: none; background: white; color: #000; border-radius: 50%; width: 45px; height: 45px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .stButton > button:hover { background: #F8BBD0; transform: scale(1.1); }
</style>
'''

st.set_page_config(page_title="Pink Audio Player", layout="centered")
st.markdown(css_code, unsafe_allow_html=True)

# ---------------- 구글 시트 연결 함수 ----------------
@st.cache_resource
def get_worksheet():
    # Secrets에서 키 꺼내기
    json_content = json.loads(st.secrets["gcp_json"], strict=False)
    creds = Credentials.from_service_account_info(json_content, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
    return sheet

# 데이터 불러오기 함수
def load_data():
    try:
        sheet = get_worksheet()
        records = sheet.get_all_records()
        # 시트가 비었으면 헤더 생성
        if not records:
            sheet.append_row(["title", "author", "progress", "total", "status", "date"])
            return [], []
        
        df = pd.DataFrame(records)
        reading = df[df['status'] == 'reading'].to_dict('records')
        finished = df[df['status'] == 'done'].to_dict('records')
        return reading, finished
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return [], []

# 데이터 저장(추가) 함수
def add_book_to_sheet(title, author, total):
    sheet = get_worksheet()
    sheet.append_row([title, author, 0, total, "reading", ""])

# 진행률 업데이트 함수
def update_progress_in_sheet(title, new_progress):
    sheet = get_worksheet()
    cell = sheet.find(title)
    # progress는 3번째 열 (C열)
    sheet.update_cell(cell.row, 3, new_progress)

# 완독 처리 함수
def mark_done_in_sheet(title):
    sheet = get_worksheet()
    cell = sheet.find(title)
    # status(5열)을 done으로, date(6열)을 오늘 날짜로
    sheet.update_cell(cell.row, 5, "done")
    sheet.update_cell(cell.row, 6, datetime.now().strftime("%Y-%m-%d"))

# 삭제 함수
def delete_book_from_sheet(title):
    sheet = get_worksheet()
    cell = sheet.find(title)
    sheet.delete_rows(cell.row)

# ---------------- 앱 로직 시작 ----------------

st.title("🎧 My Reading Playlist (DB)")

# 데이터 로딩
reading_list, finished_list = load_data()

tab1, tab2 = st.tabs(["▶ Now Playing", "✔ Done"])

with tab1:
    with st.expander("➕ 새 책 추가하기"):
        with st.form("add"):
            t = st.text_input("제목")
            a = st.text_input("저자")
            p = st.number_input("총 페이지", value=300)
            if st.form_submit_button("추가 💖") and t:
                add_book_to_sheet(t, a, p)
                st.rerun()

    for i, book in enumerate(reading_list):
        st.markdown(f'''
        <div class="book-card">
            <h3 style="margin:0; font-size:1.4rem; color:#333;">🎵 {book['title']}</h3>
            <p style="color:#666; font-size:1rem; margin-top:8px;">{book['author']}</p>
            <p style="color:#EC407A; font-weight:bold; font-size:1.2rem; margin-top:10px;">{book['progress']}%</p>
        </div>
        ''', unsafe_allow_html=True)
        
        val = st.slider(f"s_{i}", 0, 100, int(book['progress']), label_visibility="collapsed")
        
        c_left, c_mid, c_right = st.columns([2, 6, 2])
        curr_p = int(book['total'] * val / 100)
        
        with c_left: st.markdown(f"<div style='margin-top:12px; font-weight:bold; color:#555;'>{curr_p} p</div>", unsafe_allow_html=True)
        with c_mid:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1: st.button("⏮", key=f"prev_{i}") # 이전 버튼 (기능 없음, 장식)
            with col_b2:
                if st.button("■", key=f"fin_{i}", help="완독"):
                    mark_done_in_sheet(book['title'])
                    st.balloons()
                    st.rerun()
            with col_b3: st.button("⏭", key=f"next_{i}") # 다음 버튼 (기능 없음, 장식)
        with c_right: st.markdown(f"<div style='text-align:right; margin-top:12px; color:#555;'>{book['total']} p</div>", unsafe_allow_html=True)

        # 슬라이더 값이 바뀌면 즉시 DB 저장
        if val != int(book['progress']):
            update_progress_in_sheet(book['title'], val)
            st.rerun()
        st.markdown("<br><br>", unsafe_allow_html=True)

with tab2:
    if finished_list:
        st.markdown("### 🏆 명예의 전당")
        st.markdown("---")
        for i, book in enumerate(finished_list):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1: st.markdown(f"📖 {book['title']}")
            with c2: st.text(book['author'])
            with c3: st.text(book.get('date', '-'))
            with c4:
                if st.button("❌", key=f"del_fin_{i}"):
                    delete_book_from_sheet(book['title'])
                    st.rerun()
            st.markdown("<hr style='margin: 5px 0; border-top: 1px dashed #F8BBD0;'>", unsafe_allow_html=True)
    else:
        st.info("아직 완독한 책이 없어요 🍰")
