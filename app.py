import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
from datetime import datetime

# คอนฟิกหน้าเว็บเบื้องต้นเปิด Wide Mode
st.set_page_config(page_title="Risk & Corrective Tracker", layout="wide", initial_sidebar_state="expanded")

# ดึงลิงก์ผ่านระบบ Secrets ของ Streamlit Cloud อัตโนมัติ ป้องกันข้อมูลรั่วไหล
try:
    API_URL = st.secrets["SCRIPT_URL"]
except:
    # สำหรับการรันเทสบน Local คอมพิวเตอร์ตัวเองก่อนอัปขึ้นระบบจริง
    API_URL = "https://script.google.com/macros/s/XXXXX/exec" 

# ==========================================
# ฟังก์ชันโหลดข้อมูลผ่าน Web App API (ดึงจากหน้าแรกของกูเกิลชีท)
# ==========================================
@st.cache_data(ttl=60) # ตั้งเวลาดึงข้อมูลใหม่ทุกๆ 60 วินาทีเพื่อความลื่นไหลและประหยัดการทำงาน
def load_data_from_script():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 0:
                headers = raw_data[0] # แถวที่ 1 คือชื่อคอลัมน์
                rows = raw_data[1:]   # แถวที่เหลือคือข้อมูลเคสทั้งหมด
                df = pd.DataFrame(rows, columns=headers)
                df.columns = df.columns.str.strip() # ล้างช่องว่างที่อาจหลุดมาในชื่อหัวตาราง
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
        
        # 1. กล่องแสดงจำนวนเคสทั้งหมดด้านบนสุด
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            st.metric(label="📋 จำนวนเคสทั้งหมดในฐานข้อมูล Master", value=f"{total_cases} เคส")
            
        st.markdown("---")
        
        # 2. สถิติจำนวนเคสและเปอร์เซ็นต์จำแนกตามคอลัมน์ E (Status)
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
        
        # 3. สถิติจำนวนเคสและเปอร์เซ็นต์จำแนกตามคอลัมน์ K (Risk Level) เรียงลำดับจาก Low -> Medium -> High
        st.subheader("🔥 สรุปเปอร์เซ็นต์แยกตามระดับความเสี่ยง (Column K)")
        if 'Risk Level' in df.columns:
            # ใช้การ .reindex เพื่อบังคับให้ระบบเรียงลำดับ Low, Medium, High เสมอแม้บางระดับจะเป็น 0
            risk_order = ['Low', 'Medium', 'High']
            risk_df = df['Risk Level'].value_counts().reindex(risk_order, fill_value=0).reset_index()
            risk_df.columns = ['ระดับความเสี่ยง', 'จำนวน']
            risk_df['เปอร์เซ็นต์ (%)'] = ((risk_df['จำนวน'] / total_cases) * 100).round(2)
            
            c3, c4 = st.columns([1, 1])
            with c3:
                st.dataframe(risk_df, use_container_width=True, hide_index=True)
            with c4:
                # แมพสีเฉพาะตัวให้เข้ากับลำดับความปลอดภัยเสากล (Low=เขียว, Medium=ส้ม, High=แดง)
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
    st.title("📅 ปฏิทินติดตามงานและรายละเอียดข้อมูลเคสเชิงลึก")
    st.caption("ดึงข้อมูลวันเกิดเหตุจาก Column A พร้อมวิเคราะห์สถานะและรายละเอียดหลักฐานรูปภาพ")
    
    if df.empty:
        st.info("💡 ไม่มีข้อมูลแสดงผลในระบบ")
    else:
        # ดึงวันที่ทั้งหมดจาก Column A มาเรียงลำดับจากใหม่ไปเก่าเพื่อการสืบค้นที่สะดวก
        available_dates = sorted(df['Date'].unique(), reverse=True)
        
        col_sel, col_sp = st.columns([1, 2])
        with col_sel:
            selected_date = st.selectbox("📅 ค้นหาเลือกวันที่บนปฏิทิน:", available_dates)
            
        # กรองเคสตามวันที่ที่ยูเซอร์กดเลือก
        filtered_df = df[df['Date'] == selected_date]
        st.write(f"พบข้อมูลประวัติทั้งหมด **{len(filtered_df)} รายการ** ประจำวันที่ {selected_date}")
        
        # วนลูปแสดงผลเหตุการณ์ทีละรายการในรูปแบบของรายการสแกนข้อมูล (List)
        for idx, row in filtered_df.iterrows():
            topic = row.get('Topic/risk finding', 'ไม่มีชื่อหัวข้อประเด็นความเสี่ยง')
            status = str(row.get('Status', '')).strip()
            risk_level = row.get('Risk Level', 'Low')
            
            # ตั้งค่าสีและข้อความนำหน้าของ List Item บ่งบอกสถานะความคืบหน้าเบื้องต้น
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
                
            # สร้างตัวรับรู้การเปิดดูในรูปแบบ Expander (ลิสต์รายการที่คลิกเข้าไปดูข้างในได้)
            with st.expander(f"{list_badge} [{risk_level}] - หัวข้อ (Column B): {topic}"):
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown(f"**📝 รายละเอียดประเด็น (Topic):** {topic}")
                    st.markdown(f"**👤 ผู้รับผิดชอบดูแล (Column D):** {row.get('Responsible Person', '-')}")
                    st.markdown(f"**📍 สถานที่เกิดเหตุ (Location):** {row.get('Location', '-')}")
                    st.markdown(f"**🔧 แนวทางการปฏิบัติแก้ไข (Corrective Action):** {row.get('Corrective Action', '-')}")
                    
                    st.write("")
                    st.markdown("**📸 รูปภาพหลักฐานประกอบ (คอลัมน์ G และ H):**")
                    col_img1, col_img2 = st.columns(2)
                    
                    # ฟังก์ชันแกะลิงก์ URL สะอาดๆ ออกมาจากโครงสร้างสูตรฝังภาพ =IMAGE("URL") ของ Google Sheet
                    def extract_clean_url(cell_data):
                        if not cell_data: return ""
                        val_str = str(cell_data).strip()
                        if 'IMAGE("' in val_str:
                            try:
                                return val_str.split('IMAGE("')[1].split('")')[0]
                            except: pass
                        if val_str.startswith("http"): return val_str
                        return ""
                    
                    # ฟังก์ชันแสดงผลรูปภาพขึ้นเว็บเบาว์เซอร์พร้อมฟังก์ชันดักแปลงลิงก์พรีวิวของ Drive ให้เป็นลิงก์รูปดิบ
                    def render_image_by_url(url, label):
                        if url:
                            direct_download_url = url.replace('/open?id=', '/uc?export=download&id=')
                            st.image(direct_download_url, caption=label, use_container_width=True)
                        else:
                            # ดึงภาพประกอบสากลด้านความปลอดภัยมาทดแทนในกรณีที่ในระบบเซลล์นั้นว่างอยู่
                            st.image("https://images.unsplash.com/photo-1590105577767-e21a1067899f?w=400", 
                                     caption=f"{label} (ไม่พบภาพแนบ - แสดงภาพความปลอดภัยทั่วไป)", use_container_width=True)
                                     
                    img_before = extract_clean_url(row.get('Picture (before)'))
                    img_after = extract_clean_url(row.get('Picture (After)'))
                    
                    with col_img1: render_image_by_url(img_before, "รูปภาพก่อนแก้ไข (Before)")
                    with col_img2: render_image_by_url(img_after, "รูปภาพหลังแก้ไข (After)")
                    
                with col_right:
                    # แสดงบล็อกไอคอนบ่งบอกสถานะการดำเนินงานที่บริเวณ "มุมบนขวา" ของกล่องเนื้อหาเคสตามโจทย์
                    st.markdown(f"<div style='text-align: right;'><span style='{status_style}'>{status_label}</span></div>", unsafe_allow_html=True)
                    
                    st.write("") # เว้นระยะช่องไฟ
                    st.write("")
                    
                    # ไฮไลท์แถบสีสดตามระดับเงื่อนไขความรุนแรงความเสี่ยง (Column K)
                    st.markdown("**📊 ลำดับระดับความเสี่ยง (Risk Level):**")
                    if risk_level == 'High':
                        st.markdown('<p style="background-color:#d62728; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">🚨 High (ระดับอันตรายสีแดง)</p>', unsafe_allow_html=True)
                    elif risk_level == 'Medium':
                        st.markdown('<p style="background-color:#ff7f0e; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">⚠️ Medium (ความเสี่ยงปานกลาง)</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p style="background-color:#2ca02c; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">✅ Low (ความเสี่ยงต่ำสีเขียว)</p>', unsafe_allow_html=True)

