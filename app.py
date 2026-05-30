import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
import calendar
from datetime import datetime

# คอนฟิกหน้าเว็บเบื้องต้นเปิด Wide Mode
st.set_page_config(page_title="Risk & Corrective Tracker", layout="wide", initial_sidebar_state="expanded")

# ดึงลิงก์ผ่านระบบ Secrets ของ Streamlit Cloud อัตโนมัติ
try:
    API_URL = st.secrets["SCRIPT_URL"]
except:
    API_URL = "https://script.google.com/macros/s/XXXXX/exec" 

# ==========================================
# ฟังก์ชันโหลดข้อมูลผ่าน Web App API พร้อมระบบดักจับ Error
# ==========================================
@st.cache_data(ttl=10) # ตั้งให้ดึงข้อมูลบ่อยขึ้นช่วงทดสอบ
def load_data_from_script():
    try:
        if "XXXXX" in API_URL or not API_URL.startswith("http"):
            st.error("❌ ลิงก์ API_URL ไม่ถูกต้อง กรุณาตั้งค่า SCRIPT_URL ใน Streamlit Secrets")
            return pd.DataFrame()
            
        response = requests.get(API_URL)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 0:
                headers = raw_data[0]
                rows = raw_data[1:]
                
                # ตรวจสอบว่ามีแถวข้อมูลจริงไหม
                if not rows:
                    st.warning("⚠️ ดึงข้อมูลจาก Google Sheet ได้สำเร็จ แต่ไม่พบแถวข้อมูล (มีแต่หัวตาราง)")
                    return pd.DataFrame()
                    
                df = pd.DataFrame(rows, columns=headers)
                df.columns = df.columns.str.strip() # ล้างช่องว่างที่หัวตาราง
                return df
            else:
                st.error("❌ Google Sheet ส่งกลับมาเป็นอาร์เรย์ว่างเปล่า")
                return pd.DataFrame()
        else:
            st.error(f"❌ ไม่สามารถติดต่อ Web App ได้ (Status Code: {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ เกิดข้อผิดพลาดในระบบการเชื่อมต่อ (API Error): {e}")
        return pd.DataFrame()

df = load_data_from_script()

# ฟังก์ชันทำความสะอาดข้อมูลวันที่ (ดักจับค่าว่างและฟอร์แมตเพี้ยน)
def clean_and_parse_date(date_val):
    if pd.isna(date_val) or str(date_val).strip() == "":
        return None
    d_str = str(date_val).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(d_str, fmt).date()
        except ValueError:
            continue
    return None

