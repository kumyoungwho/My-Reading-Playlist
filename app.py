import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# ---------------------------------------------------------
# [설정] 구글 시트 주소 (★여기에 본인 주소를 꼭 넣으세요!★)
# ---------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8/edit?usp=sharing"

# ---------------- CSS 디자인 (배경색 + 카드 + 가운데 정렬) ----------------
css_code = '''
<style>
    /* 1. 전체 배경색 (연한 핑크) */
    .stApp { background-color: #FFC0CB !important; }
    
    /* 2. 제목 스타일 */
    h1 { color: #C2185B; text-align: center; font-family: sans-serif; font-weight: 800; margin-bottom: 20px; }
    
    /* 3. 책 정보 카드 디자인 */
    .book-card { 
        background: #FFFFFF; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); 
        text-align: center; 
        border: 2px solid #F8BBD0; 
        margin-bottom: 15px !important; 
    }
    
    /* 4. 슬라이더 색상 커스텀 */
    div[data-baseweb="slider"] > div > div:first-child { background-color: #9E9E9E !important; }
    div[data-baseweb="slider"] > div > div:nth-child(2) { background-color: #C2185B !important; }
    div[data-baseweb="slider"] div[role="slider"] { background-color: #C2185B !important; }
    
    /* 5. 버튼 동그랗게 예쁘게 만들기 */
    .stButton > button { 
        border: none; 
        background: white; 
        color: #000; 
        border-radius: 50%; 
        width: 50px; 
        height: 50px; 
        font-size: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2); 
    }
    .stButton > button:hover { background: #F8BBD0; }
    
    /* 6. 모바일 글자 크기 */
    p { font-size: 14px; }

    /* 7. ★버튼 가운데 정렬 (여기가 추가된 부분!)★ */
    div[data-testid="stHorizontalBlock"] {
        justify-content: center !important;
    }
    div[data-testid="column"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
</style>
'''

st.set_page_config(page_title="Pink Player", layout="centered")
st.markdown(css_code, unsafe_allow_html=True)

# ---------------- 구글 시트 연결 ----------------
@st.cache_resource
def get_worksheet():
    # Secrets에서 정보 가져오기
    json_content = json.loads(st.secrets["gcp_json"], strict=False)
    creds = Credentials.from_service_account_info(json_content, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
    return sheet

@st.cache_data(ttl=10) 
def load_data():
    try:
        sheet = get_worksheet()
        records = sheet.get_all_records()
        if not records: return [], []
        df = pd.DataFrame(records)
        # reading과 done 상태별로 나누기
        reading = df[df['status'] == 'reading'].to_dict('records')
        finished = df[df['status'] == 'done'].to_dict('records')
        return reading, finished
    except Exception as e:
        return [], []

def add_book_to_sheet(title, author, total):
    sheet = get_worksheet()
    sheet.append_row([title, author, 0, total, "reading", ""])
    load_data.clear()

def update_progress_in_sheet(title, new_progress):
    sheet = get_worksheet()
    cell = sheet.find(title)
    sheet.update_cell(cell.row, 3, new_progress)
    load_data.clear()

def mark_done_in_sheet(title):
    sheet = get_worksheet()
    cell = sheet.find(title)
    sheet.update_cell(cell.row, 5, "done")
    sheet.update_cell(cell.row, 6, datetime.now().strftime("%Y-%m-%d"))
    load_data.clear()

def delete_book_from_sheet(title):
    sheet = get_worksheet()
    cell = sheet.find(title)
    sheet.delete_rows(cell.row)
    load_data.clear()

# ---------------- 앱 화면 시작 ----------------

st.title("🎧 My Reading Playlist")

reading_list, finished_list = load_data()

tab1, tab2 = st.tabs(["Now Playing", "Done"])

with tab1:
    with st.expander("➕ 책 추가하기"):
        # 여기가 폼 시작입니다
        with st.form("add"):
            t = st.text_input("제목")
            a = st.text_input("저자")
            p = st.number_input("총 페이지", value=300)
            # 여기가 문제의 [추가] 버튼입니다! 꼭 들여쓰기가 되어 있어야 해요.
            submitted = st.form_submit_button("추가")
            
            if submitted and t:
                add_book_to_sheet(t, a, p)
                st.rerun()

    for i, book in enumerate(reading_list):
        # 1. 책 정보 카드
        st.markdown(f'''
        <div class="book-card">
            <h3 style="margin:0; font-size:1.3rem;">🎵 {book['title']}</h3>
            <p style="color:#666; font-size:0.9rem;">{book['author']}</p>
            <h2 style="color:#C2185B; margin: 10px 0;">{book['progress']}%</h2>
        </div>
        ''', unsafe_allow_html=True)
        
        # 2. 슬라이더
        val = st.slider(f"s_{i}", 0, 100, int(book['progress']), label_visibility="collapsed")
        
        # 3. 버튼 레이아웃 (가운데 정렬 적용됨)
        curr_p = int(book['total'] * val / 100)
        st.caption(f"📄 현재 {curr_p}p / 총 {book['total']}p")

        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1: 
            st.button("⏮", key=f"prev_{i}") 
        with c2:
            if st.button("■", key=f"fin_{i}", help="완독"):
                mark_done_in_sheet(book['title'])
                st.balloons()
                st.rerun()
        with c3: 
            st.button("⏭", key=f"next_{i}")

        if val != int(book['progress']):
            update_progress_in_sheet(book['title'], val)
            time.sleep(1)
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)

with tab2:
    if finished_list:
        for i, book in enumerate(finished_list):
            st.success(f"🏆 {book['title']} ({book.get('date','-')})")
            if st.button("삭제", key=f"del_{i}"):
                delete_book_from_sheet(book['title'])
                st.rerun()
