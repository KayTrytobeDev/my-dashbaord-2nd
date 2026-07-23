import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
import plotly.express as px
import base64
import textwrap
import io
from PIL import Image
import re  # สำหรับดึงลิงก์จากสูตร IMAGE

# ==========================================
# 1. SET PAGE CONFIG & SYSTEM INITIALIZATION
# ==========================================
st.set_page_config(page_title="Safe Together System", page_icon="🛡️", layout="wide")

# 📌 นำลิงก์ Web App ของพี่มาวางตรงนี้ครับ
API_URL = "https://script.google.com/macros/s/AKfycby1dCW6VBBUQnx1fSi3OAsN5Tf7RGjTKaEDxmAxf8lyUK9B9DQcUUxM2ekWxP1vGjuM/exec"

# ==========================================
# 2. PREMIUM LIGHT MODE CSS
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        background-color: #f4f6f8 !important; /* สีพื้นหลังสว่าง */
        color: #111827 !important; /* สีตัวอักษรเข้ม */
    }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff !important; /* แถบด้านข้างสีขาว */
        border-right: 1px solid #e5e7eb;
    }

    div[data-testid="stButton"] > button {
        background-color: #ffffff !important; 
        color: #111827 !important; 
        border: 1px solid #d1d5db !important;
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
    
    div[data-baseweb="select"] > div, input, textarea {
        background-color: #ffffff !important;
        color: #111827 !important;
        border-color: #d1d5db !important;
    }
    label, div[data-testid="stWidgetLabel"] p { color: #374151 !important; font-weight: 500; }
    
    .dashboard-card {
        background: #ffffff; padding: 24px; border-radius: 12px;
        border: 1px solid #e5e7eb; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); margin-bottom: 24px;
    }
    .dashboard-card-title {
        font-size: 16px; font-weight: 600; color: #111827;
        margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
    }

    .kpi-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 25px; }
    .kpi-card {
        background: #ffffff; border-radius: 12px; padding: 20px; border-left: 5px solid #e5e7eb;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
    .kpi-label { font-size: 13px; font-weight: 600; color: #6b7280; text-transform: uppercase; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #111827; margin: 8px 0 4px 0; }
    .kpi-subtext { font-size: 12px; color: #9ca3af; }
    
    .kpi-total { border-left-color: #0a84ff; }
    .kpi-success { border-left-color: #30d158; }
    .kpi-pending { border-left-color: #ff9f0a; }
    .kpi-rate { border-left-color: #bf5af2; }

    .responsive-card {
        background-color: #ffffff; padding: 24px; border-radius: 12px; 
        border: 1px solid #e5e7eb; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); margin-bottom: 20px; color: #111827; word-wrap: break-word;
    }
    .card-header-box { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e5e7eb; padding-bottom: 14px; margin-bottom: 18px; }
    .card-title-text { font-size: 16px; font-weight: 700; color: #111827; }
    .card-date-text { color: #6b7280; font-size: 13px; font-weight: 600; }
    .case-p { margin: 10px 0; font-size: 14px; color: #374151; line-height: 1.6; }
    .case-p-highlight { color: #0a84ff; font-weight: 600; }
    
    .timeline-container { background-color: #f9fafb; border-radius: 12px; padding: 18px; border: 1px solid #e5e7eb; margin-top: 20px; }
    .timeline-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .timeline-row { border-left: 2px solid #d1d5db; padding-left: 18px; position: relative; margin-bottom: 12px; font-size: 13px; color: #4b5563; }
    .timeline-dot { position: absolute; left: -6px; top: 2px; color: #6b7280; font-size: 11px; }
    .empty-state-box { background-color: #ffffff; padding: 50px 20px; border-radius: 12px; text-align: center; border: 1px dashed #d1d5db; color: #111827; }

    @media (max-width: 768px) {
        .kpi-container { grid-template-columns: 1fr; }
        .stButton > button { padding: 4px 2px !important; font-size: 12px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS (ระบบจัดการรูปภาพ)
# ==========================================
def compress_image_to_b64(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        img = Image.open(uploaded_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=75) 
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception:
        return ""

def decode_base64_img(b64_str):
    try:
        if "," in b64_str: 
            b64_str = b64_str.split(",")[1]
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4) 
        return base64.b64decode(b64_str)
    except Exception:
        return None

def extract_and_convert_url(raw_text):
    if not raw_text or str(raw_text).lower() in ["nan", "-", "none", ""]:
        return ""
    
    url = str(raw_text).strip()
    match_img = re.search(r'IMAGE\("([^"]+)"\)', url, re.IGNORECASE)
    if match_img:
        url = match_img.group(1)
        
    if "drive.google.com/file/d/" in url or "drive.google.com/uc" in url:
        match_id = re.search(r'([-\w]{25,})', url)
        if match_id:
            file_id = match_id.group(1)
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
            
    return url

# ==========================================
# 4. DATA CORE
# ==========================================
@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(API_URL, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                df.columns = df.columns.str.strip()
                date_col = df.columns[0]
                df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
                return df
            else:
                st.warning("⚠️ ยังไม่มีข้อมูลในตาราง")
        else:
            st.error(f"❌ ไม่สามารถเชื่อมต่อกับ Google Sheets ได้ (Status: {response.status_code})")
        return pd.DataFrame()
    except Exception as e: 
        st.error(f"❌ โหลดข้อมูลล้มเหลว: {e}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# 5. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🛡️FMS ROUND🛡️")
menu = st.sidebar.radio("เมนูใช้งาน:", ["📊 Dashboard", "📅 Calendar & Case Detail", "📝 Report New Case"])

# ==========================================
# MODULE 1: DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.markdown("<h2 style='color: #111827; font-weight: 700; margin-bottom: 20px;'>📊 Overview & Risk Analytics</h2>", unsafe_allow_html=True)
    
    if not df.empty:
        try:
            date_col = df.columns[0]
            cols = df.columns.tolist()
            status_col = 'Status' if 'Status' in cols else (cols[4] if len(cols) > 4 else cols[-1])
            risk_col = 'Risk Level' if 'Risk Level' in cols else (cols[10] if len(cols) > 10 else cols[-1])
            
            total_cases = len(df)
            completed_cases = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ|Complete|ไม่พบประเด็น', na=False, case=False)])
            pending_cases = len(df[df[status_col].astype(str).str.contains('รอดำเนินการ|กำลังดำเนินการ|Pending|In Progress', na=False, case=False)])
            success_rate = (completed_cases / total_cases * 100) if total_cases > 0 else 0
            
            st.markdown(f"""
                <div class="kpi-container">
                    <div class="kpi-card kpi-total"><div class="kpi-label">เคสทั้งหมด</div><div class="kpi-value">{total_cases}</div><div class="kpi-subtext">🔄 บันทึกสะสม</div></div>
                    <div class="kpi-card kpi-success"><div class="kpi-label">ปิดงานแล้ว</div><div class="kpi-value">{completed_cases}</div><div class="kpi-subtext">🟢 สำเร็จ</div></div>
                    <div class="kpi-card kpi-pending"><div class="kpi-label">คงค้าง</div><div class="kpi-value">{pending_cases}</div><div class="kpi-subtext">⏳ กำลังดำเนินการ</div></div>
                    <div class="kpi-card kpi-rate"><div class="kpi-label">อัตราสำเร็จ</div><div class="kpi-value">{success_rate:.1f}%</div><div class="kpi-subtext">📈 ภาพรวม</div></div>
                </div>
            """, unsafe_allow_html=True)
            
            status_colors = {
                'ดำเนินการเรียบร้อย': '#30d158', 'เรียบร้อย': '#30d158', 'Complete': '#30d158',
                'กำลังดำเนินการ': '#ff9f0a', 'In Progress': '#ff9f0a',
                'รอดำเนินการ': '#ff453a', 'Pending': '#ff453a',
                'ไม่พบประเด็น': '#8e8e93', 'No Issue': '#8e8e93'
            }

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown('<div class="dashboard-card"><div class="dashboard-card-title" style="justify-content: center; font-size: 22px; width: 100%; gap: 12px;">💡 สัดส่วนสถานะงาน</div>', unsafe_allow_html=True)
                status_counts = df[status_col].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                fig_pie = px.pie(status_counts, values='Count', names='Status', hole=0.55, color='Status', color_discrete_map=status_colors)
                fig_pie.update_layout(template='plotly_white', showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with g_col2:
                st.markdown('<div class="dashboard-card"><div class="dashboard-card-title" style="justify-content: center; font-size: 22px; width: 100%; gap: 12px;">⚡ ความเสี่ยงภาพรวม</div>', unsafe_allow_html=True)
                risk_counts = df[risk_col].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
                risk_counts.columns = ['Risk', 'Count']
                fig_bar = px.bar(risk_counts, x='Risk', y='Count', color='Risk', text='Count', color_discrete_map={'High': '#ff453a', 'Medium': '#ffb703', 'Low': '#30d158'})
                fig_bar.update_traces(textposition='outside', textfont=dict(color='#111827', size=14))
                fig_bar.update_layout(template='plotly_white', showlegend=False, xaxis_title="", yaxis_title="เคส", margin=dict(t=10, b=10, l=10, r=10), height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig_bar.update_yaxes(gridcolor='#e5e7eb')
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            # --- กล่องสรุปเจาะลึกความเสี่ยง ---
            st.markdown('<div class="dashboard-card"><div class="dashboard-card-title" style="justify-content: center; font-size: 22px; width: 100%; gap: 12px;">📊 เจาะลึกสถานะตามระดับความเสี่ยง</div>', unsafe_allow_html=True)
            risk_counts = df[risk_col].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
            
            total_high = len(df[df[risk_col].astype(str).str.strip().str.title() == 'High'])
            total_medium = len(df[df[risk_col].astype(str).str.strip().str.title() == 'Medium'])
            total_low = len(df[df[risk_col].astype(str).str.strip().str.title() == 'Low'])
            
            st.markdown(f"""
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px;">
                    <div style="background: #ffffff; border: 1px solid #e5e7eb; border-top: 4px solid #ff453a; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
                        <div style="color: #6b7280; font-weight: 600;">🚨 High</div>
                        <div style="font-size: 36px; font-weight: 700; color: #111827;">{total_high}</div>
                    </div>
                    <div style="background: #ffffff; border: 1px solid #e5e7eb; border-top: 4px solid #ffb703; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
                        <div style="color: #6b7280; font-weight: 600;">⚠️ Medium</div>
                        <div style="font-size: 36px; font-weight: 700; color: #111827;">{total_medium}</div>
                    </div>
                    <div style="background: #ffffff; border: 1px solid #e5e7eb; border-top: 4px solid #30d158; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
                        <div style="color: #6b7280; font-weight: 600;">✅ Low</div>
                        <div style="font-size: 36px; font-weight: 700; color: #111827;">{total_low}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            selected_risk = st.radio("🎯 เลือกระดับความเสี่ยง:", ["High", "Medium", "Low"], horizontal=True)
            df_filtered_risk = df[df[risk_col].astype(str).str.strip().str.title() == selected_risk.title()]
            
            r_pending = len(df_filtered_risk[df_filtered_risk[status_col].astype(str).str.contains('รอดำเนินการ|Pending', na=False, case=False)])
            r_progress = len(df_filtered_risk[df_filtered_risk[status_col].astype(str).str.contains('กำลังดำเนินการ|In Progress', na=False, case=False)])
            r_completed = len(df_filtered_risk[df_filtered_risk[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ|Complete', na=False, case=False)])
            r_no_issue = len(df_filtered_risk[df_filtered_risk[status_col].astype(str).str.contains('ไม่พบประเด็น|No Issue', na=False, case=False)])
            
            st.markdown(f"""
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-top: 15px;">
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="color: #4b5563; margin-bottom: 8px; font-weight: 600;">📥 รอดำเนินการ</div><div style="font-size: 32px; font-weight: 700; color: #ff453a;">{r_pending}</div>
                    </div>
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="color: #4b5563; margin-bottom: 8px; font-weight: 600;">🛠️ กำลังดำเนินการ</div><div style="font-size: 32px; font-weight: 700; color: #ff9f0a;">{r_progress}</div>
                    </div>
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="color: #4b5563; margin-bottom: 8px; font-weight: 600;">🟢 เรียบร้อย</div><div style="font-size: 32px; font-weight: 700; color: #30d158;">{r_completed}</div>
                    </div>
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="color: #4b5563; margin-bottom: 8px; font-weight: 600;">⚪ ไม่พบประเด็น</div><div style="font-size: 32px; font-weight: 700; color: #8e8e93;">{r_no_issue}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="dashboard-card"><div class="dashboard-card-title">📋 ข้อมูลล่าสุด</div>', unsafe_allow_html=True)
            df_table = df.copy()
            df_table[date_col] = df_table[date_col].dt.strftime('%d/%m/%Y').fillna('-')
            st.dataframe(df_table.astype(str), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e: st.error(f"❌ Error Dashboard: {e}")

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
        view_mode = st.radio("มุมมอง:", ["📅 ตารางปฏิทิน", "📱 รายการเคสประจำเดือน"], horizontal=True)
        st.markdown("---")

        monthly_data = df[(df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))]
        _, num_days = calendar.monthrange(year, month)
        if 'sel_day' not in st.session_state or st.session_state.sel_day > num_days:
            st.session_state.sel_day = 1

        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            if "ตาราง" in view_mode:
                cal = calendar.Calendar(firstweekday=6)
                month_days = cal.monthdayscalendar(year, month)
                
                header = st.columns(7)
                for i, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
                    header[i].markdown(f"<p style='text-align:center; font-weight:bold; color:#6b7280; margin-bottom:5px;'>{name}</p>", unsafe_allow_html=True)
                
                for week in month_days:
                    cols_grid = st.columns(7)
                    for i, day in enumerate(week):
                        if day != 0:
                            is_match = (df[date_col].dt.day == day) & (df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))
                            btn_type = "primary" if (day == st.session_state.sel_day) else "secondary"
                            
                            if cols_grid[i].button(f"{day}", key=f"d_{day}", type=btn_type, use_container_width=True):
                                st.session_state.sel_day = day
                                st.session_state.pop('selected_case_idx', None) 
                                st.rerun()
                            
                            if not df[is_match].empty and day != st.session_state.sel_day:
                                cols_grid[i].markdown("<p style='text-align:center; margin-top:-22px; margin-bottom:0px; color:#30d158; font-size:18px;'>•</p>", unsafe_allow_html=True)
                        else: cols_grid[i].write("")

                st.markdown("---")
                daily_cases = df[(df[date_col].dt.day == st.session_state.sel_day) & (df[date_col].dt.month == month) & ((df[date_col].dt.year == year) | (df[date_col].dt.year == sheet_year))]
                if not daily_cases.empty:
                    opts = {f"📌 [วันที่ {row[date_col].day}] - {row[topic_col]}": idx for idx, row in daily_cases.iterrows()}
                    sel = st.selectbox("เคสในวันนี้:", list(opts.keys()))
                    st.session_state.selected_case_idx = opts[sel]
                else:
                    st.info("ไม่มีเคสในวันนี้")
                    st.session_state.selected_case_idx = None
            else:
                if not monthly_data.empty:
                    opts = {f"📅 วันที่ {row[date_col].day} | {row[topic_col][:25]}...": idx for idx, row in monthly_data.sort_values(by=date_col).iterrows()}
                    sel = st.radio("เลือกเคส:", list(opts.keys()))
                    st.session_state.selected_case_idx = opts[sel]
                    st.session_state.sel_day = df.loc[opts[sel]][date_col].day
                else: st.success("เดือนนี้ไม่มีเคส")

        with col_right:
            st.subheader("🔍 Case Detail")
            idx = st.session_state.get('selected_case_idx')
            selected_case = df.loc[idx] if idx is not None and idx in df.index else (daily_cases.iloc[0] if "ตาราง" in view_mode and not daily_cases.empty else (monthly_data.iloc[0] if "รายการ" in view_mode and not monthly_data.empty else None))

            if selected_case is not None:
                display_color = "#374151"
                status_txt = str(selected_case[status_col])
                if "เรียบร้อย" in status_txt or "Complete" in status_txt: display_color = "#30d158" 
                elif "รอดำเนินการ" in status_txt or "Pending" in status_txt: display_color = "#ff453a" 
                elif "กำลังดำเนินการ" in status_txt or "In Progress" in status_txt: display_color = "#ff9f0a" 

                st.markdown(textwrap.dedent(f"""
                    <div class="responsive-card">
                        <div class="card-header-box">
                            <span class="card-title-text">ID: RT{selected_case[date_col].strftime('%Y-%m%d')}</span>
                            <span class="card-date-text">{selected_case[date_col].strftime('%b %d')}</span>
                        </div>
                        <p class="case-p"><strong>Topic:</strong> <span class="case-p-highlight">{selected_case[topic_col]}</span></p>
                        <hr style="border:0; border-top:1px solid #e5e7eb; margin:12px 0;">
                        <p class="case-p">📍 <strong>Location:</strong> {selected_case[loc_col]}</p>
                        <p class="case-p">👤 <strong>Responsible:</strong> {selected_case[resp_col]}</p>
                        <p class="case-p">🔄 <strong>Status:</strong> <span style="color: {display_color}; font-weight: bold;">{status_txt}</span></p>
                        <p class="case-p">🛠 <strong>Action:</strong> {selected_case[action_col]}</p>
                        <hr style="border:0; border-top:1px solid #e5e7eb; margin:12px 0;">
                        <p class="case-p" style="font-weight:bold; color:#111827;">Risk Level: {str(selected_case[risk_col]).title()}</p>
                    </div>
                """), unsafe_allow_html=True)
                
                # --- 📌 แสดงรูปภาพไซส์ใหญ่พิเศษ (คลิกขยายได้) ---
                st.markdown("<h4 style='color:#4b5563; font-size:16px; margin-top:20px; border-bottom:1px solid #e5e7eb; padding-bottom:10px;'>📸 ภาพประกอบ (คลิกเพื่อขยายเต็มจอ)</h4>", unsafe_allow_html=True)
                
                img_before_col = next((c for c in cols if 'before' in c.lower() or 'ก่อน' in c), cols[8] if len(cols) > 8 else None)
                img_after_col = next((c for c in cols if 'after' in c.lower() or 'หลัง' in c), cols[9] if len(cols) > 9 else None)

                img_b_raw = selected_case[img_before_col]
                img_a_raw = selected_case[img_after_col]

                # ส่งให้ฟังก์ชันดึง URL อัตโนมัติ (ไม่ว่าจะเป็นลิงก์ Drive หรือสูตร IMAGE)
                img_b_url = extract_and_convert_url(img_b_raw)
                img_a_url = extract_and_convert_url(img_a_raw)

                # ปรับความกว้างรูปล็อกตายตัว เพื่อความคมชัดใหญ่สะใจ
                IMAGE_WIDTH = 450

                i_col1, i_col2 = st.columns(2)
                
                with i_col1:
                    st.markdown("<div style='color: #ff453a; font-weight: bold; margin-bottom: 8px;'>🔴 ก่อนแก้ไข</div>", unsafe_allow_html=True)
                    if img_b_url.startswith('http'): 
                        st.image(img_b_url, width=IMAGE_WIDTH)
                    elif len(img_b_url) > 50:
                        img_data = decode_base64_img(img_b_url)
                        if img_data: st.image(img_data, width=IMAGE_WIDTH)
                        else: st.error("ไม่สามารถถอดรหัสภาพได้")
                    else: 
                        st.image("https://cdn-icons-png.flaticon.com/512/1161/1161388.png", width=150)

                with i_col2:
                    st.markdown("<div style='color: #30d158; font-weight: bold; margin-bottom: 8px;'>🟢 หลังแก้ไข</div>", unsafe_allow_html=True)
                    if img_a_url.startswith('http'): 
                        st.image(img_a_url, width=IMAGE_WIDTH)
                    elif len(img_a_url) > 50:
                        img_data = decode_base64_img(img_a_url)
                        if img_data: st.image(img_data, width=IMAGE_WIDTH)
                        else: st.error("ไม่สามารถถอดรหัสภาพได้")
                    else: 
                        st.image("https://cdn-icons-png.flaticon.com/512/1161/1161388.png", width=150)

# ==========================================
# MODULE 3: REPORT NEW CASE
# ==========================================
elif menu == "📝 Report New Case":
    st.title("📝 รายงานเคสใหม่")
    with st.form("risk_form", clear_on_submit=True):
        f_date = st.date_input("วันที่ (Date)")
        f_topic = st.text_input("หัวข้อประเด็น (Topic)")
        f_loc = st.text_input("สถานที่ (Location)")
        f_resp = st.text_input("ผู้รับผิดชอบ (Responsible)")
        f_status = st.selectbox("สถานะ (Status)", ["รอดำเนินการ", "กำลังดำเนินการ", "ดำเนินการเรียบร้อย", "ไม่พบประเด็น"])
        f_action = st.text_area("แนวทางแก้ไข (Action)")
        f_risk = st.selectbox("ระดับความเสี่ยง (Risk Level)", ["Low", "Medium", "High"])
        
        up_before = st.file_uploader("รูปก่อนแก้ไข", type=['png', 'jpg', 'jpeg'])
        up_after = st.file_uploader("รูปหลังแก้ไข", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            try:
                b64_b = compress_image_to_b64(up_before)
                b64_a = compress_image_to_b64(up_after)
                
                payload = {
                    "date": str(f_date), "topic": f_topic, "location": f_loc, "responsible": f_resp, 
                    "status": f_status, "action": f_action, "risk": f_risk,
                    "imgBeforeBase64": b64_b, "imgBeforeName": up_before.name if up_before else "",
                    "imgAfterBase64": b64_a, "imgAfterName": up_after.name if up_after else ""
                }
                res = requests.post(API_URL, json=payload, timeout=20)
                if res.status_code == 200: 
                    st.success("🎉 บันทึกสำเร็จ!")
                    st.cache_data.clear() 
                else: st.error("❌ บันทึกล้มเหลว")
            except Exception as e: st.error(f"❌ Error: {e}")