# ตรวจสอบโครงสร้างตารางข้อมูลและเตรียม Field วันที่
if not df.empty:
    # ตรวจสอบคอลัมน์สำคัญที่ต้องมีใน Google Sheet
    required_cols = ['Date', 'Topic/risk finding', 'Status', 'Risk Level']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"❌ ชื่อหัวตารางใน Google Sheet ไม่ตรงกับระบบ! ขาดคอลัมน์: {missing_cols}")
        st.info("💡 โปรดตรวจสอบให้แน่ใจว่าแถวที่ 1 ใน Google Sheet มีคำเหล่านี้สะกดถูกต้องทุกตัวอักษร")
    else:
        df['Parsed_Date'] = df['Date'].apply(clean_and_parse_date)

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
        st.warning("⚠️ ไม่มีข้อมูลในตารางระบบ ไม่สามารถวาดกราฟได้")
    elif 'missing_cols' in locals() and missing_cols:
        st.warning("⚠️ โครงสร้างตารางไม่ถูกต้อง กรุณาแก้ไขชื่อหัวตารางใน Google Sheet")
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
# หน้าที่ 2: Calendar & Case Detail
# ==========================================
elif page == "📅 Calendar & Case Detail":
    st.title("📅 Dashboard ตารางปฏิทินแผนงานความเสี่ยงรายเดือน")
    
    if df.empty or 'Parsed_Date' not in df.columns:
        st.info("💡 ระบบยังไม่มีข้อมูลรายงานที่จะนำมาพล็อตลงตารางปฏิทิน")
    else:
        today = datetime.now().date()
        col_m, col_y = st.columns(2)
        with col_m:
            month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                           "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
            selected_month_idx = st.selectbox("📅 เลือกเดือนที่ต้องการดูประวัติ:", range(1, 13), index=today.month - 1, format_func=lambda x: month_names[x-1])
        with col_y:
            selected_year = st.selectbox("🔢 เลือกปี พ.ศ./ค.ศ.:", [today.year - 1, today.year, today.year + 1], index=1)

        # คำนวณบล็อกตารางปฏิทิน
        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdayscalendar(selected_year, selected_month_idx)
        
        st.markdown("""
        <style>
            .cal-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-family: sans-serif; }
            .cal-th { width: 14.28%; background-color: #f1f3f4; border: 1px solid #dadce0; text-align: center; padding: 10px; font-weight: bold; color: #3c4043; }
            .cal-td { width: 14.28%; height: 110px; border: 1px solid #dadce0; vertical-align: top; padding: 6px; background-color: white; position: relative; }
            .cal-day-num { font-weight: bold; color: #70757a; font-size: 13px; margin-bottom: 4px; display: block; }
            .cal-empty { background-color: #f8f9fa; border: 1px solid #dadce0; }
            .event-badge { font-size: 11px; padding: 3px 6px; margin-bottom: 3px; border-radius: 4px; color: white; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; line-height: 1.2; }
            .badge-high { background-color: #d62728; border-left: 3px solid #900; }
            .badge-medium { background-color: #ff7f0e; border-left: 3px solid #c50; }
            .badge-low { background-color: #2ca02c; border-left: 3px solid #060; }
        </style>
        """, unsafe_allow_html=True)

        html_code = "<table class='cal-table'>"
        html_code += "<tr><th class='cal-th'>อา.</th><th class='cal-th'>จ.</th><th class='cal-th'>อ.</th><th class='cal-th'>พ.</th><th class='cal-th'>พฤ.</th><th class='cal-th'>ศ.</th><th class='cal-th'>ส.</th></tr>"
        
        for week in month_days:
            html_code += "<tr>"
            for day in week:
                if day == 0:
                    html_code += "<td class='cal-td cal-empty'></td>"
                else:
                    current_loop_date = datetime(selected_year, selected_month_idx, day).date()
                    day_cases = df[df['Parsed_Date'] == current_loop_date]
                    
                    html_code += "<td class='cal-td'>"
                    html_code += f"<span class='cal-day-num'>{day}</span>"
                    
                    for _, c_row in day_cases.iterrows():
                        topic_text = c_row.get('Topic/risk finding', 'ไม่มีหัวข้อ')
                        r_level = str(c_row.get('Risk Level', 'Low')).strip()
                        
                        badge_class = "badge-low"
                        if r_level == "Medium": badge_class = "badge-medium"
                        elif r_level == "High": badge_class = "badge-high"
                        
                        html_code += f"<div class='event-badge {badge_class}' title='{topic_text}'>• {topic_text[:12]}...</div>"
                        
                    html_code += "</td>"
            html_code += "</tr>"
        html_code += "</table>"
        
        st.markdown(html_code, unsafe_allow_html=True)
        st.write("")
        
        st.markdown("---")
        st.subheader("🔍 ส่วนตรวจสอบรายละเอียดและรูปภาพหลักฐาน")
        
        active_date = st.date_input("🗓️ ระบุวันที่คุณต้องการดึงข้อมูลรูปภาพและแนวทางแก้ไขเพิ่มเติม:", today)
        filtered_df = df[df['Parsed_Date'] == active_date]
        
        if filtered_df.empty:
            st.info(f"💡 วันที่ {active_date.strftime('%d/%m/%Y')} นี้ไม่มีรายงานประวัติเคสความเสี่ยงในระบบ")
        else:
            st.success(f"พบข้อมูลรายงานทั้งหมด **{len(filtered_df)} เคส** ประจำวันที่ระบุ")
            
            for idx, row in filtered_df.iterrows():
                topic = row.get('Topic/risk finding', 'ไม่มีชื่อหัวข้อประเด็นความเสี่ยง')
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
                        st.write("")
                        
                        st.markdown("**📊 ระดับความเสี่ยง:**")
                        if risk_level == 'High':
                            st.markdown('<p style="background-color:#d62728; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">🚨 High (ระดับอันตราย)</p>', unsafe_allow_html=True)
                        elif risk_level == 'Medium':
                            st.markdown('<p style="background-color:#ff7f0e; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">⚠️ Medium (ความเสี่ยงปานกลาง)</p>', unsafe_allow_html=True)
                        else:
                            st.markdown('<p style="background-color:#2ca02c; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">✅ Low (ความเสี่ยงต่ำ)</p>', unsafe_allow_html=True)

