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
                # ล้างช่องว่างที่หัวตารางเพื่อป้องกันการเรียกชื่อคอลัมน์พลาด
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
    # รองรับฟอร์แมต เดือน/วัน/ปี ค.ศ. (05/30/2026) จาก Google Sheet โดยตรง
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(d_str, fmt).date()
        except ValueError:
            continue
    return None

# สแกนหาคอลัมน์หัวข้อความเสี่ยง (Column B) และคอลัมน์วันที่
target_date_col = 'Date'
target_topic_col = 'Topic/risk finding'

if not df.empty:
    # จับคู่คอลัมน์ในกรณีมีการพิมพ์ตัวเล็กตัวใหญ่ไม่ตรงกัน
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
# หน้าที่ 2: Calendar & Case Detail (เวอร์ชันแสดงริบบิ้นข้อมูลคดีสำเร็จ)
# ==========================================
elif page == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงานและรายละเอียดข้อมูลเคสเชิงลึก")
    st.write("ดึงข้อมูลวันเกิดเหตุพร้อมวิเคราะห์สถานะและรายละเอียดหลักฐานรูปภาพในรูปแบบตารางรายเดือน")
    
    today = datetime.now().date()
    
    # ส่วนแถบเมนูเพื่อเลือก เดือน และ ปี ค.ศ. ในการแสดงผล
    col_m, col_y = st.columns(2)
    with col_m:
        month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                       "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
        # เลือกค่าเริ่มต้นให้ตรงกับเดือนปัจจุบัน
        selected_month_idx = st.selectbox("📅 เลือกเดือนที่ต้องการเปิดดู:", range(1, 13), index=today.month - 1, format_func=lambda x: month_names[x-1])
    with col_y:
        # ขยับปีเริ่มต้นให้ครอบคลุมปี 2026 ตามในแผ่นงาน Google Sheet ของพี่
        selected_year = st.selectbox("🔢 เลือกปี ค.ศ.:", [2024, 2025, 2026, 2027], index=2)

    if df.empty or 'Parsed_Date' not in df.columns:
        st.info("💡 ระบบยังไม่มีข้อมูลรายงานความเสี่ยงบันทึกไว้ในฐานข้อมูล")
    else:
        # ฝังข้อกำหนด Style CSS เพื่อเน้นให้ตัวอักษรและแถบริบบิ้นของแต่ละวันโดดเด่นสะดุดตา
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

        # ประมวลผลวันประจำสัปดาห์ในเดือนนั้นๆ
        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdayscalendar(selected_year, selected_month_idx)
        
        # จัดโครงสร้างตาราง HTML ปฏิทิน
        html_code = "<table class='g-cal-table'>"
        html_code += "<tr><th class='g-cal-th'>อา.</th><th class='g-cal-th'>จ.</th><th class='g-cal-th'>อ.</th><th class='g-cal-th'>พ.</th><th class='g-cal-th'>พฤ.</th><th class='g-cal-th'>ศ.</th><th class='g-cal-th'>ส.</th></tr>"
        
        for week in month_days:
            html_code += "<tr>"
            for day in week:
                if day == 0:
                    html_code += "<td class='g-cal-td g-cal-empty'></td>"
                else:
                    # คำนวณวันที่จริงของช่องปฏิทินนั้น
                    current_loop_date = datetime(selected_year, selected_month_idx, day).date()
                    day_cases = df[df['Parsed_Date'] == current_loop_date]
                    
                    is_today = " g-today-circle" if current_loop_date == today else ""
                    
                    html_code += "<td class='g-cal-td'>"
                    html_code += f"<span class='g-day-num{is_today}'>{day}</span>"
                    
                    # 🔴 ส่วนสำคัญ: ดึงข้อมูลประเด็นใน Column B ออกมาโชว์ในช่องวันที่แล้ว
                    for _, c_row in day_cases.iterrows():
                        topic_text = str(c_row.get(target_topic_col, 'ไม่มีข้อมูลชื่อหัวข้อ'))
                        r_level = str(c_row.get('Risk Level', 'Low')).strip()
                        
                        # แยกสีริบบิ้นตามระดับความเสี่ยง
                        bg_class = "g-bg-low"
                        if r_level.lower() == "medium": bg_class = "g-bg-medium"
                        elif r_level.lower() == "high": bg_class = "g-bg-high"
                        
                        # แสดงผลชื่อคดี (จำกัดความยาวเพื่อไม่ให้ล้นกล่องปฏิทิน)
                        display_text = topic_text if len(topic_text) <= 15 else topic_text[:15] + "..."
                        html_code += f"<div class='g-event-item {bg_class}' title='{topic_text}'>{display_text}</div>"
                        
                    html_code += "</td>"
            html_code += "</tr>"
        html_code += "</table>"
        
        # เรนเดอร์แผนผังปฏิทินรายเดือนออกหน้าจอ
        st.markdown(html_code, unsafe_allow_html=True)
        st.write("")
        
        # 🔍 ส่วนการดึงข้อมูลและแสดงรูปภาพหลักฐานดั้งเดิมที่ด้านล่างตาราง
        st.markdown("---")
        st.subheader("🔍 ตรวจสอบรายละเอียดประวัติและรูปภาพหลักฐานเพิ่มเติม")
        
        active_date = st.date_input("🗓️ ระบุวันที่ต้องการเจาะลึกภาพหลักฐานและแนวทางแก้ไขด้านล่าง:", today)
        filtered_df = df[df['Parsed_Date'] == active_date]
        
        if filtered_df.empty:
            st.info(f"💡 ไม่พบรายการประวัติความเสี่ยงในวันที่ {active_date.strftime('%d/%m/%Y')}")
        else:
            st.success(f"ค้นพบข้อมูลรายงานความเสี่ยงจำนวน **{len(filtered_df)} เคส**")
            
            for idx, row in filtered_df.iterrows():
                topic = row.get(target_topic_col, 'ไม่มีชื่อหัวข้อประเด็นความเสี่ยง')
                status = str(row.get('Status', '')).strip()
                risk_level = str(row.get('Risk Level', 'Low')).strip()
                
                if "สำเร็จ" in status or "เรียบร้อย" in status:
                    list_badge = "🟢 [สำเร็จ]"
                    status_style = "background-color: #d4edda; color: #155724; border-radius:15px; padding:6px 15px; font-weight:bold;"
                    status_label = "🟢 ดำเนินการสำเร็จ"
                elif "กำลัง" in status or "อยู่ระหว่าง" in status or "รอ" in status:
                    list_badge = "🟡 [อยู่ระหว่างดำเนินการ]"
                    status_style = "background-color: #fff3cd; color: #856404; border-radius:15px; padding:6px 15px; font-weight:bold;"
                    status_label = "🟡 อยู่ระหว่างดำเนินการ"
                else:
                    list_badge = "🔴 [รอดำเนินการ]"
                    status_style = "background-color: #f8d7da; color: #721c24; border-radius:15px; padding:6px 15px; font-weight:bold;"
                    status_label = f"🔴 {status}"
                    
                with st.expander(f"{list_badge} [{risk_level}] - หัวข้อ: {topic}"):
                    col_left, col_right = st.columns([2, 1])
                    
                    with col_left:
                        st.markdown(f"**📝 รายละเอียดประเด็น:** {topic}")
                        st.markdown(f"**👤 ผู้รับผิดชอบดูแล:** {row.get('Responsible Person', '-')}")
                        st.markdown(f"**📍 สถานที่เกิดเหตุ:** {row.get('Location', '-')}")
                        st.markdown(f"**🔧 แนวทางการปฏิบัติแก้ไข:** {row.get('Corrective Action', '-')}")
                        
                        st.write("")
                        st.markdown("**📸 รูปภาพหลักฐานประกอบเคส:**")
                        col_img1, col_img2 = st.columns(2)
                        
                        def extract_clean_url(cell_data):
                            if not cell_data: return ""
                            val_str = str(cell_data).strip()
                            if 'IMAGE("' in val_str:
                                try:
                                    return val_str.split('IMAGE("')[1].split('")')[0]
                                except: pass
                            if val_str.startswith("http"): return val_str
                            return ""
                        
                        def render_image_by_url(url, label):
                            if url:
                                direct_download_url = url.replace('/open?id=', '/uc?export=download&id=')
                                st.image(direct_download_url, caption=label, use_container_width=True)
                            else:
                                st.image("https://images.unsplash.com/photo-1590105577767-e21a1067899f?w=400", 
                                         caption=f"{label} (ไม่พบภาพแนบ)", use_container_width=True)
                                         
                        img_before = extract_clean_url(row.get('Picture (before)'))
                        img_after = extract_clean_url(row.get('Picture (After)'))
                        
                        with col_img1: render_image_by_url(img_before, "รูปภาพก่อนแก้ไข (Before)")
                        with col_img2: render_image_by_url(img_after, "รูปภาพหลังแก้ไข (After)")
                        
                    with col_right:
                        st.markdown(f"<div style='text-align: right;'><span style='{status_style}'>{status_label}</span></div>", unsafe_allow_html=True)
                        st.write("")
                        
                        st.markdown("**📊 ระดับความเสี่ยง:**")
                        if risk_level == 'High':
                            st.markdown('<p style="background-color:#d62728; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">🚨 High (ระดับอันตราย)</p>', unsafe_allow_html=True)
                        elif risk_level == 'Medium':
                            st.markdown('<p style="background-color:#ff7f0e; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">⚠️ Medium (ความเสี่ยงปานกลาง)</p>', unsafe_allow_html=True)
                        else:
                            st.markdown('<p style="background-color:#2ca02c; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">✅ Low (ความเสี่ยงต่ำ)</p>', unsafe_allow_html=True)

