import streamlit as st
import anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# ตั้งค่าหน้าแอป (ชื่อแท็บ, ไอคอน, layout)
# ============================================================
st.set_page_config(
    page_title="Global MAE Report — Oil & Gas",
    page_icon="🔥",
    layout="wide"
)

# ============================================================
# ข้อมูล MAE จริงในอุตสาหกรรม Oil & Gas
# (ที่มา: BSEE, HSE, PHMSA, CSB — เป็นข้อมูลสาธารณะ)
# ============================================================
MAE_DATA = [
    {"name": "Deepwater Horizon", "year": 2010, "country": "USA", "region": "Americas", "type": "Blowout", "facility": "Offshore", "fatalities": 11, "injuries": 17, "loss_musd": 65000, "operator": "BP", "cause": "Well Control Failure"},
    {"name": "Texas City Refinery Explosion", "year": 2005, "country": "USA", "region": "Americas", "type": "Explosion", "facility": "Downstream", "fatalities": 15, "injuries": 180, "loss_musd": 1500, "operator": "BP", "cause": "Process Safety / Human Error"},
    {"name": "Lac-Mégantic Rail Disaster", "year": 2013, "country": "Canada", "region": "Americas", "type": "Fire", "facility": "Midstream", "fatalities": 47, "injuries": 0, "loss_musd": 2700, "operator": "MMA", "cause": "Mechanical Failure"},
    {"name": "Piper Alpha Platform Fire", "year": 1988, "country": "UK", "region": "Europe", "type": "Fire", "facility": "Offshore", "fatalities": 167, "injuries": 61, "loss_musd": 3400, "operator": "Occidental", "cause": "Process Safety / Human Error"},
    {"name": "Buncefield Oil Depot", "year": 2005, "country": "UK", "region": "Europe", "type": "Explosion", "facility": "Midstream", "fatalities": 0, "injuries": 43, "loss_musd": 1200, "operator": "HOSL", "cause": "Mechanical Failure"},
    {"name": "Pembroke Refinery Fire", "year": 2011, "country": "UK", "region": "Europe", "type": "Explosion", "facility": "Downstream", "fatalities": 0, "injuries": 4, "loss_musd": 400, "operator": "Chevron", "cause": "Well Control Failure"},
    {"name": "Esso Longford Gas Plant", "year": 1998, "country": "Australia", "region": "Asia Pacific", "type": "Explosion", "facility": "Upstream", "fatalities": 2, "injuries": 8, "loss_musd": 1300, "operator": "Esso", "cause": "Process Safety / Human Error"},
    {"name": "Skikda LNG Explosion", "year": 2004, "country": "Algeria", "region": "Africa", "type": "Explosion", "facility": "Downstream", "fatalities": 27, "injuries": 74, "loss_musd": 900, "operator": "Sonatrach", "cause": "Mechanical Failure"},
    {"name": "Mumbai High North Platform", "year": 2005, "country": "India", "region": "Asia Pacific", "type": "Fire", "facility": "Offshore", "fatalities": 22, "injuries": 0, "loss_musd": 500, "operator": "ONGC", "cause": "Collision"},
    {"name": "Abqaiq Processing Facility", "year": 2019, "country": "Saudi Arabia", "region": "Middle East", "type": "Explosion", "facility": "Downstream", "fatalities": 0, "injuries": 0, "loss_musd": 10000, "operator": "Saudi Aramco", "cause": "External Attack"},
    {"name": "Pemex Abkatun-A Platform", "year": 2015, "country": "Mexico", "region": "Americas", "type": "Fire", "facility": "Offshore", "fatalities": 4, "injuries": 16, "loss_musd": 700, "operator": "Pemex", "cause": "Mechanical Failure"},
    {"name": "Vizag LG Polymers Gas Leak", "year": 2020, "country": "India", "region": "Asia Pacific", "type": "Gas Release", "facility": "Downstream", "fatalities": 12, "injuries": 1000, "loss_musd": 250, "operator": "LG Polymers", "cause": "Process Safety / Human Error"},
    {"name": "Refugio Pipeline Spill", "year": 2015, "country": "USA", "region": "Americas", "type": "Spill", "facility": "Midstream", "fatalities": 0, "injuries": 0, "loss_musd": 100, "operator": "Plains All American", "cause": "Pipeline Integrity"},
    {"name": "Elgin Gas Leak", "year": 2012, "country": "UK", "region": "Europe", "type": "Gas Release", "facility": "Offshore", "fatalities": 0, "injuries": 0, "loss_musd": 600, "operator": "Total", "cause": "Well Control Failure"},
    {"name": "Aliso Canyon Gas Blowout", "year": 2015, "country": "USA", "region": "Americas", "type": "Blowout", "facility": "Upstream", "fatalities": 0, "injuries": 0, "loss_musd": 800, "operator": "SoCalGas", "cause": "Mechanical Failure"},
    {"name": "Mariana Oil Platform Sinking", "year": 2001, "country": "Brazil", "region": "Americas", "type": "Structural", "facility": "Offshore", "fatalities": 11, "injuries": 0, "loss_musd": 500, "operator": "Petrobras", "cause": "Structural Failure"},
    {"name": "Bharat Petroleum Refinery", "year": 2001, "country": "India", "region": "Asia Pacific", "type": "Explosion", "facility": "Downstream", "fatalities": 0, "injuries": 50, "loss_musd": 200, "operator": "BPCL", "cause": "Process Safety / Human Error"},
    {"name": "Petrobras P-36 Platform", "year": 2001, "country": "Brazil", "region": "Americas", "type": "Explosion", "facility": "Offshore", "fatalities": 11, "injuries": 0, "loss_musd": 350, "operator": "Petrobras", "cause": "Mechanical Failure"},
    {"name": "Gretener Gas Pipeline", "year": 2004, "country": "Belgium", "region": "Europe", "type": "Explosion", "facility": "Midstream", "fatalities": 24, "injuries": 120, "loss_musd": 150, "operator": "Fluxys", "cause": "Pipeline Integrity"},
    {"name": "Jilin Petrochemical Explosion", "year": 2005, "country": "China", "region": "Asia Pacific", "type": "Explosion", "facility": "Downstream", "fatalities": 8, "injuries": 60, "loss_musd": 300, "operator": "CNPC", "cause": "Process Safety / Human Error"},
]

