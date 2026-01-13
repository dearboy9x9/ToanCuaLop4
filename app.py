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
from gtts import gTTS # Thư viện phát âm tiếng Anh

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# Cấu hình Email (Ông chủ điền thông tin vào đây)
EMAIL_GUI = "tkl261088@gmail.com" 
EMAIL_NHAN = "tkl261088@gmail.com" # Thay bằng email thật của ông chủ
MAT_KHAU_APP = "fusrfveagwyrhzte" # Mật khẩu ứng dụng Gmail

# --- 2. HÀM GỬI BÁO CÁO EMAIL ---
def send_daily_report(report_content):
    if MAT_KHAU_APP == "xxxx xxxx xxxx xxxx": return # Chưa cấu hình thì bỏ qua
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_GUI
        msg['To'] = EMAIL_NHAN
        msg['Subject'] = f"🚀 BÁO CÁO CHIẾN THUẬT HỌC TẬP - BÉ CUA ({datetime.now().strftime('%d/%m/%Y')})"
        msg.attach(MIMEText(report_content, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_GUI, MAT_KHAU_APP)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# --- 3. HÀM PHÁT ÂM TIẾNG ANH (LISTENING) ---
def play_english_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp, format='audio/mp3')

# --- 4. CƠ SỞ DỮ LIỆU NÂNG CẤP ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Thoi_Gian", "Mon_Hoc", "Dang_Bai", "Diem", "Thoi_Gian_Lam", "Diem_Tot", "Diem_Yeu", "Nhan_Xet"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    return pd.read_csv(DATA_FILE)

def save_detailed_log(mon, dang, diem, phut, tot, yeu, nhan_xet):
    df = load_data()
    new_entry = {
        "Thoi_Gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Mon_Hoc": mon,
        "Dang_Bai": dang,
        "Diem": diem,
        "Thoi_Gian_Lam": phut,
        "Diem_Tot": tot,
        "Diem_Yeu": yeu,
        "Nhan_Xet": nhan_xet
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 5. HÀM XỬ LÝ GIAO DIỆN & AI ---
def call_groq(prompt, system_msg=""):
    try:
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            model=MODEL_TEXT,
            temperature=0.5
        )
        return chat.choices[0].message.content
    except Exception as e: return f"Lỗi AI: {str(e)}"

def format_html_box(text, title, color_hex):
    # Tự động dọn rác và in đậm Câu X
    text = text.replace("直", "vuông").replace("\n", "<br>")
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', r'\1<b style="color: #d35400; font-size: 1.1em;">\2</b>', text)
    return f"""
    <div style="background-color: #fff; border: 2px solid {color_hex}; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid {color_hex}; padding-bottom: 10px; font-weight: 800; text-transform: uppercase;">{title}</h2>
        <div style="font-size: 16px; line-height: 1.8; color: #333;">{text}</div>
    </div>
    """

# --- 6. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Hệ Thống Học Tập Thông Minh", page_icon="🎓", layout="wide")

# Khởi tạo session
if 'start_time' not in st.session_state: st.session_state['start_time'] = None
if 'html_tn' not in st.session_state: st.session_state.update({'html_tn':"", 'html_tl':"", 'raw_ans':"", 'listening_text':""})

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10608/10608822.png", width=60)
    st.title("GIA SƯ AI V56")
    ten_hs = st.text_input("Tên học sinh:", "Cua")
    
    mon_hoc = st.selectbox("Chọn môn học:", ["🧮 Toán Lớp 4 (Cánh Diều)", "🇬🇧 Tiếng Anh 4 (Global Success)"])
    chuc_nang = st.radio("Chức năng:", ["📚 Luyện tập", "📝 Thi thử", "📈 Xem tiến độ"])
    
    st.write("---")
    if st.button("📧 GỬI BÁO CÁO CHO BỐ NGAY"):
        with st.spinner("Đang tổng hợp báo cáo..."):
            df = load_data()
            last_work = df.iloc[-1] if not df.empty else None
            if last_work is not None:
                prompt_report = f"""Dựa vào kết quả: Môn {last_work['Mon_Hoc']}, Điểm {last_work['Diem']}, Thời gian {last_work['Thoi_Gian_Lam']} phút. 
                Điểm tốt: {last_work['Diem_Tot']}, Điểm yếu: {last_work['Diem_Yeu']}.
                Viết một báo cáo gửi phụ huynh: Thực trạng, phương hướng cải thiện, đề xuất phối hợp, lộ trình cụ thể."""
                report = call_groq(prompt_report, "Bạn là chuyên gia giáo dục 20 năm kinh nghiệm.")
                if send_daily_report(report): st.success("Đã gửi báo cáo vào Email bố Kiên!")
                else: st.error("Lỗi gửi Email. Vui lòng kiểm tra cấu hình.")

# --- MÀN HÌNH CHÍNH ---
st.title(f"🌟 Chào mừng {ten_hs} đến với lớp học thông minh!")

