# ==========================================
# 1. DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 สรุปภาพรวมความเสี่ยง")
    
    if not df.empty:
        try:
            # 1. ตรวจสอบชื่อคอลัมน์ (ปรับให้ตรงกับใน Sheet ของคุณ)
            # สมมติคอลัมน์แรกคือวันที่, คอลัมน์ที่ 2 คือ Topic, คอลัมน์ที่ 5 คือ Status, คอลัมน์ที่ 7 คือ Risk Level
            # ให้ใช้ชื่อที่ตรงกับ Header ใน Google Sheets จริงๆ
            status_col = 'Status' 
            risk_col = 'Risk Level'
            
            # คำนวณค่า Metric
            total_cases = len(df)
            completed_cases = len(df[df[status_col].astype(str).str.contains('เรียบร้อย|สำเร็จ', na=False)])
            high_risk = len(df[df[risk_col].astype(str) == 'High'])
            
            # แสดง Metric
            col1, col2, col3 = st.columns(3)
            col1.metric("📌 เคสทั้งหมด", total_cases)
            col2.metric("✅ ดำเนินการสำเร็จ", completed_cases)
            col3.metric("🚨 เคสความเสี่ยงสูง", high_risk)
            
            st.markdown("---")
            
            # 2. กราฟสรุปผล
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("สัดส่วนสถานะ")
                status_df = df[status_col].value_counts().reset_index()
                status_df.columns = ['Status', 'Count']
                fig_pie = px.pie(status_df, values='Count', names='Status', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with c2:
                st.subheader("ระดับความเสี่ยง")
                risk_df = df[risk_col].value_counts().reindex(['Low', 'Medium', 'High'], fill_value=0).reset_index()
                risk_df.columns = ['Risk', 'Count']
                fig_bar = px.bar(risk_df, x='Risk', y='Count', color='Risk',
                                 color_discrete_map={'High': '#ff4b4b', 'Medium': '#ffa500', 'Low': '#00cc96'})
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # 3. ตารางข้อมูล
            st.subheader("รายการล่าสุด")
            # แปลงเป็นสตริงทั้งหมดเพื่อป้องกันปัญหาการแสดงผลคอลัมน์ประเภทวันที่หรือ Object
            st.dataframe(df.head(10).astype(str), use_container_width=True)
            
        except KeyError as e:
            st.error(f"⚠️ ไม่พบชื่อคอลัมน์ในข้อมูล: {e}")
            st.write("ตรวจสอบว่าชื่อคอลัมน์ใน Google Sheets ตรงกับในโค้ด (เช่น 'Status', 'Risk Level')")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
    else:
        st.warning("⚠️ ยังไม่มีข้อมูลโหลดเข้ามาในระบบ")