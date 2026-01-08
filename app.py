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
    # Secrets에서 인증 정보 가져오기
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
    # 제목, 저자, 진행률(0), 총페이지, 상태(reading), 완료일(빈칸)
    sheet.append_row([title, author, 0, total, "reading", ""])
    load_data.clear()

def update_progress_in_
