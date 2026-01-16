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

# --- 1. CẤU HÌNH CỐT LÕI ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# --- 2. BOOK MAP CHUẨN (CẬP NHẬT TỪ 1000041417.jpg) ---
ENGLISH_BOOK_MAP = {
    11: {"topic": "My home", "vocab": "road, street, big, busy, live, noisy, quiet", "focus": "Where someone lives"},
    12: {"topic": "Jobs", "vocab": "actor, farmer, nurse, office worker, policeman", "focus": "Jobs and workplaces"},
    13: {"topic": "Appearance", "vocab": "big, short, slim, tall, eyes, face", "focus": "Descriptions"},
    14: {"topic": "Daily activities", "vocab": "watch TV, cooking, wash clothes", "focus": "Routines"},
    15: {"topic": "My family's weekends", "vocab": "cinema, shopping centre, swimming pool", "focus": "Weekend activities"}
}

# --- 3. HÀM DỮ LIỆU & HIỂN THỊ (V86) ---
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
    # FIX V86: Sử dụng \1 an toàn (Fix image_f84e85.png)
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
st.set_page_config(page_title="Academy Supreme V86", layout="wide")
if 'html_vocab' not in st.session_state:
    st.session_state.update({'html_vocab':"", 'html_p1':"", 'html_p2':"", 'raw_ans':"", 'ket_qua':"", 'start_time': None, 'listening_text': ""})

with st.sidebar:
    st.title("🛡️ SUPREME V86")
    ten_hs = st.text_input("Chào cậu chủ:", "Cua")
    mon = st.selectbox("🎯 Môn học:", ["🇬🇧 Tiếng Anh 4", "🧮 Toán 4"])
    if "Anh" in mon:
        unit = st.number_input("Chọn Unit (11-15):", 11, 15, 11)
        data_u = ENGLISH_BOOK_MAP.get(unit)
        chu_de = f"{data_u['topic']}"
    else:
        chu_de = "Toán Lớp 4"
    mode = st.radio("Chế độ:", ["🚀 Làm bài mới", "📈 Tiến độ"])

# --- 6. LOGIC RA ĐỀ ĐA TẦNG (TỪ VỰNG -> NGHE) ---
if mode == "🚀 Làm bài mới":
    if st.button("📝 RA ĐỀ TẬP TRUNG TỪ VỰNG"):
        st.session_state.update({'html_vocab':"", 'html_p1':"", 'html_p2':"", 'ket_qua':"", 'start_time': datetime.now()})
        with st.spinner("AI đang soạn lộ trình từ vựng & bài nghe..."):
            vocab_list = ENGLISH_BOOK_MAP[unit]['vocab']
            sys_eng = "Native Teacher. 100% English. Focus on vocabulary recognition."
            
            # PHẦN 1: LÒ LUYỆN TỪ VỰNG (NEW)
            v_prompt = f"Create 3 simple vocabulary exercises (e.g., scrambled letters, fill in missing letters) for these words: {vocab_list}."
            v_content = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":v_prompt}], model=MODEL_TEXT).choices[0].message.content
            st.session_state['html_vocab'] = process_text_to_html(v_content, "🧱 VÀNG LỬA: LÒ LUYỆN TỪ VỰNG", "#9b59b6")
            
            # PHẦN 2: BÀI NGHE RÚT GỌN
            script = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Write 3 short English sentences using: {vocab_list}."}], model=MODEL_TEXT).choices[0].message.content
            st.session_state['listening_text'] = script
            p1 = client.chat.completions.create(messages=[{"role":"system","content":sys_eng},{"role":"user","content":f"Based on: '{script}', write 2 listening questions."}], model=MODEL_TEXT).choices[0].message.content
            st.session_state['html_p1'] = process_text_to_html(p1, "🎧 LUYỆN NGHE HIỂU", "#e67e22")
            
            st.session_state['raw_ans'] = client.chat.completions.create(messages=[{"role":"user","content":f"Solve this:\n{v_content}\n{p1}"}], model=MODEL_TEXT).choices[0].message.content
            st.rerun()

    if st.session_state['html_vocab']:
        st.markdown(st.session_state['html_vocab'], unsafe_allow_html=True)
        
        if st.session_state['listening_text']:
            with st.expander("🎧 BẤM ĐỂ NGHE (TỐC ĐỘ CHẬM)"): 
                play_pro_audio(st.session_state['listening_text'])
            with st.expander("📄 XEM TRANSCRIPT"): st.info(st.session_state['listening_text'])
            
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        
        with st.form("exam_form"):
            st.subheader("✍️ PHIẾU LÀM BÀI")
            tl_user = st.text_area("Cậu chủ điền từ vựng và câu trả lời vào đây nhé:")
            if st.form_submit_button("✅ NỘP BÀI & CHẤM ĐIỂM CHI TIẾT"):
                with st.spinner("Đang chấm điểm..."):
                    prompt = f"Chấm điểm thang 10. Chú trọng vào từ vựng đúng chính tả. HS làm: '{tl_user}'. Key: {st.session_state['raw_ans']}"
                    st.session_state['ket_qua'] = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=MODEL_TEXT).choices[0].message.content
                st.rerun()

    if st.session_state['ket_qua']:
        st.markdown(process_text_to_html(st.session_state['ket_qua'], "📊 KẾT QUẢ PHÂN TÍCH", "#16a085"), unsafe_allow_html=True)
