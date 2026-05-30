import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
from datetime import datetime
from streamlit_calendar import calendar

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
@st.cache_data(ttl=60)
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
# หน้าที่ 2: Calendar & Case Detail (เวอร์ชันตารางปฏิทินจริง)
# ==========================================
elif page == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงานและรายละเอียดข้อมูลเคสเชิงลึก")
    st.caption("คลิกเลือกวันที่บนตารางปฏิทินเพื่อเรียกดูรายละเอียดเหตุการณ์หรือประวัติความเสี่ยงในวันนั้น ๆ")
    
    if df.empty:
        st.info("💡 ไม่มีข้อมูลแสดงผลในระบบ")
    else:
        # เตรียมแปลงข้อมูลจาก DataFrame ให้เป็นจุดกลมกิจกรรม (Events) แปะบนตารางปฏิทิน
        calendar_events = []
        
        for idx, row in df.iterrows():
            raw_date = str(row.get('Date', '')).strip()
            topic = row.get('Topic/risk finding', 'ไม่มีชื่อหัวข้อ')
            risk_level = row.get('Risk Level', 'Low')
            status = str(row.get('Status', '')).strip()
            
            # บังคับสีของจุด Event ตามระดับความเสี่ยง
            color_hex = '#2ca02c'  # Low = เขียว
            if risk_level == 'Medium': color_hex = '#ff7f0e' # ส้ม
            elif risk_level == 'High': color_hex = '#d62728' # แดง
            
            # จัดฟอร์แมตวันที่จาก MM/DD/YYYY ให้เป็น YYYY-MM-DD เพื่อให้ปฏิทินอ่านได้
            try:
                formatted_date = datetime.strptime(raw_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            except:
                try:
                    # ดักเผื่อบางแถวเป็น ISO Format อยู่แล้ว
                    formatted_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
                except:
                    continue # ข้ามแถวที่ฟอร์แมตวันที่พัง
            
            calendar_events.append({
                "title": f"[{risk_level}] {topic[:15]}...",
                "start": formatted_date,
                "end": formatted_date,
                "color": color_hex,
                "extendedProps": {"original_date": raw_date}
            })
            
        # ตั้งค่าหน้าตาและความสามารถของตารางปฏิทิน
        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,listMonth"
            },
            "initialView": "dayGridMonth",
            "selectable": True,
            "navLinks": True
        }
        
        # แสดงผลตารางปฏิทิน (Interactive Calendar)
        cal_state = calendar(events=calendar_events, options=calendar_options, key='risk_calendar')
        
        # ดักจับเหตุการณ์การ "คลิกเลือกวันที่" บนปฏิทิน
        selected_date_str = None
        if cal_state.get("dateClick"):
            selected_date_str = cal_state["dateClick"]["date"].split("T")[0]
            # แปลงกลับเป็นฟอร์แมต MM/DD/YYYY เพื่อดึงข้อมูลมาค้นหาใน DataFrame
            try:
                target_date = datetime.strptime(selected_date_str, "%Y-%m-%d").strftime("%m/%d/%Y")
            except:
                target_date = ""
        else:
            # หากผู้ใช้ยังไม่ได้คลิกเลือกวัน ให้ดึงวันล่าสุดที่มีข้อมูลในระบบมาแสดงเป็น Default
            if len(df['Date'].unique()) > 0:
                target_date = sorted(df['Date'].unique(), reverse=True)[0]
                try:
                    selected_date_str = datetime.strptime(target_date, "%m/%d/%Y").strftime("%Y-%m-%d")
                except:
                    selected_date_str = target_date
            else:
                target_date = ""

        st.markdown("---")
        st.subheader(f"🔍 รายละเอียดเหตุการณ์ประจำวันที่เลือก: {selected_date_str if selected_date_str else '-'}")
        
        # กรองข้อมูลแสดงเฉพาะวันที่เลือก
        filtered_df = df[df['Date'] == target_date]
        
        if filtered_df.empty:
            st.info("💡 ไม่มีประวัติการรายงานเคสความเสี่ยงในวันที่คุณเลือก")
        else:
            st.write(f"พบข้อมูลทั้งหมด **{len(filtered_df)} รายการ**")
            
            for idx, row in filtered_df.iterrows():
                topic = row.get('Topic/risk finding', 'ไม่มีชื่อหัวข้อประเด็นความเสี่ยง')
                status = str(row.get('Status', '')).strip()
                risk_level = row.get('Risk Level', 'Low')
                
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
    st.info("💡 หมายเหตุ: ข้อมูลจะถูกจัดเก็บเข้าสู่ฐานข้อมูลประวัติและอัปเดตไปยังระบบหน้าแรกให้โดยอัตโนมัติ")
    
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
