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

# --- 1. CẤU HÌNH GROQ ---
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

MODEL_TEXT = "llama-3.3-70b-versatile"
MODEL_VISION = "llama-3.2-11b-vision-preview"

DATA_FILE = "bang_diem_hoc_sinh.csv"
THOI_GIAN_LAM_BAI = 40

# --- 2. HÀM XỬ LÝ TEXT & HTML (V54 - ĐỒNG BỘ HÓA FORMAT) ---
def process_text_to_html(text, title, color_hex):
    """
    Hàm biến văn bản thô thành 1 khối HTML đẹp.
    """
    if not text: return ""
    
    # 1. Dọn rác
    text = text.replace("```html", "").replace("```", "").strip()
    
    # 2. Xử lý xuống dòng
    text = re.sub(r'\n{2,}', '<br><br>', text)
    text = text.replace('\n', '<br>')
    
    # 3. CHUẨN HÓA SỐ CÂU (Xóa dấu - ở đầu, tô màu cam đậm)
    # Tìm: (Đầu dòng hoặc <br>) + (Dấu - hoặc khoảng trắng) + (Câu X: hoặc X.)
    # Thay bằng: <br><b>Câu X:</b> (Màu cam)
    text = re.sub(r'(^|<br>)\s*[-]*\s*(Câu \d+[:\.]|\d+[:\.])', r'\1<b style="color: #d35400; font-size: 1.1em;">\2</b>', text)
    
    # 4. IN ĐẬM Đáp án A. B. C. D.
    text = re.sub(r'(^|<br>)\s*([A-D][:\.])', r'\1<b>\2</b>', text)
    
    # Tạo khung HTML
    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; background-color: #fff; border: 2px solid {color_hex}; border-radius: 10px; padding: 20px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid {color_hex}; padding-bottom: 10px; font-weight: 800; text-transform: uppercase;">
            {title}
        </h2>
        <div style="font-size: 16px; line-height: 1.8;">
            {text}
        </div>
    </div>
    """
    return html

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def call_groq_simple(prompt):
    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_TEXT,
            temperature=0.5
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"Lỗi AI: {str(e)}"

# --- 3. CÁC HÀM XỬ LÝ DỮ LIỆU ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Thoi_Gian", "Ten_HS", "Dang_Bai", "Diem_So", "Nhan_Xet", "Phan_Loai_Loi"])
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

def save_score(ten, dang_bai, diem, nhan_xet, phan_loai_loi):
    df = load_data()
    new_row = {
        "Thoi_Gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Ten_HS": ten,
        "Dang_Bai": dang_bai,
        "Diem_So": diem,
        "Nhan_Xet": nhan_xet,
        "Phan_Loai_Loi": phan_loai_loi
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def get_weakness_analysis(ten):
    df = load_data()
    if df.empty: return []
    hs_data = df[df["Ten_HS"] == ten]
    bai_yeu = hs_data[hs_data["Diem_So"] < 7]
    if bai_yeu.empty: return []
    return bai_yeu["Dang_Bai"].value_counts().index.tolist()

def get_total_stars(ten):
    df = load_data()
    if df.empty: return 0
    hs_data = df[df["Ten_HS"] == ten]
    stars = hs_data[hs_data["Diem_So"] >= 8].shape[0]
    return stars

def get_adaptive_difficulty(ten):
    df = load_data()
    if df.empty: return "Cơ bản (SGK)"
    hs_data = df[df["Ten_HS"] == ten]
    if hs_data.empty: return "Cơ bản (SGK)"
    last_score = hs_data.iloc[-1]["Diem_So"]
    if last_score >= 8: return "Nâng cao (Tư duy)"
    elif last_score >= 5: return "Vận dụng"
    else: return "Cơ bản (SGK)"

# --- 4. GIAO DIỆN ---
st.set_page_config(page_title="Toán Cánh Diều Lớp 4", page_icon="kite", layout="wide")

st.markdown("""
<style>
    .block-container {
        max-width: 1000px !important;
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        margin: 0 auto !important;
    }
    .stButton>button {
        background-color: #f55036; color: white; border-radius: 6px; 
        height: 45px; font-weight: bold; font-size: 16px; width: 100%;
        margin-top: 10px;
    }
    .mc-box {
        background-color: #f8f9fa; padding: 15px; border-radius: 8px; 
        margin-bottom: 10px; border: 1px solid #e9ecef; 
        font-weight: bold; color: #495057; font-size: 16px;
    }
    .star-box {
        font-size: 18px; color: #FBC02D; font-weight: bold; padding: 8px; 
        border: 2px dashed #FBC02D; border-radius: 8px; text-align: center; margin-bottom: 10px;
    }
    h1, h2, h3 { margin-bottom: 10px !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10608/10608822.png", width=50)
    
    if 'exam_end_timestamp' not in st.session_state: st.session_state['exam_end_timestamp'] = 0.0
    if 'da_nop_bai' not in st.session_state: st.session_state['da_nop_bai'] = False
    
    # LƯU TRỮ HTML RIÊNG BIỆT
    if 'html_tn' not in st.session_state: st.session_state['html_tn'] = ""
    if 'html_tl' not in st.session_state: st.session_state['html_tl'] = ""
    
    if 'raw_dap_an' not in st.session_state: st.session_state['raw_dap_an'] = ""
    
    current_ts = datetime.now().timestamp()
    if st.session_state['exam_end_timestamp'] > current_ts and not st.session_state['da_nop_bai']:
        end_ts_int = int(st.session_state['exam_end_timestamp'] * 1000)
        html_code = f"""
        <div style="font-size: 24px; font-weight: bold; color: #D32F2F; text-align: center; border: 2px solid #D32F2F; padding: 8px; border-radius: 8px; background-color: #FFEBEE; margin-bottom: 15px; font-family: sans-serif;">
            ⏳ <span id="time_display">00:00</span>
        </div>
        <script>
        var countDownDate = {end_ts_int};
        var x = setInterval(function() {{
            var now = new Date().getTime();
            var distance = countDownDate - now;
            if (distance < 0) {{
                clearInterval(x);
                document.getElementById("time_display").innerHTML = "HẾT GIỜ";
            }} else {{
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                if (minutes < 10) minutes = "0" + minutes;
                if (seconds < 10) seconds = "0" + seconds;
                document.getElementById("time_display").innerHTML = minutes + ":" + seconds;
            }}
        }}, 1000);
        </script>
        """
        components.html(html_code, height=70)
    elif st.session_state['exam_end_timestamp'] > 0 and st.session_state['da_nop_bai']:
        st.info("🏁 Đã nộp")

    st.markdown("### TOÁN CÁNH DIỀU (Groq)")
    ten_hs = st.text_input("Tên con:", "Cua")
    so_sao = get_total_stars(ten_hs)
    st.markdown(f'<div class="star-box">⭐ {so_sao} SAO</div>', unsafe_allow_html=True)
    
    st.write("---")
    menu = st.radio("Chức năng:", [
        "📚 Luyện tập Bài lẻ", 
        "📝 Thi Thử HK1 (40p)",
        "📝 Thi Thử HK2 (40p)", 
        "🚑 Khắc phục điểm yếu"
    ])
    
    dang_bai = ""
    do_kho = "Cơ bản"
    
    if menu == "📚 Luyện tập Bài lẻ":
        dang_bai = st.selectbox("Chọn bài:", [
            "HK1 - Số tự nhiên (Hàng, Lớp)",
            "HK1 - 4 Phép tính (Số tự nhiên)",
            "HK1 - Tìm số trung bình cộng",
            "HK1 - Góc & Đường thẳng",
            "HK1 - Yến, tạ, tấn, giây, thế kỷ",
            "HK2 - Phân số (Cơ bản)",
            "HK2 - Hình thoi & Bình hành"
        ])
        do_kho = st.select_slider("Độ khó:", ["Cơ bản", "Vận dụng", "Nâng cao"])
    elif "Thi Thử" in menu:
        dang_bai = f"ĐỀ THI TỔNG HỢP"
        do_kho = get_adaptive_difficulty(ten_hs)
        st.info(f"🎯 Độ khó: {do_kho}")
    elif menu == "🚑 Khắc phục điểm yếu":
        ds_yeu = get_weakness_analysis(ten_hs)
        if not ds_yeu:
            st.success("Tốt!")
            dang_bai = "Ôn tập nâng cao"
        else:
            st.error(f"⚠️ Ôn: {ds_yeu[0]}")
            dang_bai = ds_yeu[0]
        do_kho = "Cơ bản -> Vận dụng"

    st.write("---")
    st.markdown("**🔒 Góc Phụ Huynh**")
    pin_input = st.text_input("PIN (1990):", type="password", key="pin_entry")
    if pin_input == "1990":
        st.session_state['is_parent_unlocked'] = True

# --- 6. MÀN HÌNH CHÍNH ---
st.title(f"🦀 Xin chào {ten_hs}!")

if st.button("📝 RA ĐỀ BÀI MỚI"):
    st.session_state['da_nop_bai'] = False
    st.session_state['ket_qua_cham'] = ""
    st.session_state['is_parent_unlocked'] = False
    st.session_state['html_tn'] = ""
    st.session_state['html_tl'] = ""
    
    end_time = datetime.now() + timedelta(minutes=THOI_GIAN_LAM_BAI)
    st.session_state['exam_end_timestamp'] = end_time.timestamp()

    # --- CHUẨN HÓA NỘI DUNG ---
    if menu == "📝 Thi Thử HK1 (40p)":
            noi_dung = f"ĐỀ THI TOÁN LỚP 4 HK1 (Cánh Diều). Nội dung: Số tự nhiên, 4 phép tính, Trung bình cộng, Góc, Đổi đơn vị. KHÔNG CÓ PHÂN SỐ."
    elif menu == "📝 Thi Thử HK2 (40p)":
            noi_dung = f"ĐỀ THI TOÁN LỚP 4 HK2 (Cánh Diều). Nội dung: Phân số, Hình bình hành, Hình thoi, Xác suất, Thống kê."
    elif "Luyện tập" in menu:
            noi_dung = f"LUYỆN TẬP CHUYÊN SÂU: '{dang_bai}'. Tập trung vào dạng bài này."
    else: 
            noi_dung = f"KHẮC PHỤC ĐIỂM YẾU: '{dang_bai}'. Ôn tập kỹ dạng này."

    # --- GỌI AI 2 LẦN (ÁP DỤNG CHO CẢ LUYỆN TẬP VÀ THI THỬ) ---
    
    # 1. TRẮC NGHIỆM
    with st.spinner("🤖 Đang soạn TRẮC NGHIỆM (Phần 1/2)..."):
        prompt_tn = f"""
        Vai trò: Giáo viên Toán Lớp 4.
        Nhiệm vụ: Soạn 6 câu TRẮC NGHIỆM về: {noi_dung}. Độ khó: {do_kho}.
        
        YÊU CẦU FORMAT NGHIÊM NGẶT:
        - Câu 1: [Nội dung câu hỏi]
          A. [Đáp án]
          B. [Đáp án]
          C. [Đáp án]
          D. [Đáp án]
        - Các đáp án A,B,C,D phải xuống dòng.
        - CHỈ VIẾT TỪ CÂU 1 ĐẾN CÂU 6. KHÔNG VIẾT CÂU 7, 8, 9.
        - TUYỆT ĐỐI KHÔNG VIẾT GÌ THÊM (Không lời chào).
        """
        tn_content = call_groq_simple(prompt_tn)

    # 2. TỰ LUẬN
    with st.spinner("🤖 Đang soạn TỰ LUẬN (Phần 2/2)..."):
        prompt_tl = f"""
        Vai trò: Giáo viên Toán Lớp 4.
        Nhiệm vụ: Soạn 3 câu TỰ LUẬN về: {noi_dung}. Độ khó: {do_kho}.
        
        YÊU CẦU:
        - Câu 7: [Nội dung câu hỏi]
        - Câu 8: [Nội dung câu hỏi]
        - Câu 9: [Nội dung câu hỏi]
        - CHỈ VIẾT CÂU HỎI, KHÔNG VIẾT ĐÁP ÁN.
        - TUYỆT ĐỐI KHÔNG VIẾT LẠI CÁC CÂU TRẮC NGHIỆM.
        """
        tl_content = call_groq_simple(prompt_tl)
    
    # --- CHẾ BIẾN THÀNH 2 KHỐI HTML RIÊNG BIỆT ---
    st.session_state['html_tn'] = process_text_to_html(tn_content, "PHẦN 1: TRẮC NGHIỆM (3 điểm)", "#e67e22") # Màu Cam
    st.session_state['html_tl'] = process_text_to_html(tl_content, "PHẦN 2: TỰ LUẬN (7 điểm)", "#2980b9") # Màu Xanh
    
    # Tạo đáp án ngầm
    with st.spinner("🤖 Đang tạo đáp án..."):
        prompt_ans = f"Giải chi tiết đề thi này:\n{tn_content}\n{tl_content}"
        st.session_state['raw_dap_an'] = call_groq_simple(prompt_ans)
        
    st.rerun()

# --- HIỂN THỊ ĐỀ (RENDER 2 KHỐI HTML RỜI NHAU) ---
if st.session_state['html_tn'] and st.session_state['html_tl']:
    st.markdown('<div class="review-badge">⚡ Powered by Groq Llama 3.3 (Sync Master)</div>', unsafe_allow_html=True)
    
    # HIỂN THỊ KHỐI TRẮC NGHIỆM
    st.markdown(st.session_state['html_tn'], unsafe_allow_html=True)
    
    # HIỂN THỊ KHỐI TỰ LUẬN
    st.markdown(st.session_state['html_tl'], unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown('<div class="mc-box"><b>📝 PHIẾU TRẢ LỜI TRẮC NGHIỆM</b></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        ans1 = c1.radio("Câu 1:", ["A","B","C","D"], index=None, horizontal=True)
        ans2 = c2.radio("Câu 2:", ["A","B","C","D"], index=None, horizontal=True)
        ans3 = c1.radio("Câu 3:", ["A","B","C","D"], index=None, horizontal=True)
        ans4 = c2.radio("Câu 4:", ["A","B","C","D"], index=None, horizontal=True)
        ans5 = c1.radio("Câu 5:", ["A","B","C","D"], index=None, horizontal=True)
        ans6 = c2.radio("Câu 6:", ["A","B","C","D"], index=None, horizontal=True)

    with col_r:
        st.markdown('<div class="mc-box"><b>✍️ BÀI LÀM TỰ LUẬN</b></div>', unsafe_allow_html=True)
        bai_lam_text = st.text_area("Nhập bài giải của con:", height=150)
        uploaded_files = st.file_uploader("Hoặc chụp ảnh bài làm:", type=['jpg', 'png'], accept_multiple_files=True)
        cam = st.camera_input("Chụp ảnh trực tiếp")
        final_images = []
        if uploaded_files:
            for f in uploaded_files: final_images.append(f)
        if cam: final_images.append(cam)

    st.write("")
    if not st.session_state['da_nop_bai']:
        if st.button("✅ NỘP BÀI"):
            st.session_state['exam_end_timestamp'] = 0.0
            tn_str = f"1:{ans1 or 'X'}, 2:{ans2 or 'X'}, 3:{ans3 or 'X'}, 4:{ans4 or 'X'}, 5:{ans5 or 'X'}, 6:{ans6 or 'X'}"
            
            with st.spinner("Đang chấm bài..."):
                prompt_cham = f"""
                Bạn là giáo viên Toán chấm thi nghiêm khắc.
                - Đề bài và Đáp án chuẩn: {st.session_state['raw_dap_an']}
                - Trắc nghiệm HS chọn: {tn_str}
                - Tự luận HS làm: {bai_lam_text if bai_lam_text else "TRỐNG"}
                YÊU CẦU: Chấm điểm thang 10.
                Định dạng trả về:
                DIEM: [Số điểm]
                NHAN_XET: [Nhận xét]
                LOAI_LOI: [Lỗi sai]
                """
                
                try:
                    res_text = call_groq_simple(prompt_cham)
                    st.session_state['ket_qua_cham'] = res_text
                    st.session_state['da_nop_bai'] = True
                    
                    try:
                        diem = 0
                        loai_loi = "Không"
                        for line in res_text.split('\n'):
                            if "DIEM:" in line.upper():
                                num = ''.join(filter(str.isdigit, line))
                                if num: diem = int(num)
                        if "LOAI_LOI:" in res_text:
                            parts = res_text.split("LOAI_LOI:")
                            if len(parts) > 1: loai_loi = parts[1].strip().split('\n')[0]
                        save_score(ten_hs, dang_bai, diem, "Groq AI", loai_loi)
                        if diem >= 8: st.balloons()
                    except: pass
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi chấm: {e}")

# --- KẾT QUẢ ---
if st.session_state['da_nop_bai']:
    st.success("KẾT QUẢ CHI TIẾT:")
    st.write(st.session_state['ket_qua_cham'])
    if st.button("LÀM ĐỀ TIẾP THEO"):
        st.session_state['html_tn'] = ""
        st.session_state['html_tl'] = ""
        st.session_state['da_nop_bai'] = False
        st.session_state['is_parent_unlocked'] = False
        st.rerun()

# --- GÓC PHỤ HUYNH ---
if st.session_state['raw_dap_an']:
    if st.session_state['is_parent_unlocked']:
        st.success("🔓 ĐÁP ÁN GỐC:")
        st.info(st.session_state['raw_dap_an'])
        if st.button("🔒 KHÓA LẠI"):
            st.session_state['is_parent_unlocked'] = False
            st.rerun()