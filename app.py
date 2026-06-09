import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64

# ตั้งค่าหน้าเว็บให้ดูโปรและกว้างเต็มจอ
st.set_page_config(page_title="Risk Tracker System", layout="wide")

# ลิงก์ Web App ของ Google Apps Script (ตรวจสอบให้แน่ใจว่าเป็นลิงก์เวอร์ชันล่าสุด)
API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

# --- ฟังก์ชันดึงและจัดการข้อมูล (เปิดโหมดดักจับ Error เพื่อความโปร่งใส) ---
@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                df.columns = df.columns.str.strip()  # ลบช่องว่างที่หัวคอลัมน์ออก
                
                # แปลงคอลัมน์แรกสุดให้เป็นวันที่ (DateTime Object) รองรับรูปแบบ วัน/เดือน/ปี ของไทย
                date_col = df.columns[0]
                df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
                return df
            else:
                st.warning("⚠️ ดึงข้อมูลจาก Google Sheets ได้สำเร็จ แต่ในชีทไม่มีข้อมูลแสดงผล (มีแต่แถวหัวข้อ)")
        else:
            st.error(f"❌ ลิงก์ API (Google Apps Script) ตอบกลับด้วยโค้ดผิดพลาด: {response.status_code}")
        return pd.DataFrame()
    except Exception as e: 
        # แสดง Error ตัวจริงบนหน้าเว็บทันทีหากระบบฐานข้อมูลพัง
        st.error(f"❌ เกิดปัญหาในการเชื่อมต่อข้อมูล (load_data): {e}")
        st.info("💡 คำแนะนำ: ลองนำลิงก์ API_URL ไปเปิดในเบราว์เซอร์โดยตรงดูว่ามีข้อมูล JSON แสดงขึ้นมาหรือไม่")
        return pd.DataFrame()

# โหลดข้อมูลเข้าสู่ระบบ
df = load_data()

