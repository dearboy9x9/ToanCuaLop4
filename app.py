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

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# --- 2. MA TRẬN KIẾN THỨC CHUẨN (V79 UPDATED FROM PHOTO) ---
MATH_TOPICS = {
    "Học kỳ 1": ["Số tự nhiên hàng triệu", "4 phép tính số lớn", "Trung bình cộng", "Tổng - Hiệu", "Góc & Đường thẳng", "Yến, tạ, tấn, giây"],
    "Học kỳ 2": ["Phân số: Khái niệm & Rút gọn", "Cộng, trừ, nhân, chia phân số", "Tổng - Tỉ", "Hiệu - Tỉ", "Hình bình hành & Thoi", "Diện tích mm2, dm2", "Thống kê & Xác suất"]
}

ENGLISH_BOOK_MAP = {
    11: {"topic": "My home", "vocab": "big, busy, live, noisy, quiet, street", "focus": "Where someone lives"},
    12: {"topic": "Jobs", "vocab": "actor, farmer, nurse, office worker, policeman", "focus": "Jobs and workplaces"},
    13: {"topic": "Appearance", "vocab": "big, short, slim, tall, eyes, face", "focus": "Descriptions"},
    14: {"topic": "Daily activities", "vocab": "watch TV, cooking, wash the clothes, afternoon", "focus": "Time and routines"},
    15: {"topic": "My family's weekends", "vocab": "cinema, shopping centre, swimming pool, tennis", "focus": "Weekend activities"},
    16: {"topic": "Weather", "vocab": "cloudy, rainy, sunny, windy, stormy", "focus": "Weather conditions"},
    17: {"topic": "In the city", "vocab": "go straight, left, right, turn around, campsite", "focus": "Directions"},
    18: {"topic": "At the shopping centre", "vocab": "behind, between, near, opposite, price", "focus": "Locations and prices"},
    19: {"topic": "The animal world", "vocab": "crocodiles, giraffes, hippos, lions, beautiful", "focus": "Animals"},
    20: {"topic": "At summer camp", "vocab": "building a campfire, dancing, singing songs", "focus": "Current activities"}
}

# --- 3. HÀM XỬ LÝ DỮ LIỆU & HIỂN THỊ ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Time", "Mon", "Diem", "Coins", "Yeu", "Phut"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    df = pd.read_csv(DATA_FILE)
    for col in ["Coins", "Phut", "Diem"]:
        if col not in df.columns: df[col] = 0
    return df

def save_result(mon, diem, yeu):
    df = load_data()
    coins = 10 if diem == 10 else (5 if diem >= 8 else 0)
    new_row = {"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Mon": mon, "Diem": diem, "Coins": coins, "Yeu": yeu, "Phut": 0}
    pd.concat([df, pd.DataFrame([new_row])]).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    text = text.replace("直", "vuông").strip()
    text = re.sub(r'\n{2,}', '<br><br>', text)
    text = text.replace('\n', '<br>')
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', 
                  r'\1<br><b style="color: #d35400; font-size: 1.2em; display: inline-block; margin-top: 15px;">\2</b>', text)
    return f"""<div style="background-color: #fff; border-left: 10px solid {color_hex}; border-radius: 15px; padding: 30px; margin-bottom: 30px; box-shadow: 0 6px 15px rgba(0,0,0,0.1);"><h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 12px; font-weight: 800;">{title}</h2><div style="font-size: 19px; line-height: 2.0; color: #2c3e50;">{text}</div></div>"""

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
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    audio_data = loop.run_until_complete(generate_pro_voice(text, voice=voice, rate=rate))
    st.audio(audio_data, format='audio/mp3')

def call_ai_strict(prompt, system="Giáo viên chuyên gia 20 năm."):
    chat = client.chat.completions.create(messages=[{"role":"system","content":system},{"role":"user","content":prompt}], model=MODEL_TEXT, temperature=0.5)
    return chat.choices[0].message.content

# --- 5. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Học Viện Cua V79", layout="wide")
if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'ket_qua':"", 'start_time': None, 'listening_text': ""})

