import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64
import textwrap

# ==========================================
# 1. SET PAGE CONFIG & SYSTEM INITIALIZATION
# ==========================================
st.set_page_config(page_title="Safe Together System", page_icon="🛡️", layout="wide")

# ลิงก์ Web App ของ Google Apps Script
API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

# ==========================================
# 2. PREMIUM DARK MODE CSS (ปรับปรุงเพื่อความคมชัดสูง)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');
    
    /* ฉากหลังดำสนิทตัดกับตัวหนังสือขาว */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Sarabun', sans-serif;
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* ปรับแต่งความเข้มของแถบ Sidebar */
    [data-testid="stSidebar"] {
        background-color: #09090b !important;
        border-right: 1px solid #1f1f23;
    }
    
    /* --- ส่วนหัวระบบ --- */
    .system-header {
        background: #111114;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 20px;
        border-left: 5px solid #0a84ff;
        border: 1px solid #1f1f23;
        border-left-width: 5px;
    }
    
    /* --- กล่องครอบชาร์ตและการ์ดข้อมูลสีเข้มแบบมีมิติ --- */
    .enterprise-card {
        background: #111114;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #222227;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 15px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* --- กล่องสถิติย่อยด้านบน (Mini Top Metrics) --- */
    .mini-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        margin-bottom: 15px;
    }
    .mini-kpi-card {
        background: #111114;
        padding: 12px 18px;
        border-radius: 8px;
        border: 1px solid #222227;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        display: flex;
        flex-direction: column;
    }
    .mini-kpi-label { font-size: 12px; color: #a1a1aa; font-weight: 500; }
    .mini-kpi-val { font-size: 24px; font-weight: 700; color: #ffffff; margin-top: 2px; }

    /* --- แถบแบนเนอร์สถานะขนาดใหญ่สไตล์นีออนคมชัด --- */
    .status-banner-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-bottom: 25px;
    }
    .banner-card {
        padding: 20px;
        border-radius: 8px;
        color: #ffffff;
        position: relative;
        overflow: hidden;
        min-height: 100px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .banner-num {
        position: absolute;
        right: 20px;
        top: 10px;
        font-size: 32px;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }
    .banner-label {
        font-size: 14px;
        font-weight: 600;
        margin-top: 25px;
    }
    /* คุมโทนสีเข้มชัดเจนตัดกับแอปหลังดำ */
    .bg-new { background-color: #1c2431; border: 1px solid #303f56; }       
    .bg-inspect { background-color: #631c1c; border: 1px solid #992b2b; }   
    .bg-process { background-color: #663d00; border: 1px solid #995c00; }   
    .bg-success { background-color: #14532d; border: 1px solid #166534; }   

    /* --- สไตล์การ์ดฝั่งรายละเอียดเคส --- */
    .responsive-card {
        background-color: #111114; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #222227; 
        color: #ffffff;
    }
    .card-header-box {
        display: flex; justify-content: space-between; align-items: center; 
        border-bottom: 1px solid #222227; padding-bottom: 10px; margin-bottom: 15px;
    }
    .case-p-highlight { color: #0a84ff; font-weight: 600; }
    .case-p { font-size: 14px; color: #e5e5ea; line-height: 1.5; }
    
    /* --- ไทม์ไลน์ระบบมืด --- */
    .timeline-container {
        background-color: #16161a; border-radius: 8px; padding: 15px; 
        border: 1px solid #222227; margin-top: 15px;
    }
    .timeline-row {
        border-left: 2px solid #3a3a3c; padding-left: 15px; 
        position: relative; margin-bottom: 10px; font-size: 13px; color: #d1d1d6;
    }
    .timeline-dot { position: absolute; left: -6px; top: 2px; color: #0a84ff; font-size: 11px; }

    /* ปรับแต่งสีตัวหนังสือของฟอร์ม Native Streamlit ให้สว่าง */
    label, div[data-testid="stWidgetLabel"] p { color: #ffffff !important; }
    
    @media (max-width: 768px) {
        .status-banner-grid { grid-template-columns: 1fr; }
        .mini-kpi-grid { grid-template-columns: 1fr 1fr; }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATA LAYER
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
                st.warning("⚠️ ไม่พบข้อมูลใน Google Sheets")
        else:
            st.error(f"❌ API Error: {response.status_code}")
        return pd.DataFrame()
    except Exception as e: 
        st.error(f"❌ ระบบเชื่อมต่อฐานข้อมูลขัดข้อง: {e}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# 4. NAVIGATION
# ==========================================
st.sidebar.title("⚙️ เมนูระบบ (Dark Mode)")
menu = st.sidebar.radio("เลือกหน้าต่าง:", ["📊 Dashboard Overview", "📅 ปฏิทินติดตามงาน", "📝 รายงานความเสี่ยง"])

# ==========================================
# MODULE 1: ENTERPRISE DASHBOARD OVERVIEW
# ==========================================
if menu == "📊 Dashboard Overview":
    st.markdown("""
        <div class="system-header">
            <h3 style='margin:0; color:#ffffff; font-weight:700;'>Safe Together System</h3>
            <p style='margin:5px 0 0 0; color:#a1a1aa; font-size:13px;'>ระบบส่งเสริมการมีส่วนร่วมด้านความปลอดภัยเชิงรุก (Command Center Dark Theme)</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not df.empty:
        try:
            date_col = df.columns[0]
            status_col = df.columns[4] if len(df.columns) > 4 else 'Status'
            risk_col = df.columns[10] if len(df.columns) > 10 else df.columns[-1]
            
            # --- คำนวณข้อมูลสถิติพื้นฐานภาพรวม ---
            total_cases = len(df)
            completed_cases = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ|Complete', na=False, case=False)])
            no_issue_cases = len(df[df[status_col].astype(str).str.contains('ไม่พบประเด็น|No Issue', na=False, case=False)])
            
            success_total = completed_cases + no_issue_cases
            remaining_cases = total_cases - success_total
            success_rate = (success_total / total_cases * 100) if total_cases > 0 else 0
            
            # แยกยอดตัวเลขเพื่อนำไปใส่ในการ์ดสถานะสี่สี (Banners)
            count_new = len(df[df[status_col].astype(str).str.contains('รอดำเนินการ|Pending', na=False, case=False)])
            count_inspect = len(df[df[status_col].astype(str).str.contains('ตรวจสอบ', na=False, case=False)])
            count_process = len(df[df[status_col].astype(str).str.contains('กำลังดำเนินการ|In Progress', na=False, case=False)])
            count_done = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|Complete', na=False, case=False)])

            # 1. แสดงกล่องสถิติย่อยแถวบนสุด (Mini KPI Cards)
            mini_kpi_html = textwrap.dedent(f"""
                <div class="mini-kpi-grid">
                    <div class="mini-kpi-card">
                        <span class="mini-kpi-label">รายงานทั้งหมด</span>
                        <span class="mini-kpi-val" style="color:#0a84ff;">{total_cases} ประเด็น</span>
                    </div>
                    <div class="mini-kpi-card">
                        <span class="mini-kpi-label">คงเหลือ</span>
                        <span class="mini-kpi-val" style="color:#ff453a;">{remaining_cases} ประเด็น</span>
                    </div>
                    <div class="mini-kpi-card">
                        <span class="mini-kpi-val" style="color:#30d158;">{success_total} ประเด็น</span>
                    </div>
                    <div class="mini-kpi-card">
                        <span class="mini-kpi-label">ปิดประเด็นได้</span>
                        <span class="mini-kpi-val" style="color:#ff9f0a;">{success_rate:.0f}%</span>
                    </div>
                </div>
            """)
            st.markdown(mini_kpi_html, unsafe_allow_html=True)
            
            # 2. แสดงแถวแบนเนอร์สถานะการดำเนินงานขนาดใหญ่แบบสี่สี (Status Banners)
            status_banner_html = textwrap.dedent(f"""
                <div class="status-banner-grid">
                    <div class="banner-card bg-new">
                        <div class="banner-num">{count_new}</div>
                        <div class="banner-label">📥 รับแจ้งใหม่ / รอดำเนินการ</div>
                    </div>
                    <div class="banner-card bg-inspect">
                        <div class="banner-num">{count_inspect}</div>
                        <div class="banner-label">🔍 อยู่ระหว่างตรวจสอบ</div>
                    </div>
                    <div class="banner-card bg-process">
                        <div class="banner-num">{count_process}</div>
                        <div class="banner-label">🛠️ อยู่ระหว่างดำเนินการแก้ไข</div>
                    </div>
                    <div class="banner-card bg-success">
                        <div class="banner-num">{count_done}</div>
                        <div class="banner-label">🟢 ดำเนินการเรียบร้อย</div>
                    </div>
                </div>
            """)
            st.markdown(status_banner_html, unsafe_allow_html=True)
            
            # แผนที่สีแบบ Dark Mode คมชัดสูง
            status_colors = {
                'ดำเนินการเรียบร้อย': '#30d158', 'เรียบร้อย': '#30d158', 'Complete': '#30d158',
                'กำลังดำเนินการ': '#ff9f0a', 'In Progress': '#ff9f0a',
                'รอดำเนินการ': '#546e7a', 'Pending': '#546e7a',
                'อยู่ระหว่างตรวจสอบ': '#ff453a', 'ตรวจสอบ': '#ff453a',
                'ไม่พบประเด็น': '#72727a', 'No Issue': '#72727a'
            }

            # --- แถวแสดงผลกราฟวิเคราะห์ (ปรับปรุงเป็นธีมมืด) ---
            g_col1, g_col2 = st.columns([1, 1.2])
            
            with g_col1:
                st.markdown('<div class="enterprise-card"><div class="card-title">📊 ระดับความเสี่ยง (Risk Level)</div>', unsafe_allow_html=True)
                risk_counts = df[risk_col].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
                risk_counts.columns = ['Risk Level', 'จำนวนเคส']
                
                # ใช้ template='plotly_dark' เพื่อให้กลมกลืนกับหลังบ้านสีดำ
                fig_risk_bar = px.bar(
                    risk_counts, y='Risk Level', x='จำนวนเคส', orientation='h', text='จำนวนเคส',
                    color='Risk Level', color_discrete_map={'High': '#ff453a', 'Medium': '#ff9f0a', 'Low': '#30d158'},
                    template='plotly_dark'
                )
                fig_risk_bar.update_traces(textposition='outside')
                fig_risk_bar.update_layout(
                    showlegend=False, xaxis_title="จำนวนประเด็นที่พบ", yaxis_title="",
                    height=240, margin=dict(t=10, b=10, l=10, r=30),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                fig_risk_bar.update_xaxes(showgrid=True, gridcolor='#222227')
                st.plotly_chart(fig_risk_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with g_col2:
                st.markdown('<div class="enterprise-card"><div class="card-title">📈 สรุปสัดส่วนสถานะแยกตามระดับความเสี่ยง</div>', unsafe_allow_html=True)
                df_cross = df.groupby([risk_col, status_col]).size().reset_index(name='จำนวนเคส')
                
                fig_cross = px.bar(
                    df_cross, x=risk_col, y='จำนวนเคส', color=status_col, barmode='group',
                    text='จำนวนเคส', color_discrete_map=status_colors,
                    category_orders={risk_col: ["Low", "Medium", "High"]},
                    template='plotly_dark'
                )
                fig_cross.update_traces(textposition='outside')
                fig_cross.update_layout(
                    xaxis_title="ระดับความเสี่ยง", yaxis_title="จำนวนเคส",
                    legend_title="สถานะล่าสุด", margin=dict(t=10, b=10, l=10, r=10), height=240,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                fig_cross.update_yaxes(gridcolor='#222227')
                st.plotly_chart(fig_cross, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # --- ตารางข้อมูลดิบด้านล่าง ---
            st.markdown('<div class="enterprise-card"><div class="card-title">📋 รายการบันทึกสถานการณ์ความเสี่ยงทั้งหมดในระบบ</div>', unsafe_allow_html=True)
            df_table = df.copy()
            df_table[date_col] = df_table[date_col].dt.strftime('%d/%m/%Y').fillna('ไม่ระบุ')
            st.dataframe(df_table.astype(str), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ ระบบประมวลผลแดชบอร์ดขัดข้อง: {e}")
    else:
        st.warning("⚠️ ไม่มีข้อมูลเพื่อประมวลผลแดชบอร์ด")

# ==========================================
# MODULE 2: CALENDAR & DETAILED CASE
# ==========================================
elif menu == "📅 ปฏิทินติดตามงาน":
    if not df.empty:
        date_col = df.columns[0]
        topic_col = 'Topic/risk finding' if 'Topic/risk finding' in df.columns else df.columns[1]
        loc_col = 'Location' if 'Location' in df.columns else df.columns[2]
        resp_col = 'Responsible Person' if 'Responsible Person' in df.columns else df.columns[3]
        status_col = df.columns[4] if len(df.columns) > 4 else 'Status'
        action_col = 'Corrective Action' if 'Corrective Action' in df.columns else df.columns[5]
        risk_col = df.columns[10] if len(df.columns) > 10 else df.columns[-1]

        t1, t2, t3 = st.columns([2, 1, 1])
        with t1: st.markdown("<h3 style='margin:0; color:#ffffff;'>📅 ปฏิทินติดตามงานความเสี่ยง</h3>", unsafe_allow_html=True)
        with t2: month = st.selectbox("เลือกเดือน (Month):", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with t3: year = st.selectbox("เลือกปี (Year ค.ศ.):", [2025, 2026, 2027], index=1)

        sheet_year = year + 543 
        monthly_data = df[(df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))]
        _, num_days = calendar.monthrange(year, month)
        
        if 'sel_day' not in st.session_state or st.session_state.sel_day > num_days:
            st.session_state.sel_day = 1

        col_left, col_right = st.columns([1.5, 1])

        with col_left:
            st.markdown("##### ตารางวันประจำเดือน")
            cal = calendar.Calendar(firstweekday=6)
            month_days = cal.monthdayscalendar(year, month)
            
            header = st.columns(7)
            for i, name in enumerate(["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]):
                header[i].markdown(f"<p style='text-align:center; font-weight:bold; color:#a1a1aa; margin-bottom:5px;'>{name}</p>", unsafe_allow_html=True)
            
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
                            cols[i].markdown("<p style='text-align:center; margin-top:-22px; margin-bottom:0px; color:#30d158; font-size:18px;'>•</p>", unsafe_allow_html=True)
                    else:
                        cols[i].write("")

            st.markdown("---")
            daily_cases = df[(df[date_col].dt.day == st.session_state.sel_day) & (df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))]
            
            if not daily_cases.empty:
                options_dict = {f"📌 [เคสวันที่ {row[date_col].day}] - {row[topic_col][:40]}...": idx for idx, row in daily_cases.iterrows()}
                selected_topic = st.selectbox("เลือกหัวข้อความเสี่ยงเพื่อดูเจาะลึก:", list(options_dict.keys()))
                st.session_state.selected_case_idx = options_dict[selected_topic]
            else:
                st.info("🟢 วันที่ท่านเลือกไม่มีบันทึกเหตุการณ์ความเสี่ยง")
                st.session_state.selected_case_idx = None

        with col_right:
            st.markdown("##### 🔍 รายละเอียดเคส")
            chosen_idx = st.session_state.get('selected_case_idx')
            
            if chosen_idx is not None and chosen_idx in df.index:
                selected_case = df.loc[chosen_idx]
            elif not daily_cases.empty:
                selected_case = daily_cases.iloc[0]
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

                display_color = "#ffffff"
                if "เรียบร้อย" in status_txt or "Complete" in status_txt: display_color = "#30d158"
                elif "รอดำเนินการ" in status_txt or "Pending" in status_txt: display_color = "#a1a1aa"
                elif "กำลังดำเนินการ" in status_txt or "In Progress" in status_txt: display_color = "#ff9f0a"
                elif "ตรวจสอบ" in status_txt: display_color = "#ff453a"

                card_html = textwrap.dedent(f"""
                    <div class="responsive-card">
                        <div class="card-header-box">
                            <span style="font-weight:700; color:#0a84ff;">ID: {case_id}</span>
                            <span style="color:#a1a1aa; font-size:12px;">{short_date}</span>
                        </div>
                        <p class="case-p"><strong>หัวข้อความเสี่ยง:</strong> <span class="case-p-highlight">{selected_case[topic_col]}</span></p>
                        <hr style="border:0; border-top:1px solid #222227; margin:10px 0;">
                        <p class="case-p">📍 <strong>สถานที่:</strong> {loc_txt}</p>
                        <p class="case-p">👤 <strong>ผู้รับผิดชอบ:</strong> {resp_txt}</p>
                        <p class="case-p">🔄 <strong>สถานะงาน:</strong> <span style="color:{display_color}; font-weight:bold;">{status_txt}</span></p>
                        <p class="case-p">🛠️ <strong>แนวทางแก้ไข:</strong> {action_txt}</p>
                        <hr style="border:0; border-top:1px solid #222227; margin:10px 0;">
                        <p class="case-p" style="font-weight:bold; font-size:14px; color:#ffffff;">ระดับความเสี่ยง: {risk_val} {risk_icon}</p>
                    </div>
                """)
                st.markdown(card_html, unsafe_allow_html=True)
                
                # --- ภาพถ่ายประกอบหลักการ ---
                st.markdown("<p style='font-size:13px; font-weight:600; margin-top:15px; color:#ffffff;'>📸 ภาพถ่ายเหตุการณ์ (Before / After)</p>", unsafe_allow_html=True)
                i_col1, i_col2 = st.columns(2)
                
                img_b_url = str(selected_case[df.columns[8]]).strip() if len(df.columns) > 8 and pd.notnull(selected_case[df.columns[8]]) else ""
                img_a_url = str(selected_case[df.columns[9]]).strip() if len(df.columns) > 9 and pd.notnull(selected_case[df.columns[9]]) else ""

                with i_col1:
                    if img_b_url.startswith('http'): st.image(img_b_url, caption="ก่อนแก้ไข", use_container_width=True)
                    elif len(img_b_url) > 100: st.image(base64.b64decode(img_b_url), caption="ก่อนแก้ไข", use_container_width=True)
                    else: st.image("https://cdn-icons-png.flaticon.com/512/1161/1161388.png", caption="ไม่มีรูปประกอบ", use_container_width=True)

                with i_col2:
                    if img_a_url.startswith('http'): st.image(img_a_url, caption="หลังแก้ไข", use_container_width=True)
                    elif len(img_a_url) > 100: st.image(base64.b64decode(img_a_url), caption="หลังแก้ไข", use_container_width=True)
                    else: st.image("https://cdn-icons-png.flaticon.com/512/1161/1161388.png", caption="ไม่มีรูปประกอบ", use_container_width=True)
            else:
                st.info("กรุณาเลือกเคสบนแผงควบคุมฝั่งซ้าย")
    else:
        st.warning("⚠️ ไม่มีข้อมูลแสดงผลบนปฏิทิน")

# ==========================================
# MODULE 3: REPORT NEW CASE
# ==========================================
elif menu == "📝 รายงานความเสี่ยง":
    st.markdown("<h2 style='color:#ffffff;'>📝 บันทึกรายงานสถานการณ์ความเสี่ยง</h2>", unsafe_allow_html=True)
    with st.form("risk_form", clear_on_submit=True):
        f_date = st.date_input("วันที่บันทึกพบเหตุ (Date)")
        f_topic = st.text_input("หัวข้อประเด็นความเสี่ยง/สิ่งที่พบ (Topic/risk finding)")
        f_loc = st.text_input("พื้นที่/สถานที่ปฏิบัติงาน (Location)")
        f_resp = st.text_input("ผู้รับผิดชอบหลัก (Responsible Person)")
        
        f_status = st.selectbox("สถานะการดำเนินงาน (Status)", ["รอดำเนินการ", "อยู่ระหว่างตรวจสอบ", "กำลังดำเนินการ", "ดำเนินการเรียบร้อย", "ไม่พบประเด็น"])
        f_action = st.text_area("แนวทางการแก้ไขเชิงรุก (Corrective Action)")
        f_risk = st.selectbox("ประเมินระดับความเสี่ยง (Risk Level)", ["Low", "Medium", "High"])
        
        up_before = st.file_uploader("แนบรูปถ่ายก่อนแก้ไข (Before)")
        up_after = st.file_uploader("แนบรูปถ่ายหลังแก้ไข (After)")
        
        if st.form_submit_button("🚀 บันทึกข้อมูลและอัปเดตระบบ"):
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
                    st.success("🎉 บันทึกรายงานเข้าระบบเรียบร้อยแล้ว!")
                    st.cache_data.clear() 
                else:
                    st.error(f"❌ เกิดข้อผิดพลาดจากเซิร์ฟเวอร์รหัส: {res.status_code}")
            except Exception as e:
                st.error(f"❌ ระบบส่งข้อมูลล้มเหลว: {e}")