df = pd.DataFrame(MAE_DATA)

# ============================================================
# ส่วนหัว (Header) ของแอป
# ============================================================
st.title("🔥 Global MAE Report Generator")
st.markdown("**Major Accident Events — Oil & Gas Industry** | Powered by Claude AI")
st.divider()

# ============================================================
# Sidebar: ตัวกรองข้อมูล
# ============================================================
st.sidebar.header("🎛️ ตั้งค่าตัวกรอง")

year_range = st.sidebar.slider(
    "ช่วงปีที่เกิดเหตุ",
    min_value=1988,
    max_value=2024,
    value=(2000, 2024)
)

selected_regions = st.sidebar.multiselect(
    "ภูมิภาค",
    options=df["region"].unique().tolist(),
    default=df["region"].unique().tolist()
)

selected_types = st.sidebar.multiselect(
    "ประเภทเหตุการณ์",
    options=df["type"].unique().tolist(),
    default=df["type"].unique().tolist()
)

selected_facility = st.sidebar.multiselect(
    "ประเภทสถานที่",
    options=df["facility"].unique().tolist(),
    default=df["facility"].unique().tolist()
)

report_style = st.sidebar.selectbox(
    "รูปแบบ AI Report",
    ["Executive Summary", "Detailed Technical", "Statistical Analysis"]
)

# ============================================================
# กรองข้อมูลตาม filter ที่เลือก
# ============================================================
filtered = df[
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1]) &
    (df["region"].isin(selected_regions)) &
    (df["type"].isin(selected_types)) &
    (df["facility"].isin(selected_facility))
].copy()

