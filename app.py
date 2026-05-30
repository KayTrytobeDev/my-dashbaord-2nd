import streamlit as st
import pandas as pd
import requests
import calendar
import base64
from datetime import datetime

# --- การตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="Risk Tracker System", layout="wide")

# 🔴 ใส่ลิงก์ Web App ของพี่ที่นี่
API_URL = "ใส่ลิงก์ของคุณที่นี่"

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
    except:
        return pd.DataFrame()

def parse_date_thai_to_ce(val):
    try:
        # จัดการรูปแบบ 2569-01-13T00:00:00.000Z
        date_str = str(val).split('T')[0]
        y, m, d = map(int, date_str.split('-'))
        if y > 2400: y -= 543
        return datetime(y, m, d)
    except:
        return pd.NaT

# โหลดข้อมูลและเตรียมคอลัมน์วันที่
df = load_data()
if not df.empty:
    df['Parsed_Date'] = pd.to_datetime(df.iloc[:, 0].apply(parse_date_thai_to_ce), errors='coerce')

# --- ส่วนเมนู Sidebar ---
st.sidebar.title("🚨 Risk Tracker System")
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# หน้าที่ 1: Dashboard (หน้าแรกสถิติ)
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 ภาพรวมข้อมูลความเสี่ยง")
    if df.empty:
        st.info("กำลังโหลดข้อมูล...")
    else:
        # Metric
        total = len(df)
        st.metric("จำนวนเคสทั้งหมด", f"{total} รายการ")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📌 สัดส่วนสถานะ (Status)")
            status_counts = df['Status'].value_counts()
            st.write(status_counts)
            # สามารถเพิ่มกราฟ Plotly ตรงนี้ได้
            
        with col2:
            st.subheader("🔥 ระดับความเสี่ยง (Risk Level)")
            risk_counts = df['Risk Level'].value_counts()
            st.write(risk_counts)

# ==========================================
# หน้าที่ 2: Calendar & Case Detail (ปฏิทินริบบิ้นสี)
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงาน")
    
    if df.empty:
        st.info("ไม่พบข้อมูล")
    else:
        # เลือกเดือน/ปี (พ.ศ.)
        today = datetime.now()
        c1, c2 = st.columns(2)
        with c1:
            month = st.selectbox("เลือกเดือน", range(1, 13), index=today.month-1, format_func=lambda x: calendar.month_name[x])
        with c2:
            thai_year = st.selectbox("เลือกปี พ.ศ.", [2568, 2569, 2570], index=1)
            year = thai_year - 543 # แปลงเป็น ค.ศ. เพื่อวาดปฏิทิน

        # CSS สำหรับปฏิทินแบบ Google Calendar
        st.markdown("""
        <style>
            .cal-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
            .cal-td { border: 1px solid #eee; height: 120px; vertical-align: top; padding: 5px; font-family: sans-serif; }
            .cal-header { background: #f8f9fa; text-align: center; font-weight: bold; padding: 10px; border: 1px solid #eee; }
            .event-tag { font-size: 10px; padding: 2px 5px; margin-bottom: 2px; border-radius: 3px; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .risk-high { background: #ea4335; } /* สีแดง */
            .risk-medium { background: #fbbc05; color: black; } /* สีเหลือง */
            .risk-low { background: #34a853; } /* สีเขียว */
        </style>
        """, unsafe_allow_html=True)

        cal = calendar.Calendar(firstweekday=6)
        weeks = cal.monthdayscalendar(year, month)

        # วาดปฏิทิน
        html = "<table class='cal-table'><tr>"
        for day_name in ["อา.", "จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส."]:
            html += f"<th class='cal-header'>{day_name}</th>"
        html += "</tr>"

        for week in weeks:
            html += "<tr>"
            for day in week:
                if day == 0:
                    html += "<td class='cal-td'></td>"
                else:
                    # กรองข้อมูล
                    day_data = df[
                        (df['Parsed_Date'].dt.day == day) & 
                        (df['Parsed_Date'].dt.month == month) & 
                        (df['Parsed_Date'].dt.year == year)
                    ]
                    
                    tags = ""
                    for _, row in day_data.iterrows():
                        risk = str(row['Risk Level']).lower()
                        color_class = "risk-low"
                        if 'high' in risk: color_class = "risk-high"
                        elif 'medium' in risk: color_class = "risk-medium"
                        
                        tags += f"<div class='event-tag {color_class}'>• {row['Topic/risk finding']}</div>"
                    
                    html += f"<td class='cal-td'><strong>{day}</strong><br>{tags}</td>"
            html += "</tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

        # --- ส่วนแสดงรายละเอียดด้านล่างปฏิทิน ---
        st.markdown("---")
        st.subheader("🔍 รายละเอียดเคสรายวัน")
        select_date = st.date_input("เลือกวันที่ต้องการดูรายละเอียด", datetime(year, month, 1))
        
        detail_df = df[df['Parsed_Date'].dt.date == select_date]
        
        if detail_df.empty:
            st.write("ไม่มีเคสในวันที่เลือก")
        else:
            for _, row in detail_df.iterrows():
                with st.expander(f"📌 {row['Topic/risk finding']} (สถานะ: {row['Status']})"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**สถานที่:** {row['Location']}")
                        st.write(f"**ผู้รับผิดชอบ:** {row['Responsible Person']}")
                        st.write(f"**แนวทางแก้ไข:** {row['Corrective Action']}")
                    with col_b:
                        # ฟังก์ชันแสดงรูปภาพ (ถ้ามี)
                        img_url = row['Picture (before)']
                        if img_url and str(img_url).startswith("http"):
                            # แปลงลิงก์ google drive ให้แสดงผลได้
                            display_url = img_url.replace("open?id=", "uc?export=view&id=")
                            st.image(display_url, caption="รูปภาพหลักฐาน")

# ==========================================
# หน้าที่ 3: Report New Case (ฟอร์มบันทึกข้อมูล)
# ==========================================
elif menu == "📝 Report New Case":
    st.title("📝 รายงานเคสความเสี่ยงใหม่")
    with st.form("risk_form", clear_on_submit=True):
        f_date = st.date_input("วันที่เกิดเหตุ", datetime.now())
        f_topic = st.text_input("หัวข้อประเด็นความเสี่ยง*")
        f_loc = st.text_input("สถานที่")
        f_resp = st.text_input("ผู้รับผิดชอบ")
        f_status = st.selectbox("สถานะ", ["รอดำเนินการ", "กำลังดำเนินการ", "เรียบร้อย"])
        f_risk = st.selectbox("ระดับความเสี่ยง", ["Low", "Medium", "High"])
        f_action = st.text_area("แนวทางแก้ไข")
        
        submitted = st.form_submit_button("🚀 บันทึกข้อมูล")
        
        if submitted:
            if f_topic:
                # ส่งข้อมูลไป Google Sheets
                payload = {
                    "date": f_date.strftime("%Y-%m-%d"),
                    "topic": f_topic,
                    "location": f_loc,
                    "responsible": f_resp,
                    "status": f_status,
                    "risk": f_risk,
                    "action": f_action
                }
                res = requests.post(API_URL, json=payload)
                if res.status_code == 200:
                    st.success("บันทึกข้อมูลสำเร็จแล้ว!")
                    st.cache_data.clear()
            else:
                st.warning("กรุณากรอกหัวข้อประเด็นความเสี่ยง")
