# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq
from PIL import Image
import pandas as pd
import os
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import re
import base64
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

# Ông chủ điền thông tin Email vào đây
EMAIL_GUI = "cua.hoc.toan.ai@gmail.com" 
EMAIL_NHAN = "kien.nguyen@example.com" 
MAT_KHAU_APP = "xxxx xxxx xxxx xxxx" 

# --- 2. HÀM TIỆN ÍCH ---
def send_daily_report(report_content):
    if MAT_KHAU_APP == "xxxx xxxx xxxx xxxx": return False
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_GUI
        msg['To'] = EMAIL_NHAN
        msg['Subject'] = f"🚀 BÁO CÁO HỌC TẬP - BÉ CUA ({datetime.now().strftime('%d/%m/%Y')})"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_GUI, MAT_KHAU_APP)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

def play_english_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp, format='audio/mp3')

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    text = text.replace("直", "vuông").strip()
    text = re.sub(r'\n{2,}', '<br><br>', text)
    text = text.replace('\n', '<br>')
    # Fix format: Bỏ dấu -, in đậm Câu X màu cam
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', r'\1<b style="color: #d35400; font-size: 1.1em;">\2</b>', text)
    return f"""
    <div style="background-color: #fff; border: 2px solid {color_hex}; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid {color_hex}; padding-bottom: 10px; font-weight: 800; text-transform: uppercase;">{title}</h2>
        <div style="font-size: 16px; line-height: 1.8; color: #333;">{text}</div>
    </div>
    """

def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Thoi_Gian", "Mon", "Dang", "Diem", "Phut", "Tot", "Yeu", "NhanXet"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    return pd.read_csv(DATA_FILE)

# --- 3. GIAO DIỆN SIDEBAR ---
st.set_page_config(page_title="Gia Sư AI V57", page_icon="🎓", layout="wide")

