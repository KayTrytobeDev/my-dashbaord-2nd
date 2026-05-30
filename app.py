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
API_URL = "https://script.google.com/macros/s/AKfycbxMCFK88knNYwWyw_aRBqqP4ARGozoWXAfZxgZCndtqK5NCwKZyIyaQ7GvNGp1fBJPP/exec" 

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

# ฟังก์ชันจัดการแปลงวันที่ให้อยู่ในฟอร์แมตระบบอย่างยืดหยุ่นสูง
def clean_and_parse_date(date_val):
    if pd.isna(date_val) or str(date_val).strip() == "":
        return None
    d_str = str(date_val).strip()
    
    # ดึงเฉพาะส่วนวันที่ในกรณีมีเวลาพ่วงท้ายมาด้วย (เช่น 5/30/2026 14:30:00)
    if " " in d_str:
        d_str = d_str.split(" ")[0]
        
    # ลูปทดสอบแกะฟอร์แมตวันที่ยอดฮิตทุกรูปแบบ
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(d_str, fmt).date()
        except ValueError:
            continue
    return None

# ค้นหาคอลัมน์อัตโนมัติ (Smart Auto-Detect)
target_date_col = None
target_topic_col = None

if not df.empty:
    # 1. ค้นหาคอลัมน์สำหรับ "วันที่"
    for col in df.columns:
        c_low = col.lower()
        if 'date' in c_low or 'time' in c_low or 'วัน' in c_low:
            target_date_col = col
            break
    if not target_date_col:  # ถ้าไม่เจอคำคีย์เวิร์ด ให้เลือกเอาคอลัมน์แรก (Column A) ทันที
        target_date_col = df.columns[0]
        
    # 2. ค้นหาคอลัมน์สำหรับ "หัวข้อคดี" (Column B)
    for col in df.columns:
        c_low = col.lower()
        if 'topic' in c_low or 'finding' in c_low or 'ประเด็น' in c_low or 'รายการ' in c_low:
            target_topic_col = col
            break
    if not target_topic_col and len(df.columns) > 1: # ถ้าไม่เจอ ให้เลือกคอลัมน์ที่สอง (Column B) ทันที
        target_topic_col = df.columns[1]

    # ทำการแปลงวันที่ลงคอลัมน์ใหม่
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
    
    if df.empty:
        st.info("💡 ไม่พบข้อมูลในระบบฐานข้อมูล")
    else:
        total_cases = len(df)
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            st.metric(label="📋 จำนวนเคสทั้งหมดในฐานข้อมูล Master", value=f"{total_cases} เคส")
            
        st.markdown("---")
        
        # สรุปสถานะการดำเนินงาน (Column E หรือมองหาคอลัมน์ Status)
        status_col = 'Status' if 'Status' in df.columns else (df.columns[4] if len(df.columns) > 4 else None)
        if status_col and status_col in df.columns:
            st.subheader(f"📌 สรุปสถานะการดำเนินงานแต่ละประเภท (คอลัมน์ {status_col})")
            status_df = df[status_col].value_counts().reset_index()
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

