# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq
import pandas as pd
import os
from datetime import datetime
import re
import io
import edge_tts
import asyncio
import base64
from streamlit_mic_recorder import mic_recorder
import random

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# --- 2. MA TRẬN KIẾN THỨC (TOÁN CÁNH DIỀU & ANH GLOBAL SUCCESS) ---
MATH_TOPICS = {
    "Học kỳ 1": ["Số tự nhiên hàng triệu", "4 phép tính số lớn", "Trung bình cộng", "Tổng - Hiệu", "Góc & Đường thẳng"],
    "Học kỳ 2": ["Phân số: Khái niệm & Rút gọn", "Cộng, trừ, nhân, chia phân số", "Tổng - Tỉ", "Hiệu - Tỉ", "Hình bình hành & Thoi", "Diện tích mm2, dm2"]
}

ENGLISH_BOOK_MAP = {
    11: {"topic": "My home", "vocab": "road, street, big, busy, live, noisy, quiet", "focus": "Where someone lives"},
    12: {"topic": "Jobs", "vocab": "actor, farmer, nurse, office worker, policeman", "focus": "Jobs and workplaces"},
    13: {"topic": "Appearance", "vocab": "big, short, slim, tall, eyes, face", "focus": "Descriptions"},
    14: {"topic": "Daily activities", "vocab": "watch TV, cooking, wash clothes", "focus": "Routines"},
    15: {"topic": "My family's weekends", "vocab": "cinema, shopping centre, swimming pool", "focus": "Weekend activities"}
}

# --- 3. HÀM DỮ LIỆU & HIỂN THỊ KHOA HỌC ---
def load_data():
    req = ["Time", "Mon", "Diem", "Coins", "Yeu", "Phut"]
    if not os.path.exists(DATA_FILE): return pd.DataFrame(columns=req)
    df = pd.read_csv(DATA_FILE)
    for c in req:
        if c not in df.columns: df[c] = 0 if c in ["Diem", "Coins", "Phut"] else "N/A"
    return df

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    text = text.replace("直", "vuông").strip()
    text = re.sub(r'\n{2,}', '<br><br>', text).replace('\n', '<br>')
    text = re.sub(r'(Câu \d+[:\.])', r'<br><b style="color: #d35400; font-size: 1.2em; display: inline-block; margin-top: 15px;">\1</b>', text)
    return f"""<div style="background-color: #fff; border-left: 10px solid {color_hex}; border-radius: 15px; padding: 30px; margin-bottom: 30px; box-shadow: 0 6px 15px rgba(0,0,0,0.1);"><h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 12px; font-weight: 800;">{title}</h2><div style="font-size: 19px; line-height: 2.0; color: #34495e;">{text}</div></div>"""

# --- 4. HÀM ÂM THANH BASE64 CHO IPAD (FIX IMAGE.PNG) ---
async def generate_pro_voice(text, voice="en-US-EmmaNeural", rate="-20%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def play_pro_audio(text, speed="Normal"):
    rate = "-40%" if speed == "Slow" else "-20%"
    voice = "en-US-AndrewNeural" if "Tom:" in text or "A:" in text else "en-US-EmmaNeural"
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    audio_bytes = loop.run_until_complete(generate_pro_voice(text, voice=voice, rate=rate))
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f"""<audio controls style="width: 100%;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>""", unsafe_allow_html=True)

# --- 5. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Academy Supreme V87", layout="wide")
if 'html_vocab' not in st.session_state:
    st.session_state.update({'html_vocab':"", 'html_p1':"", 'html_p2':"", 'raw_ans':"", 'ket_qua':"", 'start_time': None, 'listening_text': ""})

with st.sidebar:
    st.title("🛡️ SUPREME V87")
    ten_hs = st.text_input("Chào cậu chủ:", "Cua")
    mon = st.selectbox("🎯 Môn học:", ["🇬🇧 Tiếng Anh 4", "🧮 Toán 4"])
    
    if "Anh" in mon:
        unit = st.number_input("Chọn Unit (11-15):", 11, 15, 11)
        data_u = ENGLISH_BOOK_MAP.get(unit)
        chu_de = f"{data_u['topic']}"; do_kho = "Standard"
    else:
        hk = st.radio("Chọn kỳ học:", ["Học kỳ 1", "Học kỳ 2"])
        chu_de = st.selectbox("Chủ đề Toán:", MATH_TOPICS[hk])
        do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Khá", "Nâng cao"])
    
    mode = st.radio("Chế độ:", ["🚀 Làm bài mới", "📈 Tiến độ"])

