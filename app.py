import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
import calendar
from datetime import datetime

# คอนฟิกหน้าเว็บเบื้องต้นเปิด Wide Mode
st.set_page_config(page_title="Risk & Corrective Tracker", layout="wide", initial_sidebar_state="expanded")

# 🔴 ใส่ลิงก์ Web App (URL ของ Google Apps Script ที่ลงท้ายด้วย /exec) ของพี่ตรงนี้ได้เลยครับ
API_URL = "เอาลิงก์_Web_App_มาวางตรงนี้" 

# ==========================================
# ฟังก์ชันโหลดข้อมูลผ่าน Web App API
# ==========================================
@st.cache_data(ttl=5)
def load_data_from_script():
    try:
        if "เอาลิงก์" in API_URL or not API_URL.startswith("http"):
            return pd.DataFrame()
            
        response = requests.get(API_URL)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 0:
                headers = raw_data[0]
                rows = raw_data[1:]
                
                if not rows:
                    return pd.DataFrame()
                    
                df = pd.DataFrame(rows, columns=headers)
                df.columns = df.columns.str.strip() 
                return df
            else:
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

df = load_data_from_script()

# ฟังก์ชันจัดการแปลงวันที่ให้อยู่ในฟอร์แมตระบบอย่างยืดหยุ่นและแม่นยำ
def clean_and_parse_date(date_val):
    if pd.isna(date_val) or str(date_val).strip() == "":
        return None
    d_str = str(date_val).strip()
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(d_str, fmt).date()
        except ValueError:
            continue
    return None

target_date_col = 'Date'
target_topic_col = 'Topic/risk finding'

if not df.empty:
    for col in df.columns:
        if col.lower() == 'date': target_date_col = col
        if 'topic' in col.lower() or 'finding' in col.lower(): target_topic_col = col
        
    df['Parsed_Date'] = df[target_date_col].apply(clean_and_parse_date)

# ==========================================
# ระบบเมนูนำทางฝั่งซ้าย (Sidebar Navigator)
# ==========================================
st.sidebar.title("🚨 Risk Tracker System")
page = st.sidebar.radio("เมนูใช้งานระบบ:", [
    "📊 Data Visualizer (หน้าแรก)", 
    "📅 Calendar & Case Detail", 
    "📝 Report New Case"
])

# ==========================================
# หน้าที่ 1: Data Visualizer (หน้าแรก)
# ==========================================
if page == "📊 Data Visualizer (หน้าแรก)":
    st.title("📊 ภาพรวมและสถิติข้อมูลความเสี่ยงประจำองค์กร")
    
    if df.empty or 'Parsed_Date' not in df.columns:
        st.info("💡 ระบบพร้อมใช้งาน ข้อมูลฐานข้อมูลเชื่อมต่อสำเร็จ")
    else:
        total_cases = len(df)
        
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            st.metric(label="📋 จำนวนเคสทั้งหมดในฐานข้อมูล Master", value=f"{total_cases} เคส")
            
        st.markdown("---")
        
        # สรุปสถานะการดำเนินงาน (Column E)
        st.subheader("📌 สรุปสถานะการดำเนินงานแต่ละประเภท (Column E)")
        if 'Status' in df.columns:
            status_df = df['Status'].value_counts().reset_index()
            status_df.columns = ['สถานะ', 'จำนวน']
            status_df['เปอร์เซ็นต์ (%)'] = ((status_df['จำนวน'] / total_cases) * 100).round(2)
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.dataframe(status_df, use_container_width=True, hide_index=True)
            with c2:
                fig_status = px.pie(status_df, values='จำนวน', names='สถานะ', hole=0.4, 
                                    title="สัดส่วนเปอร์เซ็นต์ของสถานะเคสทั้งหมด",
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_status, use_container_width
