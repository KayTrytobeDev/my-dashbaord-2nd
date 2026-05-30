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

st.title("🔍 ตรวจสอบข้อมูลดิบใน Google Sheet")

if not df.empty:
    st.write(f"พบข้อมูลทั้งหมด {len(df)} แถว")
    
    # 1. โชว์ชื่อคอลัมน์ทั้งหมด
    st.write("### รายชื่อคอลัมน์ที่ระบบอ่านได้:")
    st.write(df.columns.tolist())
    
    # 2. โชว์ข้อมูลดิบๆ ในคอลัมน์ที่น่าจะเป็นวันที่ (เช่นคอลัมน์แรก)
    st.write("### ข้อมูล 5 แถวแรกในคอลัมน์แรก (ลองเช็กดูว่าคือวันที่ใช่ไหม):")
    st.write(df.iloc[:, 0].head())
    
    # 3. ลองพยายามแปลงให้ดู
    st.write("### ทดสอบแปลงวันที่ (ตัวอย่าง):")
    def try_parse(val):
        return pd.to_datetime(val, errors='coerce')
    
    test_df = df.iloc[:, 0].apply(try_parse)
    st.write(test_df.head())
    
    st.info("💡 พี่ครับ: ถ้าตารางด้านบนคอลัมน์แรกไม่ใช่วันที่ หรือช่องแปลงวันที่เป็น NaT (ว่างเปล่า) แสดงว่าต้องเปลี่ยนคอลัมน์ที่ดึงครับ")
else:
    st.error("ยังไม่สามารถดึงข้อมูลได้ รบกวนเช็ก URL Web App ครับ")
