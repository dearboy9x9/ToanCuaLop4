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

# --- 3. HÀM XỬ LÝ DỮ LIỆU & VÁ LỖI (V66 FIX) ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Time", "Mon", "Diem", "Coins", "Yeu", "Tot", "Phut"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    
    df = pd.read_csv(DATA_FILE)
    # Tự động vá lỗi thiếu cột Coins hoặc các cột mới (Fix KeyError image_c435b1.png)
    required_cols = ["Time", "Mon", "Diem", "Coins", "Yeu", "Tot", "Phut"]
    changed = False
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0 if col in ["Diem", "Coins", "Phut"] else "N/A"
            changed = True
    if changed:
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    return df

def save_result(mon, diem, coins, phut, tot, yeu, nx):
    df = load_data()
    new_row = {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Mon": mon, "Diem": diem, "Coins": coins, "Phut": phut,
        "Tot": tot, "Yeu": yeu
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 4. HÀM AI & ÂM THANH ---
async def generate_pro_voice(text, voice="en-US-EmmaNeural", rate="-10%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def play_pro_audio(text, speed="Normal"):
    rate = "-35%" if speed == "Slow" else "-5%"
    voice = "en-US-AndrewNeural" if "Tom:" in text or "A:" in text else "en-US-EmmaNeural"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio_data = loop.run_until_complete(generate_pro_voice(text, voice, rate))
    st.audio(audio_data, format='audio/mp3')

def call_ai_strict(prompt, system="Giáo viên chuyên gia. Chỉ dùng Tiếng Việt cho Toán, Tiếng Anh cho Anh văn. Không dùng chữ Hán."):
    chat = client.chat.completions.create(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        model=MODEL_TEXT, temperature=0.5
    )
    return chat.choices[0].message.content

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    text = text.replace("直", "vuông").replace("\n", "<br>")
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', r'\1<b style="color: #d35400; font-size: 1.1em;">\2</b>', text)
    return f"""<div style="background-color: #fff; border: 2px solid {color_hex}; border-radius: 10px; padding: 20px; margin-bottom: 20px;"><h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid {color_hex}; padding-bottom: 10px;">{title}</h2><div style="font-size: 16px; line-height: 1.8;">{text}</div></div>"""

# --- 5. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Gia Sư AI V66", layout="wide")

if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'listening_text':"", 'start_time': None, 'wm_score': 0})

