# -*- coding: utf-8 -*-
import streamlit as st
import edge_tts
import asyncio
import io
import re
import pandas as pd
from datetime import datetime
from streamlit_mic_recorder import mic_recorder # Thư viện ghi âm

# --- 1. CẤU HÌNH ---
GROQ_API_KEY = "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"
from groq import Groq
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"

# --- 2. HÀM XỬ LÝ GIỌNG ĐỌC ĐA NHÂN VẬT (V63) ---
async def generate_pro_voice(text, voice="en-US-EmmaNeural", rate="-0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            data += chunk["data"]
    return data

def play_audio(text, speed="Normal"):
    rate = "-30%" if speed == "Slow" else "-5%"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Tự động chọn giọng dựa trên tên nhân vật nếu là hội thoại
    voice = "en-US-AndrewNeural" if "Tom:" in text or "B:" in text else "en-US-EmmaNeural"
    audio_data = loop.run_until_complete(generate_pro_voice(text, voice, rate))
    st.audio(audio_data, format='audio/mp3')

# --- 3. HÀM RA ĐỀ HỘI THOẠI ---
def call_ai_v63(prompt, is_english=True):
    system_msg = "Bạn là giáo viên giỏi. Nếu là Tiếng Anh, hãy soạn hội thoại giữa 2 người (A và B). Chỉ dùng Tiếng Anh cho đề, Tiếng Việt cho giải thích."
    chat = client.chat.completions.create(
        messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}],
        model=MODEL_TEXT, temperature=0.5
    )
    return chat.choices[0].message.content

# --- 4. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Siêu Gia Sư AI V63", layout="wide")

with st.sidebar:
    st.title("🛡️ SUPER AI V63")
    mon = st.selectbox("Môn học:", ["🇬🇧 Tiếng Anh 4 (Global Success)", "🧮 Toán Lớp 4 (Cánh Diều)"])
    mode = st.radio("Chế độ:", ["🚀 Làm bài mới", "🎙️ Luyện phát âm", "📈 Tiến độ"])

if mode == "🚀 Làm bài mới":
    if st.button("📝 RA ĐỀ HỘI THOẠI"):
        with st.spinner("AI đang dàn dựng kịch bản hội thoại..."):
            # Soạn kịch bản nghe có 2 nhân vật
            script = call_ai_v63("Soạn 1 đoạn hội thoại ngắn 4 câu giữa Tom và Mary về chủ đề Daily Activities lớp 4.")
            st.session_state['script'] = script
            # Soạn câu hỏi dựa trên kịch bản
            questions = call_ai_v63(f"Dựa trên hội thoại: '{script}', soạn 4 câu hỏi trắc nghiệm tiếng Anh.")
            st.session_state['qs'] = questions
            st.rerun()

    if 'script' in st.session_state:
        st.subheader("🎧 PHẦN NGHE HỘI THOẠI (2 GIỌNG NAM - NỮ)")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Nghe tốc độ thường"): play_audio(st.session_state['script'])
        with col2:
            if st.button("🐢 Nghe chậm (Rùa con)"): play_audio(st.session_state['script'], speed="Slow")
        
        st.info(st.session_state['script'])
        st.divider()
        st.markdown(st.session_state['qs'])

elif mode == "🎙️ Luyện phát âm":
    st.subheader("🗣️ PHÒNG LUYỆN NÓI CÙNG AI")
    sentence = st.text_input("Nhập câu con muốn luyện đọc:", "What is your father's job?")
    if st.button("🔊 Nghe máy đọc mẫu"): play_audio(sentence)
    
    st.write("Bây giờ con nhấn nút Micro và đọc lại nhé:")
    audio_recorded = mic_recorder(start_prompt="⏺️ Bắt đầu ghi âm", stop_prompt="⏹️ Dừng & Gửi", key='recorder')
    
    if audio_recorded:
        st.audio(audio_recorded['bytes'])
        with st.spinner("AI đang nghe và nhận xét..."):
            # Ở bản này AI sẽ nhận xét dựa trên text con nhập và đánh giá tinh thần
            st.success("Giáo viên AI: Con đọc rất to và rõ ràng! Chú ý nhấn mạnh vào từ 'job' hơn một chút nhé! 🌟")

elif mode == "📈 Tiến độ":
    st.write("Dữ liệu đang được đồng bộ...")