# ==========================================
# หน้าที่ 3: Report New Case (ฟอร์มส่งข้อมูล)
# ==========================================
elif page == "📝 Report New Case":
    st.title("📝 ฟอร์มกรอกข้อมูลผ่านหน้าเว็บไซต์")
    
    with st.form("web_incident_form", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            f_date = st.date_input("วันที่เกิดเหตุ:", datetime.now()).strftime("%m/%d/%Y")
            f_topic = st.text_input("หัวข้อเหตุการณ์ (Topic):*")
            f_location = st.text_input("สถานที่ (Location):")
            f_responsible = st.text_input("ผู้รับผิดชอบ:")
            
        with col_form2:
            f_status = st.selectbox("สถานะ (Status):", ["รอดำเนินการ", "กำลังดำเนินการ", "ดำเนินการเรียบร้อย"])
            f_action = st.text_area("แนวทางการแก้ไข:")
            f_risk = st.selectbox("ระดับความเสี่ยง (Risk Level):", ["Low", "Medium", "High"])
            
            file_before = st.file_uploader("รูปภาพก่อนแก้ไข (Before):", type=["png", "jpg", "jpeg"])
            file_after = st.file_uploader("รูปภาพหลังแก้ไข (After):", type=["png", "jpg", "jpeg"])
            
        submit_action = st.form_submit_button("🚀 บันทึกข้อมูลส่งเข้าระบบ")
        
        if submit_action:
            if f_topic:
                with st.spinner("🚀 ระบบกำลังจัดส่งรายงานเคส..."):
                    payload = {
                        "date": f_date, "topic": f_topic, "location": f_location,
                        "responsible": f_responsible, "status": f_status, "action": f_action, "risk": f_risk,
                        "imgBeforeBase64": "", "imgBeforeName": "", "imgBeforeType": "",
                        "imgAfterBase64": "", "imgAfterName": "", "imgAfterType": ""
                    }
                    
                    if file_before:
                        payload["imgBeforeBase64"] = base64.b64encode(file_before.read()).decode()
                        payload["imgBeforeName"] = file_before.name
                        payload["imgBeforeType"] = file_before.type
                    if file_after:
                        payload["imgAfterBase64"] = base64.b64encode(file_after.read()).decode()
                        payload["imgAfterName"] = file_after.name
                        payload["imgAfterType"] = file_after.type
                        
                    try:
                        api_response = requests.post(API_URL, json=payload)
                        if api_response.status_code == 200 and api_response.json().get("status") == "success":
                            st.success("🎉 บันทึกข้อมูลและอัปโหลดภาพเข้า Google Sheet เรียบร้อยแล้ว")
                            st.cache_data.clear() 
                    except Exception:
                        pass
