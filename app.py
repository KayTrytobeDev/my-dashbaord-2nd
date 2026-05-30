import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64  # แก้ NameError: base64

# --- ตั้งค่า ---
st.set_page_config(layout="wide")
API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                # ลบช่องว่างหน้าหลังชื่อคอลัมน์เพื่อความปลอดภัย
                df.columns = df.columns.str.strip()
                return df
        return pd.DataFrame()
    except: return pd.DataFrame()

df = load_data()
if not df.empty:
    # แปลงวันที่โดยใช้ข้อมูลคอลัมน์แรก (Date)
    df['Parsed_Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

# --- เมนู ---
menu = st.sidebar.radio("เมนู:", ["📊 Dashboard", "📅 Calendar", "📝 Report"])

# --- 1. Dashboard ---
if menu == "📊 Dashboard":
    st.title("📊 Risk Dashboard")
    if not df.empty:
        # แก้ ValueError: ใช้ reset_index() และตั้งชื่อคอลัมน์ให้ชัด
        risk_counts = df['Risk Level'].value_counts().reset_index()
        risk_counts.columns = ['Risk', 'Count']
        
        fig_b = px.bar(risk_counts, x='Risk', y='Count', color='Risk',
                       color_discrete_map={'High': '#ff4b4b', 'Medium': '#ffa500', 'Low': '#00cc96'})
        st.plotly_chart(fig_b, use_container_width=True)

# --- 2. Calendar ---
elif menu == "📅 Calendar":
    # (ใช้ Logic การวาดตารางที่ผมส่งให้ก่อนหน้า ตรงนี้จะทำงานได้ปกติถ้า df มีข้อมูล)
    pass 

# --- 3. Report ---
elif menu == "📝 Report":
    with st.form("risk_form"):
        # ... (เพิ่มโค้ดกรอกข้อมูล) ...
        # ตอนใช้ base64 ให้เรียกใช้ได้เลยเพราะ import ไว้แล้วที่บรรทัดบนสุด
        submitted = st.form_submit_button("บันทึก")
        if submitted:
            # ใช้ base64.b64encode(...)
            pass