with st.sidebar:
    st.title("🛡️ SUPREME V79")
    ten_hs = st.text_input("Chào cậu chủ:", "Cua")
    df_h = load_data(); st.metric("💰 Cua Coins", df_h['Coins'].sum())
    mon_hoc = st.selectbox("🎯 Môn học:", ["🧮 Toán 4", "🇬🇧 Tiếng Anh 4"])
    
    if "Toán" in mon_hoc:
        hk = st.radio("Kỳ học:", ["Học kỳ 1", "Học kỳ 2"])
        chu_de = st.selectbox("Chủ đề:", MATH_TOPICS[hk]); do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Khá", "Nâng cao"])
    else:
        unit = st.number_input("Unit (11-20):", 11, 20, 11)
        data_u = ENGLISH_BOOK_MAP.get(unit)
        chu_de = f"{data_u['topic']} (Vocab: {data_u['vocab']})"; do_kho = "Standard"

    mode = st.radio("Chế độ:", ["🚀 Làm bài mới", "⚡ Tính nhẩm", "🎙️ Luyện phát âm", "📈 Tiến độ"])

# --- 6. LOGIC XỬ LÝ CHÍNH ---
if mode == "🚀 Làm bài mới":
    st.title(f"🦀 Chào cậu chủ {ten_hs}!")
    if st.button("📝 RA ĐỀ CHI TIẾT"):
        st.session_state.update({'html_p1':"", 'html_p2':"", 'ket_qua':"", 'start_time': datetime.now()})
        with st.spinner("AI đang soạn đề..."):
            if "Toán" in mon_hoc:
                p1 = call_ai_strict(f"Soạn 6 câu trắc nghiệm Toán 4, {chu_de}, {do_kho}. NO ANSWERS.")
                p2 = call_ai_strict(f"Soạn 3 câu tự luận Toán 4 {chu_de}. NO ANSWERS.")
                st.session_state['html_p1'] = process_text_to_html(p1, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PHẦN 2: TỰ LUẬN", "#2c3e50")
            else:
                sys_eng = "Native English Teacher. 100% English. No Vietnamese."
                script = call_ai_strict(f"Write a 4-sentence English dialogue for Grade 4 about {chu_de}.", system=sys_eng)
                st.session_state['listening_text'] = script
                p1 = call_ai_strict(f"Based on: '{script}', write 2 listening & 4 MCQ questions. 100% English. NO ANSWERS.", system=sys_eng)
                p2 = call_ai_strict(f"Write 3 'Word ordering' questions about {chu_de}. 100% English. NO ANSWERS.", system=sys_eng)
                st.session_state['html_p1'] = process_text_to_html(p1, "PART 1: LISTENING", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(p2, "PART 2: WRITING", "#27ae60")
            st.session_state['raw_ans'] = call_ai_strict(f"Giải chi tiết đề này để chấm bài:\n{p1}\n{p2}")
            st.rerun()

    if st.session_state['html_p1']:
        if st.session_state['listening_text']:
            with st.expander("🎧 BẤM ĐỂ NGHE (LISTENING)"): 
                play_pro_audio(st.session_state['listening_text'])
                if st.button("🐢 Nghe chậm"): play_pro_audio(st.session_state['listening_text'], speed="Slow")
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
        
        with st.form("exam_form"):
            st.subheader("✍️ PHIẾU LÀM BÀI")
            ans_hs = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
            tl_hs = st.text_area("Bài giải/viết của con (Để trống = 0 điểm):")
            if st.form_submit_button("✅ NỘP BÀI & CHẤM CHI TIẾT"):
                with st.spinner("Đang soi xét từng câu..."):
                    status_tl = "BỎ TRỐNG (0 ĐIỂM)" if not tl_hs.strip() else f"HS LÀM: '{tl_hs}'"
                    prompt_grading = f"""
                    Giáo viên nghiêm khắc. Thang điểm 10. Chấm chi tiết từng câu.
                    - Key: {st.session_state['raw_ans']}
                    - HS: TN {ans_hs}, {status_tl}.
                    Trả về:
                    1. KẾT QUẢ TỪNG CÂU: (Đúng/Sai - Giải thích)
                    2. DIEM: [Số]
                    3. NHẬN XÉT & YEU: [Kiến thức yếu]
                    """
                    st.session_state['ket_qua'] = call_ai_strict(prompt_grading)
                    try:
                        d = int(re.search(r"DIEM:\s*(\d+)", st.session_state['ket_qua']).group(1))
                        save_result(mon_hoc, d, "Xem chi tiết")
                    except: pass
                st.rerun()

    if st.session_state['ket_qua']:
        st.markdown(process_text_to_html(st.session_state['ket_qua'], "📊 KẾT QUẢ PHÂN TÍCH", "#16a085"), unsafe_allow_html=True)
        if "10" in st.session_state['ket_qua']: st.balloons()
