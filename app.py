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
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# Cấu hình Email (Bố Kiên điền ở đây)
EMAIL_GUI = "cua.hoc.toan.ai@gmail.com" 
EMAIL_NHAN = "kien.nguyen@example.com" 
MAT_KHAU_APP = "xxxx xxxx xxxx xxxx" 

# --- 2. HÀM HỖ TRỢ ---
def call_ai_strict(user_prompt, system_role="Giáo viên"):
    strict_system = f"{system_role}. QUY TẮC: CHỈ DÙNG TIẾNG VIỆT. KHÔNG DÙNG CHỮ HÁN. TRÌNH BÀY ĐẸP."
    try:
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": strict_system}, {"role": "user", "content": user_prompt}],
            model=MODEL_TEXT, temperature=0.5
        )
        return chat.choices[0].message.content
    except Exception as e: return f"Lỗi AI: {str(e)}"

def generate_geometry_plot(problem_text):
    prompt_coder = f"Dựa vào đề bài: '{problem_text}', viết code Python Matplotlib để vẽ hình minh họa. Tắt trục, chỉ trả về code trong ```python...```"
    code_res = call_ai_strict(prompt_coder, "Coder Python")
    try:
        match = re.search(r"```python(.*?)```", code_res, re.DOTALL)
        if match:
            clean_code = match.group(1)
            fig, ax = plt.subplots(figsize=(4, 3))
            exec(clean_code, {'plt': plt, 'patches': patches, 'np': np, 'ax': ax, 'fig': fig})
            buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight'); buf.seek(0); plt.close(fig)
            return buf
    except: return None

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    text = text.replace("直", "vuông").replace("\n", "<br>")
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', r'\1<b style="color: #d35400; font-size: 1.1em;">\2</b>', text)
    return f"""<div style="background-color: #fff; border: 2px solid {color_hex}; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"><h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid {color_hex}; padding-bottom: 10px; font-weight: 800; text-transform: uppercase;">{title}</h2><div style="font-size: 16px; line-height: 1.8; color: #333;">{text}</div></div>"""

def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Thoi_Gian", "Mon", "Dang", "Diem", "Phut", "Tot", "Yeu", "NhanXet"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    return pd.read_csv(DATA_FILE)