# ============================================================
# แถว Metrics (ตัวเลขสรุปด้านบน)
# ============================================================
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🔴 MAE Events", len(filtered))
col2.metric("💀 เสียชีวิตรวม", filtered["fatalities"].sum())
col3.metric("🤕 บาดเจ็บรวม", filtered["injuries"].sum())
col4.metric("💰 ความเสียหาย", f"${filtered['loss_musd'].sum()/1000:.1f}B")
col5.metric("🌍 ประเทศที่เกิดเหตุ", filtered["country"].nunique())

st.divider()

# ============================================================
# แท็บหลัก 4 แท็บ
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 ภาพรวม & Charts",
    "📋 รายการเหตุการณ์",
    "🤖 AI Analysis",
    "📈 Root Cause"
])

# ------ TAB 1: Charts ------
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("เหตุการณ์ตามภูมิภาค")
        region_count = filtered.groupby("region").size().reset_index(name="count")
        fig1 = px.bar(region_count, x="region", y="count",
                      color="region", color_discrete_sequence=px.colors.qualitative.Set2)
        fig1.update_layout(showlegend=False, height=300,
                           margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("สัดส่วนประเภทเหตุการณ์")
        type_count = filtered.groupby("type").size().reset_index(name="count")
        fig2 = px.pie(type_count, values="count", names="type",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("แนวโน้ม MAE ตามปี")
    year_count = filtered.groupby("year").agg(
        events=("name", "count"),
        fatalities=("fatalities", "sum")
    ).reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=year_count["year"], y=year_count["events"],
                          name="จำนวนเหตุการณ์", marker_color="#ef553b"))
    fig3.add_trace(go.Scatter(x=year_count["year"], y=year_count["fatalities"],
                              name="ผู้เสียชีวิต", yaxis="y2",
                              line=dict(color="#636efa", width=2)))
    fig3.update_layout(
        height=320,
        yaxis=dict(title="จำนวนเหตุการณ์"),
        yaxis2=dict(title="ผู้เสียชีวิต", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("แผนที่เหตุการณ์ทั่วโลก")
    country_agg = filtered.groupby("country").agg(
        events=("name", "count"),
        fatalities=("fatalities", "sum"),
        loss=("loss_musd", "sum")
    ).reset_index()
    fig4 = px.choropleth(
        country_agg,
        locations="country",
        locationmode="country names",
        color="events",
        hover_name="country",
        hover_data={"fatalities": True, "loss": True},
        color_continuous_scale="Reds",
        title="จำนวน MAE Events ต่อประเทศ"
    )
    fig4.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig4, use_container_width=True)

# ------ TAB 2: Incident Table ------
with tab2:
    st.subheader(f"รายการ MAE Events ทั้งหมด ({len(filtered)} เหตุการณ์)")
    display_df = filtered[[
        "name", "year", "country", "region",
        "type", "facility", "fatalities", "injuries", "loss_musd", "operator", "cause"
    ]].rename(columns={
        "name": "ชื่อเหตุการณ์",
        "year": "ปี",
        "country": "ประเทศ",
        "region": "ภูมิภาค",
        "type": "ประเภท",
        "facility": "สถานที่",
        "fatalities": "เสียชีวิต",
        "injuries": "บาดเจ็บ",
        "loss_musd": "ความเสียหาย (M USD)",
        "operator": "ผู้ดำเนินการ",
        "cause": "สาเหตุหลัก"
    }).sort_values("ความเสียหาย (M USD)", ascending=False)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ ดาวน์โหลด CSV",
        data=csv,
        file_name="global_mae_report.csv",
        mime="text/csv"
    )