if 'html_p1' not in st.session_state: 
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'listening_text':"", 'start_time': None})

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10608/10608822.png", width=60)
    st.title("GIA SƯ AI V57")
    ten_hs = st.text_input("Học sinh:", "Cua")
    mon_hoc = st.selectbox("Môn học:", ["🧮 Toán Lớp 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    
    # PHÂN LOẠI CHI TIẾT THEO MÔN
    if "Toán" in mon_hoc:
        dang_de = st.selectbox("Dạng đề:", ["Luyện tập Bài lẻ", "Thi thử HK1", "Thi thử HK2"])
        if "Bài lẻ" in dang_de:
            chu_de = st.selectbox("Chủ đề:", ["Số tự nhiên", "4 Phép tính", "Trung bình cộng", "Hình học", "Đơn vị đo", "Phân số"])
        else: chu_de = "Tổng hợp"
        do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Khá", "Nâng cao"])
    else:
        dang_de = st.selectbox("Dạng đề:", ["Luyện tập Unit", "Thi thử HK1 (Unit 1-10)", "Thi thử HK2 (Unit 11-20)"])
        if "Unit" in dang_de:
            chu_de = st.number_input("Chọn Unit (1-20):", 1, 20, 1)
        else: chu_de = "Tổng hợp chương trình"
        do_kho = "Theo chuẩn đề thi"

    chuc_nang = st.radio("Menu:", ["🚀 Làm bài mới", "📈 Tiến độ", "📧 Báo cáo"])

# --- 4. XỬ LÝ CHỨC NĂNG ---
if chuc_nang == "📈 Tiến độ":
    df = load_data()
    if df.empty: st.info("Chưa có dữ liệu.")
    else:
        st.subheader("Biểu đồ tiến bộ")
        st.line_chart(df['Diem'])
        st.dataframe(df)

elif chuc_nang == "📧 Báo cáo":
    if st.button("Gửi báo cáo qua Email"):
        df = load_data()
        if not df.empty:
            last = df.iloc[-1]
            prompt = f"Phân tích kết quả: {last['Mon']}, Điểm {last['Diem']}, Yếu: {last['Yeu']}. Viết báo cáo gửi bố Kiên, đề xuất lộ trình."
            res = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=MODEL_TEXT).choices[0].message.content
            if send_daily_report(res): st.success("Đã gửi báo cáo!")
            else: st.error("Cấu hình Email chưa đúng.")

elif chuc_nang == "🚀 Làm bài mới":
    st.title(f"🦀 Chào {ten_hs}!")
    
    if st.button("📝 BẮT ĐẦU RA ĐỀ"):
        st.session_state['start_time'] = datetime.now()
        with st.spinner("AI đang soạn đề chuẩn..."):
            if "Toán" in mon_hoc:
                prompt_tn = f"Soạn 6 câu trắc nghiệm Toán 4 Cánh Diều, chủ đề {chu_de}, độ khó {do_kho}. Format: Câu 1: ... A. B. C. D."
                prompt_tl = f"Soạn 3 câu tự luận Toán 4: Câu 7 (Tính toán), Câu 8 (Toán đố {chu_de}), Câu 9 (Nâng cao). KHÔNG ghi đáp án."
                tn_res = client.chat.completions.create(messages=[{"role":"user","content":prompt_tn}], model=MODEL_TEXT).choices[0].message.content
                tl_res = client.chat.completions.create(messages=[{"role":"user","content":prompt_tl}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['html_p1'] = process_text_to_html(tn_res, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(tl_res, "PHẦN 2: TỰ LUẬN", "#2980b9")
                st.session_state['listening_text'] = ""
            else:
                # TIẾNG ANH CHẾ ĐỘ CHIA ĐỀ
                listening_script = client.chat.completions.create(messages=[{"role":"user","content":f"Viết 1 đoạn văn tiếng Anh lớp 4 ngắn về {chu_de} (3-4 câu)."}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['listening_text'] = listening_script
                prompt_tn = f"Dựa vào bài nghe: '{listening_script}', soạn Câu 1, 2 là câu hỏi nghe. Câu 3, 4, 5, 6 là ngữ pháp {chu_de}. Trắc nghiệm A,B,C,D."
                prompt_tl = f"Phần Writing Tiếng Anh lớp 4: Soạn 3 câu yêu cầu sắp xếp từ thành câu (Reorder words to make sentences) về {chu_de}. KHÔNG ghi đáp án."
                tn_res = client.chat.completions.create(messages=[{"role":"user","content":prompt_tn}], model=MODEL_TEXT).choices[0].message.content
                tl_res = client.chat.completions.create(messages=[{"role":"user","content":prompt_tl}], model=MODEL_TEXT).choices[0].message.content
                st.session_state['html_p1'] = process_text_to_html(tn_res, "PART 1: LISTENING & QUIZ", "#e67e22")
                st.session_state['html_p2'] = process_text_to_html(tl_res, "PART 2: READING & WRITING", "#27ae60")
            
            st.session_state['raw_ans'] = client.chat.completions.create(messages=[{"role":"user","content":f"Giải chi tiết:\n{tn_res}\n{tl_res}"}], model=MODEL_TEXT).choices[0].message.content
            st.rerun()

    if st.session_state['html_p1']:
        st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
        if st.session_state['listening_text']:
            with st.expander("🎧 BẤM VÀO ĐÂY ĐỂ NGHE (LISTENING)"):
                play_english_audio(st.session_state['listening_text'])
                st.info("Nghe và trả lời Câu 1, Câu 2 ở phía trên.")
        
        st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📝 Phiếu Trắc Nghiệm")
            ans = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
        with c2:
            st.subheader("✍️ Phần Tự Luận / Viết")
            tl_user = st.text_area("Nhập bài làm của con:")
            img = st.file_uploader("Hoặc gửi ảnh bài làm:")

        if st.button("✅ NỘP BÀI"):
            phut = round((datetime.now() - st.session_state['start_time']).total_seconds()/60, 1)
            with st.spinner("Đang chấm bài..."):
                prompt_cham = f"Đề/Đáp án: {st.session_state['raw_ans']}. HS làm: TN {ans}, TL {tl_user}. Chấm thang 10. Trả về: DIEM: [số], TOT: [], YEU: [], NHANXET: []"
                res = client.chat.completions.create(messages=[{"role":"user","content":prompt_cham}], model=MODEL_TEXT).choices[0].message.content
                st.success(f"Kết quả: {res}")
                try:
                    d = int(re.search(r"DIEM:\s*(\d+)", res).group(1))
                    tot = re.search(r"TOT:\s*(.*)", res).group(1)
                    yeu = re.search(r"YEU:\s*(.*)", res).group(1)
                    nx = re.search(r"NHANXET:\s*(.*)", res).group(1)
                    df = load_data()
                    new = {"Thoi_Gian":datetime.now(),"Mon":mon_hoc,"Dang":dang_de,"Diem":d,"Phut":phut,"Tot":tot,"Yeu":yeu,"NhanXet":nx}
                    pd.concat([df, pd.DataFrame([new])]).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                    if d >= 8: st.balloons()
                except: pass

if st.session_state['raw_ans'] and st.sidebar.text_input("PIN Bố:", type="password") == "1990":
    st.info(st.session_state['raw_ans'])
