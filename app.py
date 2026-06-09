import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64

# ตั้งค่าหน้าเว็บให้ดูโปรและกว้างเต็มจอ
st.set_page_config(page_title="Risk Tracker System", layout="wide")

# ลิงก์ Web App ของ Google Apps Script
API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

# --- ฟังก์ชันดึงและจัดการข้อมูล (ป้องกัน Error เรื่องวันที่) ---
@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                df.columns = df.columns.str.strip() # ลบช่องว่างหัวคอลัมน์
                
                # แปลงคอลัมน์แรกให้เป็นวันที่แบบ Datetime Object ของ Python รองรับ วัน/เดือน/ปี ไทย
                date_col = df.columns[0]
                df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
                return df
        return pd.DataFrame()
    except: 
        return pd.DataFrame()

# โหลดข้อมูลเข้าสู่ระบบ
df = load_data()

# --- เมนู Sidebar ---
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# 1. SUPERCHARGED DASHBOARD (หน้าแดชบอร์ดประสิทธิภาพสูง)
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 ระบบวิเคราะห์และสรุปภาพรวมความเสี่ยง")
    st.markdown("ข้อมูลอัปเดตแบบ Real-time จากระบบจัดการความเสี่ยง")
    
    if not df.empty:
        try:
            # กำหนดชื่อคอลัมน์หลัก
            date_col = df.columns[0]
            status_col = 'Status'
            risk_col = 'Risk Level'
            
            # --- ส่วนที่ 1: KPI Metrics Card ---
            total_cases = len(df)
            completed_cases = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ', na=False)])
            high_risk_cases = len(df[df[risk_col].astype(str) == 'High'])
            
            # คำนวณร้อยละความสำเร็จในการปิดเคส
            success_rate = (completed_cases / total_cases * 100) if total_cases > 0 else 0
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric(label="📌 เคสความเสี่ยงทั้งหมด", value=f"{total_cases} เคส")
            m_col2.metric(label="✅ ดำเนินการสำเร็จแล้ว", value=f"{completed_cases} เคส")
            m_col3.metric(label="🚨 เคสวิกฤต (High Risk)", value=f"{high_risk_cases} เคส")
            m_col4.metric(label="📈 อัตราการแก้ปัญหาสำเร็จ", value=f"{success_rate:.1f}%")
            
            st.markdown("---")
            
            # --- ส่วนที่ 2: Interactive Charts ---
            g_col1, g_col2 = st.columns(2)
            
            with g_col1:
                st.subheader("💡 สัดส่วนสถานะการดำเนินงาน")
                status_counts = df[status_col].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                # ทำเป็น Donut Chart สวยๆ
                fig_pie = px.pie(status_counts, values='Count', names='Status', hole=0.5,
                                 color_discrete_sequence=px.colors.qualitative.Safe)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with g_col2:
                st.subheader("⚡ จำนวนเคสแบ่งตามระดับความเสี่ยง")
                risk_counts = df[risk_col].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
                risk_counts.columns = ['Risk', 'Count']
                
                # บาร์ชาร์ตแนวตั้ง สีสากล (เขียว เหลือง แดง)
                fig_bar = px.bar(risk_counts, x='Risk', y='Count', color='Risk',
                                 color_discrete_map={'High': '#EF553B', 'Medium': '#FECB52', 'Low': '#00CC96'})
                fig_bar.update_layout(showlegend=False, xaxis_title="ระดับความเสี่ยง", yaxis_title="จำนวน (เคส)",
                                      margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_bar, use_container_width=True)
                
            st.markdown("---")
            
            # --- ส่วนที่ 3: Smart Data Table ---
            st.subheader("📋 รายการบันทึกความเสี่ยงล่าสุด")
            
            # เพิ่มแผ่นกรอง (Filter) ความเสี่ยง เพื่อความสะดวกในการค้นหาข้อมูล
            filter_risk = st.multiselect("กรองข้อมูลตามระดับความเสี่ยง:", ["Low", "Medium", "High"], default=["Low", "Medium", "High"])
            
            # คัดลอกตารางมาเพื่อฟอร์แมตวันที่
            df_table = df[df[risk_col].isin(filter_risk)].copy()
            df_table[date_col] = df_table[date_col].dt.strftime('%d/%m/%Y').fillna('ไม่ระบุ')
            
            # แสดงตารางแบบดึงข้อมูลล่าสุดขึ้นก่อน (สลับด้านให้อ่านง่าย)
            st.dataframe(df_table.astype(str), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในหน้า Dashboard: {e}")
            st.info("ตรวจสอบว่าโครงสร้างหัวคอลัมน์ใน Google Sheets มีคอลัมน์ 'Status' และ 'Risk Level' ครบถ้วน")
    else:
        st.warning("⚠️ ยังไม่มีข้อมูลโหลดเข้ามาในระบบ กรุณาตรวจสอบการตั้งค่า API หรือรอ