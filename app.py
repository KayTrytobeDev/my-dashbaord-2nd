import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px

# การตั้งค่าหน้าจอ
st.set_page_config(page_title="Risk Tracker System", layout="wide")

# 🔴 ใส่ลิงก์ Web App ของพี่ที่นี่
API_URL = "https://script.google.com/macros/s/AKfycbxMCFK88knNYwWyw_aRBqqP4ARGozoWXAfZxgZCndtqK5NCwKZyIyaQ7GvNGp1fBJPP/exec"

# --- ฟังก์ชันจัดการข้อมูล ---
@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                df.columns = df.columns.str.strip()
                return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def parse_date_thai_to_ce(val):
    try:
        date_str = str(val).split('T')[0]
        y, m, d = map(int, date_str.split('-'))
        if y > 2400: y -= 543
        return datetime(y, m, d)
    except: return pd.NaT

# ดึงและแปลงข้อมูล
df = load_data()
if not df.empty:
    df['Parsed_Date'] = pd.to_datetime(df.iloc[:, 0].apply(parse_date_thai_to_ce), errors='coerce')

# --- CSS ปรับแต่งหน้าจอ ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .event-tag { font-size: 10px; padding: 2px 6px; margin: 2px; border-radius: 4px; color: white; }
    .risk-high { background: #ff4b4b; }
    .risk-medium { background: #ffa500; }
    .risk-low { background: #00cc96; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("🚨 Risk Tracker")
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 ภาพรวมระบบความเสี่ยง")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("📌 จำนวนเคสทั้งหมด", len(df))
        c2.metric("✅ สำเร็จแล้ว", len(df[df['Status'].str.contains('เรียบร้อย|สำเร็จ', na=False)]))
        c3.metric("🚨 ความเสี่ยงสูง", len(df[df['Risk Level'] == 'High']))
        
        st.write("")
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("สถานะการดำเนินงาน")
            fig_p = px.pie(df, names='Status', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_p, use_container_width=True)
        with col_r:
            st.subheader("ระดับความเสี่ยง")
            fig_b = px.bar(df['Risk Level'].value_counts().reset_index(), x='index', y='Risk Level', color='index', color_discrete_map={'High': '#ff4b4b', 'Medium': '#ffa500', 'Low': '#00cc96'})
            st.plotly_chart(fig_b, use_container_width=True)

# ==========================================
# 2. CALENDAR
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงาน")
    month = st.selectbox("เลือกเดือน", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
    year = st.selectbox("เลือกปี พ.ศ.", [2568, 2569, 2570], index=1) - 543
    
    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    html = "<table style='width:100%; border-collapse:collapse;'>"
    for w in weeks:
        html += "<tr>"
        for d in w:
            if d == 0: html += "<td style='height:100px; border:1px solid #eee;'></td>"
            else:
                day_data = df[(df['Parsed_Date'].dt.day == d) & (df['Parsed_Date'].dt.month == month) & (df['Parsed_Date'].dt.year == year)]
                tags = "".join([f"<div class='event-tag risk-{str(r['Risk Level']).lower()}'>• {r['Topic/risk finding']}</div>" for _, r in day_data.iterrows()])
                html += f"<td style='height:100px; border:1px solid #eee; vertical-align:top;'><strong>{d}</strong><br>{tags}</td>"
        html += "</tr>"
    st.markdown(html + "</table>", unsafe_allow_html=True)

# ==========================================
# 3. REPORT NEW CASE
# ==========================================
elif menu == "📝 Report New Case":
    st.title("📝 รายงานเคสความเสี่ยงใหม่")
    
    with st.form("risk_form", clear_on_submit=True):
        f_date = st.date_input("วันที่ (Date)")
        f_topic = st.text_input("หัวข้อประเด็นความเสี่ยง (Topic)")
        f_location = st.text_input("สถานที่ (Location)")
        f_resp = st.text_input("ผู้รับผิดชอบ (Responsible)")
        f_status = st.selectbox("สถานะ (Status)", ["รอดำเนินการ", "กำลังดำเนินการ", "เรียบร้อย"])
        f_action = st.text_area("แนวทางแก้ไข (Action)")
        f_risk = st.selectbox("ระดับความเสี่ยง (Risk Level)", ["Low", "Medium", "High"])
        
        # เพิ่มส่วนอัปโหลดรูปภาพให้ตรงกับ doPost
        file_before = st.file_uploader("รูปก่อนแก้ไข", type=["jpg", "png"])
        file_after = st.file_uploader("รูปหลังแก้ไข", type=["jpg", "png"])
        
        submitted = st.form_submit_button("🚀 บันทึกข้อมูล")
        
        if submitted:
            # เตรียมข้อมูลให้ตรงกับโครงสร้าง doPost ของพี่
            payload = {
                "date": f_date.strftime("%Y-%m-%d"),
                "topic": f_topic,
                "location": f_location,
                "responsible": f_resp,
                "status": f_status,
                "action": f_action,
                "risk": f_risk,
                "imgBeforeBase64": "", "imgBeforeName": "", "imgBeforeType": "",
                "imgAfterBase64": "", "imgAfterName": "", "imgAfterType": ""
            }
            
            # แปลงรูปเป็น Base64 (ถ้ามีการเลือกไฟล์)
            if file_before:
                payload["imgBeforeBase64"] = base64.b64encode(file_before.read()).decode()
                payload["imgBeforeName"] = file_before.name
                payload["imgBeforeType"] = file_before.type
            
            # ส่งข้อมูลไปที่ Google Apps Script
            res = requests.post(API_URL, json=payload)
            if res.status_code == 200:
                st.success("บันทึกข้อมูลเรียบร้อย!")
            else:
                st.error("บันทึกไม่สำเร็จ")
