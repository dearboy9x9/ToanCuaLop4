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
from streamlit_mic_recorder import mic_recorder
import random
import time

# --- 1. CẤU HÌNH HỆ THỐNG (API KEY MỚI CỦA ÔNG CHỦ) ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# --- 2. MA TRẬN KIẾN THỨC CHUẨN (BOOK MAP 1000041417.jpg) ---
ENGLISH_BOOK_MAP = {
    11: {"topic": "My home", "vocab": "road, street, big, busy, live, noisy, quiet", "focus": "Where someone lives"},
    12: {"topic": "Jobs", "vocab": "actor, farmer, nurse, office worker, policeman", "focus": "Jobs and workplaces"},
    13: {"topic": "Appearance", "vocab": "big, short, slim, tall, eyes, face", "focus": "Descriptions"},
    14: {"topic": "Daily activities", "vocab": "watch TV, cooking, wash clothes, afternoon", "focus": "Routines"},
    15: {"topic": "My family's weekends", "vocab": "cinema, shopping centre, swimming pool, tennis", "focus": "Weekend activities"},
}

# --- 3. HÀM DỮ LIỆU & HIỂN THỊ (V84 FIX LỖI REF \1) ---
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
    # FIX V84: Sửa \2 thành \1 để tránh re.PatternError
    text = re.sub(r'(Câu \d+[:\.])', r'<br><b style="color: #d35400; font-size: 1.2em; display: inline-block; margin-top: 15px;">\1</b>', text)
    return f"""<div style="background-color: #fff; border-left: 10px solid {color_hex}; border-radius: 15px; padding: 30px; margin-bottom: 30px; box-shadow: 0 6px 15px rgba(0,0,0,0.1);"><h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 12px; font-weight: 800;">{title}</h2><div style="font-size: 19px; line-height: 2.0; color: #34495e;">{text}</div></div>"""

# --- 4. HÀM ÂM THANH IPAD READY ---
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
    st.audio(io.BytesIO(audio_bytes), format='audio/mp3')

# --- 5. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Academy V84", layout="wide")
if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'ket_qua':"", 'start_time': None, 'listening_text': ""})

with st.sidebar:
    st.title("🛡️ SUPREME V84")
    ten_hs = st.text_input("Chào cậu chủ:", "Cua")
    df_h = load_data(); st.metric("💰 Cua Coins", df_h['Coins'].sum() if 'Coins' in df_h.columns else 0)
    mon = st.selectbox("🎯 Môn học:", ["🇬🇧 Tiếng Anh 4", "🧮 Toán 4"])
    if "Anh" in mon:
        unit = st.number_input("Unit (11-20):", 11, 20, 11)
        data_u = ENGLISH_BOOK_MAP.get(unit)
        chu_de = f"{data_u['topic']} (Vocab: {data_u['vocab']})"; do_kho = "Standard"
    else:
        hk = st.radio("Kỳ học:", ["Học kỳ 1", "Học kỳ 2"])
        chu_de = "Phân số & Giải toán" if hk=="Học kỳ 2" else "Số tự nhiên"; do_kho = "Khá"
    mode = st.radio("Chế độ:", ["🚀 Làm bài mới", "🎙️ Luyện phát âm", "📈 Tiến độ"])

# --- 6. LOGIC RA ĐỀ ---
if mode == "🚀 Làm bài mới":
    if st.button("📝 RA ĐỀ CHUẨN (FIX ERROR)"):
        st.session_state.update({'html_p1':"", 'html_p2':"", 'ket_qua':"", 'start_time': datetime.now()})
        with st.spinner("AI đang soạn đề..."):
            if "Anh" in mon:
                sys_eng = "Native Teacher. 100% English. NO Vietnamese."
                script = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Write 4 sentences for Grade 4 about {chu_de}."}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['listening_text'] = script
                p1 = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Based on: '{script}', write 2 listening & 4 MCQ questions."}], model=MODEL_TEXT).choices[0].message.content
                p2 = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Write 3 'Word ordering' questions."}], model=MODEL_TEXT).choices[0].message.content
                # Dòng 94 - Nơi gây ra lỗi trong image_f84e85.png
                st.session_state['html_p1'] = process_text_to_html(p1, "PART 1: LISTENING & QUIZ", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PART 2: WRITING", "#27ae60")
            else:
                p1 = client.chat.completions.create(messages=[{"role":"user","content":f"Soạn 6 câu trắc nghiệm Toán 4 {chu_de}."}], model=MODEL_TEXT).choices[0].message.content
                p2 = client.chat.completions.create(messages=[{"role":"user","content":f"Soạn 3 câu tự luận Toán 4 {chu_de}."}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['html_p1'] = process_text_to_html(p1, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PHẦN 2: TỰ LUẬN", "#2c3e50")
            
            st.session_state['raw_ans'] = client.chat.completions.create(messages=[{"role":"user","content":f"Solve this:\n{p1}\n{p2}"}], model=MODEL_TEXT).choices[0].message.content
            st.rerun()

    if st.session_state['html_p1']:
        if st.session_state['listening_text']:
            with st.expander("🎧 BẤM ĐỂ NGHE (IPAD READY)"): 
                play_pro_audio(st.session_state['listening_text'])
            with st.expander("📄 XEM TRANSCRIPT"): st.info(st.session_state['listening_text'])
        
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
