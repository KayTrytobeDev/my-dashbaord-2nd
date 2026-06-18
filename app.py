import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64
import textwrap

# ==========================================
# 1. SET PAGE CONFIG & THEME PRESET
# ==========================================
st.set_page_config(page_title="Risk Tracker System", page_icon="🛡️", layout="wide")

API_URL = "https://script.google.com/macros/s/AKfycbwLPuQzhvnuLBCsrRz-iPyOtwt-N_njyHORXN8FseVpL2-Pt7m7TqZaj3uHTkdlWTwA/exec"

# ==========================================
# 2. PREMIUM DARK MODE CSS (พื้นหลังดำสนิท)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ฉากหลังดำสนิทตัดกับตัวหนังสือขาว */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #09090b !important;
        border-right: 1px solid #1f1f23;
    }

    /* ล็อกสีปุ่มในปฏิทินให้มองเห็นชัดเจนใน Dark Mode */
    div[data-testid="stButton"] > button {
        background-color: #18181b !important; 
        color: #ffffff !important; 
        border: 1px solid #33333a !important;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #0a84ff !important;
        color: #0a84ff !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #2ec4b6 !important;
        border-color: #2ec4b6 !important;
        color: #ffffff !important;
    }
    
    /* บังคับฟอร์ม Input ให้เป็นสีเข้ม */
    div[data-baseweb="select"] > div, input, textarea {
        background-color: #18181b !important;
        color: #ffffff !important;
        border-color: #33333a !important;
    }
    label, div[data-testid="stWidgetLabel"] p { color: #e5e5ea !important; }
    
    /* --- Dashboard Widget Card --- */
    .dashboard-card {
        background: #111114; padding: 24px; border-radius: 12px;
        border: 1px solid #222227; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4); margin-bottom: 24px;
    }
    .dashboard-card-title {
        font-size: 16px; font-weight: 600; color: #ffffff;
        margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
    }

    /* --- Custom KPI Cards --- */
    .kpi-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 25px; }
    .kpi-card {
        background: #111114; border-radius: 12px; padding: 20px; border-left: 5px solid #333;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); border-top: 1px solid #222227; border-right: 1px solid #222227; border-bottom: 1px solid #222227;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .kpi-label { font-size: 13px; font-weight: 500; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin: 8px 0 4px 0; }
    .kpi-subtext { font-size: 12px; color: #8e8e93; }
    
    .kpi-total { border-left-color: #0a84ff; }
    .kpi-success { border-left-color: #30d158; }
    .kpi-pending { border-left-color: #ff9f0a; }
    .kpi-rate { border-left-color: #bf5af2; }

    /* --- Case Detail Card --- */
    .responsive-card {
        background-color: #111114; padding: 24px; border-radius: 12px; 
        border: 1px solid #222227; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4); margin-bottom: 20px; word-wrap: break-word; color: #ffffff;
    }
    .card-header-box { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #222227; padding-bottom: 14px; margin-bottom: 18px; }
    .card-title-text { font-size: 16px; font-weight: 700; color: #ffffff; }
    .card-date-text { color: #a1a1aa; font-size: 13px; font-weight: 500; }
    .case-p { margin: 10px 0; font-size: 14px; color: #e5e5ea; line-height: 1.6; }
    .case-p-highlight { color: #0a84ff; font-weight: 600; }
    
    /* --- Timeline --- */
    .timeline-container { background-color: #16161a; border-radius: 12px; padding: 18px; border: 1px solid #222227; margin-top: 20px; }
    .timeline-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .timeline-row { border-left: 2px solid #3a3a3c; padding-left: 18px; position: relative; margin-bottom: 12px; font-size: 13px; color: #d1d1d6; }
    .timeline-dot { position: absolute; left: -6px; top: 2px; color: #a1a1aa; font-size: 11px; }
    .empty-state-box { background-color: #111114; padding: 50px 20px; border-radius: 12px; text-align: center; border: 1px dashed #3a3a3c; color: #ffffff; }

    @media (max-width: 768px) {
        .dashboard-card { padding: 16px; }
        .kpi-container { grid-template-columns: 1fr; gap: 12px; }
        .responsive-card { padding: 16px; }
        .card-header-box { flex-direction: column; align-items: flex-start; gap: 6px; }
        .stButton > button { padding: 4px 2px !important; font-size: 12px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATA CORE
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
# 4. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🛡️ Risk Tracker")
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# MODULE 1: DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.markdown("<h2 style='color: #ffffff; font-weight: 700; margin-bottom: 20px;'>📊 Overview & Risk Analytics</h2>", unsafe_allow_html=True)
    
    if not df.empty:
        try:
            # 📌 ระบบดึงหัวตารางอัจฉริยะ 
            date_col = df.columns[0]
            cols = df.columns.tolist()
            status_col = 'Status' if 'Status' in cols else (cols[4] if len(cols) > 4 else cols[-1])
            risk_col = 'Risk Level' if 'Risk Level' in cols else (cols[10] if len(cols) > 10 else cols[-1])
            
            # --- KPI Cards ---
            total_cases = len(df)
            completed_cases = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ|Complete|ไม่พบประเด็น', na=False, case=False)])
            pending_cases = len(df[df[status_col].astype(str).str.contains('รอดำเนินการ|กำลังดำเนินการ|Pending|In Progress', na=False, case=False)])
            success_rate = (completed_cases / total_cases * 100) if total_cases > 0 else 0
            
            kpi_html = textwrap.dedent(f"""
                <div class="kpi-container">
                    <div class="kpi-card kpi-total">
                        <div class="kpi-label">เคสความเสี่ยงทั้งหมด</div>
                        <div class="kpi-value">{total_cases}</div>
                        <div class="kpi-subtext">🔄 บันทึกสะสมในระบบ</div>
                    </div>
                    <div class="kpi-card kpi-success">
                        <div class="kpi-label">ปิดงานเรียบร้อยแล้ว</div>
                        <div class="kpi-value">{completed_cases}</div>
                        <div class="kpi-subtext">🟢 ปิดงานสำเร็จ</div>
                    </div>
                    <div class="kpi-card kpi-pending">
                        <div class="kpi-label">รอดำเนินการ / กำลังทำ</div>
                        <div class="kpi-value">{pending_cases}</div>
                        <div class="kpi-subtext">⏳ อยู่ระหว่างกระบวนการ</div>
                    </div>
                    <div class="kpi-card kpi-rate">
                        <div class="kpi-label">อัตราความสำเร็จภาพรวม</div>
                        <div class="kpi-value">{success_rate:.1f}%</div>
                        <div class="kpi-subtext">📈 ดัชนีประสิทธิภาพ</div>
                    </div>
                </div>
            """)
            st.markdown(kpi_html, unsafe_allow_html=True)
            
            # ปรับชุดสีให้สว่างสู้พื้นหลังดำ
            status_colors = {
                'ดำเนินการเรียบร้อย': '#30d158', 'เรียบร้อย': '#30d158', 'Complete': '#30d158',
                'กำลังดำเนินการ': '#ff9f0a', 'In Progress': '#ff9f0a',
                'รอดำเนินการ': '#ff453a', 'Pending': '#ff453a',
                'ไม่พบประเด็น': '#8e8e93', 'No Issue': '#8e8e93'
            }

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown('<div class="dashboard-card"><div class="dashboard-card-title">💡 สัดส่วนสถานะการดำเนินงานภาพรวม</div>', unsafe_allow_html=True)
                status_counts = df[status_col].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                fig_pie = px.pie(status_counts, values='Count', names='Status', hole=0.55, color='Status', color_discrete_map=status_colors)
                # 📌 บังคับกราฟใช้ Theme Dark
                fig_pie.update_layout(template='plotly_dark', showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#111114', width=2)))
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with g_col2:
                st.markdown('<div class="dashboard-card"><div class="dashboard-card-title">⚡ ปริมาณเคสแยกตามระดับความเสี่ยง</div>', unsafe_allow_html=True)
                risk_counts = df[risk_col].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
                risk_counts.columns = ['Risk', 'Count']
                
                # 📌 บังคับฟอนต์กราฟและ Theme Dark
                fig_bar = px.bar(risk_counts, x='Risk', y='Count', color='Risk', text='Count', color_discrete_map={'High': '#ff453a', 'Medium': '#ffb703', 'Low': '#30d158'})
                fig_bar.update_traces(textposition='outside', textfont=dict(color='#ffffff', size=14))
                fig_bar.update_layout(template='plotly_dark', showlegend=False, xaxis_title="", yaxis_title="จำนวนเคส", margin=dict(t=10, b=10, l=10, r=10), height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig_bar.update_yaxes(gridcolor='#222227')
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('<div class="dashboard-card"><div class="dashboard-card-title">📊 สรุปสถานะการทำงานแยกตามระดับความเสี่ยง</div>', unsafe_allow_html=True)
            df_cross = df.groupby([risk_col, status_col]).size().reset_index(name='จำนวนเคส')
            
            # 📌 บังคับฟอนต์กราฟกลุ่มและ Theme Dark
            fig_cross = px.bar(
                df_cross, x=risk_col, y='จำนวนเคส', color=status_col, barmode='group',
                text='จำนวนเคส', color_discrete_map=status_colors,
                category_orders={risk_col: ["Low", "Medium", "High"]}
            )
            fig_cross.update_traces(textposition='outside', textfont=dict(color='#ffffff', size=13), marker=dict(line=dict(width=0)))
            fig_cross.update_layout(
                template='plotly_dark',
                xaxis_title="ระดับความเสี่ยง (Risk Level)", yaxis_title="จำนวนบันทึก (เคส)",
                legend_title="สถานะปัจจุบัน", margin=dict(t=30, b=10, l=10, r=10), height=340,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            fig_cross.update_yaxes(gridcolor='#222227')
            st.plotly_chart(fig_cross, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="dashboard-card"><div class="dashboard-card-title">📋 รายการบันทึกสถานการณ์ล่าสุด</div>', unsafe_allow_html=True)
            df_table = df.copy()
            df_table[date_col] = df_table[date_col].dt.strftime('%d/%m/%Y').fillna('ไม่ระบุ')
            st.dataframe(df_table.astype(str), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในหน้า Dashboard: {e}")
    else:
        st.warning("⚠️ ไม่มีข้อมูลในระบบ")

# ==========================================
# MODULE 2: CALENDAR & CASE DETAIL 
# ==========================================
elif menu == "📅 Calendar & Case Detail":
    if not df.empty:
        cols = df.columns.tolist()
        date_col = cols[0]
        topic_col = 'Topic/risk finding' if 'Topic/risk finding' in cols else cols[1]
        loc_col = 'Location' if 'Location' in cols else cols[2]
        resp_col = 'Responsible Person' if 'Responsible Person' in cols else cols[3]
        status_col = 'Status' if 'Status' in cols else (cols[4] if len(cols) > 4 else cols[-1])
        action_col = 'Corrective Action' if 'Corrective Action' in cols else cols[5]
        risk_col = 'Risk Level' if 'Risk Level' in cols else (cols[10] if len(cols) > 10 else cols[-1])

        t1, t2, t3 = st.columns([2, 1, 1])
        with t1: st.title("📅 Calendar & Case")
        with t2: month = st.selectbox("Month:", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with t3: year = st.selectbox("Year:", [2025, 2026, 2027], index=1)

        sheet_year = year + 543 

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

        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            if "📅 ตารางปฏิทิน" in view_mode:
                cal = calendar.Calendar(firstweekday=6)
                month_days = cal.monthdayscalendar(year, month)
                
                header = st.columns(7)
                for i, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
                    header[i].markdown(f"<p style='text-align:center; font-weight:bold; color:#a1a1aa; margin-bottom:5px;'>{name}</p>", unsafe_allow_html=True)
                
                for week in month_days:
                    cols_grid = st.columns(7)
                    for i, day in enumerate(week):
                        if day != 0:
                            is_match = (df[date_col].dt.day == day) & (df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))
                            day_data = df[is_match]
                            
                            has_case = not day_data.empty
                            is_selected = (day == st.session_state.sel_day)
                            btn_type = "primary" if is_selected else "secondary"
                            
                            if cols_grid[i].button(f"{day}", key=f"d_{day}", type=btn_type, use_container_width=True):
                                st.session_state.sel_day = day
                                st.session_state.pop('selected_case_idx', None) 
                                st.rerun()
                            
                            if has_case and not is_selected:
                                cols_grid[i].markdown("<p style='text-align:center; margin-top:-22px; margin-bottom:0px; color:#30d158; font-size:18px;'>•</p>", unsafe_allow_html=True)
                        else:
                            cols_grid[i].write("")

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
                st.subheader(f"📋 รายการเคสประจำเดือน {calendar.month_name[month]}")
                
                if not monthly_data.empty:
                    monthly_data = monthly_data.sort_values(by=date_col)
                    options_dict = {f"📅 วันที่ {row[date_col].day} | {row[topic_col][:25]}...": idx for idx, row in monthly_data.iterrows()}
                    
                    selected_mobile_case = st.radio(
                        "📱 แตะเลือกเคสเพื่ออัปเดตรายละเอียดฝั่งขวา (หรือด้านล่าง):", 
                        list(options_dict.keys()), key="mobile_case_radio"
                    )
                    st.session_state.selected_case_idx = options_dict[selected_mobile_case]
                    st.session_state.sel_day = df.loc[st.session_state.selected_case_idx][date_col].day
                else:
                    st.success(f"🎉 เดือนนี้ปลอดภัยดี ไม่มีบันทึกเคสความเสี่ยงใดๆ")
                    st.session_state.selected_case_idx = None

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

                display_color = "#e5e5ea"
                if "เรียบร้อย" in status_txt or "Complete" in status_txt: display_color = "#30d158" 
                elif "รอดำเนินการ" in status_txt or "Pending" in status_txt: display_color = "#ff453a" 
                elif "กำลังดำเนินการ" in status_txt or "In Progress" in status_txt: display_color = "#ff9f0a" 
                elif "ไม่พบประเด็น" in status_txt or "No Issue" in status_txt: display_color = "#8e8e93" 

                card_html = textwrap.dedent(f"""
                    <div class="responsive-card">
                        <div class="card-header-box">
                            <span class="card-title-text">Case ID: {case_id}</span>
                            <span class="card-date-text">For {short_date}</span>
                        </div>
                        <p class="case-p"><strong>Date:</strong> {display_date}</p>
                        <p class="case-p"><strong>Topic/risk finding:</strong> <span class="case-p-highlight">{selected_case[topic_col]}</span></p>
                        <hr style="border: 0; border-top: 1px solid #222227; margin: 12px 0;">
                        <p class="case-p">📍 <strong>Location:</strong> {loc_txt}</p>
                        <p class="case-p">👤 <strong>Responsible Person:</strong> {resp_txt}</p>
                        <p class="case-p">🔄 <strong>Status:</strong> <span style="color: {display_color}; font-weight: bold;">{status_txt}</span></p>
                        <p class="case-p">🛠 <strong>Corrective Action:</strong> {action_txt}</p>
                        <hr style="border: 0; border-top: 1px solid #222227; margin: 12px 0;">
                        <p class="case-p" style="font-weight:bold; color:#ffffff;">Risk Level: {risk_val} {risk_icon}</p>
                    </div>
                """)
                st.markdown(card_html, unsafe_allow_html=True)
                
                st.markdown("<h4 style='color: #a1a1aa; font-size: 15px; margin-top: 15px;'>📸 ภาพประกอบ (Before & After)</h4>", unsafe_allow_html=True)
                
                col_index_before = 8
                col_index_after = 9
                img_before_col = df.columns[col_index_before] if len(df.columns) > col_index_before else None 
                img_after_col = df.columns[col_index_after] if len(df.columns) > col_index_after else None  

                img_b_url = str(selected_case[img_before_col]).strip() if img_before_col and pd.notnull(selected_case[img_before_col]) else ""
                img_a_url = str(selected_case[img_after_col]).strip() if img_after_col and pd.notnull(selected_case[img_after_col]) else ""

                i_col1, i_col2 = st.columns(2)
                
                with i_col1:
                    if img_b_url.startswith('http'):
                        st.image(img_b_url, caption="🔴 ก่อนแก้ไข (Before)", use_container_width=True)
                    elif len(img_b_url) > 100:
                        try:
                            image_bytes = base64.b64decode(img_b_url)
                            st.image(image_bytes, caption="🔴 ก่อนแก้ไข (Before)", use_container_width=True)
                        except: st.error("ข้อมูลรูปรหัส Base64 ไม่สมบูรณ์")
                    else: st.image("https://cdn-icons-png.flaticon.com/512/1161/1161388.png", caption="ไม่มีภาพก่อนแก้ไข", use_container_width=True)

                with i_col2:
                    if img_a_url.startswith('http'):
                        st.image(img_a_url, caption="🟢 หลังแก้ไข (After)", use_container_width=True)
                    elif len(img_a_url) > 100:
                        try:
                            image_bytes = base64.b64decode(img_a_url)
                            st.image(image_bytes, caption="🟢 หลังแก้ไข (After)", use_container_width=True)
                        except: st.error("ข้อมูลรูปรหัส Base64 ไม่สมบูรณ์")
                    else: st.image("https://cdn-icons-png.flaticon.com/512/1161/1161388.png", caption="ไม่มีภาพหลังแก้ไข", use_container_width=True)
                
                st.markdown("---")
                
                timeline_html = textwrap.dedent(f"""
                    <div class="timeline-container">
                        <div class="timeline-header">
                            <span style="font-size: 14px; font-weight: bold; color: #ffffff;">Timeline & Activity</span>
                            <span style="color: #a1a1aa; font-size: 13px;">✏️ 🖨️ 📥</span>
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
                        <h3 style="color: #64748b; margin-bottom: 10px;">🔍</h3>
                        <p style="color: #8e8e93; font-size: 14px;">No case selected.<br>Please choose a case from the left panel.</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ ไม่มีข้อมูลเพื่อแสดงผลบนปฏิทิน")

# ==========================================
# MODULE 3: REPORT NEW CASE
# ==========================================
elif menu == "📝 Report New Case":
    st.title("📝 รายงานเคสความเสี่ยงใหม่")
    with st.form("risk_form", clear_on_submit=True):
        f_date = st.date_input("วันที่ (Date)")
        f_topic = st.text_input("หัวข้อประเด็นความเสี่ยง (Topic/risk finding)")
        f_loc = st.text_input("สถานที่ (Location)")
        f_resp = st.text_input("ผู้รับผิดชอบ (Responsible Person)")
        
        f_status = st.selectbox("สถานะ (Status)", ["รอดำเนินการ", "กำลังดำเนินการ", "ดำเนินการเรียบร้อย", "ไม่พบประเด็น"])
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
                else: st.error(f"❌ ไม่สามารถบันทึกได้ API รหัส: {res.status_code}")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดขณะส่งข้อมูล: {e}")
