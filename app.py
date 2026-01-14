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

# --- 2. BẢN ĐỒ KIẾN THỨC TOÁN 4 CÁNH DIỀU (V67 UPDATED) ---
MATH_TOPICS = {
    "Học kỳ 1": [
        "Số tự nhiên đến hàng triệu",
        "Cộng, trừ, nhân, chia số có nhiều chữ số",
        "Tìm số trung bình cộng",
        "Góc nhọn, góc tù, góc bẹt",
        "Đường thẳng vuông góc, song song",
        "Yến, tạ, tấn, giây, thế kỷ"
    ],
    "Học kỳ 2": [
        "Phân số và các phép tính phân số",
        "Hình bình hành và Hình thoi",
        "Thống kê và Biểu đồ cột",
        "Làm quen với xác suất/khả năng",
        "Ôn tập cuối năm"
    ]
}

ENGLISH_UNITS = {
    i: f"Unit {i}: {name}" for i, name in enumerate([
        "", "My friends", "Time/Routines", "My week", "My birthday", "Things we can do",
        "School facilities", "School subjects", "What are you reading?", "Sports day",
        "Yesterday", "Family's jobs", "Jobs/Workplaces", "Appearance", "Daily activities",
        "Weekend", "Weather", "Toy store", "Favourite food/drink", "My city", "Summer camp"
    ]) if i > 0
}

# --- 3. HÀM XỬ LÝ DỮ LIỆU ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Time", "Mon", "Diem", "Coins", "Yeu", "Tot", "Phut"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    df = pd.read_csv(DATA_FILE)
    # Vá lỗi cột Coins (image_c435b1.png)
    for col in ["Coins", "Phut", "Diem"]:
        if col not in df.columns: df[col] = 0
    return df

# --- 4. HÀM AI & ÂM THANH ---
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

def call_ai_strict(prompt, system="Giáo viên chuyên gia."):
    chat = client.chat.completions.create(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        model=MODEL_TEXT, temperature=0.5
    )
    return chat.choices[0].message.content

# --- 5. GIAO DIỆN SIDEBAR ---
st.set_page_config(page_title="Học Viện Cua V67", layout="wide")

if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'listening_text':"", 'start_time': None})

with st.sidebar:
    st.title("🛡️ SUPREME V67")
    ten_hs = st.text_input("Chào cậu chủ:", "Cua")
    
    df_h = load_data()
    total_c = df_h['Coins'].sum() if 'Coins' in df_h.columns else 0
    st.metric("💰 Cua Coins", total_c)
    
    mon_hoc = st.selectbox("🎯 Chọn môn học:", ["🧮 Toán 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    
    if "Toán" in mon_hoc:
        hoc_ky = st.radio("Chọn kỳ học:", ["Học kỳ 1", "Học kỳ 2"])
        chu_de = st.selectbox("Chủ đề bám sát SGK:", MATH_TOPICS[hoc_ky])
        do_kho = st.select_slider("Độ khó đề thi:", ["Cơ bản", "Vận dụng", "Nâng cao"])
    else:
        unit_num = st.number_input("Chọn Unit (1-20):", 1, 20, 11)
        chu_de = ENGLISH_UNITS[unit_num]
        do_kho = "Chuẩn Global Success"

    chuc_nang = st.radio("Chế độ:", ["🚀 Làm bài mới", "⚡ Tính nhẩm", "🎙️ Luyện phát âm", "📈 Tiến độ"])

# --- 6. LOGIC RA ĐỀ ---
if chuc_nang == "🚀 Làm bài mới":
    st.title(f"🦀 Cậu chủ {ten_hs} ơi!")
    if st.button("📝 RA ĐỀ BÁM SÁT CHƯƠNG TRÌNH"):
        st.session_state['start_time'] = datetime.now()
        with st.spinner("AI đang nghiên cứu SGK để soạn đề..."):
            if "Toán" in mon_hoc:
                prompt_tn = f"Soạn 6 câu trắc nghiệm Toán 4 Cánh Diều, {hoc_ky}, chủ đề {chu_de}, độ khó {do_kho}. Format: Câu 1: ... A. B. C. D."
                prompt_tl = f"Soạn 3 câu tự luận Toán 4 {chu_de} bám sát đề thi thực tế. Không đáp án."
                p1 = call_ai_strict(prompt_tn, "Giáo viên Toán VN. Chỉ dùng Tiếng Việt.")
                p2 = call_ai_strict(prompt_tl, "Giáo viên Toán VN. Chỉ dùng Tiếng Việt.")
            else:
                script = call_ai_strict(f"Write a 4-sentence English dialogue about {chu_de} for Grade 4.", "English Teacher")
                st.session_state['listening_text'] = script
                p1 = call_ai_strict(f"Based on: '{script}', write 2 listening and 4 grammar questions about {chu_de}. English only.")
                p2 = call_ai_strict(f"Write 3 'Reorder words' sentences about {chu_de}.")
            
            st.session_state['html_p1'] = p1
            st.session_state['html_p2'] = p2
            st.session_state['raw_ans'] = call_ai_strict(f"Giải chi tiết đề sau:\n{p1}\n{p2}")
            st.rerun()

    if st.session_state['html_p1']:
        st.info(f"📍 Đề luyện tập: {chu_de}")
        if st.session_state['listening_text']:
            with st.expander("🎧 NGHE HỘI THOẠI"):
                play_pro_audio(st.session_state['listening_text'])
        
        st.write(st.session_state['html_p1'])
        st.write(st.session_state['html_p2'])
        
        ans = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
        tl_user = st.text_area("Bài làm tự luận (Có thể để trống):")

        if st.button("✅ NỘP BÀI"):
            phut = round((datetime.now() - st.session_state['start_time']).total_seconds()/60, 1)
            with st.spinner("Đang chấm bài..."):
                prompt = f"Chấm bài. Key: {st.session_state['raw_ans']}. HS: {ans}, {tl_user}. Trả về format: DIEM: [số], YEU: [phần yếu], GIẢI THÍCH: [chi tiết tiếng Việt]"
                res = call_ai_strict(prompt)
                st.success(res)
                score = int(re.search(r"DIEM:\s*(\d+)", res).group(1))
                coins = 10 if score == 10 else (5 if score >= 8 else 0)
                # Lưu vào lịch sử (Hàm lưu ở bản V66)
                st.session_state['coins'] = coins
                if score >= 8: st.balloons()

# (Các phần Tính nhẩm, Phát âm, Tiến độ giữ nguyên logic V66)
