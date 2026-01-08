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
        with st.form("add"):
            t = st.text_input("제목")