# ==========================================
# หน้าที่ 3: Report New Case (ฟอร์มหน้าเว็บส่งข้อมูล)
# ==========================================
elif page == "📝 Report New Case":
    st.title("📝 ฟอร์มรายงานเคสความเสี่ยงใหม่ผ่านทางหน้าเว็บไซต์")
    st.info("💡 ข้อมูลจะถูกส่งเข้าสู่ Google Sheet และนำมาคำนวณที่หน้าหลักทันที")
    
    with st.form("web_incident_form", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            f_date = st.date_input("เลือกวันที่เกิดเหตุการณ์ความเสี่ยง:", datetime.now()).strftime("%m/%d/%Y")
            f_topic = st.text_input("หัวข้อหรือประเด็นความเสี่ยงที่ตรวจพบ:*")
            f_location = st.text_input("สถานที่ระบุพิกัดที่พบ:")
            f_responsible = st.text_input("ชื่อเจ้าหน้าที่หรือหน่วยงานรับผิดชอบ:")
            
        with col_form2:
            f_status = st.selectbox("สถานะการดำเนินงานเบื้องต้น:", ["รอดำเนินการ", "กำลังดำเนินการ", "ดำเนินการเรียบร้อย"])
            f_action = st.text_area("มาตรการหรือแนวทางแก้ไขเบื้องต้น:")
            f_risk = st.selectbox("ระบุระดับความเสี่ยงของเคสนี้:", ["Low", "Medium", "High"])
            
            file_before = st.file_uploader("แนบรูปภาพก่อนทำแก้ไข:", type=["png", "jpg", "jpeg"])
            file_after = st.file_uploader("แนบรูปภาพหลังดำเนินการแก้ไข:", type=["png", "jpg", "jpeg"])
            
        submit_action = st.form_submit_button("🚀 บันทึกข้อมูลและรายงานส่งเข้าระบบ")
        
        if submit_action:
            if not f_topic:
                st.error("❌ เกิดข้อผิดพลาด: จำเป็นต้องระบุข้อมูลในช่องหัวข้อความเสี่ยงก่อนทำการส่งข้อมูล!")
            else:
                with st.spinner("🚀 ระบบกำลังจัดส่งรายงานเคสและทำการบันทึกข้อมูล..."):
                    
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
                            st.success("🎉 บันทึกรายงานเหตุการณ์สำเร็จ! ข้อมูลและรูปภาพถูกฝังเข้าสู่ระบบหลักเรียบร้อยแล้ว")
                            st.cache_data.clear() 
                        else:
                            st.error(f"❌ ระบบปลายทางตอบปฏิเสธคำขอ: {api_response.text}")
                    except Exception as err:
                        st.error(f"❌ ไม่สามารถติดต่อเชื่อมโยงกับเซิร์ฟเวอร์ระบบจัดเก็บได้: {err}")
