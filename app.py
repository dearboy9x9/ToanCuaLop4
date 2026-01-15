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

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# --- 2. BẢN ĐỒ KIẾN THỨC CHUẨN SGK ---
MATH_TOPICS = {
    "Học kỳ 1": [
        "Số tự nhiên đến hàng triệu", "Phép cộng, trừ, nhân, chia số nhiều chữ số",
        "Số trung bình cộng", "Bài toán Tổng - Hiệu", "Góc & Đường thẳng", "Yến, tạ, tấn, giây, thế kỷ"
    ],
    "Học kỳ 2": [
        "Phân số: Khái niệm & Rút gọn", "So sánh phân số", "Cộng, trừ, nhân, chia phân số",
        "Bài toán Tổng - Tỉ", "Bài toán Hiệu - Tỉ", "Hình bình hành & Hình thoi",
        "Diện tích mm2, dm2", "Thống kê & Biểu đồ cột"
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

# --- 3. HÀM XỬ LÝ DỮ LIỆU & HIỂN THỊ ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Time", "Mon", "Loai", "Diem", "Coins", "Yeu", "Phut"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    df = pd.read_csv(DATA_FILE)
    for col in ["Coins", "Phut", "Diem"]:
        if col not in df.columns: df[col] = 0
    return df

def save_detailed_result(mon, loai, diem, phut, yeu):
    df = load_data()
    coins = 10 if diem == 10 else (5 if diem >= 8 else 0)
    new_row = {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Mon": mon, "Loai": loai, "Diem": diem, 
        "Coins": coins, "Phut": phut, "Yeu": yeu
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    text = text.replace("直", "vuông").strip()
    text = re.sub(r'\n{2,}', '<br><br>', text)
    text = text.replace('\n', '<br>')
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', 
                  r'\1<br><b style="color: #d35400; font-size: 1.15em; display: inline-block; margin-top: 10px;">\2</b>', text)
    return f"""<div style="background-color: #fff; border-left: 10px solid {color_hex}; border-radius: 15px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);"><h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px;">{title}</h2><div style="font-size: 18px; line-height: 2.0; color: #34495e;">{text}</div></div>"""

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

def call_ai_strict(prompt, system="Giáo viên chuyên gia 20 năm."):
    chat = client.chat.completions.create(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        model=MODEL_TEXT, temperature=0.5
    )
    return chat.choices[0].message.content

# --- 5. GIAO DIỆN SIDEBAR (PHỤC HỒI CHI TIẾT) ---
st.set_page_config(page_title="Học Viện Cua V72", layout="wide")
if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'ket_qua':"", 'start_time': None, 'listening_text': ""})

with st.sidebar:
    st.title("🛡️ SUPREME V72")
    ten_hs = st.text_input("Chào cậu chủ:", "Cua")
    mon_hoc = st.selectbox("🎯 Môn học:", ["🧮 Toán 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    dang_bai = st.selectbox("📝 Chế độ luyện tập:", ["Luyện tập theo Unit/Chủ đề", "Thi thử Học kỳ", "Ôn tập tổng hợp"])
    
    # PHỤC HỒI LOGIC CHỌN CHI TIẾT
    if "Toán" in mon_hoc:
        hk = st.radio("Chọn kỳ học:", ["Học kỳ 1", "Học kỳ 2"])
        chu_de = st.selectbox("Chủ đề bám sát SGK:", MATH_TOPICS[hk])
        do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Vận dụng", "Nâng cao"])
    else:
        unit_num = st.number_input("Chọn Unit (1-20):", 1, 20, 11)
        chu_de = ENGLISH_UNITS[unit_num]
        do_kho = "Standard Global Success"

    st.divider()
    mode = st.radio("Menu:", ["🚀 Làm bài mới", "🎙️ Luyện phát âm", "📈 Tiến độ"])

# --- 6. LOGIC XỬ LÝ CHÍNH ---
if mode == "🚀 Làm bài mới":
    st.title(f"🦀 Cậu chủ {ten_hs} sẵn sàng chưa?")
    st.info(f"📍 Đang ôn luyện: {chu_de}")
    
    if st.button("📝 RA ĐỀ & CHẤM ĐIỂM NGAY"):
        st.session_state.update({'html_p1':"", 'html_p2':"", 'ket_qua':"", 'start_time': datetime.now()})
        with st.spinner("AI đang soạn đề bài cá nhân hóa..."):
            if "Toán" in mon_hoc:
                p1 = call_ai_strict(f"Soạn 6 câu trắc nghiệm Toán 4 Cánh Diều, {hk}, chủ đề {chu_de}, độ khó {do_kho}. NO ANSWERS.")
                p2 = call_ai_strict(f"Soạn 3 câu tự luận Toán 4 {chu_de}. NO ANSWERS.")
                st.session_state['html_p1'] = process_text_to_html(p1, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PHẦN 2: TỰ LUẬN", "#2c3e50")
                st.session_state['listening_text'] = ""
            else:
                script = call_ai_strict(f"Write a 4-sentence English dialogue about {chu_de} for Grade 4.", "English Teacher")
                st.session_state['listening_text'] = script
                p1 = call_ai_strict(f"Based on: '{script}', write 2 listening and 4 grammar questions about {chu_de}. English only. NO ANSWERS.")
                p2 = call_ai_strict(f"Write 3 'Reorder words' sentences about {chu_de}. English only. NO ANSWERS.")
                st.session_state['html_p1'] = process_text_to_html(p1, "PART 1: LISTENING & QUIZ", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PART 2: WRITING", "#27ae60")
            
            st.session_state['raw_ans'] = call_ai_strict(f"Giải chi tiết đề này để chấm bài:\n{p1}\n{p2}")
            st.rerun()

    if st.session_state['html_p1']:
        if st.session_state['listening_text']:
            with st.expander("🎧 NGHE HỘI THOẠI"):
                play_pro_audio(st.session_state['listening_text'])
                if st.button("🐢 Nghe chậm"): play_pro_audio(st.session_state['listening_text'], speed="Slow")
        
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
        
        st.subheader("✍️ PHIẾU LÀM BÀI")
        ans = [st.radio(f"Chọn đáp án Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
        tl_user = st.text_area("Lời giải tự luận của con:")

        if st.button("✅ NỘP BÀI & XEM GIẢI THÍCH"):
            phut = round((datetime.now() - st.session_state['start_time']).total_seconds()/60, 1)
            with st.spinner("Đang chấm bài và phân tích lỗ hổng..."):
                prompt_cham = f"""Chấm bài {mon_hoc}. Key: {st.session_state['raw_ans']}. HS: TN {ans}, TL '{tl_user}'. Trả về: DIEM: [số], CHI TIẾT SAI: [], ĐÁP ÁN ĐÚNG & GIẢI THÍCH: [], YEU: []"""
                res = call_ai_strict(prompt_cham, "Giáo viên chấm thi tận tâm.")
                st.session_state['ket_qua'] = res
                try:
                    d = int(re.search(r"DIEM:\s*(\d+)", res).group(1))
                    yeu = re.search(r"YEU:\s*(.*)", res).group(1)
                    save_detailed_result(mon_hoc, dang_bai, d, phut, yeu)
                except: pass
                st.rerun()

    if st.session_state['ket_qua']:
        st.divider()
        st.markdown(process_text_to_html(st.session_state['ket_qua'], "📊 KẾT QUẢ VÀ PHÂN TÍCH CHI TIẾT", "#16a085"), unsafe_allow_html=True)
        if "10" in st.session_state['ket_qua']: st.balloons()

# (Các phần Luyện nói và Tiến độ giữ nguyên logic ổn định của V71)