# --- เมนู Sidebar ---
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# 1. SUPERCHARGED DASHBOARD (หน้าแดชบอร์ดประสิทธิภาพสูง)
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 ระบบวิเคราะห์และสรุปภาพรวมความเสี่ยง")
    st.markdown("ข้อมูลอัปเดตแบบ Real-time จากระบบจัดการความเสี่ยง")
    
    if not df.empty:
        try:
            # กำหนดชื่อคอลัมน์หลักให้ตรงกับชีทจริง
            date_col = df.columns[0]
            status_col = 'Status'
            risk_col = 'Risk Level'
            
            # ตรวจสอบเบื้องต้นว่ามีคอลัมน์ครบตามเงื่อนไขไหม
            if status_col not in df.columns or risk_col not in df.columns:
                st.error(f"❌ โครงสร้างคอลัมน์ใน Google Sheets ไม่ตรงกับที่ระบบต้องการ")
                st.info(f"ระบบมองหาคอลัมน์ชื่อ **'{status_col}'** และ **'{risk_col}'** แต่คอลัมน์ที่พบจริงในชีทของพี่คือ: {df.columns.tolist()}")
            else:
                # --- ส่วนที่ 1: KPI Metrics Card ---
                total_cases = len(df)
                completed_cases = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ', na=False)])
                high_risk_cases = len(df[df[risk_col].astype(str) == 'High'])
                
                # คำนวณร้อยละความสำเร็จในการปิดเคส
                success_rate = (completed_cases / total_cases * 100) if total_cases > 0 else 0
                
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric(label="📌 เคสความเสี่ยงทั้งหมด", value=f"{total_cases} เคส")
                m_col2.metric(label="✅ ดำเนินการสำเร็จแล้ว", value=f"{completed_cases} เคส")
                m_col3.metric(label="🚨 เคสวิกฤต (High Risk)", value=f"{high_risk_cases} เคส")
                m_col4.metric(label="📈 อัตราการแก้ปัญหาสำเร็จ", value=f"{success_rate:.1f}%")
                
                st.markdown("---")
                
                # --- ส่วนที่ 2: Interactive Charts ---
                g_col1, g_col2 = st.columns(2)
                
                with g_col1:
                    st.subheader("💡 สัดส่วนสถานะการดำเนินงาน")
                    status_counts = df[status_col].value_counts().reset_index()
                    status_counts.columns = ['Status', 'Count']
                    
                    fig_pie = px.pie(status_counts, values='Count', names='Status', hole=0.5,
                                     color_discrete_sequence=px.colors.qualitative.Safe)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                with g_col2:
                    st.subheader("⚡ จำนวนเคสแบ่งตามระดับความเสี่ยง")
                    risk_counts = df[risk_col].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
                    risk_counts.columns = ['Risk', 'Count']
                    
                    fig_bar = px.bar(risk_counts, x='Risk', y='Count', color='Risk',
                                     color_discrete_map={'High': '#EF553B', 'Medium': '#FECB52', 'Low': '#00CC96'})
                    fig_bar.update_layout(showlegend=False, xaxis_title="ระดับความเสี่ยง", yaxis_title="จำนวน (เคส)",
                                          margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                st.markdown("---")
                
                # --- ส่วนที่ 3: Smart Data Table ---
                st.subheader("📋 รายการบันทึกความเสี่ยงล่าสุด")
                
                # เพิ่มแผ่นกรอง (Filter) ความเสี่ยง เพื่อความสะดวกในการค้นหาข้อมูล
                filter_risk = st.multiselect("กรองข้อมูลตามระดับความเสี่ยง:", ["Low", "Medium", "High"], default=["Low", "Medium", "High"])
                
                # คัดลอกตารางมาเพื่อฟอร์แมตวันที่ก่อนจัดโชว์
                df_table = df[df[risk_col].isin(filter_risk)].copy()
                df_table[date_col] = df_table[date_col].dt.strftime('%d/%m/%Y').fillna('ไม่ระบุ')
                
                # แสดงตารางแบบดึงข้อมูลล่าสุดขึ้นก่อน (แปลงทุกช่องเป็น string บล็อกอาการตารางค้าง)
                st.dataframe(df_table.astype(str), use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในหน้า Dashboard: {e}")
    else:
        st.warning("⚠️ หน้าเว็บไม่สามารถแสดงผล Dashboard ได้เนื่องจากไม่มีข้อมูลในระบบ")

# ==========================================
# 2. CALENDAR & CASE DETAIL (อิงข้อมูลเดิม)
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    st.title("📅 ปฏิทินติดตามงาน")

    if not df.empty:
        try:
            date_col = df.columns[0]
            
            # 1. เลือกเดือน/ปี
            col_a, col_b = st.columns(2)
            with col_a: month = st.selectbox("เลือกเดือน", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
            with col_b: year = st.selectbox("เลือกปี (ค.ศ.)", [2026, 2027], index=0)

            # 2. สร้างโครงสร้างปฏิทิน
            cal = calendar.Calendar(firstweekday=6)
            month_days = cal.monthdayscalendar(year, month)
            
            header = st.columns(7)
            for i, name in enumerate(["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]):
                header[i].markdown(f"**{name}**")
            
            for week in month_days:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day != 0:
                        # กรองข้อมูลวันที่ให้ตรงตัวแม่นยำ
                        day_data = df[(df[date_col].dt.day == day) & 
                                      (df[date_col].dt.month == month) & 
                                      (df[date_col].dt.year == year)]
                        
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

            # 3. เมนูดรอปดาวน์เลือกดูรายละเอียดแบบเจาะลึก
            st.write("---")
            topic_list = df.iloc[:, 1].unique().tolist()
            selected = st.selectbox("เลือกหัวข้อเพื่อดูรายละเอียด:", topic_list)
            
            if selected:
                case = df[df.iloc[:, 1] == selected].iloc[0]
                st.subheader("🔍 รายละเอียดเคส")
                
                case_display = case.copy()
                if pd.notnull(case_display[date_col]):
                    case_display[date_col] = case_display[date_col].strftime('%d/%m/%Y')
                else:
                    case_display[date_col] = 'ไม่ระบุ'
                    
                for col in df.columns:
                    st.write(f"**{col}:** {case_display[col]}")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในหน้าปฏิทิน: {e}")
    else:
        st.warning("⚠️ ไม่มีข้อมูลแสดงผลในหน้าปฏิทิน")

# ==========================================
# 3. REPORT NEW CASE (อิงข้อมูลเดิม)
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
            try:
                payload = {
                    "date": str(f_date), "topic": f_topic, "location": f_loc,
                    "responsible": f_resp, "status": f_status, "action": f_action, "risk": f_risk,
                    "imgBeforeBase64": base64.b64encode(up_before.read()).decode() if up_before else "",
                    "imgBeforeName": up_before.name if up_before else "",
                    "imgAfterBase64": base64.b64encode(up_after.read()).decode() if up_after else "",
                    "imgAfterName": up_after.name if up_after else ""
                }
                res = requests.post(API_URL, json=payload, timeout=15)
                if res.status_code == 200: 
                    st.success("🎉 บันทึกข้อมูลความเสี่ยงลงระบบเรียบร้อยแล้ว! ข้อมูลจะอัปเดตไปที่หน้า Dashboard ทันที")
                    st.cache_data.clear() # ล้างแคชเพื่อให้ระบบโหลดข้อมูลใหม่ทันทีที่มีการส่งฟอร์ม
                else:
                    st.error(f"❌ ไม่สามารถบันทึกข้อมูลได้ API ตอบกลับด้วยรหัส: {res.status_code}")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดขณะส่งข้อมูลแบบฟอร์ม: {e}")