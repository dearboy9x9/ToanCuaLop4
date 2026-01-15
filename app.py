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
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from streamlit_mic_recorder import mic_recorder

# --- 1. CẤU HÌNH HỆ THỐNG ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_TEXT = "llama-3.3-70b-versatile"
DATA_FILE = "nhat_ky_hoc_tap_cua.csv"

# --- 2. BẢN ĐỒ KIẾN THỨC MỚI CẬP NHẬT (V78) ---
ENGLISH_BOOK_MAP_V78 = {
    11: {"topic": "My home", "vocab": "big, busy, live, noisy, quiet, street", "focus": "Asking about where someone lives"},
    12: {"topic": "Jobs", "vocab": "actor, farmer, nurse, office worker, policeman", "focus": "Asking about jobs and workplaces"},
    13: {"topic": "Appearance", "vocab": "big, short, slim, tall, eyes, face", "focus": "Asking about appearance"},
    14: {"topic": "Daily activities", "vocab": "watch TV, cooking, wash the clothes, in the afternoon", "focus": "Asking about daily activities"},
    15: {"topic": "My family's weekends", "vocab": "cinema, shopping centre, swimming pool, tennis", "focus": "Asking about weekend activities"},
    16: {"topic": "Weather", "vocab": "cloudy, rainy, sunny, windy, stormy", "focus": "Asking about the weather"},
    17: {"topic": "In the city", "vocab": "go straight, left, right, turn around, campsite", "focus": "Giving directions and signs"},
    18: {"topic": "At the shopping centre", "vocab": "behind, between, near, opposite, price", "focus": "Asking about locations and prices"},
    19: {"topic": "The animal world", "vocab": "crocodiles, giraffes, hippos, lions, dance beautifully", "focus": "Asking about animals"},
    20: {"topic": "At summer camp", "vocab": "building a campfire, dancing around the campfire, singing songs", "focus": "Asking what people are doing"}
}

# --- 3. HÀM DỮ LIỆU & TRÌNH BÀY (FIX LỖI) ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Time", "Mon", "Diem", "Coins", "Yeu", "Phut"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        return df
    df = pd.read_csv(DATA_FILE)
    # Vá lỗi Coins (image_c435b1.png)
    for col in ["Coins", "Phut", "Diem"]:
        if col not in df.columns: df[col] = 0
    return df

def process_text_to_html(text, title, color_hex):
    if not text: return ""
    # Giãn cách dòng khoa học (Tránh lỗi image_c4b4d2.png)
    text = text.replace("\n", "<br>")
    text = re.sub(r'(Câu \d+[:\.])', r'<br><b style="color: #d35400; font-size: 1.1em; display: inline-block; margin-top: 10px;">\1</b>', text)
    
    return f"""
    <div style="background-color: #fdfefe; border-left: 10px solid {color_hex}; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
        <h2 style="color: {color_hex}; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px;">{title}</h2>
        <div style="font-size: 18px; line-height: 1.8; color: #2c3e50;">{text}</div>
    </div>
    """

# --- 4. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Gia Sư AI V78", layout="wide")
with st.sidebar:
    st.title("🛡️ SUPREME V78")
    ten_hs = st.text_input("Học sinh:", "Cua")
    mon_hoc = st.selectbox("🎯 Môn học:", ["🇬🇧 Tiếng Anh 4 (Global Success)", "🧮 Toán 4 (Cánh Diều)"])
    
    if "Tiếng Anh" in mon_hoc:
        unit = st.number_input("Chọn Unit (11-20):", 11, 20, 11)
        data_unit = ENGLISH_BOOK_MAP_V78.get(unit)
        st.info(f"📍 Topic: {data_unit['topic']}")
        st.write(f"Vocab: {data_unit['vocab']}")

# (Tiếp tục các logic xử lý AI và Chấm điểm như bản V77)