# ==========================================
# หน้าที่ 3: Report New Case (ฟอร์มหน้าเว็บส่งข้อมูล)
# ==========================================
elif page == "📝 Report New Case":
    st.title("📝 ฟอร์มรายงานเคสความเสี่ยงใหม่ผ่านทางหน้าเว็บไซต์")
    st.info("💡 หมายเหตุ: ข้อมูลทั้งหมดที่บันทึกผ่านหน้านี้ จะถูกส่งเข้าไปบันทึกเก็บเป็นประวัติแยกต่างหากที่แท็บย่อย 'User_Submissions' และจะสำเนาต่อท้ายเข้าตาราง 'Sheet1 (Master)' ให้ทันทีเพื่อความปลอดภัยสูงสุดและไม่รบกวนสูตรเดิม")
    
    # สร้างฟอร์มการรับข้อมูลในช่องตารางเว็บบราวเซอร์
    with st.form("web_incident_form", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            f_date = st.date_input("เลือกวันที่เกิดเหตุการณ์ความเสี่ยง (Date):", datetime.now()).strftime("%m/%d/%Y")
            f_topic = st.text_input("หัวข้อหรือประเด็นความเสี่ยงที่ตรวจพบ (Topic/risk finding):*")
            f_location = st.text_input("สถานที่ระบุพิกัดที่พบ (Location):")
            f_responsible = st.text_input("ชื่อเจ้าหน้าที่หรือหน่วยงานรับผิดชอบ (Responsible Person):")
            
        with col_form2:
            f_status = st.selectbox("สถานะการดำเนินงานเบื้องต้น (Status):", ["รอดำเนินการ", "กำลังดำเนินการ", "ดำเนินการเรียบร้อย"])
            f_action = st.text_area("มาตรการหรือแนวทางแก้ไขเบื้องต้น (Corrective Action):")
            f_risk = st.selectbox("ระบุระดับความเสี่ยงของเคสนี้ (Risk Level):", ["Low", "Medium", "High"])
            
            # คอมโพเนนต์อัปโหลดรูปภาพผ่านหน้าเว็บ (รองรับไฟล์ PNG, JPG, JPEG)
            file_before = st.file_uploader("แนบรูปภาพก่อนทำแก้ไข (Picture before):", type=["png", "jpg", "jpeg"])
            file_after = st.file_uploader("แนบรูปภาพหลังดำเนินการแก้ไข (Picture After):", type=["png", "jpg", "jpeg"])
            
        submit_action = st.form_submit_button("🚀 บันทึกข้อมูลและรายงานส่งเข้าระบบ")
        
        if submit_action:
            # ดักจับค่าว่างกรณีลืมกรอกหัวข้อสำคัญ
            if not f_topic:
                st.error("❌ เกิดข้อผิดพลาด: จำเป็นต้องระบุข้อมูลในช่อง 'หัวข้อหรือประเด็นความเสี่ยงที่ตรวจพบ' ก่อนทำการส่งข้อมูล!")
            else:
                with st.spinner("🚀 ระบบกำลังจัดส่งรายงานเคสและทำการแปลงไฟล์อัปโหลดภาพเข้าคลัง Google Drive..."):
                    
                    # เตรียมชุดอาร์เรย์พารามิเตอร์ Payload ส่งข้ามแพลตฟอร์ม
                    payload = {
                        "date": f_date, "topic": f_topic, "location": f_location,
                        "responsible": f_responsible, "status": f_status, "action": f_action, "risk": f_risk,
                        "imgBeforeBase64": "", "imgBeforeName": "", "imgBeforeType": "",
                        "imgAfterBase64": "", "imgAfterName": "", "imgAfterType": ""
                    }
                    
                    # ตรวจสอบและแปลงไฟล์ภาพชิ้นที่ 1 เป็นรหัส Base64 String
                    if file_before:
                        payload["imgBeforeBase64"] = base64.b64encode(file_before.read()).decode()
                        payload["imgBeforeName"] = file_before.name
                        payload["imgBeforeType"] = file_before.type
                        
                    # ตรวจสอบและแปลงไฟล์ภาพชิ้นที่ 2 เป็นรหัส Base64 String
                    if file_after:
                        payload["imgAfterBase64"] = base64.b64encode(file_after.read()).decode()
                        payload["imgAfterName"] = file_after.name
                        payload["imgAfterType"] = file_after.type
                        
                    # ทำการยิงคำสั่งส่ง HTTP POST ยิงตรงเข้าหา Google Sheet API Web App
                    try:
                        api_response = requests.post(API_URL, json=payload)
                        
                        if api_response.status_code == 200 and api_response.json().get("status") == "success":
                            st.success("🎉 บันทึกรายงานเหตุการณ์สำเร็จ! ข้อมูลถูกฝังภาพแบบ In-cell เข้าทั้งตารางประวัติและตาราง Master หลักเรียบร้อยแล้ว")
                            st.cache_data.clear() # ทำการล้างแคชเพื่อให้ระบบดึงค่าใหม่ล่าสุดมาคำนวณที่หน้าแรกได้ทันที
                        else:
                            st.error(f"❌ ระบบปลายทางตอบปฏิเสธคำขอ: {api_response.text}")
                    except Exception as err:
                        st.error(f"❌ ไม่สามารถติดต่อเชื่อมโยงกับเซิร์ฟเวอร์ระบบจัดเก็บได้: {err}")
