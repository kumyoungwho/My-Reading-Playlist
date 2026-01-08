import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# =========================================================
# [설정] 구글 시트 주소 (★여기에 본인 주소를 꼭 넣으세요!★)
# =========================================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1mOcqHyjRqAgWFOm1_8btKzsLVzP88vv4qDJwmECNtj8/edit?usp=sharing"

# =========================================================
# [디자인] CSS (분홍 배경 + 카드 디자인 + 버튼 가운데 정렬)
# =========================================================
css_code = '''
<style>
    /* 1. 전체 배경색 (연한 핑크) - 절대 지워지지 않도록 !important 사용 */
    .stApp { background-color: #FFC0CB !important; }
    
    /* 2. 제목 스타일 */
    h1 { color: #C2185B; text-align: center; font-weight: 800; margin-bottom: 20px; }
    
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
    
    /* 5. 버튼 동그랗게 꾸미기 */
    .stButton > button { 
        border: none; 
        background: white; 
        color: #000; 
        border-radius: 50%; 
        width: 50px; 
        height: 50px; 
        font-size: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2); 
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .stButton > button:hover { background: #F8BBD0; }
    
    /* 6. ★★★ 버튼 가운데 정렬 핵심 코드 ★★★ */
    /* 버튼이 들어있는 가로줄 전체를 가운데로 */
    div[data-testid="stHorizontalBlock"] {
        justify-content: center !important;
    }
    /* 각 버튼 상자(컬럼) 내부도 가운데로 */
    div[data-testid="column"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
</style>
'''

# 페이지 설정 및 CSS 적용
st.set_page_config(page_title="Pink Player", layout="centered")
st.markdown(css_code, unsafe_allow_html=True)

# =========================================================
# [기능] 구글 시트 연결 및 데이터 처리
# =========================================================
@st.cache_resource
def get_worksheet():
    try:
        # Secrets에서 인증 정보 가져오기
        json_content = json.loads(st.secrets["gcp_json"], strict=False)
        creds = Credentials.from_service_account_info(
            json_content, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SHEET_URL).sheet1
        return sheet
    except Exception as e:
        st.error(f"구글 시트 연결 실패: {str(e)}")
        st.stop()

@st.cache_data(ttl=30) 
def load_data():
    try:
        sheet = get_worksheet()
        records = sheet.get_all_records()
        if not records: 
            return [], []
        df = pd.DataFrame(records)
        reading = df[df['status'] == 'reading'].to_dict('records')
        finished = df[df['status'] == 'done'].to_dict('records')
        return reading, finished
    except Exception as e:
        st.error(f"데이터 로드 실패: {str(e)}")
        return [], []

def add_book_to_sheet(title, author, total):
    try:
        sheet = get_worksheet()
        # 제목, 저자, 진행률(0), 총페이지, 상태(reading), 완료일(빈칸)
        sheet.append_row([title, author, 0, total, "reading", ""])
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"책 추가 실패: {str(e)}")
        return False

def update_progress_in_sheet(title, new_progress):
    try:
        sheet = get_worksheet()
        cell = sheet.find(title)
        sheet.update_cell(cell.row, 3, new_progress)
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"진행률 업데이트 실패: {str(e)}")
        return False

def mark_done_in_sheet(title):
    try:
        sheet = get_worksheet()
        cell = sheet.find(title)
        sheet.update_cell(cell.row, 3, 100)  # 진행률 100%로 설정
        sheet.update_cell(cell.row, 5, "done")
        sheet.update_cell(cell.row, 6, datetime.now().strftime("%Y-%m-%d"))
        load_data.clear()
        # Session State에서도 제거
        book_keys_to_remove = [k for k in st.session_state.prev_progress.keys() if title in k]
        for k in book_keys_to_remove:
            del st.session_state.prev_progress[k]
        return True
    except Exception as e:
        st.error(f"완독 처리 실패: {str(e)}")
        return False

def delete_book_from_sheet(title):
    try:
        sheet = get_worksheet()
        cell = sheet.find(title)
        sheet.delete_rows(cell.row)
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"삭제 실패: {str(e)}")
        return False

