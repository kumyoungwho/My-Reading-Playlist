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
# 🎨 CSS
# =================================================
css_code = '''
<style>
/* 전체 핑크색 배경 */
.stApp {
    background-color: #FFC0CB !important;
    background-image: none;
}

/* 제목 스타일 */
h1 {
    color: #2C3E50;
    text-align: center;
    font-family: sans-serif;
    font-weight: 800;
    margin-bottom: 30px;
    font-size: 2.5rem;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    justify-content: flex-start;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.7);
    border-radius: 20px;
    border: none;
    padding: 12px 24px !important;
    font-size: 1rem;
    font-weight: 600;
    color: #666;
}

.stTabs [aria-selected="true"] {
    background: #EC407A !important;
    color: white !important;
    font-weight: bold;
}

/* Expander 스타일 */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.7) !important;
    border-radius: 15px !important;
    border: 2px solid #F8BBD0 !important;
    padding: 15px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #666 !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(255,255,255,0.9) !important;
}

/* 카드 디자인 */
.book-card {
    background: #FFFFFF;
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    text-align: center;
    border: 2px solid #F8BBD0;
    margin-bottom: 20px;
}

.book-card h3 {
    color: #2C3E50;
    font-size: 1.5rem;
    margin-bottom: 10px;
    font-weight: 700;
}

.book-card .author {
    color: #666;
    font-size: 1rem;
    margin-bottom: 20px;
}

.book-card .progress-text {
    color: #EC407A;
    font-size: 1.8rem;
    font-weight: 800;
    margin-top: 10px;
}

/* 슬라이더 컨테이너 */
.slider-container {
    padding: 20px 0;
    position: relative;
}

/* 슬라이더 값 표시 */
.slider-value {
    position: absolute;
    top: -5px;
    font-size: 0.9rem;
    color: #666;
    font-weight: 600;
    transform: translateX(-50%);
}

/* 슬라이더 스타일 */
div[data-baseweb="slider"] {
    padding-top: 20px !important;
    padding-bottom: 10px !important;
}

div[data-baseweb="slider"] > div > div:first-child {
    background-color: #E0E0E0 !important;
    height: 6px !important;
}

div[data-baseweb="slider"] > div > div:nth-child(2) {
    background-color: #EC407A !important;
    height: 6px !important;
}

div[data-baseweb="slider"] div[role="slider"] {
    background-color: #2C3E50 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    width: 22px !important;
    height: 22px !important;
    top: -2px !important;
}

/* 슬라이더 틱 숨김 */
div[data-testid="stSliderTickBarMin"],
div[data-testid="stSliderTickBarMax"],
div[data-baseweb="tooltip"] {
    display: none !important;
}

/* 페이지 정보 */
.page-info {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    margin-bottom: 20px;
    font-size: 1rem;
    color: #2C3E50;
    font-weight: 600;
}

/* 버튼 스타일 */
.stButton > button {
    border: none;
    background: white;
    color: #2C3E50;
    border-radius: 50%;
    width: 55px;
    height: 55px;
    font-size: 1.3rem;
    box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    transition: all 0.2s;
}

.stButton > button:hover {
    background: #F8BBD0;
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

/* 버튼 정렬 */
div[data-testid="column"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

/* Input 스타일 */
.stTextInput input, .stNumberInput input {
    border-radius: 10px !important;
    border: 2px solid #F8BBD0 !important;
}

/* 완료 목록 카드 */
.done-card {
    background: rgba(255,255,255,0.8);
    padding: 15px 20px;
    border-radius: 15px;
    margin-bottom: 10px;
    border: 2px solid #E0E0E0;
}

.done-card .title {
    font-weight: 700;
    color: #2C3E50;
    font-size: 1.1rem;
}

.done-card .author {
    color: #666;
    font-size: 0.9rem;
}

.done-card .date {
    color: #999;
    font-size: 0.8rem;
    margin-top: 5px;
}
</style>
'''
st.markdown(css_code, unsafe_allow_html=True)

# =================================================
# Google Sheets 인증
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
def load_data():
    df = pd.DataFrame(ws.get_all_records())
    
    def safe_int(x):
        try:
            return int(x)
        except:
            return 0
    
    df["progress"] = df["progress"].apply(safe_int)
    df["total"] = df["total"].apply(safe_int)
    
    return df

df = load_data()

# =================================================
# 제목
# =================================================
st.markdown("<h1>🎧 My Reading Playlist</h1>", unsafe_allow_html=True)

# =================================================
# 탭
# =================================================
tab1, tab2 = st.tabs(["▶ Now Playing", "✓ Done"])

# =================================================
# Now Playing 탭
# =================================================
with tab1:
    # 새 책 추가하기
    with st.expander("➕ 새 책 추가하기"):
        with st.form("add_book"):
            new_title = st.text_input("책 제목")
            new_author = st.text_input("저자")
            new_total = st.number_input("총 페이지", min_value=1, value=100, step=1)
            
            if st.form_submit_button("추가하기"):
                if new_title and new_author:
                    ws.append_row([new_title, new_author, 0, new_total, "reading", ""])
                    st.success(f"'{new_title}' 추가 완료!")
                    st.rerun()
                else:
                    st.error("제목과 저자를 입력해주세요.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 읽고 있는 책
    reading = df[df["status"] == "reading"].reset_index(drop=True)
    
    if reading.empty:
        st.info("읽고 있는 책이 없습니다.")
    else:
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
            <div class="author">{book['author']}</div>
            <div class="progress-text">{st.session_state.progress}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 슬라이더 컨테이너
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        
        # 슬라이더 위 값 표시
        slider_percent = (st.session_state.progress / 100) * 100
        st.markdown(f'<div class="slider-value" style="left: {slider_percent}%;">{st.session_state.progress}</div>', unsafe_allow_html=True)
        
        st.slider(
            "",
            0, 100,
            key="progress",
            on_change=save,
            label_visibility="collapsed"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 페이지 정보
        read_pages = int(book["total"] * st.session_state.progress / 100)
        st.markdown(f"""
        <div class="page-info">
            <span>{read_pages} p</span>
            <span>{book['total']} p</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⏮"):
                st.session_state.progress = max(0, st.session_state.progress - 5)
                save()
                st.rerun()
        
        with col2:
            if st.button("■"):
                st.session_state.progress = 100
                save()
                st.balloons()
                st.rerun()
        
        with col3:
            if st.button("⏭"):
                st.session_state.progress = min(100, st.session_state.progress + 5)
                save()
                st.rerun()

# =================================================
# Done 탭
# =================================================
with tab2:
    done = df[df["status"] == "done"].reset_index(drop=True)
    
    if done.empty:
        st.info("완료한 책이 없습니다.")
    else:
        for _, book in done.iterrows():
            st.markdown(f"""
            <div class="done-card">
                <div class="title">✓ {book['title']}</div>
                <div class="author">{book['author']}</div>
                <div class="date">완료일: {book.get('date', '-')}</div>
            </div>
            """, unsafe_allow_html=True)