if chuc_nang == "📈 Xem tiến độ":
    df = load_data()
    if df.empty: st.info("Chưa có dữ liệu học tập.")
    else:
        st.subheader("Biểu đồ điểm số gần đây")
        st.line_chart(df['Diem'])
        st.write("Nhật ký chi tiết:")
        st.dataframe(df)

elif "Toán" in mon_hoc or "Tiếng Anh" in mon_hoc:
    if st.button("🚀 BẮT ĐẦU LÀM BÀI MỚI"):
        st.session_state['start_time'] = datetime.now()
        st.session_state['da_nop_bai'] = False
        
        is_english = "Tiếng Anh" in mon_hoc
        subject_info = "Global Success" if is_english else "Cánh Diều"
        
        with st.spinner("AI đang soạn đề bài cá nhân hóa..."):
            # Soạn trắc nghiệm
            prompt_tn = f"Soạn 6 câu trắc nghiệm {mon_hoc} {subject_info}. Nếu là Tiếng Anh, hãy có 2 câu nghe (viết văn bản nghe ngắn)."
            tn_res = call_groq(prompt_tn, "Giáo viên chuyên môn cao.")
            st.session_state['html_tn'] = format_html_box(tn_res, "PHẦN 1: TRẮC NGHIỆM (3 điểm)", "#e67e22")
            
            # Soạn tự luận
            prompt_tl = f"Soạn 3 câu tự luận {mon_hoc} {subject_info}. Chỉ viết câu hỏi."
            tl_res = call_groq(prompt_tl, "Giáo viên chuyên môn cao.")
            st.session_state['html_tl'] = format_html_box(tl_res, "PHẦN 2: TỰ LUẬN (7 điểm)", "#2980b9")
            
            # Đáp án ngầm
            st.session_state['raw_ans'] = call_groq(f"Giải chi tiết:\n{tn_res}\n{tl_res}")
            
            # Xử lý phần nghe nếu là tiếng Anh
            if is_english:
                listening_part = call_groq(f"Viết 1 đoạn văn tiếng Anh cực ngắn (3 câu) dùng cho bài nghe lớp 4 từ đề trên.")
                st.session_state['listening_text'] = listening_part

    # HIỂN THỊ ĐỀ
    if st.session_state['html_tn']:
        st.markdown(st.session_state['html_tn'], unsafe_allow_html=True)
        
        if st.session_state['listening_text']:
            with st.expander("🎧 PHẦN NGHE (Bấm để nghe đoạn văn)"):
                play_english_audio(st.session_state['listening_text'])
                st.info("Con nghe đoạn văn trên và trả lời câu hỏi trắc nghiệm nhé!")

        st.markdown(st.session_state['html_tl'], unsafe_allow_html=True)
        
        # PHIẾU LÀM BÀI
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📝 Đáp án trắc nghiệm:")
            ans = [st.radio(f"Câu {i+1}:", ["A","B","C","D"], index=None, horizontal=True, key=f"q{i}") for i in range(6)]
        with col2:
            st.subheader("✍️ Bài làm tự luận:")
            tl_text = st.text_area("Nhập lời giải hoặc mô tả bài làm:")
            img_files = st.file_uploader("Gửi ảnh bài làm (nếu có):", accept_multiple_files=True)

        if st.button("✅ NỘP BÀI & CHẤM ĐIỂM"):
            end_time = datetime.now()
            duration = round((end_time - st.session_state['start_time']).total_seconds() / 60, 1)
            
            with st.spinner("AI đang phân tích và đánh giá..."):
                prompt_cham = f"""Chấm bài nghiêm khắc. 
                Đề/Đáp án: {st.session_state['raw_ans']}
                HS làm: TN: {ans}, TL: {tl_text}.
                YÊU CẦU TRẢ VỀ ĐÚNG ĐỊNH DẠNG:
                DIEM: [số]
                TOT: [những điểm làm tốt]
                YEU: [những điểm cần cải thiện]
                NHANXET: [lời khuyên]
                """
                res = call_groq(prompt_cham, "Giáo viên Toán/Anh chuyên nghiệp.")
                st.write(res)
                
                # Trích xuất dữ liệu lưu log
                try:
                    d = int(re.search(r"DIEM:\s*(\d+)", res).group(1))
                    t = re.search(r"TOT:\s*(.*)", res).group(1)
                    y = re.search(r"YEU:\s*(.*)", res).group(1)
                    nx = re.search(r"NHANXET:\s*(.*)", res).group(1)
                    save_detailed_log(mon_hoc, chuc_nang, d, duration, t, y, nx)
                    if d >= 8: st.balloons()
                    st.success(f"Đã hoàn thành bài trong {duration} phút! Dữ liệu đã được lưu.")
                except: st.warning("Lưu dữ liệu gặp chút trục trặc, nhưng kết quả đã hiện ở trên.")

# GÓC PHỤ HUYNH
if st.session_state['raw_ans'] and st.sidebar.text_input("PIN Bố Kiên:", type="password") == "1990":
    st.divider()
    st.subheader("🔓 ĐÁP ÁN CHI TIẾT DÀNH CHO PHỤ HUYNH")
    st.info(st.session_state['raw_ans'])