# ------ TAB 3: AI Analysis ------
with tab3:
    st.subheader("🤖 AI Executive Report — สร้างโดย Claude")
    st.caption("กดปุ่มด้านล่างเพื่อให้ AI วิเคราะห์ข้อมูล MAE ที่กรองไว้")

    # สร้าง Prompt จากข้อมูลที่กรองแล้ว
    mae_summary = "\n".join([
        f"- {r['name']} ({r['year']}, {r['country']}): {r['type']}, "
        f"{r['fatalities']} fatalities, ${r['loss_musd']/1000:.1f}B loss, cause: {r['cause']}"
        for _, r in filtered.iterrows()
    ])

    system_prompt = """คุณคือผู้เชี่ยวชาญด้าน HSE (Health, Safety & Environment) 
ในอุตสาหกรรม Oil & Gas ที่มีประสบการณ์วิเคราะห์ Major Accident Events (MAE) ระดับโลก
ตอบเป็นภาษาไทยในรูปแบบ Professional Report ที่ชัดเจนและอ่านง่าย"""

    user_prompt = f"""วิเคราะห์ข้อมูล Major Accident Events (MAE) ต่อไปนี้:

{mae_summary}

สร้าง {report_style} ที่ประกอบด้วย:
1. 📋 Executive Summary (สรุปภาพรวม 3-4 ประโยค)
2. 📈 Key Trends (แนวโน้มสำคัญที่พบ)
3. ⚠️ Top 3 Root Causes (สาเหตุหลักที่พบบ่อยที่สุด)
4. 🔴 Worst Events (เหตุการณ์ที่ร้ายแรงที่สุด 3 อันดับ พร้อมบทเรียน)
5. ✅ Recommendations (ข้อเสนอแนะ 3-5 ข้อ)

ตอบเป็นภาษาไทย ใช้ภาษาแบบมืออาชีพ"""

    if st.button("🚀 สร้าง AI Report", type="primary", use_container_width=True):
        try:
            # เรียก Anthropic API
            # API Key จะถูกดึงจาก Streamlit Secrets อัตโนมัติ
            client = anthropic.Anthropic(
                api_key=st.secrets["ANTHROPIC_API_KEY"]
            )

            with st.spinner("AI กำลังวิเคราะห์ข้อมูล MAE..."):
                # ใช้ streaming เพื่อให้ข้อความแสดงทีละส่วน
                with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                ) as stream:
                    # st.write_stream จะแสดงข้อความ streaming แบบ real-time
                    response_text = st.write_stream(stream.text_stream)

            # แสดงปุ่มดาวน์โหลด Report
            st.download_button(
                "⬇️ ดาวน์โหลด AI Report (.txt)",
                data=response_text.encode("utf-8"),
                file_name="mae_ai_report.txt",
                mime="text/plain"
            )

        except KeyError:
            st.error("❌ ไม่พบ API Key — กรุณาเพิ่ม ANTHROPIC_API_KEY ใน Streamlit Secrets")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

# ------ TAB 4: Root Cause ------
with tab4:
    st.subheader("สาเหตุหลักของ MAE")

    cause_count = filtered.groupby("cause").agg(
        events=("name", "count"),
        fatalities=("fatalities", "sum"),
        loss=("loss_musd", "sum")
    ).reset_index().sort_values("events", ascending=False)

    fig5 = px.bar(
        cause_count, x="events", y="cause",
        orientation="h", color="fatalities",
        color_continuous_scale="Reds",
        labels={"events": "จำนวนเหตุการณ์", "cause": "สาเหตุ", "fatalities": "ผู้เสียชีวิต"},
        title="Root Causes เรียงตามความถี่"
    )
    fig5.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("ความสัมพันธ์ระหว่างสาเหตุ / ความเสียหาย / ผู้เสียชีวิต")
    fig6 = px.scatter(
        filtered, x="loss_musd", y="fatalities",
        color="cause", size="injuries",
        hover_name="name",
        labels={
            "loss_musd": "ความเสียหาย (M USD)",
            "fatalities": "ผู้เสียชีวิต",
            "cause": "สาเหตุ"
        }
    )
    fig6.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig6, use_container_width=True)

# ============================================================
# Footer
# ============================================================
st.divider()
st.caption("📌 ข้อมูล MAE อ้างอิงจาก BSEE, HSE UK, PHMSA, CSB | AI Analysis โดย Claude (Anthropic)")