# --- 6. LOGIC RA ĐỀ ĐA TẦNG ---
if mode == "🚀 Làm bài mới":
    st.title(f"🦀 Cậu chủ {ten_hs} - Môn: {mon}")
    if st.button("📝 RA ĐỀ CHI TIẾT (FULL MATH & ENGLISH)"):
        st.session_state.update({'html_vocab':"", 'html_p1':"", 'html_p2':"", 'ket_qua':"", 'start_time': datetime.now()})
        with st.spinner("AI đang soạn ma trận kiến thức..."):
            if "Anh" in mon:
                # Logic Anh ngữ chuyên sâu từ vựng (V86)
                vocab_list = ENGLISH_BOOK_MAP[unit]['vocab']
                sys_eng = "Native Teacher. 100% English. NO Vietnamese."
                v_content = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Create 3 vocab exercises for: {vocab_list}."}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['html_vocab'] = process_text_to_html(v_content, "🧱 LÒ LUYỆN TỪ VỰNG", "#9b59b6")
                script = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Write 3 sentences using: {vocab_list}."}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['listening_text'] = script
                p1 = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Based on: '{script}', write 2 listening questions."}], model=MODEL_TEXT).choices[0].message.content
                p2 = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Write 3 'Word ordering' questions."}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['html_p1'] = process_text_to_html(p1, "🎧 LUYỆN NGHE HIỂU", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "✍️ LUYỆN VIẾT", "#27ae60")
            else:
                # PHỤC HỒI LOGIC TOÁN (V87 FIX)
                p1 = client.chat.completions.create(messages=[{"role":"user","content":f"Soạn 6 câu trắc nghiệm Toán 4 {chu_de}, {do_kho}. Trình bày đẹp. NO ANSWERS."}], model=MODEL_TEXT).choices[0].message.content
                p2 = client.chat.completions.create(messages=[{"role":"user","content":f"Soạn 3 câu tự luận Toán 4 {chu_de}, {do_kho}. Giải bài toán có lời văn. NO ANSWERS."}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['html_p1'] = process_text_to_html(p1, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PHẦN 2: TỰ LUẬN", "#2c3e50")
            
            st.session_state['raw_ans'] = client.chat.completions.create(messages=[{"role":"user","content":f"Giải chi tiết đề sau để chấm điểm:\n{p1}\n{p2}"}], model=MODEL_TEXT).choices[0].message.content
            st.rerun()

    # Hiển thị bài làm
    if st.session_state['html_p1']:
        if st.session_state['html_vocab']: st.markdown(st.session_state['html_vocab'], unsafe_allow_html=True)
        if st.session_state['listening_text']:
            with st.expander("🎧 NGHE HỘI THOẠI"): play_pro_audio(st.session_state['listening_text'])
            with st.expander("📄 XEM TRANSCRIPT"): st.info(st.session_state['listening_text'])
        
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
        
        with st.form("exam_form"):
            st.subheader("✍️ PHIẾU LÀM BÀI")
            tl_user = st.text_area("Cậu chủ điền đáp án và lời giải vào đây nhé:")
            if st.form_submit_button("✅ NỘP BÀI & CHẤM ĐIỂM"):
                with st.spinner("Đang chấm điểm chi tiết..."):
                    tl_check = "BỎ TRỐNG (0 ĐIỂM)" if not tl_user.strip() else f"HS LÀM: '{tl_user}'"
                    prompt = f"Chấm điểm thang 10. Key: {st.session_state['raw_ans']}. HS: {tl_check}. Trả về: 1. ĐÚNG/SAI TỪNG CÂU | 2. DIEM: [Số] | 3. GIẢI THÍCH."
                    st.session_state['ket_qua'] = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=MODEL_TEXT).choices[0].message.content
                st.rerun()

    if st.session_state['ket_qua']:
        st.markdown(process_text_to_html(st.session_state['ket_qua'], "📊 KẾT QUẢ PHÂN TÍCH", "#16a085"), unsafe_allow_html=True)
