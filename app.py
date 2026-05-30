import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
from datetime import datetime

# คอนฟิกหน้าเว็บเบื้องต้นเปิด Wide Mode
st.set_page_config(page_title="Risk & Corrective Tracker", layout="wide", initial_sidebar_state="expanded")

# ดึงลิงก์ผ่านระบบ Secrets ของ Streamlit Cloud อัตโนมัติ
try:
    API_URL = st.secrets["SCRIPT_URL"]
except:
    API_URL = "https://script.google.com/macros/s/XXXXX/exec" 

# ==========================================
# ฟังก์ชันโหลดข้อมูลผ่าน Web App API
# ==========================================
@st.cache_data(ttl=30) # ลด Cache ลงเหลือ 30 วินาทีเพื่อให้ข้อมูลอัปเดตไวขึ้น
def load_data_from_script():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 0:
                headers = raw_data[0]
                rows = raw_data[1:]
                df = pd.DataFrame(rows, columns=headers)
                df.columns = df.columns.str.strip() # ล้างช่องว่างที่หัวตาราง
                return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
        return pd.DataFrame()

df = load_data_from_script()

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
    
    if df.empty:
        st.warning("⚠️ ไม่พบข้อมูลในระบบหรือระบบเชื่อมต่อขัดข้อง กรุณาตรวจสอบการตั้งค่า!")
    else:
        total_cases = len(df)
        
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            st.metric(label="📋 จำนวนเคสทั้งหมดในฐานข้อมูล Master", value=f"{total_cases} เคส")
            
        st.markdown("---")
        
        # สรุปสถานะการดำเนินงาน
        st.subheader("📌 สรุปสถานะการดำเนินงานแต่ละประเภท")
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
                st.plotly_chart(fig_status, use_container_width=True)
                
        st.markdown("---")
        
        # สรุประดับความเสี่ยง
        st.subheader("🔥 สรุปเปอร์เซ็นต์แยกตามระดับความเสี่ยง")
        if 'Risk Level' in df.columns:
            risk_order = ['Low', 'Medium', 'High']
            risk_df = df['Risk Level'].value_counts().reindex(risk_order, fill_value=0).reset_index()
            risk_df.columns = ['ระดับความเสี่ยง', 'จำนวน']
            risk_df['เปอร์เซ็นต์ (%)'] = ((risk_df['จำนวน'] / total_cases) * 100).round(2)
            
            c3, c4 = st.columns([1, 1])
            with c3:
                st.dataframe(risk_df, use_container_width=True, hide_index=True)
            with c4:
                color_map = {'Low': '#2ca02c', 'Medium': '#ff7f0e', 'High': '#d62728'}
                fig_risk = px.bar(risk_df, x='ระดับความเสี่ยง', y='จำนวน', text='เปอร์เซ็นต์ (%)',
                                  title="กราฟแสดงเปอร์เซ็นต์ระดับความเสี่ยง",
                                  color='ระดับความเสี่ยง', color_discrete_map=color_map)
                fig_risk.update_traces(texttemplate='%{text}%', textposition='outside')
                st.plotly_chart(fig_risk, use_container_width=True)

# ==========================================
# หน้าที่ 2: Calendar & Case Detail (เวอร์ชันกันล่ม)
# ==========================================
elif page == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงานและรายละเอียดข้อมูลเคสเชิงลึก")
    st.caption("เลือกตรวจสอบวันที่ต้องการจากตัวเลือกปฏิทินเพื่อเรียกดูประวัติและหลักฐานการแก้ไข")
    
    if df.empty:
        st.info("💡 ไม่มีข้อมูลแสดงผลในระบบ")
    else:
        # ระบบจัดการและทำความสะอาดฟอร์แมตวันที่เพื่อความปลอดภัย ป้องกันข้อมูลในชีทเพี้ยน
        parsed_dates = []
        for d in df['Date'].dropna().unique():
            d_str = str(d).strip()
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    parsed_dates.append(datetime.strptime(d_str, fmt).date())
                    break
                except ValueError:
                    continue
        
        # ค้นหาวันที่ล่าสุดที่มีข้อมูลเพื่อตั้งเป็นค่าเริ่มต้น
        default_date = max(parsed_dates) if parsed_dates else datetime.now().date()
        
        # แสดงกล่องปฏิทินให้เลือกวัน (เสถียรสูง หน้าเว็บไม่มีทางล่ม)
        col_cal, col_info = st.columns([1, 2])
        with col_cal:
            selected_date = st.date_input("📆 คลิกเลือกวันที่บนปฏิทิน:", default_date)
        
        # แปลงวันที่ยูเซอร์เลือกให้อยู่ในรูปแบบ String เพื่อไปค้นใน DataFrame
        search_str_1 = selected_date.strftime("%m/%d/%Y")
        search_str_2 = selected_date
