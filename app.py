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

# --- 2. BẢN ĐỒ KIẾN THỨC & HÌNH ẢNH ---
ENGLISH_DATA = {
    11: {"topic": "My family's jobs", "img": "https://img.freepik.com/premium-vector/group-people-various-occupations-standing-together_53500-163.jpg"},
    12: {"topic": "Jobs and workplaces", "img": "https://img.freepik.com/premium-vector/hospital-factory-school-office-buildings_1639-12345.jpg"},
    13: {"topic": "Appearance", "img": "https://img.freepik.com/free-vector/people-with-different-body-shapes_23-2148813358.jpg"},
    14: {"topic": "Daily activities", "img": "https://img.freepik.com/free-vector/daily-routine-concept-with-boy_23-2148476147.jpg"},
    15: {"topic": "My family's weekend", "img": "https://img.freepik.com/free-vector/family-enjoying-weekend-activities_23-2148530412.jpg"}
}

# --- 3. HÀM TIỆN ÍCH CHUYÊN GIA ---
async def generate_voice(text, rate="-10%"):
    communicate = edge_tts.Communicate(text, "en-US-EmmaNeural", rate=rate)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def play_audio(text, speed="Normal"):
    rate = "-35%" if speed == "Slow" else "-5%"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio_data = loop.run_until_complete(generate_voice(text, rate))
    st.audio(audio_data, format='audio/mp3')

def call_ai(prompt, system="Giáo viên chuyên gia 20 năm."):
    chat = client.chat.completions.create(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        model=MODEL_TEXT, temperature=0.5
    )
    return chat.choices[0].message.content

def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["Time", "Mon", "Diem", "Coins", "Yeu"])
    return pd.read_csv(DATA_FILE)

# --- 4. GIAO DIỆN SUPREME ---
st.set_page_config(page_title="Học Viện Cua V65", layout="wide")

# Khởi tạo session
if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'listening_text':"", 'coins': 0, 'warmup': False})

with st.sidebar:
    st.title("🛡️ SUPREME ACADEMY")
    ten = st.text_input("Chào cậu chủ:", "Cua")
    
    df_history = load_data()
    total_coins = df_history['Coins'].sum() if not df_history.empty else 0
    st.markdown(f"### 💰 Cua Coins: {total_coins}")
    st.markdown("---")
    
    mon = st.selectbox("🎯 Môn học:", ["🧮 Toán Lớp 4", "🇬🇧 Tiếng Anh 4"])
    mode = st.radio("🕹️ Chức năng:", ["🚀 Bài thi chính", "⚡ Khởi động tính nhẩm", "🎙️ Luyện phát âm"])
    
    if "Toán" in mon:
        dang = st.selectbox("Dạng đề:", ["Luyện tập Unit", "Thi HK1", "Thi HK2"])
        chu_de = st.selectbox("Chủ đề:", ["Tổng hợp", "Hình học", "Số tự nhiên", "4 Phép tính"])
        do_kho = st.select_slider("Độ khó:", ["Dễ", "Trung bình", "Khó"])
    else:
        unit = st.number_input("Chọn Unit (11-20):", 11, 20, 11)
        data = ENGLISH_DATA.get(unit, {"topic": "General", "img": ""})
        chu_de = data['topic']
        img_url = data['img']

# --- 5. LOGIC CHỨC NĂNG ---

# A. KHỞI ĐỘNG TÍNH NHẨM
if mode == "⚡ Khởi động tính nhẩm":
    st.subheader("⚡ THỬ THÁCH TÍNH NHẨM 120 GIÂY")
    if st.button("BẮT ĐẦU CHẠY!"):
        st.session_state['warmup'] = True
        st.session_state['wm_score'] = 0
        st.session_state['start_wm'] = time.time()
        
    if st.session_state.get('warmup'):
        elapsed = time.time() - st.session_state['start_wm']
        if elapsed < 120:
            st.metric("⏳ Thời gian còn lại", f"{int(120 - elapsed)} giây")
            # Sinh phép tính ngẫu nhiên
            a, b = random.randint(10, 99), random.randint(10, 99)
            st.write(f"### {a} + {b} = ?")
            ans_input = st.number_input("Kết quả:", key=f"wm_{int(elapsed)}")
            if ans_input == (a + b):
                st.session_state['wm_score'] += 1
                st.success("Đúng rồi!")
        else:
            st.session_state['warmup'] = False
            st.balloons()
            st.success(f"Chúc mừng! Cậu chủ đã làm được {st.session_state['wm_score']} phép tính!")

# B. BÀI THI CHÍNH
elif mode == "🚀 Bài thi chính":
    st.title(f"🦀 Cậu chủ {ten} ơi, sẵn sàng chưa?")
    if st.button("📝 RA ĐỀ NGAY"):
        st.session_state['start_time'] = datetime.now()
        with st.spinner("AI đang soạn đề thi chuẩn..."):
            if "Toán" in mon:
                p1 = call_ai(f"Soạn 6 câu trắc nghiệm Toán 4, chủ đề {chu_de}, độ khó {do_kho}.")
                p2 = call_ai(f"Soạn 3 câu tự luận Toán 4 {chu_de}.")
            else:
                script = call_ai(f"Write a 4-sentence dialogue about {chu_de} for Grade 4.")
                st.session_state['listening_text'] = script
                p1 = call_ai(f"Based on: '{script}', write 2 listening and 4 multiple choice questions.")
                p2 = call_ai(f"Write 3 'Reorder words' sentences about {chu_de}.")
            
            st.session_state['html_p1'] = p1
            st.session_state['html_p2'] = p2
            st.session_state['raw_ans'] = call_ai(f"Giải chi tiết:\n{p1}\n{p2}")
            st.rerun()

    if st.session_state['html_p1']:
        if "Tiếng Anh" in mon and img_url:
            st.image(img_url, caption=f"🖼️ Từ điển hình ảnh: {chu_de}", width=500)
            
        if st.session_state['listening_text']:
            with st.expander("🎧 NGHE HỘI THOẠI"):
                play_audio(st.session_state['listening_text'])
                if st.button("🐢 Nghe chậm"): play_audio(st.session_state['listening_text'], speed="Slow")

        st.markdown(f"### 📍 {mon.upper()} - {chu_de}")
        st.write(st.session_state['html_p1'])
        st.divider()
        st.write(st.session_state['html_p2'])
        
        # Phiếu làm bài
        ans = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"exam_{i}") for i in range(6)]
        tl = st.text_area("Bài làm tự luận:")

        if st.button("✅ NỘP BÀI"):
            with st.spinner("Chấm điểm và tặng quà..."):
                prompt = f"Chấm bài. Key: {st.session_state['raw_ans']}. HS: {ans}, {tl}. Return: DIEM: [số], YEU: []"
                res = call_ai(prompt)
                st.success(res)
                score = int(re.search(r"DIEM:\s*(\d+)", res).group(1))
                coins = 10 if score == 10 else (5 if score >= 8 else 0)
                
                # Lưu log
                df = load_data()
                new_row = {"Time": datetime.now(), "Mon": mon, "Diem": score, "Coins": coins, "Yeu": "Cần luyện thêm"}
                pd.concat([df, pd.DataFrame([new_row])]).to_csv(DATA_FILE, index=False)
                
                if score == 10: 
                    st.balloons()
                    st.success(f"🏆 TUYỆT VỜI! CẬU CHỦ NHẬN ĐƯỢC 1 HUY CHƯƠNG VÀNG & {coins} COINS!")
