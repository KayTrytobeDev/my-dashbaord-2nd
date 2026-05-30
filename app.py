import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Risk Tracker System", layout="wide")
API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

# --- โหลดข้อมูล ---
@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data[1:], columns=data[0])
            df.columns = df.columns.str.strip()
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

df = load_data()
if not df.empty:
    df['Parsed_Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

# --- เมนู Sidebar ---
menu = st.sidebar.radio("เมนู:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# 1. DASHBOARD (ปรับสี/กราฟสวยงาม)
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 Risk Management Overview")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("📌 จำนวนเคสทั้งหมด", len(df))
        c2.metric("✅ สำเร็จแล้ว", len(df[df['Status'] == 'เรียบร้อย']))
        c3.metric("🚨 ความเสี่ยงสูง", len(df[df['Risk Level'] == 'High']))
        
        st.write("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("สถานะการดำเนินงาน")
            fig_p = px.pie(df, names='Status', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_p, use_container_width=True)
        with col_r:
            st.subheader("ระดับความเสี่ยง")
            risk_data = df['Risk Level'].value_counts().reset_index()
            risk_data.columns = ['Risk', 'Count']
            fig_b = px.bar(risk_data, x='Risk', y='Count', color='Risk', color_discrete_map={'High': '#ff4b4b', 'Medium': '#ffa500', 'Low': '#00cc96'})
            st.plotly_chart(fig_b, use_container_width=True)

# ==========================================
# 2. CALENDAR (แสดงชื่อเคสชัดเจน)
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงาน (Marked Grid View)")
    
    # 1. ให้มันเลือกปี/เดือน ตามข้อมูลที่มีอยู่จริงใน Sheet (ไม่ต้องเดา)
    available_years = sorted(df['Date_Obj'].dt.year.dropna().unique().astype(int))
    year = st.selectbox("เลือกปี (ค.ศ.)", available_years, index=len(available_years)-1)
    month = st.selectbox("เลือกเดือน", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
    
    # 2. สร้าง Grid ปฏิทิน
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    # วาดหัวตาราง
    cols = st.columns(7)
    for i, name in enumerate(["อา.", "จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส."]):
        cols[i].markdown(f"**{name}**")
    
    # 3. วาด Grid และ Mark สี
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                # กรองข้อมูลวันนี้
                day_data = df[(df['Date_Obj'].dt.day == day) & 
                              (df['Date_Obj'].dt.month == month) & 
                              (df['Date_Obj'].dt.year == year)]
                
                with cols[i]:
                    # ตรวจสอบว่าวันนี้มีเคสไหม? ถ้ามีให้เปลี่ยนสีพื้นหลังช่อง (Mark สี)
                    bg_color = "#e6ffe6" if not day_data.empty else "#ffffff" # เขียวอ่อนถ้ามีเคส
                    
                    st.markdown(f"""
                        <div style='background-color: {bg_color}; padding: 5px; border-radius: 5px; border: 1px solid #ddd;'>
                            <strong>{day}</strong>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # โชว์หัวข้อสั้นๆ
                    for _, row in day_data.iterrows():
                        st.caption(f"• {str(row.iloc[1])[:8]}")
            else:
                cols[i].write("")

    # 4. ส่วนเลือกรายละเอียด (เหมือนเดิม)
    st.write("---")
    selected = st.selectbox("ดูรายละเอียดเพิ่มเติม:", df.iloc[:, 1].unique())
    if selected:
        st.table(df[df.iloc[:, 1] == selected].iloc[0])
# ==========================================
# 3. REPORT (ครบทุกช่องตามชีท)
# ==========================================
elif menu == "📝 Report New Case":
    st.title("📝 รายงานเคสความเสี่ยงใหม่")
    with st.form("risk_form", clear_on_submit=True):
        f_date = st.date_input("วันที่ (Date)")
        f_topic = st.text_input("หัวข้อประเด็นความเสี่ยง (Topic/risk finding)")
        f_loc = st.text_input("สถานที่ (Location)")
        f_resp = st.text_input("ผู้รับผิดชอบ (Responsible Person)")
        f_status = st.selectbox("สถานะ (Status)", ["รอดำเนินการ", "กำลังดำเนินการ", "เรียบร้อย"])
        f_action = st.text_area("แนวทางแก้ไข (Corrective Action)")
        f_risk = st.selectbox("ระดับความเสี่ยง (Risk Level)", ["Low", "Medium", "High"])
        
        up_before = st.file_uploader("รูปก่อนแก้ไข")
        up_after = st.file_uploader("รูปหลังแก้ไข")
        
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            payload = {
                "date": str(f_date), "topic": f_topic, "location": f_loc,
                "responsible": f_resp, "status": f_status, "action": f_action, "risk": f_risk,
                "imgBeforeBase64": base64.b64encode(up_before.read()).decode() if up_before else "",
                "imgBeforeName": up_before.name if up_before else "",
                "imgAfterBase64": base64.b64encode(up_after.read()).decode() if up_after else "",
                "imgAfterName": up_after.name if up_after else ""
            }
            res = requests.post(API_URL, json=payload)
            if res.status_code == 200: st.success("บันทึกสำเร็จ!")
