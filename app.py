# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq
import pandas as pd
import os
from datetime import datetime
import re
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

# --- 2. MA TRẬN KIẾN THỨC CÁNH DIỀU & GLOBAL SUCCESS ---
MATH_TOPICS = {
    "Học kỳ 1": [
        "Số tự nhiên đến hàng triệu", "4 phép tính (Cộng, trừ, nhân, chia)",
        "Số trung bình cộng", "Góc (nhọn, tù, bẹt)", "Song song & Vuông góc", "Yến, tạ, tấn, giây, thế kỷ"
    ],
    "Học kỳ 2": [
        "Phân số & Phép tính phân số", "Hình bình hành & Hình thoi",
        "Thống kê & Biểu đồ cột", "Xác suất & Khả năng", "Ôn tập tổng hợp"
    ]
}

ENGLISH_UNITS = {i: f"Unit {i}" for i in range(1, 21)}

# --- 3. HÀM XỬ LÝ HIỂN THỊ (QUYẾT ĐỊNH ĐỘ ĐẸP) ---
def process_text_to_html(text, title, color_hex):
    """Biến văn bản thô thành HTML có khung, giãn cách khoa học."""
    if not text: return ""
    # Dọn dẹp rác ký tự
    text = text.replace("直", "vuông").strip()
    
    # Ép xuống dòng khoa học
    text = re.sub(r'\n{2,}', '<br><br>', text)
    text = text.replace('\n', '<br>')
    
    # IN ĐẬM CÂU HỎI (MÀU CAM ĐẬM)
    # Tìm kiếm: Câu 1: hoặc 1.
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', 
                  r'\1<br><b style="color: #d35400; font-size: 1.1em; display: inline-block; margin-bottom: 5px;">\2</b>', text)
    
    # Khung bao bọc
    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; background-color: #fff; 
                border: 2px solid {color_hex}; border-radius: 12px; 
                padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
        <h2 style="color: {color_hex}; margin-top: 0; border-bottom: 3px solid {color_hex}; 
                   padding-bottom: 10px; text-transform: uppercase; font-weight: 900;">
            {title}
        </h2>
        <div style="font-size: 17px; line-height: 1.8; color: #2c3e50;">
            {text}
        </div>
    </div>
    """
    return html

# --- 4. HÀM LOAD DỮ LIỆU (FIX LỖI COINS) ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["Time", "Mon", "Diem", "Coins", "Yeu", "Tot", "Phut"])
    df = pd.read_csv(DATA_FILE)
    for col in ["Coins", "Phut", "Diem"]:
        if col not in df.columns: df[col] = 0
    return df

# --- 5. HÀM AI & ÂM THANH ---
async def generate_pro_voice(text, rate="-10%"):
    communicate = edge_tts.Communicate(text, "en-US-EmmaNeural", rate=rate)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def play_pro_audio(text, speed="Normal"):
    rate = "-35%" if speed == "Slow" else "-5%"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio_data = loop.run_until_complete(generate_pro_voice(text, rate=rate))
    st.audio(audio_data, format='audio/mp3')

def call_ai_strict(prompt, system="Giáo viên chuyên môn cao."):
    chat = client.chat.completions.create(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        model=MODEL_TEXT, temperature=0.5
    )
    return chat.choices[0].message.content

# --- 6. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Gia Sư AI V68", layout="wide")

if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'listening_text':"", 'start_time': None})

with st.sidebar:
    st.markdown(f"## 🏛️ ACADEMY V68")
    ten_hs = st.text_input("Chào cậu chủ:", "Cua")
    
    df_h = load_data()
    total_c = df_h['Coins'].sum() if 'Coins' in df_h.columns else 0
    st.metric("💰 Cua Coins Tích Lũy", total_c)
    
    mon_hoc = st.selectbox("🎯 Chọn môn học:", ["🧮 Toán 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    
    if "Toán" in mon_hoc:
        hoc_ky = st.radio("Chọn kỳ học:", ["Học kỳ 1", "Học kỳ 2"])
        chu_de = st.selectbox("Chủ đề bám sát SGK:", MATH_TOPICS[hoc_ky])
        do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Vận dụng", "Nâng cao"])
    else:
        unit_num = st.number_input("Chọn Unit (1-20):", 1, 20, 11)
        chu_de = ENGLISH_UNITS[unit_num]
        do_kho = "Standard"

    mode = st.radio("Menu Chức năng:", ["🚀 Làm bài mới", "⚡ Tính nhẩm", "🎙️ Luyện phát âm", "📈 Tiến độ"])

# --- 7. LOGIC RA ĐỀ VÀ HIỂN THỊ ---
if mode == "🚀 Làm bài mới":
    st.title(f"🦀 Cậu chủ {ten_hs} sẵn sàng chưa?")
    if st.button("📝 RA ĐỀ BÀI (FORMAT CHUẨN)"):
        st.session_state['start_time'] = datetime.now()
        with st.spinner("Đang biên soạn đề thi khoa học..."):
            if "Toán" in mon_hoc:
                prompt_tn = f"Soạn 6 câu trắc nghiệm Toán 4 Cánh Diều, {hoc_ky}, chủ đề {chu_de}, độ khó {do_kho}. Format: Câu 1: ... A. B. C. D."
                prompt_tl = f"Soạn 3 câu tự luận Toán 4 {chu_de}. Trình bày khoa học."
                p1 = call_ai_strict(prompt_tn, "Giáo viên Toán VN. Chỉ dùng Tiếng Việt.")
                p2 = call_ai_strict(prompt_tl, "Giáo viên Toán VN. Chỉ dùng Tiếng Việt.")
                st.session_state['html_p1'] = process_text_to_html(p1, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PHẦN 2: TỰ LUẬN", "#2980b9")
            else:
                script = call_ai_strict(f"Write a 4-sentence English dialogue about {chu_de} for Grade 4.", "English Teacher")
                st.session_state['listening_text'] = script
                p1 = call_ai_strict(f"Based on: '{script}', write 2 listening and 4 grammar questions about {chu_de}. A. B. C. D.")
                p2 = call_ai_strict(f"Write 3 'Reorder words' questions about {chu_de}.")
                st.session_state['html_p1'] = process_text_to_html(p1, "PART 1: LISTENING & QUIZ", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PART 2: WRITING", "#27ae60")
            
            st.session_state['raw_ans'] = call_ai_strict(f"Giải chi tiết:\n{p1}\n{p2}")
            st.rerun()

    # HIỂN THỊ ĐỀ TRONG KHUNG HTML (KHÔNG CÒN DẦY DI DÍT)
    if st.session_state['html_p1']:
        if st.session_state['listening_text']:
            with st.expander("🎧 NGHE ĐOẠN VĂN (LISTENING)"):
                play_pro_audio(st.session_state['listening_text'])
        
        # HIỂN THỊ TRẮC NGHIỆM
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        # HIỂN THỊ TỰ LUẬN
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
        
        # Phiếu nộp bài
        ans = [st.radio(f"Chọn đáp án Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
        tl_user = st.text_area("Bài giải tự luận của con:")

        if st.button("✅ NỘP BÀI"):
            with st.spinner("Đang chấm điểm..."):
                prompt = f"Chấm bài. Key: {st.session_state['raw_ans']}. HS: {ans}, {tl_user}."
                res = call_ai_strict(prompt)
                st.success(res)
                if "10" in res: st.balloons()
