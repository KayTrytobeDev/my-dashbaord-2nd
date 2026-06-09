import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64
import textwrap

# ==========================================
# ตั้งค่าหน้าเว็บ
# ==========================================
st.set_page_config(page_title="Risk Tracker System", page_icon="🛡️", layout="wide")

# ลิงก์ Web App ของ Google Apps Script
API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

# ==========================================
# ฟังก์ชันดึงและจัดการข้อมูล
# ==========================================
@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                df.columns = df.columns.str.strip()  # ลบช่องว่างที่หัวคอลัมน์
                
                # แปลงคอลัมน์แรกสุดให้เป็นวันที่
                date_col = df.columns[0]
                df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
                return df
            else:
                st.warning("⚠️ ใน Google Sheets มีแต่หัวข้อตาราง ยังไม่มีข้อมูลเคสความเสี่ยง")
        else:
            st.error(f"❌ API Error: {response.status_code}")
        return pd.DataFrame()
    except Exception as e: 
        st.error(f"❌ เกิดปัญหาในการเชื่อมต่อข้อมูล: {e}")
        return pd.DataFrame()

# โหลดข้อมูลเข้าสู่ระบบ
df = load_data()

# ==========================================
# เมนู Sidebar
# ==========================================
st.sidebar.title("🛡️ Risk Tracker")
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 ระบบวิเคราะห์และสรุปภาพรวมความเสี่ยง")
    
    if not df.empty:
        try:
            date_col = df.columns[0]
            status_col = 'Status' if 'Status' in df.columns else df.columns[4]
            risk_col = 'Risk Level' if 'Risk Level' in df.columns else df.columns[-1]
            
            # --- KPI Metrics Card ---
            total_cases = len(df)
            completed_cases = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ|Complete', na=False, case=False)])
            high_risk_cases = len(df[df[risk_col].astype(str).str.contains('High', case=False, na=False)])
            success_rate = (completed_cases / total_cases * 100) if total_cases > 0 else 0
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("📌 เคสความเสี่ยงทั้งหมด", f"{total_cases} เคส")
            m_col2.metric("✅ ดำเนินการสำเร็จแล้ว", f"{completed_cases} เคส")
            m_col3.metric("🚨 เคสวิกฤต (High Risk)", f"{high_risk_cases} เคส")
            m_col4.metric("📈 อัตราการแก้ปัญหา", f"{success_rate:.1f}%")
            
            st.markdown("---")
            
            # --- Interactive Charts ---
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.subheader("💡 สัดส่วนสถานะการดำเนินงาน")
                status_counts = df[status_col].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                fig_pie = px.pie(status_counts, values='Count', names='Status', hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with g_col2:
                st.subheader("⚡ จำนวนเคสแบ่งตามระดับความเสี่ยง")
                risk_counts = df[risk_col].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
                risk_counts.columns = ['Risk', 'Count']
                fig_bar = px.bar(risk_counts, x='Risk', y='Count', color='Risk', color_discrete_map={'High': '#EF553B', 'Medium': '#FECB52', 'Low': '#00CC96'})
                fig_bar.update_layout(showlegend=False, xaxis_title="ระดับความเสี่ยง", yaxis_title="จำนวน (เคส)", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_bar, use_container_width=True)
                
            st.markdown("---")
            
            # --- Smart Data Table ---
            st.subheader("📋 รายการบันทึกความเสี่ยงล่าสุด")
            df_table = df.copy()
            df_table[date_col] = df_table[date_col].dt.strftime('%d/%m/%Y').fillna('ไม่ระบุ')
            st.dataframe(df_table.astype(str), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในหน้า Dashboard: {e}")
    else:
        st.warning("⚠️ ไม่มีข้อมูลในระบบ")

# ==========================================
# 2. CALENDAR & CASE DETAIL
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    if not df.empty:
        # จับคู่ชื่อคอลัมน์ให้ยืดหยุ่นที่สุด
        date_col = df.columns[0]
        topic_col = 'Topic/risk finding' if 'Topic/risk finding' in df.columns else df.columns[1]
        loc_col = 'Location' if 'Location' in df.columns else df.columns[2]
        resp_col = 'Responsible Person' if 'Responsible Person' in df.columns else df.columns[3]
        status_col = 'Status' if 'Status' in df.columns else df.columns[4]
        action_col = 'Corrective Action' if 'Corrective Action' in df.columns else df.columns[5]
        risk_col = 'Risk Level' if 'Risk Level' in df.columns else df.columns[-1]

        # ส่วนหัวเลือก เดือน/ปี
        t1, t2, t3 = st.columns([2, 1, 1])
        with t1: st.title("📅 Calendar & Case Detail")
        with t2: month = st.selectbox("Month:", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with t3: year = st.selectbox("Year:", [2025, 2026, 2027], index=1)

        sheet_year = year + 543 # คำนวณปี พ.ศ. เผื่อไว้ใช้เทียบ
        col_left, col_right = st.columns([1.7, 1]) # แบ่งฝั่งจอ 65:35

        # เช็ควันปัจจุบันใน Session
        _, num_days = calendar.monthrange(year, month)
        if 'sel_day' not in st.session_state or st.session_state.sel_day > num_days:
            st.session_state.sel_day = 1

        # ---------------- ฝั่งซ้าย (ปฏิทิน) ----------------
        with col_left:
            cal = calendar.Calendar(firstweekday=6)
            month_days = cal.monthdayscalendar(year, month)
            
            header = st.columns(7)
            for i, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
                header[i].markdown(f"<p style='text-align:center; font-weight:bold; color:#666; margin-bottom:5px;'>{name}</p>", unsafe_allow_html=True)
            
            for week in month_days:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day != 0:
                        # กรองข้อมูลวันที่มีเคส (รองรับทั้ง พ.ศ. และ ค.ศ.)
                        is_match = (df[date_col].dt.day == day) & (df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))
                        day_data = df[is_match]
                        
                        has_case = not day_data.empty
                        is_selected = (day == st.session_state.sel_day)
                        
                        btn_type = "primary" if is_selected else "secondary"
                        
                        if cols[i].button(f"{day}", key=f"d_{day}", type=btn_type, use_container_width=True):
                            st.session_state.sel_day = day
                            st.session_state.pop('selected_case_idx', None) 
                            st.rerun()
                        
                        if has_case and not is_selected:
                            cols[i].markdown("<p style='text-align:center; margin-top:-22px; margin-bottom:0px; color:#28a745; font-size:18px;'>•</p>", unsafe_allow_html=True)
                    else:
                        cols[i].write("")

            # สรุปรายการเคสด้านล่างปฏิทิน
            st.markdown("---")
            st.subheader(f"Selected Date Summary: {calendar.month_name[month]} {st.session_state.sel_day}, {year}")
            
            daily_cases = df[(df[date_col].dt.day == st.session_state.sel_day) & (df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))]
            
            if not daily_cases.empty:
                options_dict = {row[topic_col]: idx for idx, row in daily_cases.iterrows()}
                selected_topic = st.selectbox("พบเคสในวันนี้ แตะเพื่อเลือกดูรายละเอียดเจาะลึก:", list(options_dict.keys()))
                st.session_state.selected_case_idx = options_dict[selected_topic]
            else:
                st.info("🟢 ไม่มีเคสความเสี่ยงในวันที่เลือก")
                st.session_state.selected_case_idx = None

        # ---------------- ฝั่งขวา (รายละเอียดเคส - เวอร์ชันแก้ไขการเรนเดอร์) ----------------
        with col_right:
            st.subheader("🔍 Detailed Case View")
            
            chosen_idx = st.session_state.get('selected_case_idx')
            
            if chosen_idx is not None and chosen_idx in df.index:
                selected_case = df.loc[chosen_idx]
            elif not daily_cases.empty:
                selected_case = daily_cases.iloc[0]
            else:
                selected_case = None

            if selected_case is not None:
                # สร้าง ID และรูปแบบข้อมูล
                formatted_date_id = selected_case[date_col].strftime('%Y-%m%d')
                case_id = f"RT{formatted_date_id}"
                
                risk_val = str(selected_case[risk_col]).strip().capitalize()
                risk_icon = "🔴" if risk_val == 'High' else ("🟡" if risk_val == 'Medium' else "🟢")
                
                display_date = selected_case[date_col].strftime('%B %d, %Y')
                short_date = selected_case[date_col].strftime('%b %d')

                loc_txt = str(selected_case[loc_col]) if pd.notnull(selected_case[loc_col]) else "-"
                resp_txt = str(selected_case[resp_col]) if pd.notnull(selected_case[resp_col]) else "-"
                status_txt = str(selected_case[status_col]) if pd.notnull(selected_case[status_col]) else "-"
                action_txt = str(selected_case[action_col]) if pd.notnull(selected_case[action_col]) else "-"

                # ใช้ dedent ล้างย่อหน้าเพื่อบังคับ Streamlit ให้เรนเดอร์เป็นความสวยงาม ไม่ใช่โชว์โค้ดดิบ
                card_html = textwrap.dedent(f"""
                    <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e6e6e6; box-shadow: 0 2px 5px rgba(0,0,0,0.04); margin-bottom: 20px;">
                        <p style="margin: 6px 0; font-size: 14px; color: #333;"><strong>Case ID:</strong> {case_id}</p>
                        <p style="margin: 6px 0; font-size: 14px; color: #333;"><strong>Date:</strong> {display_date}</p>
                        <p style="margin: 6px 0 15px 0; font-size: 14px; color: #333;"><strong>Topic/risk finding:</strong> <span style="color:#d9534f; font-weight:600;">{selected_case[topic_col]}</span></p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 12px 0;">
                        <p style="margin: 8px 0; font-size: 14px; color: #444;">📍 <strong>Location:</strong> {loc_txt}</p>
                        <p style="margin: 8px 0; font-size: 14px; color: #444;">👤 <strong>Responsible Person:</strong> {resp_txt}</p>
                        <p style="margin: 8px 0; font-size: 14px; color: #444;">🔄 <strong>Status:</strong> {status_txt}</p>
                        <p style="margin: 8px 0 15px 0; font-size: 14px; color: #444;">🛠 <strong>Corrective Action:</strong> {action_txt}</p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 12px 0;">
                        <p style="margin: 6px 0; font-size: 14px; color: #111; font-weight:bold;">Risk Level: {risk_val} ({risk_icon})</p>
                    </div>
                """)
                st.markdown(card_html, unsafe_allow_html=True)
                
                # กล่อง Timeline ด้านล่างการ์ด
                timeline_html = textwrap.dedent(f"""
                    <div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border: 1px solid #eee;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <span style="font-size: 15px; font-weight: bold; color: #333;">Timeline & Activity</span>
                            <span style="color: #888; font-size: 14px;">✏️ 🖨️ 📥</span>
                        </div>
                        <div style="border-left: 2px solid #ddd; padding-left: 15px; position: relative; margin-bottom: 10px; font-size: 13px; color: #555;">
                            <span style="position: absolute; left: -5px; top: 3px; color: #bbb; font-size: 10px;">●</span>
                            <strong>{short_date}, 09:00</strong> - บันทึกข้อมูลความเสี่ยงเข้าระบบเสร็จสิ้น
                        </div>
                        <div style="border-left: 2px solid #ddd; padding-left: 15px; position: relative; font-size: 13px; color: #555;">
                            <span style="position: absolute; left: -5px; top: 3px; color: #bbb; font-size: 10px;">●</span>
                            <strong>สถานะปัจจุบัน</strong> - [{status_txt}] มอบหมายให้ทีม {resp_txt}
                        </div>
                    </div>
                """)
                st.markdown(timeline_html, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: #f8f9fa; padding: 40px 20px; border-radius: 8px; text-align: center; border: 1px dashed #ccc;">
                        <h3 style="color: #888; margin-bottom: 10px;">🔍</h3>
                        <p style="color: #666; font-size: 14px;">Select a date with a green dot on the calendar<br>to view details.</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ ไม่มีข้อมูลเพื่อแสดงผลบนปฏิทิน")

# ==========================================
# 3. REPORT NEW CASE
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
                    st.success("🎉 บันทึกข้อมูลสำเร็จ! อัปเดตในระบบเรียบร้อย")
                    st.cache_data.clear() 
                else:
                    st.error(f"❌ ไม่สามารถบันทึกได้ API รหัส: {res.status_code}")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดขณะส่งข้อมูล: {e}")