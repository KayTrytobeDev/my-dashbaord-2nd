import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64
import textwrap

# ==========================================
# 1. SET PAGE CONFIG (ตั้งค่าระบบหน้าเว็บ)
# ==========================================
st.set_page_config(page_title="Risk Tracker System", page_icon="🛡️", layout="wide")

# ลิงก์ Web App ของ Google Apps Script
API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

# ==========================================
# 2. GLOBAL RESPONSIVE CSS (ระบบแต่งหน้าตาสำหรับทุกอุปกรณ์)
# ==========================================
st.markdown("""
    <style>
    /* --- สไตล์การ์ดรายละเอียด (Desktop First) --- */
    .responsive-card {
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 8px; 
        border: 1px solid #e6e6e6; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.04); 
        margin-bottom: 20px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .card-header-box {
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-bottom: 1px solid #f0f0f0; 
        padding-bottom: 12px; 
        margin-bottom: 15px;
    }
    .card-title-text { font-size: 16px; font-weight: bold; color: #111; }
    .card-date-text { color: #888; font-size: 13px; }
    .case-p { margin: 8px 0; font-size: 14px; color: #444; line-height: 1.5; }
    .case-p-highlight { color:#d9534f; font-weight:600; }
    
    /* --- สไตล์สำหรับกล่อง Timeline --- */
    .timeline-container {
        background-color: #f8f9fa; 
        border-radius: 8px; 
        padding: 15px; 
        border: 1px solid #eee;
    }
    .timeline-header {
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        margin-bottom: 12px;
    }
    .timeline-row {
        border-left: 2px solid #ddd; 
        padding-left: 15px; 
        position: relative; 
        margin-bottom: 10px; 
        font-size: 13px; 
        color: #555;
    }
    .timeline-dot { position: absolute; left: -5px; top: 3px; color: #bbb; font-size: 10px; }
    
    /* กล่องกรณีไม่มีข้อมูล */
    .empty-state-box {
        background-color: #f8f9fa; 
        padding: 40px 20px; 
        border-radius: 8px; 
        text-align: center; 
        border: 1px dashed #ccc;
    }

    /* ==========================================
       🔥 Media Queries สำหรับ iPhone / หน้าจอมือถือ (< 768px)
       ========================================== */
    @media (max-width: 768px) {
        .responsive-card { padding: 14px; margin-bottom: 15px; }
        .card-header-box { flex-direction: column; align-items: flex-start; gap: 5px; }
        .card-title-text { font-size: 15px; }
        .case-p { font-size: 13px; margin: 6px 0; }
        .timeline-container { padding: 12px; }
        .timeline-row { font-size: 12px; }
        
        /* ย่อขนาดปุ่มปฏิทินบนหน้าจอมือถือไม่ให้ดันกันล้นจอ */
        .stButton > button {
            padding: 4px 2px !important;
            font-size: 12px !important;
            min-height: 35px !important;
        }
        .calendar-day-header { font-size: 11px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATA CORE (ระบบดึงข้อมูลหลังบ้าน)
# ==========================================
@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                df.columns = df.columns.str.strip()
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

df = load_data()

# ==========================================
# 4. SIDEBAR NAVIGATION (เมนูหลัก)
# ==========================================
st.sidebar.title("🛡️ Risk Tracker")
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# MODULE 1: DASHBOARD (หน้าสรุปภาพรวม)
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 ระบบวิเคราะห์และสรุปภาพรวมความเสี่ยง")
    
    if not df.empty:
        try:
            date_col = df.columns[0]
            status_col = 'Status' if 'Status' in df.columns else df.columns[4]
            risk_col = 'Risk Level' if 'Risk Level' in df.columns else df.columns[-1]
            
            # --- KPI Cards ---
            total_cases = len(df)
            completed_cases = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ|Complete', na=False, case=False)])
            high_risk_cases = len(df[df[risk_col].astype(str).str.contains('High', case=False, na=False)])
            success_rate = (completed_cases / total_cases * 100) if total_cases > 0 else 0
            
            m_col1, m_col2, m_col3, m_col4 = st.columns([1, 1, 1, 1])
            m_col1.metric("📌 เคสความเสี่ยงทั้งหมด", f"{total_cases} เคส")
            m_col2.metric("✅ ดำเนินการสำเร็จแล้ว", f"{completed_cases} เคส")
            m_col3.metric("🚨 เคสวิกฤต (High Risk)", f"{high_risk_cases} เคส")
            m_col4.metric("📈 อัตราการแก้ปัญหา", f"{success_rate:.1f}%")
            
            st.markdown("---")
            
            # --- กราฟวิเคราะห์ (สไตล์ยืดหยุ่นตามหน้าจออัตโนมัติ) ---
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
            
            # --- ตารางข้อมูลดิบ ---
            st.subheader("📋 รายการบันทึกความเสี่ยงล่าสุด")
            df_table = df.copy()
            df_table[date_col] = df_table[date_col].dt.strftime('%d/%m/%Y').fillna('ไม่ระบุ')
            st.dataframe(df_table.astype(str), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในหน้า Dashboard: {e}")
    else:
        st.warning("⚠️ ไม่มีข้อมูลในระบบ")

# ==========================================
# MODULE 2: CALENDAR & CASE DETAIL (หน้าจออัจฉริยะรองรับ iPhone)
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    if not df.empty:
        date_col = df.columns[0]
        topic_col = 'Topic/risk finding' if 'Topic/risk finding' in df.columns else df.columns[1]
        loc_col = 'Location' if 'Location' in df.columns else df.columns[2]
        resp_col = 'Responsible Person' if 'Responsible Person' in df.columns else df.columns[3]
        status_col = 'Status' if 'Status' in df.columns else df.columns[4]
        action_col = 'Corrective Action' if 'Corrective Action' in df.columns else df.columns[5]
        risk_col = 'Risk Level' if 'Risk Level' in df.columns else df.columns[-1]

        # แถบควบคุมเวลาด้านบน
        t1, t2, t3 = st.columns([2, 1, 1])
        with t1: st.title("📅 Calendar & Case")
        with t2: month = st.selectbox("Month:", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with t3: year = st.selectbox("Year:", [2025, 2026, 2027], index=1)

        sheet_year = year + 543 

        # สวิตช์สลับโหมดตามขนาดอุปกรณ์เพื่อป้องกันตารางล้นใน iPhone
        view_mode = st.radio(
            "รูปแบบการแสดงผลที่เหมาะสมกับอุปกรณ์ของคุณ:", 
            ["📅 ตารางปฏิทิน (สำหรับคอมพิวเตอร์/แท็บเล็ต)", "📱 รายการเคสประจำเดือน (แนะนำสำหรับ iPhone/มือถือ)"], 
            horizontal=True
        )
        st.markdown("---")

        monthly_data = df[(df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))]

        _, num_days = calendar.monthrange(year, month)
        if 'sel_day' not in st.session_state or st.session_state.sel_day > num_days:
            st.session_state.sel_day = 1

        # แบ่งฝั่งการ์ด 65:35 (สลับเป็นบนล่างอัตโนมัติบนสมาร์ทโฟน)
        col_left, col_right = st.columns([1.6, 1])

        # ---- ฝั่งซ้าย: แหล่งจิ้มเลือกข้อมูล ----
        with col_left:
            if "📅 ตารางปฏิทิน" in view_mode:
                # โหมดวาดตารางปฏิทินปกติ
                cal = calendar.Calendar(firstweekday=6)
                month_days = cal.monthdayscalendar(year, month)
                
                header = st.columns(7)
                for i, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
                    header[i].markdown(f"<p class='calendar-day-header' style='text-align:center; font-weight:bold; color:#666; margin-bottom:5px;'>{name}</p>", unsafe_allow_html=True)
                
                for week in month_days:
                    cols = st.columns(7)
                    for i, day in enumerate(week):
                        if day != 0:
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

                st.markdown("---")
                st.subheader(f"Selected Date Summary: {calendar.month_name[month]} {st.session_state.sel_day}, {year}")
                
                daily_cases = df[(df[date_col].dt.day == st.session_state.sel_day) & (df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))]
                
                if not daily_cases.empty:
                    options_dict = {f"📌 [วันที่ {row[date_col].day}] - {row[topic_col]}": idx for idx, row in daily_cases.iterrows()}
                    selected_topic = st.selectbox("พบเคสในวันนี้ แตะเพื่อเลือกดูเจาะลึก:", list(options_dict.keys()))
                    st.session_state.selected_case_idx = options_dict[selected_topic]
                else:
                    st.info("🟢 ไม่มีเคสความเสี่ยงในวันที่เลือก")
                    st.session_state.selected_case_idx = None

            else:
                # โหมดรายการแนวตั้ง หมดปัญหาหน้าจอ iPhone บีบตารางจิ๋ว
                st.subheader(f"📋 รายการเคสประจำเดือน {calendar.month_name[month]}")
                
                if not monthly_data.empty:
                    monthly_data = monthly_data.sort_values(by=date_col)
                    options_dict = {f"📅 วันที่ {row[date_col].day} | {row[topic_col][:25]}...": idx for idx, row in monthly_data.iterrows()}
                    
                    selected_mobile_case = st.radio(
                        "📱 แตะเลือกเคสเพื่ออัปเดตรายละเอียดฝั่งขวา (หรือด้านล่าง):", 
                        list(options_dict.keys()),
                        key="mobile_case_radio"
                    )
                    st.session_state.selected_case_idx = options_dict[selected_mobile_case]
                    st.session_state.sel_day = df.loc[st.session_state.selected_case_idx][date_col].day
                else:
                    st.success(f"🎉 เดือนนี้ปลอดภัยดี ไม่มีบันทึกเคสความเสี่ยงใดๆ")
                    st.session_state.selected_case_idx = None

        # ---- ฝั่งขวา: การ์ดแสดงข้อมูลเจาะลึก (Responsive Card) ----
        with col_right:
            st.subheader("🔍 Detailed Case View")
            chosen_idx = st.session_state.get('selected_case_idx')
            
            if chosen_idx is not None and chosen_idx in df.index:
                selected_case = df.loc[chosen_idx]
            elif "📅 ตารางปฏิทิน" in view_mode and not daily_cases.empty:
                selected_case = daily_cases.iloc[0]
            elif "📱 รายการเคสประจำเดือน" in view_mode and not monthly_data.empty:
                selected_case = monthly_data.iloc[0]
            else:
                selected_case = None

            if selected_case is not None:
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

                # ใช้คลาส CSS อัจฉริยะตัดคำอัตโนมัติป้องกันตัวหนังสือทะลุกรอบในจอโทรศัพท์
                card_html = textwrap.dedent(f"""
                    <div class="responsive-card">
                        <div class="card-header-box">
                            <span class="card-title-text">Case ID: {case_id}</span>
                            <span class="card-date-text">For {short_date}</span>
                        </div>
                        <p class="case-p"><strong>Date:</strong> {display_date}</p>
                        <p class="case-p"><strong>Topic/risk finding:</strong> <span class="case-p-highlight">{selected_case[topic_col]}</span></p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 12px 0;">
                        <p class="case-p">📍 <strong>Location:</strong> {loc_txt}</p>
                        <p class="case-p">👤 <strong>Responsible Person:</strong> {resp_txt}</p>
                        <p class="case-p">🔄 <strong>Status:</strong> {status_txt}</p>
                        <p class="case-p">🛠 <strong>Corrective Action:</strong> {action_txt}</p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 12px 0;">
                        <p class="case-p" style="font-weight:bold; color:#111;">Risk Level: {risk_val} {risk_icon}</p>
                    </div>
                """)
                st.markdown(card_html, unsafe_allow_html=True)
                
                # กล่องประวัติ Timeline
                timeline_html = textwrap.dedent(f"""
                    <div class="timeline-container">
                        <div class="timeline-header">
                            <span style="font-size: 14px; font-weight: bold; color: #333;">Timeline & Activity</span>
                            <span style="color: #888; font-size: 13px;">✏️ 🖨️ 📥</span>
                        </div>
                        <div class="timeline-row">
                            <span class="timeline-dot">●</span>
                            <strong>{short_date}, 09:00</strong> - บันทึกข้อมูลความเสี่ยงเข้าระบบเสร็จสิ้น
                        </div>
                        <div class="timeline-row">
                            <span class="timeline-dot">●</span>
                            <strong>สถานะปัจจุบัน</strong> - [{status_txt}] มอบหมายให้ทีม {resp_txt}
                        </div>
                    </div>
                """)
                st.markdown(timeline_html, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="empty-state-box">
                        <h3 style="color: #888; margin-bottom: 10px;">🔍</h3>
                        <p style="color: #666; font-size: 14px;">No case selected.<br>Please choose a case from the left panel.</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ ไม่มีข้อมูลเพื่อแสดงผลบนปฏิทิน")

# ==========================================
# MODULE 3: REPORT NEW CASE (หน้าฟอร์มรายงาน)
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