with st.sidebar:
    st.title("🛡️ SUPREME V66")
    ten_hs = st.text_input("Chào cậu chủ:", "Cua")
    
    df_h = load_data()
    total_c = df_h['Coins'].sum() if 'Coins' in df_h.columns else 0
    st.metric("💰 Cua Coins", total_c)
    
    mon_hoc = st.selectbox("🎯 Môn học:", ["🧮 Toán Lớp 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    chuc_nang = st.radio(" Menu:", ["🚀 Bài thi chính", "⚡ Tính nhẩm nhanh", "🎙️ Luyện phát âm", "📈 Xem tiến độ"])
    
    if "Toán" in mon_hoc:
        dang_de = st.selectbox("Dạng đề:", ["Luyện tập Unit", "Thi thử HK1", "Thi thử HK2"])
        chu_de = st.selectbox("Chủ đề:", ["Tổng hợp", "Hình học (Có vẽ hình)", "Số tự nhiên", "4 Phép tính"])
        do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Khá", "Nâng cao"])
    else:
        unit_num = st.number_input("Chọn Unit (1-20):", 1, 20, 11)
        chu_de = ENGLISH_DATA.get(unit_num, {"topic": f"Unit {unit_num}"})['topic']
        img_url = ENGLISH_DATA.get(unit_num, {"img": ""})['img']

# --- 6. LOGIC XỬ LÝ ---
if chuc_nang == "⚡ Tính nhẩm nhanh":
    st.subheader("⚡ THỬ THÁCH 120 GIÂY")
    if st.button("BẮT ĐẦU!"):
        st.session_state['wm_score'] = 0
        st.session_state['wm_start'] = time.time()
        st.rerun()
    
    if 'wm_start' in st.session_state:
        remain = 120 - (time.time() - st.session_state['wm_start'])
        if remain > 0:
            st.write(f"⏳ Còn lại: {int(remain)} giây")
            a, b = random.randint(10, 99), random.randint(10, 99)
            st.write(f"### {a} + {b} = ?")
            # Logic tính điểm đơn giản ở đây
        else:
            st.success("Hết giờ! Cậu chủ giỏi lắm.")

elif chuc_nang == "🚀 Bài thi chính":
    if st.button("📝 RA ĐỀ CHUẨN"):
        st.session_state['start_time'] = datetime.now()
        with st.spinner("AI đang soạn đề..."):
            if "Toán" in mon_hoc:
                tn = call_ai_strict(f"Soạn 6 câu trắc nghiệm Toán 4 {chu_de}, {do_kho}. Trình bày đẹp.")
                tl = call_ai_strict(f"Soạn 3 câu tự luận Toán 4 {chu_de}. Không đáp án.")
                st.session_state['html_p1'] = process_text_to_html(tn, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(tl, "PHẦN 2: TỰ LUẬN", "#2980b9")
                st.session_state['listening_text'] = ""
            else:
                script = call_ai_strict(f"Write a 4-sentence dialogue about {chu_de} for Grade 4.", "English Teacher")
                st.session_state['listening_text'] = script
                tn = call_ai_strict(f"Based on: '{script}', write 2 listening and 4 grammar questions. English only.")
                tl = call_ai_strict(f"Write 3 'Reorder words' sentences about {chu_de}.")
                st.session_state['html_p1'] = process_text_to_html(tn, "PART 1: LISTENING & QUIZ", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(tl, "PART 2: WRITING", "#27ae60")
            
            st.session_state['raw_ans'] = call_ai_strict(f"Giải chi tiết:\n{tn}\n{tl}")
            st.rerun()

    if st.session_state['html_p1']:
        if "Tiếng Anh" in mon_hoc and img_url: st.image(img_url, width=400)
        if st.session_state['listening_text']:
            with st.expander("🎧 NGHE HỘI THOẠI"):
                play_pro_audio(st.session_state['listening_text'])
                if st.button("🐢 Nghe chậm"): play_pro_audio(st.session_state['listening_text'], speed="Slow")
        
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
        
        ans = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
        tl_user = st.text_area("Bài làm tự luận (Có thể để trống):")

        if st.button("✅ NỘP BÀI"):
            phut = round((datetime.now() - st.session_state['start_time']).total_seconds()/60, 1)
            with st.spinner("Đang chấm bài..."):
                prompt = f"Chấm bài. Key: {st.session_state['raw_ans']}. HS: {ans}, {tl_user}. Trả về format: DIEM: [số], TOT: [], YEU: [], NHANXET: [giải thích chi tiết bằng Tiếng Việt]"
                res = call_ai_strict(prompt)
                st.write(res)
                try:
                    score = int(re.search(r"DIEM:\s*(\d+)", res).group(1))
                    coins = 10 if score == 10 else (5 if score >= 8 else 0)
                    save_result(mon_hoc, score, coins, phut, "Tốt", "Cần luyện thêm", res)
                    if score >= 8: st.balloons()
                except: pass

elif chuc_nang == "🎙️ Luyện phát âm":
    st.subheader("🗣️ PHÒNG LUYỆN NÓI")
    txt = st.text_input("Nhập câu luyện nói:", "Where does your father work?")
    if st.button("🔊 Nghe mẫu"): play_pro_audio(txt)
    rec = mic_recorder(start_prompt="⏺️ Ghi âm", stop_prompt="⏹️ Dừng", key='speaks')
    if rec: st.audio(rec['bytes']); st.success("Giỏi lắm! Con đã đọc rất tốt.")

elif chuc_nang == "📈 Xem tiến độ":
    df = load_data()
    if not df.empty: st.line_chart(df['Diem']); st.dataframe(df)
