import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# ---------------------------------------------------------
# [설정] 구글 시트 주소 (본인 걸로 유지하세요!)
# ---------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8/edit?usp=sharing"

# ---------------- CSS 디자인 (모바일 최적화 & 가운데 정렬) ----------------
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

    /* ★★★ [여기가 추가된 마법의 코드!] 버튼 가운데 정렬 ★★★ */
    /* 가로줄 전체를 가운데로 */
    div[data-testid="stHorizontalBlock"] {
        justify-content: center !important;
    }
    /* 버튼 상자 안의 내용물도 가운데로 */
    div[data-testid="column"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
</style>
'''
# ---------------- 구글 시트 연결 ----------------
@st.cache_resource
def get_worksheet():
    json_content = json.loads(st.secrets["gcp_json"], strict=False)
    creds = Credentials.from_service_account_info(json_content, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
    return sheet

# [핵심 수정 1] 캐싱 기능 추가! (10초 동안은 구글을 안 괴롭힘)
@st.cache_data(ttl=10) 
def load_data():
    try:
        sheet = get_worksheet()
        records = sheet.get_all_records()
        if not records: return [], []
        df = pd.DataFrame(records)
        reading = df[df['status'] == 'reading'].to_dict('records')
        finished = df[df['status'] == 'done'].to_dict('records')
        return reading, finished
    except Exception as e:
        # 에러나면 빈 리스트 반환 (앱이 안 죽게)
        return [], []

def add_book_to_sheet(title, author, total):
    sheet = get_worksheet()
    sheet.append_row([title, author, 0, total, "reading", ""])
    load_data.clear() # 데이터 갱신했으니 캐시 삭제

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
        with st.form("add"):
            t = st.text_input("제목")
            a = st.text_input("저자")
            p = st.number_input("총 페이지", value=300)
            if st.form_submit_button("추가") and t:
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
        
        # 2. 슬라이더 (값 저장)
        val = st.slider(f"s_{i}", 0, 100, int(book['progress']), label_visibility="collapsed")
        
        # 3. [핵심 수정 2] 레이아웃 단순화 (모바일에서 버튼 가로로 뜨게!)
        curr_p = int(book['total'] * val / 100)
        
        # 페이지 정보는 버튼 위에 텍스트로 깔끔하게 표시
        st.caption(f"📄 현재 {curr_p}p / 총 {book['total']}p")

        # 버튼을 위한 3칸 (중첩 없이 깔끔하게!)
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

        # 값이 바뀌면 저장 (이때만 통신)
        if val != int(book['progress']):
            update_progress_in_sheet(book['title'], val)
            time.sleep(1) # 1초 딜레이 (에러 방지용)
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)

with tab2:
    if finished_list:
        for i, book in enumerate(finished_list):
            st.success(f"🏆 {book['title']} ({book.get('date','-')})")
            if st.button("삭제", key=f"del_{i}"):
                delete_book_from_sheet(book['title'])
                st.rerun()
