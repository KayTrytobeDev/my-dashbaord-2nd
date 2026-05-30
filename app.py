import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
from datetime import datetime

# คอนฟิกหน้าเว็บเบื้องต้นเปิด Wide Mode
st.set_page_config(page_title="Risk & Corrective Tracker", layout="wide", initial_sidebar_state="expanded")

# 🔴 ใส่ลิงก์ Web App (URL ของ Google Apps Script ที่ลงท้ายด้วย /exec) ของพี่ตรงนี้ได้เลยครับ
API_URL = "https://script.google.com/macros/s/AKfycbxMCFK88knNYwWyw_aRBqqP4ARGozoWXAfZxgZCndtqK5NCwKZyIyaQ7GvNGp1fBJPP/exec" 

# ==========================================
# ฟังก์ชันโหลดข้อมูลผ่าน Web App API (ลบการแจ้งเตือน Error ออกทั้งหมด)
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

# ฟังก์ชันทำความสะอาดและแปลงข้อมูลวันที่
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

if not df.empty:
    required_cols = ['Date', 'Topic/risk finding', 'Status', 'Risk Level']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if not missing_cols:
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
    
    if df.empty or ('missing_cols' in locals() and missing_cols):
        st.info("💡 ระบบพร้อมใช้งาน ดึงข้อมูลสำเร็จ")
    else:
        total_cases = len(df)
        
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            st.metric(label="📋 จำนวนเคสทั้งหมดในฐานข้อมูล Master", value=f"{total_cases} เคส")
            
        st.markdown("---")
        
        # สรุปสถานะการดำเนินงาน (Column E)
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
# หน้าที่ 2: Calendar & Case Detail (ใช้ตัวเลือกวันที่แบบมาตรฐาน)
# ==========================================
elif page == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงานและรายละเอียดข้อมูลเคสเชิงลึก")
    st.write("เลือกตรวจสอบวันที่ต้องการจากตัวเลือกปฏิทินเพื่อเรียกดูประวัติและหลักฐานการแก้ไข")
    
    today = datetime.now().date()
    active_date = st.date_input("📅 คลิกเลือกวันที่บนปฏิทิน:", today)
    
    if not df.empty and 'Parsed_Date' in df.columns:
        filtered_df = df[df['Parsed_Date'] == active_date]
        
        if not filtered_df.empty:
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
    st.title("📝 ฟอร์มรายงานเคสความเสี่ยงใหม่ผ่านทางหน้าเว็บไซต์")
    
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
