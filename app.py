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
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from streamlit_mic_recorder import mic_recorder
import random
import time

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# Thông tin Email (Bố Kiên cập nhật tại đây)
EMAIL_GUI = "cua.hoc.toan.ai@gmail.com" 
EMAIL_NHAN = "kien.nguyen@example.com" 
MAT_KHAU_APP = "xxxx xxxx xxxx xxxx" 

# --- 2. MA TRẬN KIẾN THỨC ---
MATH_TOPICS = {
    "Học kỳ 1": ["Số tự nhiên hàng triệu", "4 phép tính", "Trung bình cộng", "Tổng - Hiệu", "Góc & Đường thẳng", "Yến, tạ, tấn, giây"],
    "Học kỳ 2": ["Phân số & Phép tính phân số", "Tổng - Tỉ", "Hiệu - Tỉ", "Hình bình hành & Thoi", "Diện tích mm2, dm2", "Thống kê & Xác suất"]
}
ENGLISH_UNITS = {i: f"Unit {i}" for i in range(1, 21)}

# --- 3. HÀM DỮ LIỆU & HIỂN THỊ ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Time", "Mon", "Diem", "Coins", "Yeu", "Phut"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    df = pd.read_csv(DATA_FILE)
    for col in ["Coins", "Phut", "Diem"]:
        if col not in df.columns: df[col] = 0
    return df

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    text = text.replace("直", "vuông").strip()
    text = re.sub(r'\n{2,}', '<br><br>', text)
    text = text.replace('\n', '<br>')
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', 
                  r'\1<br><b style="color: #d35400; font-size: 1.15em; display: inline-block; margin-top: 15px;">\2</b>', text)
    return f"""<div style="background-color: #fff; border-left: 10px solid {color_hex}; border-radius: 15px; padding: 30px; margin-bottom: 30px; box-shadow: 0 6px 15px rgba(0,0,0,0.1);"><h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 12px; font-weight: 800;">{title}</h2><div style="font-size: 18px; line-height: 2.0; color: #34495e;">{text}</div></div>"""

# --- 4. HÀM AI & ÂM THANH ---
async def generate_pro_voice(text, rate="-10%"):
    communicate = edge_tts.Communicate(text, "en-US-EmmaNeural", rate=rate)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def play_pro_audio(text, speed="Normal"):
    rate = "-35%" if speed == "Slow" else "-5%"
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    audio_data = loop.run_until_complete(generate_pro_voice(text, rate=rate))
    st.audio(audio_data, format='audio/mp3')

def call_ai_strict(prompt, system="Giáo viên chuyên gia."):
    chat = client.chat.completions.create(messages=[{"role":"system","content":system},{"role":"user","content":prompt}], model=MODEL_TEXT, temperature=0.5)
    return chat.choices[0].message.content

# --- 5. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Gia Sư AI V73", layout="wide")
if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'ket_qua':"", 'start_time': None, 'listening_text': ""})

with st.sidebar:
    st.title("🛡️ SUPREME V73")
    ten_hs = st.text_input("Học sinh:", "Cua")
    df_h = load_data(); st.metric("💰 Cua Coins", df_h['Coins'].sum())
    mon_hoc = st.selectbox("🎯 Môn học:", ["🧮 Toán 4", "🇬🇧 Tiếng Anh 4"])
    
    if "Toán" in mon_hoc:
        hk = st.radio("Kỳ học:", ["Học kỳ 1", "Học kỳ 2"])
        chu_de = st.selectbox("Chủ đề:", MATH_TOPICS[hk]); do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Vận dụng", "Nâng cao"])
    else:
        unit = st.number_input("Unit (1-20):", 1, 20, 11); chu_de = ENGLISH_UNITS[unit]; do_kho = "Standard"

    mode = st.radio("Chế độ:", ["🚀 Làm bài mới", "⚡ Tính nhẩm", "🎙️ Luyện phát âm", "📈 Tiến độ"])

# --- 6. LOGIC XỬ LÝ CHÍNH ---
if mode == "🚀 Làm bài mới":
    st.title(f"🦀 Chào cậu chủ {ten_hs}!")
    
    # Nút ra đề luôn xóa kết quả cũ
    if st.button("📝 RA ĐỀ MỚI"):
        st.session_state.update({'html_p1':"", 'html_p2':"", 'ket_qua':"", 'start_time': datetime.now()})
        with st.spinner("AI đang soạn đề..."):
            if "Toán" in mon_hoc:
                p1 = call_ai_strict(f"Soạn 6 câu trắc nghiệm Toán 4 {chu_de}, {do_kho}. NO ANSWERS.")
                p2 = call_ai_strict(f"Soạn 3 câu tự luận Toán 4 {chu_de}. NO ANSWERS.")
                st.session_state['html_p1'] = process_text_to_html(p1, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PHẦN 2: TỰ LUẬN", "#2c3e50")
            else:
                script = call_ai_strict(f"Write a 4-sentence dialogue about {chu_de}.")
                st.session_state['listening_text'] = script
                p1 = call_ai_strict(f"Based on: '{script}', write 2 listening & 4 grammar questions. NO ANSWERS.")
                p2 = call_ai_strict(f"Write 3 'Word ordering' questions. NO ANSWERS.")
                st.session_state['html_p1'] = process_text_to_html(p1, "PART 1: LISTENING", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PART 2: WRITING", "#27ae60")
            st.session_state['raw_ans'] = call_ai_strict(f"Giải chi tiết đề này để chấm bài:\n{p1}\n{p2}")
            st.rerun()

    if st.session_state['html_p1']:
        if st.session_state['listening_text']:
            with st.expander("🎧 NGHE ĐOẠN VĂN"): play_pro_audio(st.session_state['listening_text'])
        
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
        
        # SỬ DỤNG FORM ĐỂ ỔN ĐỊNH VIỆC NỘP BÀI
        with st.form("exam_form"):
            st.subheader("✍️ PHIẾU LÀM BÀI")
            ans = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
            tl_user = st.text_area("Lời giải tự luận:")
            submit = st.form_submit_button("✅ NỘP BÀI & CHẤM ĐIỂM")

            if submit:
                with st.spinner("Đang chấm bài..."):
                    prompt = f"Chấm bài. Key: {st.session_state['raw_ans']}. HS: {ans}, {tl_user}."
                    res = call_ai_strict(prompt, "Giáo viên chấm thi tận tâm.")
                    st.session_state['ket_qua'] = res # Lưu kết quả vào session
                    
        # Hiển thị kết quả bên ngoài form để không bị mất khi rerun
        if st.session_state['ket_qua']:
            st.divider()
            st.markdown(process_text_to_html(st.session_state['ket_qua'], "📊 KẾT QUẢ VÀ GIẢI THÍCH CHI TIẾT", "#16a085"), unsafe_allow_html=True)
            if "10" in st.session_state['ket_qua']: st.balloons()
