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
from gtts import gTTS

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# Thông tin Email của Ông chủ Kiên
EMAIL_GUI = "cua.hoc.toan.ai@gmail.com" 
EMAIL_NHAN = "kien.nguyen@example.com" 
MAT_KHAU_APP = "xxxx xxxx xxxx xxxx" 

# --- 2. TỪ ĐIỂN KIẾN THỨC GLOBAL SUCCESS ---
ENGLISH_UNITS = {
    11: "My family's jobs (Teacher, Doctor, Nurse, Worker, Clerk)",
    12: "Jobs and workplaces (School, Hospital, Factory, Farm, Office)",
    13: "Appearance (Tall, Short, Slim, Old, Young)",
    14: "Daily activities (Get up, Have breakfast, Go to school)",
    15: "My family's weekend (Watch TV, Listen to music, Clean the room)"
}

# --- 3. HÀM TIỆN ÍCH ---
def speak_text(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

def send_detailed_report(content):
    if MAT_KHAU_APP == "xxxx xxxx xxxx xxxx": return False
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_GUI
        msg['To'] = EMAIL_NHAN
        msg['Subject'] = f"📋 BÁO CÁO LỖ HỔNG KIẾN THỨC - BÉ CUA ({datetime.now().strftime('%d/%m/%Y')})"
        msg.attach(MIMEText(content, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_GUI, MAT_KHAU_APP)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# --- 4. GIAO DIỆN ---
st.set_page_config(page_title="Gia Sư AI V61 - Supreme", layout="wide")
if 'html_p1' not in st.session_state: 
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'listening_text':"", 'start_time': None, 'unit_info': ""})

with st.sidebar:
    st.title("🛡️ GIA SƯ AI V61")
    mon_hoc = st.selectbox("Môn học:", ["🧮 Toán Lớp 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    chuc_nang = st.radio("Menu:", ["🚀 Làm bài mới", "🚑 Luyện tập cải thiện", "📉 Xem tiến độ"])
    
    if "Tiếng Anh" in mon_hoc:
        unit_num = st.number_input("Chọn Unit (11-20):", 11, 20, 11)
        st.session_state['unit_info'] = ENGLISH_UNITS.get(unit_num, "General Topic")
        st.info(f"Chủ đề: {st.session_state['unit_info']}")

# --- 5. LOGIC RA ĐỀ ---
if chuc_nang == "🚀 Làm bài mới" and st.button("📝 RA ĐỀ TOÀN DIỆN"):
    st.session_state['start_time'] = datetime.now()
    with st.spinner("AI đang soạn đề & chuẩn bị hình ảnh minh họa..."):
        if "Toán" in mon_hoc:
            # Code Toán giữ nguyên logic V59
            pass
        else:
            topic = st.session_state['unit_info']
            # Soạn phần nghe
            script = client.chat.completions.create(messages=[{"role":"user","content":f"Write 4 sentences in English about {topic} for Grade 4."}], model=MODEL_TEXT).choices[0].message.content
            st.session_state['listening_text'] = script
            
            # Soạn trắc nghiệm & Tự luận
            p1 = client.chat.completions.create(messages=[{"role":"user","content":f"Based on '{script}', write 2 listening and 4 grammar/vocab questions about {topic}. English only. Format: Question 1: ... A. B. C. D."}], model=MODEL_TEXT).choices[0].message.content
            p2 = client.chat.completions.create(messages=[{"role":"user","content":f"Write 3 'Reorder words' questions about {topic}. English only."}], model=MODEL_TEXT).choices[0].message.content
            
            st.session_state['html_p1'] = p1
            st.session_state['html_p2'] = p2
            st.session_state['raw_ans'] = client.chat.completions.create(messages=[{"role":"user","content":f"Solve this:\n{p1}\n{p2}"}], model=MODEL_TEXT).choices[0].message.content
            st.rerun()

# --- 6. HIỂN THỊ ĐỀ ---
if st.session_state['html_p1']:
    st.subheader(f"🌟 ĐỀ THI: {st.session_state['unit_info']}")
    
    # Suggesting visual dictionary
    if "Jobs" in st.session_state['unit_info'] or "11" in str(st.session_state['unit_info']):
        st.write("🖼️ **Từ điển hình ảnh nhanh:**")
        st.markdown("")
    
    if st.session_state['listening_text']:
        with st.expander("🎧 NGHE ĐOẠN VĂN"):
            st.audio(speak_text(st.session_state['listening_text']), format='audio/mp3')

    # Hiển thị Câu hỏi & Nút phát âm
    st.markdown("### PART 1: QUESTIONS")
    questions = st.session_state['html_p1'].split('<br><br>') if '<br><br>' in st.session_state['html_p1'] else st.session_state['html_p1'].split('\n\n')
    
    for q in questions:
        if q.strip():
            st.write(q)
            # Nút "Đọc theo con" cho từng câu
            if st.button(f"🔊 Nghe câu này", key=hash(q)):
                st.audio(speak_text(q), format='audio/mp3')

    st.divider()
    st.write(st.session_state['html_p2'])
    
    ans = [st.radio(f"Chọn đáp án Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"ans{i}") for i in range(6)]
    tl_user = st.text_area("Phần viết (Sắp xếp câu):")

    if st.button("✅ NỘP BÀI & PHÂN TÍCH LỖ HỔNG"):
        with st.spinner("AI đang soi xét từng lỗi sai..."):
            prompt_cham = f"""
            Chấm bài Tiếng Anh Lớp 4. 
            Key: {st.session_state['raw_ans']}
            HS: TN {ans}, Viết '{tl_user}'
            
            YÊU CẦU TRẢ VỀ:
            DIEM: [Số]
            LO_HONG_TU_VUNG: [Liệt kê từ con chưa thuộc]
            LO_HONG_NGU_PHAP: [Liệt kê cấu trúc con làm sai]
            GIAI_THICH_LOI_SAI: [Giải thích chi tiết bằng tiếng Việt]
            """
            res = client.chat.completions.create(messages=[{"role":"user","content":prompt_cham}], model=MODEL_TEXT).choices[0].message.content
            st.success("KẾT QUẢ PHÂN TÍCH")
            st.write(res)
            
            # Gửi Email báo cáo lỗ hổng
            if send_detailed_report(res): st.info("📬 Bố Kiên ơi, báo cáo lỗ hổng kiến thức đã được gửi vào Email của bố rồi ạ!")
