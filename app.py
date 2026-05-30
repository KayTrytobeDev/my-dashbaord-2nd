import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Risk Tracker System", layout="wide")

# 🔴 ใส่ลิงก์ Web App ของพี่ที่นี่ (ต้องเป็นลิงก์ที่ Deploy แล้ว)
API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

# --- ฟังก์ชันจัดการข้อมูล ---
@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                df.columns = df.columns.str.strip() # ลบช่องว่างหัวคอลัมน์
                return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# โหลดข้อมูล
df = load_data()

# --- แปลงวันที่แบบรัดกุม ---
if not df.empty:
    # ใช้ errors='coerce' เพื่อให้ค่าที่แปลงไม่ได้กลายเป็น NaT แทนที่จะ Error
    df['Parsed_Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

# --- เมนู Sidebar ---
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 สรุปภาพรวมความเสี่ยง")
    
    if not df.empty:
        # คำนวณข้อมูลเบื้องต้น
        total_cases = len(df)
        # ตรวจสอบชื่อคอลัมน์ในไฟล์พี่ให้ตรง (เช่น 'Status' หรือ 'สถานะ')
        completed_cases = len(df[df['Status'].str.contains('เรียบร้อย|สำเร็จ', na=False)])
        
        # 1. แสดงตัวเลข Metric เด่นๆ
        col1, col2, col3 = st.columns(3)
        col1.metric("📌 เคสทั้งหมด", total_cases)
        col2.metric("✅ ดำเนินการสำเร็จ", completed_cases)
        col3.metric("🚨 เคสความเสี่ยงสูง", len(df[df['Risk Level'] == 'High']))
        
        st.markdown("---")
        
        # 2. จัดวางกราฟ 2 ฝั่ง (สถานะ vs ความเสี่ยง)
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("สัดส่วนสถานะการดำเนินงาน")
            # ใช้ value_counts() แล้วแปลงเป็น DataFrame ให้ Plotly อ่านง่าย
            status_df = df['Status'].value_counts().reset_index()
            status_df.columns = ['Status', 'Count']
            fig_pie = px.pie(status_df, values='Count', names='Status', hole=0.4, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("ระดับความเสี่ยง (Risk Level)")
            # เรียงลำดับ Low -> Medium -> High ก่อนแสดงผล
            risk_df = df['Risk Level'].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
            risk_df.columns = ['Risk', 'Count']
            fig_bar = px.bar(risk_df, x='Risk', y='Count', color='Risk',
                             color_discrete_map={'High': '#ff4b4b', 'Medium': '#ffa500', 'Low': '#00cc96'})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        # 3. ตารางข้อมูลย่อ
        st.subheader("รายการล่าสุด")
        st.dataframe(df.head(5), use_container_width=True)
    else:
        st.warning("⚠️ ยังไม่มีข้อมูลโหลดเข้ามาในระบบ")
# ==========================================
# 2. CALENDAR (แสดงชื่อเคสชัดเจน)
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงาน")

    # 1. จัดการวันที่ (ใช้คอลัมน์แรก)
    df['date_dt'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
    
    # 2. เลือกเดือน/ปี
    col_a, col_b = st.columns(2)
    with col_a: month = st.selectbox("เลือกเดือน", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
    with col_b: year = st.selectbox("เลือกปี (ค.ศ.)", [2026, 2027], index=0)

    # 3. สร้าง Grid ปฏิทิน
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    # วาดหัวตาราง
    header = st.columns(7)
    for i, name in enumerate(["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]):
        header[i].markdown(f"**{name}**")
    
    # วาดตาราง Grid และใส่สี
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                # กรองข้อมูลของวันนั้นๆ
                day_data = df[(df['date_dt'].dt.day == day) & 
                             (df['date_dt'].dt.month == month) & 
                             (df['date_dt'].dt.year == year)]
                
                # ถ้ามีเคสให้สีเป็นเขียวอ่อน (#d4edda) ถ้าไม่มีให้เป็นสีขาว (#ffffff)
                bg_color = "#d4edda" if not day_data.empty else "#ffffff"
                border_style = "2px solid #28a745" if not day_data.empty else "1px solid #ccc"
                
                with cols[i]:
                    st.markdown(f"""
                        <div style='background-color:{bg_color}; border:{border_style}; border-radius:5px; padding:10px; text-align:center;'>
                            <strong>{day}</strong>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                cols[i].write("")

    # 4. เลือกดูรายละเอียด
    st.write("---")
    topic_list = df.iloc[:, 1].unique().tolist()
    selected = st.selectbox("เลือกหัวข้อเพื่อดูรายละเอียด:", topic_list)
    
    if selected:
        case = df[df.iloc[:, 1] == selected].iloc[0]
        st.subheader("🔍 รายละเอียดเคส")
        for col in df.columns:
            st.write(f"**{col}:** {case[col]}")
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