# --- 3. GIAO DIỆN SIDEBAR ---
st.set_page_config(page_title="Gia Sư AI V59", page_icon="🎓", layout="wide")
if 'html_p1' not in st.session_state: 
    st.session_state.update({'html_p1':"", 'html_p2':"", 'raw_ans':"", 'listening_text':"", 'start_time': None, 'geo_image': None})

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10608/10608822.png", width=60)
    st.title("GIA SƯ AI V59")
    ten_hs = st.text_input("Học sinh:", "Cua")
    mon_hoc = st.selectbox("Môn học:", ["🧮 Toán Lớp 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    
    # CHỨC NĂNG ADAPTIVE (MỚI)
    chuc_nang = st.radio("Menu:", ["🚀 Làm bài mới", "🚑 Luyện tập cải thiện", "📈 Tiến độ", "📧 Báo cáo"])
    
    st.write("---")
    if "Toán" in mon_hoc:
        dang_de = st.selectbox("Dạng đề:", ["Luyện tập Bài lẻ", "Thi thử HK1", "Thi thử HK2"])
        chu_de = st.selectbox("Chủ đề:", ["Tổng hợp", "Hình học (Có vẽ hình)", "Số tự nhiên", "4 Phép tính", "Trung bình cộng", "Đơn vị đo", "Phân số"])
        do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Khá", "Nâng cao"])
    else:
        dang_de = st.selectbox("Dạng đề:", ["Luyện tập Unit", "Thi thử HK1", "Thi thử HK2"])
        chu_de = f"Unit {st.number_input('Unit:', 1, 20, 1)}"
        do_kho = "Chuẩn"

# --- 4. HÀM XỬ LÝ RA ĐỀ ---
def generate_exam(subject, type_de, topic, difficulty, improve_mode=False):
    st.session_state['start_time'] = datetime.now()
    st.session_state['geo_image'] = None
    
    extra = "Tập trung vào các lỗi sai trước đây để cải thiện." if improve_mode else ""
    
    with st.spinner("AI đang soạn đề bài..."):
        if "Toán" in subject:
            prompt_tn = f"Soạn 6 câu trắc nghiệm Toán 4 {type_de}, chủ đề {topic}, độ khó {difficulty}. {extra} Format: Câu 1: ... A. B. C. D."
            prompt_tl = f"Soạn 3 câu tự luận Toán 4 chủ đề {topic}. {extra} Chỉ viết câu hỏi."
            tn_res = call_ai_strict(prompt_tn)
            tl_res = call_ai_strict(prompt_tl)
            if "Hình học" in topic: st.session_state['geo_image'] = generate_geometry_plot(tn_res[:500])
            st.session_state['html_p1'] = process_text_to_html(tn_res, "PHẦN 1: TRẮC NGHIỆM", "#e67e22")
            st.session_state['html_p2'] = process_text_to_html(tl_res, "PHẦN 2: TỰ LUẬN", "#2980b9")
        else:
            listening_script = call_ai_strict(f"Viết đoạn văn tiếng Anh lớp 4 về {topic}. {extra}")
            st.session_state['listening_text'] = listening_script
            tn_res = call_ai_strict(f"Dựa vào: '{listening_script}', soạn 2 câu nghe. Soạn tiếp 4 câu trắc nghiệm {topic}.")
            tl_res = call_ai_strict(f"Soạn 3 câu sắp xếp từ thành câu về {topic}. {extra}")
            st.session_state['html_p1'] = process_text_to_html(tn_res, "PART 1: LISTENING & QUIZ", "#e67e22")
            st.session_state['html_p2'] = process_text_to_html(tl_res, "PART 2: READING & WRITING", "#27ae60")
        
        st.session_state['raw_ans'] = call_ai_strict(f"Giải chi tiết đề sau (để chấm bài):\n{tn_res}\n{tl_res}")
        st.rerun()

# --- 5. ĐIỀU HƯỚNG MÀN HÌNH ---
if chuc_nang == "🚀 Làm bài mới":
    st.title(f"🦀 Chào {ten_hs}!")
    if st.button("📝 RA ĐỀ MỚI"): generate_exam(mon_hoc, dang_de, chu_de, do_kho)

elif chuc_nang == "🚑 Luyện tập cải thiện":
    st.title("🚑 Phục thù các lỗi sai cũ")
    df = load_data()
    if df.empty: st.info("Con chưa làm bài nào nên chưa có lỗi để cải thiện. Hãy làm bài mới trước nhé!")
    else:
        last_yeu = df.iloc[-1]['Yeu']
        st.warning(f"Dựa trên bài cũ, con cần cải thiện: {last_yeu}")
        if st.button("💪 BẮT ĐẦU LUYỆN TẬP CẢI THIỆN"):
            generate_exam(mon_hoc, "Luyện tập cải thiện", last_yeu, "Vừa sức", improve_mode=True)

# --- 6. HIỂN THỊ ĐỀ & CHẤM BÀI ---
if st.session_state['html_p1']:
    if st.session_state['geo_image']: st.image(st.session_state['geo_image'], width=400)
    if st.session_state['listening_text']:
        with st.expander("🎧 NGHE ĐOẠN VĂN"):
            gTTS(text=st.session_state['listening_text'], lang='en').write_to_fp(fp := io.BytesIO())
            st.audio(fp, format='audio/mp3')

    st.markdown(st.session_state['html_p1'], unsafe_allow_html=True)
    st.markdown(st.session_state['html_p2'], unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📝 Đáp án TN")
        ans = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
    with c2:
        st.subheader("✍️ Bài làm Tự luận")
        tl_user = st.text_area("Con nhập lời giải vào đây (có thể để trống nếu chưa làm xong):")

    if st.button("✅ NỘP BÀI (Chấp nhận bài dở dang)"):
        phut = round((datetime.now() - st.session_state['start_time']).total_seconds()/60, 1)
        with st.spinner("Đang chấm bài và giải thích chi tiết..."):
            prompt_cham = f"""
            Bạn là giáo viên chấm bài tận tâm. 
            - Đề bài/Đáp án chuẩn: {st.session_state['raw_ans']}
            - Bài làm của HS: TN chọn {ans}, Tự luận viết '{tl_user}'.
            - Chấp nhận bài dở dang (để trống coi như 0 điểm câu đó).
            
            YÊU CẦU PHẢN HỒI (CHỈ TIẾNG VIỆT):
            1. DIEM: [Số điểm thang 10]
            2. PHÂN TÍCH:
               - Những câu làm đúng: Giải thích tại sao đúng.
               - Những câu làm sai hoặc bỏ trống: Chỉ rõ con sai ở đâu, đáp án đúng là gì và GIẢI THÍCH chi tiết để con hiểu.
            3. TOT: [Kỹ năng con đã vững]
            4. YEU: [Dạng bài con cần luyện thêm]
            5. NHANXET: [Lời khuyên cho con]
            """
            res = call_ai_strict(prompt_cham)
            st.markdown(f"### 📊 KẾT QUẢ CỦA {ten_hs.upper()}")
            st.write(res)
            
            try:
                d = int(re.search(r"DIEM:\s*(\d+)", res).group(1))
                tot = re.search(r"TOT:\s*(.*)", res).group(1); yeu = re.search(r"YEU:\s*(.*)", res).group(1)
                nx = re.search(r"NHANXET:\s*(.*)", res).group(1)
                df = load_data(); new = {"Thoi_Gian":datetime.now(),"Mon":mon_hoc,"Dang":chuc_nang,"Diem":d,"Phut":phut,"Tot":tot,"Yeu":yeu,"NhanXet":nx}
                pd.concat([df, pd.DataFrame([new])]).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                if d >= 8: st.balloons()
            except: st.warning("Lưu kết quả gặp lỗi nhỏ, nhưng điểm đã hiện ở trên.")

# --- CÁC PHẦN CÒN LẠI (TIẾN ĐỘ, BÁO CÁO) GIỮ NGUYÊN ---
elif chuc_nang == "📈 Tiến độ":
    df = load_data()
    if not df.empty: st.line_chart(df['Diem']); st.dataframe(df)
elif chuc_nang == "📧 Báo cáo":
    if st.button("Gửi báo cáo cho Bố"):
        df = load_data()
        if not df.empty:
            last = df.iloc[-1]
            prompt = f"Viết báo cáo chuyên sâu gửi bố Kiên dựa trên: Môn {last['Mon']}, Điểm {last['Diem']}, Vùng kiến thức yếu {last['Yeu']}. Đề xuất biện pháp."
            report = call_ai_strict(prompt, "Chuyên gia giáo dục")
            if send_daily_report(report): st.success("Báo cáo đã gửi vào Email của Bố!")