# =========================================================
# [화면] 앱 메인 화면 구성
# =========================================================

st.title("🎧 My Reading Playlist")

# Session State 초기화
if 'prev_progress' not in st.session_state:
    st.session_state.prev_progress = {}

reading_list, finished_list = load_data()

tab1, tab2 = st.tabs(["Now Playing", "Done"])

# 탭 1: 읽고 있는 책 (Now Playing)
with tab1:
    with st.expander("➕ 책 추가하기"):
        with st.form("add_form", clear_on_submit=True):
            t = st.text_input("제목")
            a = st.text_input("저자")
            p = st.number_input("총 페이지", value=300, min_value=1)
            submitted = st.form_submit_button("추가")
        
        # Form 밖에서 처리
        if submitted:
            if t and a:
                if add_book_to_sheet(t, a, p):
                    st.success(f"'{t}' 추가 완료!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("제목과 저자를 입력해주세요.")

    # 책 목록 보여주기
    if reading_list:
        for i, book in enumerate(reading_list):
            # 1. 책 정보 카드 (HTML)
            st.markdown(f'''
            <div class="book-card">
                <h3 style="margin:0; font-size:1.3rem;">🎵 {book['title']}</h3>
                <p style="color:#666; font-size:0.9rem;">{book['author']}</p>
                <h2 style="color:#C2185B; margin: 10px 0;">{book['progress']}%</h2>
            </div>
            ''', unsafe_allow_html=True)
            
            # 2. 슬라이더 (진행률 조절) - Session State로 관리
            book_key = f"{book['title']}_{i}"
            prev_val = st.session_state.prev_progress.get(book_key, int(book['progress']))
            
            val = st.slider(
                f"s_{i}", 
                0, 100, 
                prev_val, 
                label_visibility="collapsed",
                key=f"slider_{i}"
            )
            
            # 3. 현재 페이지 표시
            curr_p = int(book['total'] * val / 100)
            st.caption(f"📄 현재 {curr_p}p / 총 {book['total']}p")

            # 4. 버튼 레이아웃 (가운데 정렬)
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            
            # 이전 버튼 (10페이지 뒤로)
            with c1:
                if st.button("⏮", key=f"prev_{i}", help="10페이지 뒤로"):
                    page_percent = int(10 * 100 / book['total'])
                    new_val = max(0, val - page_percent)
                    if update_progress_in_sheet(book['title'], new_val):
                        st.session_state.prev_progress[book_key] = new_val
                        time.sleep(0.3)
                        st.rerun()
            
            # 완독 버튼
            with c2:
                if st.button("■", key=f"fin_{i}", help="완독 처리"):
                    if mark_done_in_sheet(book['title']):
                        st.balloons()
                        time.sleep(0.5)
                        st.rerun()
            
            # 다음 버튼 (10페이지 앞으로)
            with c3:
                if st.button("⏭", key=f"next_{i}", help="10페이지 앞으로"):
                    page_percent = int(10 * 100 / book['total'])
                    new_val = min(100, val + page_percent)
                    if update_progress_in_sheet(book['title'], new_val):
                        st.session_state.prev_progress[book_key] = new_val
                        time.sleep(0.3)
                        st.rerun()
            
            # 저장 버튼 (슬라이더 값 반영) - 제일 오른쪽
            with c4:
                if st.button("💾", key=f"save_{i}", help="진행률 저장"):
                    if val != int(book['progress']):
                        if update_progress_in_sheet(book['title'], val):
                            st.session_state.prev_progress[book_key] = val
                            st.success("저장 완료!")
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.info("변경사항이 없습니다.")
                
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("읽고 있는 책이 없습니다. '+ 책 추가하기'를 눌러보세요!")

# 탭 2: 다 읽은 책 (Done)
with tab2:
    if finished_list:
        for i, book in enumerate(finished_list):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.success(f"🏆 {book['title']} ({book.get('date','-')})")
            with col2:
                if st.button("❌", key=f"del_{i}", help="삭제"):
                    if delete_book_from_sheet(book['title']):
                        st.rerun()
    else:
        st.info("아직 다 읽은 책이 없어요. 화이팅!")
