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
# 2. CALENDAR & CASE DETAIL (UI ปรับปรุงใหม่ตามรูป)
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    # --- Custom CSS สำหรับ UI สไตล์ Modern ---
    st.markdown("""
        <style>
        .case-card {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid #28a745;
            margin-bottom: 20px;
        }
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }
        .risk-high { background-color: #ff4b4b; }
        .risk-medium { background-color: #ffa500; }
        .risk-low { background-color: #00cc96; }
        .timeline-item {
            border-left: 2px solid #ddd;
            padding-left: 20px;
            position: relative;
            margin-bottom: 15px;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -7px;
            top: 5px;
            width: 12px;
            height: 12px;
            background-color: #28a745;
            border-radius: 50%;
        }
        </style>
    """, unsafe_allow_html=True)

    if not df.empty:
        date_col = df.columns[0]
        
        # ส่วนหัว: ชื่อหน้าและตัวเลือกเดือน/ปี
        t1, t2, t3 = st.columns([2, 1, 1])
        with t1: st.title("📅 Calendar & Case Detail")
        with t2: month = st.selectbox("Month:", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with t3: year = st.selectbox("Year:", [2024, 2025, 2026], index=2)

        # แบ่ง Layout เป็น 2 ฝั่ง (ซ้าย: ปฏิทิน, ขวา: รายละเอียด)
        col_left, col_right = st.columns([1.8, 1])

        # --- ฝั่งซ้าย: ปฏิทิน ---
        with col_left:
            cal = calendar.Calendar(firstweekday=6)
            month_days = cal.monthdayscalendar(year, month)
            
            # วาด Grid ปฏิทิน
            header = st.columns(7)
            days_abbr = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            for i, name in enumerate(days_abbr):
                header[i].markdown(f"<p style='text-align:center; color:#888;'>{name}</p>", unsafe_allow_html=True)
            
            # ตัวแปรสำหรับเก็บวันที่ผู้ใช้เลือก (Default วันนี้หรือวันแรกที่มีเคส)
            selected_date = st.session_state.get('sel_date', datetime.now().day)

            for week in month_days:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day != 0:
                        # ตรวจสอบว่าวันนั้นมีเคสไหม
                        day_data = df[(df[date_col].dt.day == day) & (df[date_col].dt.month == month) & (df[date_col].dt.year == year)]
                        
                        has_case = not day_data.empty
                        is_selected = (day == selected_date)
                        
                        # สไตล์ปุ่มปฏิทิน
                        bg = "#28a745" if is_selected else ("#f0f2f6" if has_case else "#ffffff")
                        txt = "#ffffff" if is_selected else "#31333F"
                        border = "1px solid #ddd"
                        
                        if cols[i].button(f"{day}", key=f"day_{day}", use_container_width=True):
                            st.session_state.sel_date = day
                            st.rerun()

                        if has_case and not is_selected:
                            cols[i].markdown("<p style='text-align:center; margin-top:-15px; color:#28a745;'>●</p>", unsafe_allow_html=True)
                    else:
                        cols[i].write("")

            # รายชื่อเคสของวันที่เลือก (ด้านล่างปฏิทิน)
            st.write("---")
            curr_date_str = f"{year}-{month:02d}-{st.session_state.get('sel_date', 1):02d}"
            st.subheader(f"Selected Date Summary: {st.session_state.get('sel_date', 1)} {calendar.month_name[month]}")
            
            daily_cases = df[(df[date_col].dt.day == st.session_state.get('sel_date', 1)) & 
                           (df[date_col].dt.month == month) & 
                           (df[date_col].dt.year == year)]
            
            if not daily_cases.empty:
                for idx, row in daily_cases.iterrows():
                    if st.button(f"🚩 {row.iloc[1]}", key=f"btn_{idx}"):
                        st.session_state.selected_case_id = idx
            else:
                st.info("No cases reported for this date.")

        # --- ฝั่งขวา: รายละเอียดเคส (Case Detail Card) ---
        with col_right:
            st.subheader("📋 Detailed Case View")
            
            # ดึงข้อมูลเคสที่เลือก (ถ้าไม่มีให้เอาเคสแรกของวันนั้น)
            target_idx = st.session_state.get('selected_case_id')
            if target_idx is not None and target_idx in df.index:
                case = df.loc[target_idx]
            elif not daily_cases.empty:
                case = daily_cases.iloc[0]
            else:
                case = None

            if case is not None:
                risk_class = f"risk-{case['Risk Level'].lower()}"
                
                # แสดงผลแบบ Card
                st.markdown(f"""
                    <div class="case-card">
                        <p style='color:#888; font-size:12px; margin-bottom:5px;'>For {case[date_col].strftime('%b %d')}</p>
                        <h3 style='margin-top:0;'>{case.iloc[1]}</h3>
                        <hr>
                        <p><strong>📍 Location:</strong> {case['Location']}</p>
                        <p><strong>👤 Responsible:</strong> {case['Responsible Person']}</p>
                        <p><strong>🔄 Status:</strong> {case['Status']}</p>
                        <p><strong>🛠 Action:</strong> {case['Corrective Action']}</p>
                        <div style='margin-top:15px;'>
                            <span class="status-badge {risk_class}">Risk Level: {case['Risk Level']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Timeline จำลอง
                st.write("---")
                st.markdown("#### 🕒 Timeline & Activity")
                st.markdown(f"""
                    <div class="timeline-item">
                        <p style='margin-bottom:0;'><strong>{case[date_col].strftime('%b %d')}</strong> - Case reported by system</p>
                    </div>
                    <div class="timeline-item">
                        <p style='margin-bottom:0;'><strong>{case[date_col].strftime('%b %d')}</strong> - Assigned to {case['Responsible Person']}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.write("Please select a date with a case to view details.")

    else:
        st.warning("No data available. Please check your API connection.")
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