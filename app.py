import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(layout="wide")

# 🔴 ใส่ลิงก์ Web App ของพี่ที่นี่
API_URL = "https://script.google.com/macros/s/AKfycbxMCFK88knNYwWyw_aRBqqP4ARGozoWXAfZxgZCndtqK5NCwKZyIyaQ7GvNGp1fBJPP/exec"

@st.cache_data(ttl=5)
def load_data_from_script():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = load_data_from_script()

st.title("🔍 ตรวจสอบข้อมูลดิบใน Google Sheet")

if not df.empty:
    st.write(f"พบข้อมูลทั้งหมด {len(df)} แถว")
    
    # 1. โชว์ชื่อคอลัมน์ทั้งหมด
    st.write("### รายชื่อคอลัมน์ที่ระบบอ่านได้:")
    st.write(df.columns.tolist())
    import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(layout="wide")

# 🔴 ใส่ลิงก์ Web App ของพี่ที่นี่
API_URL = "ใส่ลิงก์ของคุณที่นี่"

@st.cache_data(ttl=5)
def load_data_from_script():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = load_data_from_script()

# ฟังก์ชันแปลงวันที่ พ.ศ. เป็น ค.ศ. แบบแม่นยำ
def parse_thai_date(val):
    try:
        # ตัดเอาแค่ส่วนวันที่ (เช่น 2569-01-13)
        date_str = str(val).split('T')[0]
        y, m, d = map(int, date_str.split('-'))
        # ถ้าปีเป็น พ.ศ. (เกิน 2400) ให้ลบ 543
        if y > 2400:
            y -= 543
        return datetime(y, m, d).date()
    except:
        return None

if not df.empty:
    # แปลงคอลัมน์ "Date" (คอลัมน์แรก)
    df['Parsed_Date'] = df.iloc[:, 0].apply(parse_thai_date)
    
    # เช็กดูว่าแปลงสำเร็จไหม
    success_count = df['Parsed_Date'].notna().sum()
    st.write(f"✅ แปลงวันที่สำเร็จ {success_count} รายการ จากทั้งหมด {len(df)} รายการ")
    
    # ถ้าสำเร็จแล้ว ให้โชว์ตัวอย่าง
    if success_count > 0:
        st.write("ตัวอย่างข้อมูลที่แปลงแล้ว:")
        st.write(df[['Date', 'Parsed_Date']].head())
    else:
        st.error("ยังแปลงวันที่ไม่สำเร็จ รบกวนดู Format ในชีตอีกทีครับ")
else:
    st.info("กำลังโหลดข้อมูล...")