# ==========================================
# หน้าที่ 2: Calendar & Case Detail (เวอร์ชันแก้เออร์เรอร์ 100%)
# ==========================================
elif page == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงานและรายละเอียดข้อมูลเคสเชิงลึก")
    
    today = datetime.now().date()
    
    # เมนูเลือก เดือน และ ปี พ.ศ.
    col_m, col_y = st.columns(2)
    with col_m:
        month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                       "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
        selected_month_idx = st.selectbox("📅 เลือกเดือนที่ต้องการเปิดดู:", range(1, 13), index=today.month - 1, format_func=lambda x: month_names[x-1])
    with col_y:
        selected_thai_year = st.selectbox("🔢 เลือกปี พ.ศ.:", [2567, 2568, 2569, 2570], index=2)
        thai_to_iso_year = {2567: 2024, 2568: 2025, 2569: 2026, 2570: 2027}
        selected_year = thai_to_iso_year[selected_thai_year]

    if df.empty:
        st.info("💡 ระบบไม่สามารถดึงข้อมูลจาก Google Sheet ได้ หรือตารางว่างเปล่า")
    else:
        # แสดง Log ตรวจสอบชื่อคอลัมน์ที่ระบบค้นเจอแบบเรียลไทม์
        valid_dates_count = df['Parsed_Date'].notna().sum()
        st.success(f"🔍 **ระบบดึงข้อมูลสำเร็จ:** ทั้งหมด `{len(df)}` แถว | ล้างคอลัมน์วันที่สำเร็จ `{valid_dates_count}` รายการ (ใช้คอลัมน์ข้อมูลชื่อ: `{target_date_col}` และคอลัมน์หัวข้อชื่อ: `{target_topic_col}`)")
        
        # สไตล์ CSS ปฏิทิน
        st.markdown("""
        <style>
            .g-cal-table { width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px; overflow: hidden; }
            .g-cal-th { background-color: #f1f3f4; border: 1px solid #dadce0; text-align: center; padding: 14px; font-weight: bold; color: #3c4043; font-size: 14px; width: 14.28%; }
            .g-cal-td { border: 1px solid #dadce0; vertical-align: top; padding: 6px; background-color: #ffffff; height: 130px; position: relative; }
            .g-day-num { font-weight: bold; color: #3c4043; font-size: 13px; display: inline-block; width: 24px; height: 24px; text-align: center; line-height: 24px; margin-bottom: 6px; }
            .g-today-circle { background-color: #1a73e8; color: white !important; border-radius: 50%; }
            .g-cal-empty { background-color: #f8f9fa; border: 1px solid #dadce0; }
            .g-event-item { font-size: 12px; padding: 4px 6px; margin-top: 4px; border-radius: 4px; color: white !important; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: bold; line-height: 1.4; display: block; text-decoration: none; }
            .g-bg-high { background-color: #ea4335; border-left: 4px solid #b31412; }
            .g-bg-medium { background-color: #fbbc05; color: #202124 !important; border-left: 4px solid #c89200; }
            .g-bg-low { background-color: #34a853; border-left: 4px solid #187230; }
        </style>
        """, unsafe_allow_html=True)

        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdayscalendar(selected_year, selected_month_idx)
        
        html_code = "<table class='g-cal-table'>"
        html_code += "<tr><th class='g-cal-th'>อา.</th><th class='g-cal-th'>จ.</th><th class='g-cal-th'>อ.</th><th class='g-cal-th'>พ.</th><th class='g-cal-th'>พฤ.</th><th class='g-cal-th'>ศ.</th><th class='g-cal-th'>ส.</th></tr>"
        
        for week in month_days:
            html_code += "<tr>"
            for day in week:
                if day == 0:
                    html_code += "<td class='g-cal-td g-cal-empty'></td>"
                else:
                    # 🔴 เพิ่มเงื่อนไขป้องกันค่า Null (notna()) ป้องกันไม่ให้หน้าจอเออร์เรอร์สีแดงแบบเดิมเด็ดขาด
                    day_cases = df[
                        (df['Parsed_Date'].notna()) & 
                        (df['Parsed_Date'].apply(lambda x: x.day == day if x else False)) & 
                        (df['Parsed_Date'].apply(lambda x: x.month == selected_month_idx if x else False))
                    ]
                    
                    is_current_day = (today.day == day and today.month == selected_month_idx and today.year == selected_year)
                    is_today_style = " g-today-circle" if is_current_day else ""
                    
                    html_code += "<td class='g-cal-td'>"
                    html_code += f"<span class='g-day-num{is_today_style}'>{day}</span>"
                    
                    for _, c_row in day_cases.iterrows():
                        topic_text = str(c_row.get(target_topic_col, 'เคสไม่มีหัวข้อ'))
                        r_level = str(c_row.get('Risk Level', 'Low')).strip()
                        
                        bg_class = "g-bg-low"
                        if r_level.lower() == "medium": bg_class = "g-bg-medium"
                        elif r_level.lower() == "high": bg_class = "g-bg-high"
                        
                        display_text = topic_text if len(topic_text) <= 12 else topic_text[:12] + "..."
                        html_code += f"<div class='g-event-item {bg_class}' title='{topic_text}'>{display_text}</div>"
                        
                    html_code += "</td>"
            html_code += "</tr>"
        html_code += "</table>"
        
        st.markdown(html_code, unsafe_allow_html=True)
        st.write("")
        
        # 🔍 ส่วนการดึงดีเทลประวัติด้านล่างตาราง
        st.markdown("---")
        st.subheader("🔍 ตรวจสอบรายละเอียดประวัติและรูปภาพหลักฐานเพิ่มเติม")
        
        active_date = st.date_input("🗓️ ระบุวันที่ต้องการตรวจสอบข้อมูลเชิงลึกด้านล่าง:", today)
        filtered_df = df[df['Parsed_Date'] == active_date] if 'Parsed_Date' in df.columns else pd.DataFrame()
        
        if filtered_df.empty:
            st.info(f"💡 วันที่ {active_date.strftime('%d/%m/%Y')} นี้ยังไม่มีประวัติเคสความเสี่ยงบันทึกไว้")
        else:
            st.success(f"ค้นพบข้อมูลรายงานความเสี่ยงจำนวน **{len(filtered_df)} เคส**")
            for idx, row in filtered_df.iterrows():
                topic = row.get(target_topic_col, 'ไม่มีชื่อหัวข้อประเด็นความเสี่ยง')
                status = str(row.get('Status', row.get(df.columns[4] if len(df.columns) > 4 else '', '-'))).strip()
                risk_level = str(row.get('Risk Level', 'Low')).strip()
                
                with st.expander(f"📋 [{risk_level}] - หัวข้อ: {topic} (สถานะ: {status})"):
                    col_left, col_right = st.columns([2, 1])
                    with col_left:
                        st.markdown(f"**📝 รายละเอียดประเด็น:** {topic}")
                        st.markdown(f"**📍 สถานที่เกิดเหตุ:** {row.get('Location', row.get('สถานที่', '-'))}")
                        st.markdown(f"**🔧 แนวทางการปฏิบัติแก้ไข:** {row.get('Corrective Action', '-')}")
                    with col_right:
                        st.markdown(f"**📊 ระดับความเสี่ยง:** {risk_level}")

