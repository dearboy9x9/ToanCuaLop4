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

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# --- 2. HÀM XỬ LÝ DỮ LIỆU & AI ---
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

def call_ai_strict(prompt, system="Giáo viên chuyên gia."):
    chat = client.chat.completions.create(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        model=MODEL_TEXT, temperature=0.5
    )
    return chat.choices[0].message.content

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    text = text.replace("直", "vuông").strip()
    text = re.sub(r'\n{2,}', '<br><br>', text)
    text = text.replace('\n', '<br>')
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', 
                  r'\1<br><b style="color: #d35400; font-size: 1.15em; display: inline-block; margin-top: 10px;">\2</b>', text)
    return f"""<div style="background-color: #fff; border-left: 10px solid {color_hex}; border-radius: 15px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);"><h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2,px solid #eee;">{title}</h2><div style="font-size: 18px; line-height: 1.8;">{text}</div></div>"""

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="Gia Sư AI V71", layout="wide")
if 'html_p1' not in st.session_state:
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'ket_qua':"", 'start_time': None})

with st.sidebar:
    st.title("🛡️ SUPREME V71")
    ten_hs = st.text_input("Học sinh:", "Cua")
    mon_hoc = st.selectbox("🎯 Môn học:", ["🧮 Toán 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    dang_bai = st.selectbox("📝 Chế độ luyện tập:", ["Luyện tập theo Unit", "Thi thử Học kỳ", "Ôn tập tổng hợp"])
    
    # Logic chọn chủ đề bám sát SGK (đã hoàn thiện ở V70)
    chu_de = "Kiến thức trọng tâm" 
    
    st.divider()
    mode = st.radio("Menu:", ["🚀 Vào học ngay", "🎙️ Luyện nói", "📈 Xem tiến độ"])

# --- 4. LOGIC CHẤM ĐIỂM TỔNG LỰC ---
if mode == "🚀 Vào học ngay":
    st.title(f"🦀 Cậu chủ {ten_hs} - Chế độ: {dang_bai}")
    
    if st.button("📝 BẮT ĐẦU RA ĐỀ & CHẤM ĐIỂM"):
        st.session_state.update({'html_p1':"", 'html_p2':"", 'ket_qua':"", 'start_time': datetime.now()})
        with st.spinner("AI đang soạn đề thi bám sát chương trình..."):
            # Soạn đề (Toán hoặc Anh tùy chọn)
            p1 = call_ai_strict(f"Soạn 6 câu trắc nghiệm {mon_hoc} {dang_bai}. NO ANSWERS.")
            p2 = call_ai_strict(f"Soạn 3 câu tự luận {mon_hoc} {dang_bai}. NO ANSWERS.")
            st.session_state['html_p1'] = process_text_to_html(p1, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
            st.session_state['html_p2'] = process_text_to_html(p2, "PHẦN 2: TỰ LUẬN", "#2c3e50")
            st.session_state['raw_ans'] = call_ai_strict(f"Giải chi tiết đề này để chấm bài:\n{p1}\n{p2}")
            st.rerun()

    if st.session_state['html_p1']:
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
        
        # Phiếu nộp bài luôn hiện diện
        st.subheader("✍️ PHIẾU LÀM BÀI")
        ans = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
        tl_user = st.text_area("Lời giải tự luận (AI sẽ chấm chi tiết từng bước):")

        if st.button("✅ NỘP BÀI & XEM ĐIỂM"):
            phut = round((datetime.now() - st.session_state['start_time']).total_seconds()/60, 1)
            with st.spinner("AI đang phân tích bài làm của con..."):
                prompt_cham = f"""
                Bạn là giáo viên chấm bài nghiêm khắc nhưng tận tâm. 
                Key: {st.session_state['raw_ans']}
                Student: TN {ans}, TL '{tl_user}'
                
                YÊU CẦU:
                1. DIEM: [Số điểm/10]
                2. CHI TIẾT LỖI SAI: Giải thích tại sao con sai, kiến thức nào bị hổng.
                3. ĐÁP ÁN ĐÚNG & GIẢI THÍCH: Cung cấp đáp án đúng và cách giải ngắn gọn bằng tiếng Việt.
                4. YEU: [Tóm tắt 1 dòng vùng kiến thức yếu]
                """
                res = call_ai_strict(prompt_cham, "Giáo viên chấm thi chuyên nghiệp.")
                st.session_state['ket_qua'] = res
                
                # Trích xuất điểm và vùng yếu để lưu log
                try:
                    d = int(re.search(r"DIEM:\s*(\d+)", res).group(1))
                    yeu = re.search(r"YEU:\s*(.*)", res).group(1)
                    save_detailed_result(mon_hoc, dang_bai, d, phut, yeu)
                except: pass
                st.rerun()

    if st.session_state['ket_qua']:
        st.divider()
        st.markdown(process_text_to_html(st.session_state['ket_qua'], "📊 KẾT QUẢ VÀ GIẢI THÍCH CHI TIẾT", "#16a085"), unsafe_allow_html=True)
        if "10" in st.session_state['ket_qua']: st.balloons()
