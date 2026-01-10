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
# 🎨 CSS - 이미지 기준 완벽 재현
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
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-weight: 800;
    margin-bottom: 30px;
    font-size: 2.5rem;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    gap: 15px;
    justify-content: center;
    margin-bottom: 25px;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.8);
    border-radius: 25px;
    border: none;
    padding: 12px 28px !important;
    font-size: 1rem;
    font-weight: 600;
    color: #666;
    box-shadow: 0 2px 5px rgba(0,0,0,0.08);
}

.stTabs [aria-selected="true"] {
    background: #EC407A !important;
    color: white !important;
    font-weight: bold;
    box-shadow: 0 3px 8px rgba(236, 64, 122, 0.3);
}

/* Expander 스타일 - 닫혔을 때 */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.8) !important;
    border-radius: 15px !important;
    border: 2px solid #E8E8E8 !important;
    padding: 15px 20px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #666 !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.06) !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(255,255,255,0.95) !important;
    border-color: #F8BBD0 !important;
}

/* Expander 내부 */
details[open] > summary {
    border-bottom: 1px solid #F8BBD0 !important;
    margin-bottom: 15px !important;
}

/* 카드 디자인 */
.book-card {
    background: #FFFFFF;
    padding: 35px;
    border-radius: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    text-align: center;
    border: 2px solid #F0F0F0;
    margin-bottom: 30px;
}

.book-card h3 {
    color: #000000 !important;
    font-size: 14pt !important;
    margin-bottom: 12px;
    font-weight: 700;
}

.book-card .book-title {
    color: #000000 !important;
    font-size: 14pt !important;
    font-weight: 700;
    margin-bottom: 8px;
}

.book-card .author {
    color: #888;
    font-size: 1rem;
    margin-bottom: 20px;
}

.book-card .progress-text {
    color: #EC407A;
    font-size: 2rem;
    font-weight: 800;
    margin-top: 15px;
}

/* 슬라이더 영역 */
.slider-area {
    padding: 30px 0 10px 0;
    margin-bottom: 15px;
}

/* 슬라이더 스타일 */
div[data-baseweb="slider"] {
    padding-top: 25px !important;
    padding-bottom: 5px !important;
}

div[data-baseweb="slider"] > div > div:first-child {
    background-color: #D3D3D3 !important;
    height: 8px !important;
    border-radius: 10px !important;
}

div[data-baseweb="slider"] > div > div:nth-child(2) {
    background-color: #EC407A !important;
    height: 8px !important;
    border-radius: 10px !important;
}

div[data-baseweb="slider"] div[role="slider"] {
    background-color: #2C3E50 !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.25) !important;
    width: 24px !important;
    height: 24px !important;
    top: -2px !important;
    border: 3px solid white !important;
}

/* 슬라이더 값 표시 - 핸들 바로 위 */
div[data-baseweb="slider"]::before {
    content: attr(data-value);
    position: absolute;
    top: -8px;
    left: var(--slider-position, 50%);
    transform: translateX(-50%);
    font-size: 0.85rem;
    color: #666;
    font-weight: 700;
    z-index: 100;
}

/* 슬라이더 틱/툴팁 숨김 */
div[data-testid="stSliderTickBarMin"],
div[data-testid="stSliderTickBarMax"],
div[data-baseweb="tooltip"] {
    display: none !important;
}

/* 페이지 정보 - 슬라이더 아래 양쪽 */
.page-info-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 10px 0 25px 0;
    padding: 0 5px;
}

.page-info-left, .page-info-right {
    font-size: 1.05rem;
    color: #2C3E50;
    font-weight: 700;
}

/* 버튼 영역 */
.button-area {
    display: flex;
    justify-content: center;
    gap: 25px;
    margin-top: 20px;
}

/* 버튼 스타일 - 완전한 원형 */
.stButton > button {
    border: none !important;
    background: white !important;
    color: #2C3E50 !important;
    border-radius: 50% !important;
    width: 60px !important;
    height: 60px !important;
    font-size: 1.4rem !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.12) !important;
    transition: all 0.2s ease !important;
    padding: 0 !important;
    min-height: 60px !important;
}

.stButton > button:hover {
    background: #F8BBD0 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 15px rgba(0,0,0,0.18) !important;
}

.stButton > button:active {
    transform: translateY(0px) !important;
}

/* 버튼 정렬 */
div[data-testid="column"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

/* Form 스타일 */
.stTextInput label, .stNumberInput label {
    color: #666 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

.stTextInput input, .stNumberInput input {
    border-radius: 12px !important;
    border: 2px solid #E8E8E8 !important;
    padding: 10px 15px !important;
    background: rgba(255,255,255,0.9) !important;
}

.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #EC407A !important;
    box-shadow: 0 0 0 1px #EC407A !important;
}

/* Form 버튼 */
.stFormSubmitButton > button {
    background: #EC407A !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 25px !important;
    font-weight: 600 !important;
    box-shadow: 0 3px 8px rgba(236, 64, 122, 0.3) !important;
}

.stFormSubmitButton > button:hover {
    background: #D81B60 !important;
    transform: translateY(-1px) !important;
}

/* Done 카드 */
.done-card {
    background: rgba(255,255,255,0.9);
    padding: 18px 22px;
    border-radius: 15px;
    margin-bottom: 12px;
    border: 2px solid #E8E8E8;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

.done-card .title {
    font-weight: 700;
    color: #000000 !important;
    font-size: 14pt !important;
    margin-bottom: 5px;
}

.done-card .author {
    color: #888;
    font-size: 0.95rem;
    margin-bottom: 8px;
}

.done-card .date {
    color: #AAA;
    font-size: 0.85rem;
}

/* 여백 조정 */
.block-container {
    padding-top: 3rem !important;
    padding-bottom: 3rem !important;
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
            new_title = st.text_input("제목")
            new_author = st.text_input("저자")
            new_total = st.number_input("총 페이지", min_value=1, value=692, step=1)
            
            submitted = st.form_submit_button("추가 ❤️")
            
            if submitted:
                if new_title and new_author:
                    ws.append_row([new_title, new_author, 0, new_total, "reading", ""])
                    st.success(f"'{new_title}' 추가 완료!")
                    st.cache_resource.clear()
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
                st.cache_resource.clear()
        
        # 카드
        st.markdown(f"""
        <div class="book-card">
            <div class="book-title">🎵 {book['title']}</div>
            <div class="author">{book['author']}</div>
            <div class="progress-text">{st.session_state.progress}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 슬라이더 영역
        st.markdown('<div class="slider-area">', unsafe_allow_html=True)
        
        # 슬라이더 위 값 표시용 JavaScript
        slider_position = st.session_state.progress
        st.markdown(f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const slider = document.querySelector('[data-baseweb="slider"]');
            if (slider) {{
                slider.setAttribute('data-value', '{slider_position}');
                slider.style.setProperty('--slider-position', '{slider_position}%');
            }}
        }});
        </script>
        """, unsafe_allow_html=True)
        
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
        <div class="page-info-container">
            <div class="page-info-left">{read_pages} p</div>
            <div class="page-info-right">{book['total']} p</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 버튼 영역
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
