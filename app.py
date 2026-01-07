import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------- CSS 디자인 ----------------
css_code = '''
<style>
    .stApp {
        background-color: #FFC0CB !important;
    }
    h1 {
        color: #C2185B;
        text-align: center;
        font-family: sans-serif;
        font-weight: 800;
        margin-bottom: 20px;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
    }
    .book-card {
        background: #FFFFFF;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        text-align: center;
        border: 2px solid #F8BBD0;
        margin-bottom: 40px !important; 
    }
    div[data-baseweb="slider"] {
        padding-top: 10px !important;
        padding-bottom: 0px !important;
    }
    div[data-baseweb="slider"] > div > div:first-child {
        background-color: #9E9E9E !important;
        height: 4px !important;
    }
    div[data-baseweb="slider"] > div > div:nth-child(2) {
        background-color: #212121 !important; 
        height: 4px !important;
    }
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: #212121 !important;
        width: 18px !important;
        height: 18px !important;
        top: -3px !important; 
    }
    div[data-testid="stSliderTickBarMin"], 
    div[data-testid="stSliderTickBarMax"],
    div[data-baseweb="tooltip"] {
        display: none !important;
    }
    .stButton > button {
        border: none;
        background: white;
        color: #000;
        border-radius: 50%;
        width: 45px;
        height: 45px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        background: #F8BBD0;
        transform: scale(1.1);
    }
</style>
'''

st.set_page_config(page_title="Pink Audio Player", layout="centered")
st.markdown(css_code, unsafe_allow_html=True)

if 'reading_list' not in st.session_state:
    st.session_state.reading_list = [{
        "id": 1, 
        "title": "도파민네이션", 
        "author": "애나 렘키", 
        "progress": 45, 
        "total": 300
    }]
if 'finished_list' not in st.session_state:
    st.session_state.finished_list = []

st.title("🎧 My Reading Playlist")
tab1, tab2 = st.tabs(["▶ Now Playing", "✔ Done"])

with tab1:
    with st.expander("➕ 새 책 추가하기"):
        with st.form("add"):
            t = st.text_input("제목")
            a = st.text_input("저자")
            p = st.number_input("총 페이지", value=300)
            if st.form_submit_button("추가 💖") and t:
                new_book = {"id": datetime.now().timestamp(), "title": t, "author": a, "progress": 0, "total": p}
                st.session_state.reading_list.append(new_book)
                st.rerun()

    for i, book in enumerate(st.session_state.reading_list):
        st.markdown(f'''
        <div class="book-card">
            <h3 style="margin:0; font-size:1.4rem; color:#333;">🎵 {book['title']}</h3>
            <p style="color:#666; font-size:1rem; margin-top:8px;">{book['author']}</p>
            <p style="color:#EC407A; font-weight:bold; font-size:1.2rem; margin-top:10px;">{book['progress']}%</p>
        </div>
        ''', unsafe_allow_html=True)
        
        val = st.slider(f"s_{i}", 0, 100, book['progress'], label_visibility="collapsed")
        
        c_left, c_mid, c_right = st.columns([2, 6, 2])
        curr_p = int(book['total'] * val / 100)
        
        with c_left: st.markdown(f"<div style='margin-top:12px; font-weight:bold; color:#555;'>{curr_p} p</div>", unsafe_allow_html=True)
        with c_mid:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1: st.button("⏮", key=f"prev_{i}")
            with col_b2:
                if st.button("■", key=f"fin_{i}", help="완독"):
                    book['date'] = datetime.now().strftime("%Y-%m-%d")
                    st.session_state.finished_list.append(book)
                    st.session_state.reading_list.pop(i)
                    st.balloons()
                    st.rerun()
            with col_b3: st.button("⏭", key=f"next_{i}")
        with c_right: st.markdown(f"<div style='text-align:right; margin-top:12px; color:#555;'>{book['total']} p</div>", unsafe_allow_html=True)

        if val != book['progress']:
            st.session_state.reading_list[i]['progress'] = val
            st.rerun()
        st.markdown("<br><br>", unsafe_allow_html=True)

with tab2:
    if st.session_state.finished_list:
        st.markdown("### 🏆 명예의 전당")
        st.markdown("---")
        for i, book in enumerate(st.session_state.finished_list):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1: st.markdown(f"📖 {book['title']}")
            with c2: st.text(book['author'])
            with c3: st.text(book.get('date', '-'))
            with c4:
                if st.button("❌", key=f"del_fin_{i}"):
                    st.session_state.finished_list.pop(i)
                    st.rerun()
            st.markdown("<hr style='margin: 5px 0; border-top: 1px dashed #F8BBD0;'>", unsafe_allow_html=True)
    else:
        st.info("아직 완독한 책이 없어요 🍰")