# ==========================================
# หน้าที่ 3: Report New Case 
# ==========================================
elif page == "📝 Report New Case":
    st.title("📝 ฟอร์มกรอกข้อมูลผ่านหน้าเว็บไซต์")
    with st.form("web_incident_form", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            f_date = st.date_input("วันที่เกิดเหตุ:", datetime.now()).strftime("%m/%d/%Y")
            f_topic = st.text_input("หัวข้อเหตุการณ์ (Topic):*")
            f_location = st.text_input("สถานที่ (Location):")
        with col_form2:
            f_status = st.selectbox("สถานะ (Status):", ["รอดำเนินการ", "กำลังดำเนินการ", "ดำเนินการเรียบร้อย"])
            f_action = st.text_area("แนวทางการแก้ไข:")
            f_risk = st.selectbox("ระดับความเสี่ยง (Risk Level):", ["Low", "Medium", "High"])
            
        submit_action = st.form_submit_button("🚀 บันทึกข้อมูลส่งเข้าระบบ")
        if submit_action and f_topic:
            with St.spinner("🚀 กำลังจัดส่งรายงาน..."):
                payload = {
                    "date": f_date, "topic": f_topic, "location": f_location,
                    "status": f_status, "action": f_action, "risk": f_risk
                }
                try:
                    api_response = requests.post(API_URL, json=payload)
                    if api_response.status_code == 200:
                        st.success("🎉 บันทึกข้อมูลสำเร็จ")
                        st.cache_data.clear()
                except Exception:
                    pass
