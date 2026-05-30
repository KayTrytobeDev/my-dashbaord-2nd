import streamlit as st
import pandas as pd
import requests
import calendar
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

# ฟังก์ชันแปลงวันที่ที่เสถียรที่สุด
def parse_thai_date_fixed(val):
    try:
        date_str = str(val).split('T')[0]
        y, m, d = map(int, date_str.split('-'))
        if y > 2400: y -= 543
        return datetime(y, m, d) # ต้องเป็น datetime object ถึงจะใช้ .dt ได้
    except: return pd.NaT

df = load_data_from_script()
if not df.empty:
    df['Parsed_Date'] = pd.to_datetime(df.iloc[:, 0].apply(parse_thai_date_fixed), errors='coerce')

st.title("📅 ปฏิทินติดตามงานและรายละเอียดข้อมูล")

if df.empty:
    st.info("กำลังโหลดข้อมูล หรือไม่มีข้อมูลในระบบ")
else:
    today = datetime.now()
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("เลือกเดือน", range(1, 13), index=today.month-1, format_func=lambda x: calendar.month_name[x])
    with col2:
        year = st.selectbox("เลือกปี ค.ศ.", [2025, 2026, 2027], index=1)

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    data_html = "<table style='width:100%; border:1px solid #ddd;'>"
    data_html += "<tr><th>อา.</th><th>จ.</th><th>อ.</th><th>พ.</th><th>พฤ.</th><th>ศ.</th><th>ส.</th></tr>"
    
    for week in month_days:
        data_html += "<tr>"
        for day in week:
            if day == 0:
                data_html += "<td style='height:80px;'></td>"
            else:
                # 🔴 ใช้ .dt accessor เพื่อความปลอดภัยของข้อมูล
                day_data = df[
                    (df['Parsed_Date'].dt.day == day) & 
                    (df['Parsed_Date'].dt.month == month) & 
                    (df['Parsed_Date'].dt.year == year)
                ]
                
                items = ""
                for _, row in day_data.iterrows():
                    items += f"<div style='background:#e0f7fa; font-size:10px; margin:2px; padding:2px;'>{row.iloc[1]}</div>"
                data_html += f"<td style='height:80px; vertical-align:top; border:1px solid #eee;'><strong>{day}</strong><br>{items}</td>"
        data_html += "</tr>"
    data_html += "</table>"
    
    st.markdown(data_html, unsafe_allow_html=True)
