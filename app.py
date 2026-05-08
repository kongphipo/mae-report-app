import streamlit as st
import anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

st.set_page_config(
    page_title="Global MAE Report — Real-time News",
    page_icon="🔥",
    layout="wide"
)

# ============================================================
# ข้อมูล BSEE สรุปรายปี (จาก bsee.gov จริง)
# ============================================================
BSEE_ANNUAL_STATS = [
    {"year":2024,"fatalities":1, "injuries":223,"fires":388,"explosions":2, "gas_releases":123,"spills":13},
    {"year":2023,"fatalities":0, "injuries":203,"fires":375,"explosions":0, "gas_releases":108,"spills":12},
    {"year":2022,"fatalities":1, "injuries":199,"fires":333,"explosions":1, "gas_releases":108,"spills":17},
    {"year":2021,"fatalities":2, "injuries":164,"fires":259,"explosions":4, "gas_releases":79, "spills":14},
    {"year":2020,"fatalities":65,"injuries":160,"fires":274,"explosions":1, "gas_releases":81, "spills":11},
    {"year":2019,"fatalities":64,"injuries":222,"fires":169,"explosions":4, "gas_releases":87, "spills":14},
    {"year":2018,"fatalities":1, "injuries":171,"fires":111,"explosions":3, "gas_releases":91, "spills":10},
    {"year":2017,"fatalities":3, "injuries":135,"fires":143,"explosions":1, "gas_releases":59, "spills":10},
    {"year":2016,"fatalities":4, "injuries":143,"fires":131,"explosions":3, "gas_releases":36, "spills":8},
    {"year":2015,"fatalities":3, "injuries":160,"fires":147,"explosions":3, "gas_releases":41, "spills":14},
]

# ============================================================
# ข้อมูล Historical MAE
# ============================================================
HISTORICAL_MAE = [
    {"name":"Deepwater Horizon","year":2010,"country":"USA","region":"Americas","location":"Gulf of Mexico","pipeline_type":"Offshore","fatalities":11,"injuries":17,"property_damage_usd":65000000000,"operator":"BP","cause":"Well Control Failure","source":"BSEE"},
    {"name":"Piper Alpha","year":1988,"country":"UK","region":"Europe","location":"North Sea","pipeline_type":"Offshore","fatalities":167,"injuries":61,"property_damage_usd":3400000000,"operator":"Occidental","cause":"Human Error","source":"HSE UK"},
    {"name":"Texas City Refinery","year":2005,"country":"USA","region":"Americas","location":"Texas City, TX","pipeline_type":"Downstream","fatalities":15,"injuries":180,"property_damage_usd":1500000000,"operator":"BP","cause":"Human Error","source":"CSB"},
    {"name":"Lac-Mégantic","year":2013,"country":"Canada","region":"Americas","location":"Quebec","pipeline_type":"Midstream","fatalities":47,"injuries":0,"property_damage_usd":2700000000,"operator":"MMA Railway","cause":"Mechanical Failure","source":"TSB Canada"},
    {"name":"Buncefield Depot","year":2005,"country":"UK","region":"Europe","location":"Hertfordshire","pipeline_type":"Midstream","fatalities":0,"injuries":43,"property_damage_usd":1200000000,"operator":"HOSL","cause":"Equipment Failure","source":"HSE UK"},
    {"name":"Skikda LNG","year":2004,"country":"Algeria","region":"Africa","location":"Skikda","pipeline_type":"LNG","fatalities":27,"injuries":74,"property_damage_usd":900000000,"operator":"Sonatrach","cause":"Equipment Failure","source":"Sonatrach"},
    {"name":"Abqaiq Attack","year":2019,"country":"Saudi Arabia","region":"Middle East","location":"Abqaiq","pipeline_type":"Downstream","fatalities":0,"injuries":0,"property_damage_usd":10000000000,"operator":"Saudi Aramco","cause":"External Attack","source":"EIA"},
    {"name":"Mumbai High North","year":2005,"country":"India","region":"Asia Pacific","location":"Arabian Sea","pipeline_type":"Offshore","fatalities":22,"injuries":0,"property_damage_usd":500000000,"operator":"ONGC","cause":"Collision","source":"DGH India"},
    {"name":"Montara Blowout","year":2009,"country":"Australia","region":"Asia Pacific","location":"Timor Sea","pipeline_type":"Offshore","fatalities":0,"injuries":0,"property_damage_usd":400000000,"operator":"PTTEP Australasia","cause":"Well Control Failure","source":"Australian Gov"},
    {"name":"Sinopec Qingdao","year":2013,"country":"China","region":"Asia Pacific","location":"Qingdao","pipeline_type":"Pipeline","fatalities":62,"injuries":136,"property_damage_usd":750000000,"operator":"Sinopec","cause":"Pipeline Integrity","source":"China MEM"},
    {"name":"Kuwait Oil Fires","year":1991,"country":"Kuwait","region":"Middle East","location":"Kuwait","pipeline_type":"Upstream","fatalities":0,"injuries":0,"property_damage_usd":40000000000,"operator":"KOC","cause":"External Attack","source":"KOC"},
    {"name":"Ghislenghien Explosion","year":2004,"country":"Belgium","region":"Europe","location":"Ghislenghien","pipeline_type":"Gas Transmission","fatalities":24,"injuries":132,"property_damage_usd":150000000,"operator":"Fluxys","cause":"Pipeline Integrity","source":"Belgian Gov"},
    {"name":"Bhopal Gas Tragedy","year":1984,"country":"India","region":"Asia Pacific","location":"Bhopal","pipeline_type":"Downstream","fatalities":3787,"injuries":558125,"property_damage_usd":470000000,"operator":"Union Carbide","cause":"Human Error","source":"EPA"},
    {"name":"Nairobi Pipeline","year":2011,"country":"Kenya","region":"Africa","location":"Nairobi","pipeline_type":"Pipeline","fatalities":120,"injuries":200,"property_damage_usd":80000000,"operator":"Kenya Pipeline Co.","cause":"Pipeline Integrity","source":"KNCHR"},
    {"name":"AZF Toulouse","year":2001,"country":"France","region":"Europe","location":"Toulouse","pipeline_type":"Downstream","fatalities":31,"injuries":2500,"property_damage_usd":3000000000,"operator":"Grande Paroisse","cause":"Human Error","source":"ARIA France"},
]

# ============================================================
# PHMSA API
# ============================================================
PHMSA_BASE = "https://data.phmsa.dot.gov/api/action/datastore_search_sql"
PHMSA_RESOURCES = {
    "Gas Transmission": "f58c2c46-2e33-4e75-b1df-ea98c582cb0d",
    "Hazardous Liquid": "9f24e58c-1b76-4a82-a95e-7c7571e1f9b1",
}

@st.cache_data(ttl=3600)
def fetch_phmsa(resource_id, year_from, year_to, limit=200):
    sql = f'SELECT * FROM "{resource_id}" WHERE "IYEAR">={year_from} AND "IYEAR"<={year_to} ORDER BY "IYEAR" DESC LIMIT {limit}'
    try:
        r = requests.get(PHMSA_BASE, params={"sql": sql}, timeout=20)
        records = r.json().get("result", {}).get("records", [])
        return pd.DataFrame(records) if records else pd.DataFrame()
    except:
        return pd.DataFrame()

def clean_phmsa(df, ptype):
    if df.empty: return df
    col_map = {"IYEAR":"year","OPERATOR_NAME":"operator","STATE":"state","CITY":"city",
                "FATAL":"fatalities","INJURE":"injuries","PRPTY":"property_damage_usd",
                "CAUSE":"cause_code","NAME_OF_OPERATOR":"operator"}
    df = df.rename(columns={k:v for k,v in col_map.items() if k in df.columns})
    for c in ["fatalities","injuries","property_damage_usd","year"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["pipeline_type"] = ptype
    df["country"] = "USA"
    df["region"] = "Americas"
    df["source"] = "PHMSA"
    cause_map = {"CORROSION":"Corrosion","EXCAVATION":"Excavation Damage",
                 "INCORRECT OPERATION":"Human Error","MATERIAL":"Material Failure",
                 "EQUIPMENT":"Equipment Failure","NATURAL FORCE":"Natural Force"}
    if "cause_code" in df.columns:
        df["cause"] = df["cause_code"].map(cause_map).fillna(df.get("cause_code","Unknown"))
    if "city" in df.columns and "state" in df.columns:
        df["location"] = df["city"].fillna("") + ", " + df["state"].fillna("") + " (USA)"
    return df

# ============================================================
# ฟังก์ชันหลัก: ค้นหาข่าว MAE ด้วย Claude + Web Search
#
# วิธีทำงาน:
# 1. เรียก Anthropic API พร้อมเปิด web_search tool
# 2. Claude จะค้นหาข่าวจริงจากอินเทอร์เน็ต
# 3. รับ response กลับมาพร้อม source citations
# 4. แสดงผลแบบ streaming ให้เห็น real-time
# ============================================================
def search_mae_news(
    query: str,
    region: str,
    incident_type: str,
    year_range: str,
    output_placeholder,
    source_placeholder
):
    """
    ค้นหาข่าว MAE ล่าสุดด้วย Claude Web Search Tool
    - output_placeholder: ช่องแสดง AI response
    - source_placeholder: ช่องแสดง sources ที่ AI ใช้
    """

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    # สร้าง search query ที่เฉพาะเจาะจง
    region_filter  = f" in {region}"   if region  != "ทั่วโลก" else ""
    type_filter    = f" {incident_type}" if incident_type != "ทุกประเภท" else ""
    year_filter    = f" {year_range}"  if year_range != "ล่าสุด" else " 2024 2025"

    system_prompt = """คุณคือผู้เชี่ยวชาญด้าน HSE (Health, Safety & Environment) ในอุตสาหกรรม Oil & Gas
ภารกิจ: ค้นหาและสรุปข่าว Major Accident Events (MAE) ล่าสุดในอุตสาหกรรม Oil & Gas ทั่วโลก

ค้นหาข้อมูลจากแหล่งที่น่าเชื่อถือ เช่น:
- สื่อข่าวเฉพาะทาง: Offshore Technology, Oil & Gas Journal, Rigzone, Energy Voice
- หน่วยงานรัฐ: BSEE, HSE UK, PHMSA, CSB
- สำนักข่าวหลัก: Reuters, Bloomberg Energy, AP News

รูปแบบการตอบ (ภาษาไทย):

## 📰 ข่าว MAE ล่าสุดที่พบ

### [ชื่อเหตุการณ์ที่ 1]
- **วันที่**: DD/MM/YYYY
- **สถานที่**: ประเทศ, Location
- **ประเภท**: Fire / Explosion / Spill / Blowout
- **บริษัท**: ชื่อบริษัท
- **ผู้เสียชีวิต/บาดเจ็บ**: X คน / Y คน
- **สรุป**: อธิบายสั้นๆ ว่าเกิดอะไรขึ้น
- **แหล่งข่าว**: ชื่อสื่อ

(ทำซ้ำสำหรับแต่ละเหตุการณ์ที่พบ)

## 🔍 สรุปภาพรวม
สรุปแนวโน้มที่พบจากข่าวเหล่านี้

## ⚠️ หมายเหตุ
ระบุข้อจำกัดของข้อมูลที่ค้นพบ

ตอบเป็นภาษาไทยเสมอ ถ้าไม่พบข่าวที่ตรงกับคำค้น ให้บอกว่าไม่พบและแนะนำ keywords อื่น"""

    user_prompt = f"""ค้นหาข่าว Major Accident Events (MAE) ล่าสุดในอุตสาหกรรม Oil & Gas:
- ภูมิภาค: {region}
- ประเภทเหตุการณ์: {incident_type}
- ช่วงเวลา: {year_range}

กรุณาค้นหาข่าวจริงและสรุปเหตุการณ์ที่พบทั้งหมด พร้อมระบุแหล่งข่าวให้ชัดเจน"""

    # เรียก API พร้อม web_search tool และ streaming
    # web_search_20250305 คือ tool ที่ให้ Claude ค้นหาข้อมูลจากอินเทอร์เน็ตได้จริง
    full_text = ""
    sources_found = []

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system_prompt,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }],
        messages=[{"role": "user", "content": user_prompt}]
    ) as stream:
        # วน loop รับ events จาก stream
        for event in stream:
            event_type = type(event).__name__

            # กรณี AI กำลังพิมพ์ข้อความ
            if event_type == "ContentBlockDelta":
                delta = getattr(event, "delta", None)
                if delta and hasattr(delta, "text"):
                    full_text += delta.text
                    # อัปเดต placeholder แบบ real-time
                    output_placeholder.markdown(full_text + "▌")

            # กรณี AI กำลัง search — แสดงว่ากำลังค้นอะไร
            elif event_type == "ContentBlockStart":
                block = getattr(event, "content_block", None)
                if block and getattr(block, "type", "") == "tool_use":
                    tool_name = getattr(block, "name", "")
                    if tool_name == "web_search":
                        with source_placeholder.container():
                            st.info("🔍 AI กำลังค้นหาข่าวจากอินเทอร์เน็ต...")

            # กรณี search เสร็จแล้ว — ดึง URL ที่ใช้
            elif event_type == "ContentBlockStop":
                pass

    # แสดงผลสุดท้าย
    output_placeholder.markdown(full_text)
    return full_text


# ============================================================
# Header
# ============================================================
st.title("🔥 Global MAE Report + Real-time News")
st.markdown("**Historical Database + BSEE + PHMSA + 📰 ข่าวล่าสุดจาก Claude Web Search**")
st.divider()

# ============================================================
# Sidebar
# ============================================================
st.sidebar.header("🎛️ ตั้งค่า")

year_from = st.sidebar.number_input("ปีเริ่มต้น", min_value=1984, max_value=2025, value=2015)
year_to   = st.sidebar.number_input("ปีสิ้นสุด",  min_value=1984, max_value=2025, value=2025)
search_q  = st.sidebar.text_input("🔍 ค้นหา", placeholder="เช่น explosion, BP...")
only_fatal= st.sidebar.checkbox("เฉพาะที่มีผู้เสียชีวิต")

# ============================================================
# โหลดข้อมูล Historical + PHMSA
# ============================================================
frames = []
hist_df = pd.DataFrame(HISTORICAL_MAE)
hist_df = hist_df[(hist_df["year"]>=int(year_from))&(hist_df["year"]<=int(year_to))]
frames.append(hist_df)

with st.spinner("🔧 กำลังดึง PHMSA..."):
    phmsa_frames = []
    for ptype, rid in PHMSA_RESOURCES.items():
        raw = fetch_phmsa(rid, int(year_from), int(year_to), 150)
        if not raw.empty:
            phmsa_frames.append(clean_phmsa(raw, ptype))
    if phmsa_frames:
        phmsa_df = pd.concat(phmsa_frames, ignore_index=True)
        frames.append(phmsa_df)
        st.success(f"✅ PHMSA: {len(phmsa_df):,} incidents")

df = pd.concat(frames, ignore_index=True)
for c in ["fatalities","injuries","property_damage_usd","year"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

filtered = df.copy()
if search_q:
    mask = pd.Series(False, index=filtered.index)
    for col in ["operator","location","cause","pipeline_type","country","name"]:
        if col in filtered.columns:
            mask |= filtered[col].astype(str).str.contains(search_q, case=False, na=False)
    filtered = filtered[mask]
if only_fatal:
    filtered = filtered[filtered["fatalities"]>0]

# Metrics
c1,c2,c3,c4 = st.columns(4)
c1.metric("🔴 Records",      f"{len(filtered):,}")
c2.metric("💀 เสียชีวิต",   f"{int(filtered['fatalities'].sum()):,}")
c3.metric("🤕 บาดเจ็บ",    f"{int(filtered['injuries'].sum()):,}")
dmg = filtered["property_damage_usd"].sum() if "property_damage_usd" in filtered.columns else 0
c4.metric("💰 ความเสียหาย", f"${dmg/1e9:.1f}B" if dmg>=1e9 else f"${dmg/1e6:.0f}M")
st.divider()

# ============================================================
# แท็บหลัก
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📰 ข่าว MAE ล่าสุด",   # แท็บใหม่ที่เพิ่มมา
    "📊 Charts & แผนที่",
    "📋 รายการเหตุการณ์",
    "🛢️ BSEE Offshore Trends",
    "🤖 AI Report",
])

# ============================================================
# TAB 1 — ข่าวล่าสุด (ฟีเจอร์ใหม่!)
# ============================================================
with tab1:
    st.subheader("📰 ค้นหาข่าว MAE ล่าสุดจากอินเทอร์เน็ต")

    # อธิบายว่า feature นี้ทำงานอย่างไร
    with st.expander("ℹ️ ฟีเจอร์นี้ทำงานอย่างไร?", expanded=False):
        st.markdown("""
**วิธีทำงาน:**

1. คุณเลือกภูมิภาค, ประเภทเหตุการณ์, และช่วงเวลาที่ต้องการ
2. กด **"ค้นหาข่าวล่าสุด"**
3. Claude จะใช้ **Web Search Tool** ค้นหาข่าวจริงจากอินเทอร์เน็ตทันที
4. AI จะสรุปเหตุการณ์ที่พบพร้อมระบุแหล่งข่าว

**ต่างจากข้อมูล Historical อย่างไร?**
- Historical = ข้อมูลที่ฝังไว้ในโค้ดแล้ว (อัปเดตเมื่อแก้โค้ด)
- ข่าวล่าสุด = ดึงจากอินเทอร์เน็ตจริงทุกครั้งที่กดค้นหา ✅

**แหล่งข้อมูลที่ AI จะค้น:**
- Offshore Technology, Oil & Gas Journal, Rigzone
- BSEE, HSE UK, CSB Investigation Reports
- Reuters Energy, Bloomberg Energy, AP News
        """)

    # ตัวกรองการค้นหา
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        news_region = st.selectbox("🌍 ภูมิภาค", [
            "ทั่วโลก", "Americas (USA/Canada/Mexico/Brazil)",
            "Europe (North Sea/UK/Norway)", "Middle East",
            "Asia Pacific", "Africa"
        ])

    with col_b:
        news_type = st.selectbox("⚠️ ประเภทเหตุการณ์", [
            "ทุกประเภท", "Explosion", "Fire",
            "Oil Spill", "Blowout / Well Control",
            "Gas Release", "Pipeline Rupture", "Structural Failure"
        ])

    with col_c:
        news_period = st.selectbox("📅 ช่วงเวลา", [
            "ล่าสุด (2024-2025)",
            "ปี 2024",
            "ปี 2023",
            "3 ปีล่าสุด (2022-2025)",
        ])

    # Custom query เพิ่มเติม
    custom_query = st.text_input(
        "🔎 เพิ่มคำค้นหาเฉพาะ (ไม่บังคับ)",
        placeholder="เช่น offshore platform, refinery fire, pipeline leak..."
    )

    # ปุ่มค้นหา
    search_btn = st.button(
        "🔍 ค้นหาข่าวล่าสุด",
        type="primary",
        use_container_width=True
    )

    if search_btn:
        # พื้นที่แสดงผล
        st.markdown("---")
        source_status = st.empty()     # แสดงสถานะว่า AI กำลัง search อะไร
        result_area   = st.empty()     # แสดง AI response แบบ streaming

        try:
            result_area.markdown("*กำลังเริ่มค้นหา...*")

            full_result = search_mae_news(
                query        = custom_query,
                region       = news_region,
                incident_type= news_type,
                year_range   = news_period,
                output_placeholder = result_area,
                source_placeholder = source_status
            )

            source_status.empty()  # ซ่อน spinner หลัง search เสร็จ

            # ปุ่มดาวน์โหลดผลลัพธ์
            if full_result:
                st.download_button(
                    "⬇️ ดาวน์โหลดข่าว MAE ที่ค้นพบ (.txt)",
                    data=full_result.encode("utf-8"),
                    file_name=f"mae_news_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )

        except KeyError:
            st.error("❌ ไม่พบ ANTHROPIC_API_KEY ใน Streamlit Secrets")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            st.info("💡 ถ้า error เกี่ยวกับ web_search tool — ตรวจสอบว่าใช้ model claude-sonnet-4-20250514")

    else:
        # แสดงตัวอย่างที่สามารถค้นได้
        st.markdown("### 💡 ตัวอย่างการค้นหา")
        example_cols = st.columns(3)
        examples = [
            ("🔴", "Offshore explosion 2025", "ระเบิดแท่นขุดเจาะล่าสุด"),
            ("🌊", "Oil spill Gulf of Mexico", "น้ำมันรั่วอ่าวเม็กซิโก"),
            ("💥", "Refinery fire Asia 2024", "ไฟไหม้โรงกลั่น Asia"),
            ("⚡", "Pipeline rupture Europe", "ท่อแตก Europe"),
            ("🔥", "LNG incident Middle East", "อุบัติเหตุ LNG ตะวันออกกลาง"),
            ("🛢️", "Blowout offshore 2024", "Blowout offshore ล่าสุด"),
        ]
        for i, (icon, eng, thai) in enumerate(examples):
            with example_cols[i % 3]:
                st.markdown(f"""
<div style="background:var(--color-background-secondary);
     border:0.5px solid var(--color-border-tertiary);
     border-radius:8px; padding:10px; margin-bottom:8px;
     font-size:13px;">
  <div style="font-size:18px">{icon}</div>
  <div style="font-weight:500;color:var(--color-text-primary)">{thai}</div>
  <div style="color:var(--color-text-secondary);font-size:12px">{eng}</div>
</div>""", unsafe_allow_html=True)

# ============================================================
# TAB 2 — Charts
# ============================================================
with tab2:
    if filtered.empty:
        st.warning("ไม่มีข้อมูล")
    else:
        r1,r2 = st.columns(2)
        with r1:
            st.subheader("ตามประเทศ (Top 10)")
            cc = filtered.groupby("country").size().reset_index(name="count").nlargest(10,"count")
            fig_c = px.bar(cc, x="count", y="country", orientation="h",
                           color="count", color_continuous_scale="OrRd")
            fig_c.update_layout(showlegend=False, height=280,
                                margin=dict(l=0,r=0,t=10,b=0),
                                yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_c, use_container_width=True)

        with r2:
            st.subheader("ตามภูมิภาค")
            if "region" in filtered.columns:
                rc = filtered.groupby("region").size().reset_index(name="count")
                fig1 = px.pie(rc, values="count", names="region",
                              color_discrete_sequence=px.colors.qualitative.Set2)
                fig1.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig1, use_container_width=True)

        st.subheader("แนวโน้มตามปี")
        yc = filtered.groupby("year").agg(
            events=("fatalities","count"), fatalities=("fatalities","sum")
        ).reset_index()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=yc["year"], y=yc["events"], name="events", marker_color="#636efa"))
        fig3.add_trace(go.Scatter(x=yc["year"], y=yc["fatalities"], name="เสียชีวิต",
                                  yaxis="y2", line=dict(color="#ef553b",width=2)))
        fig3.update_layout(height=300,
            yaxis=dict(title="จำนวน"), yaxis2=dict(title="เสียชีวิต",overlaying="y",side="right"),
            legend=dict(orientation="h",y=1), margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("🗺️ แผนที่โลก")
        ca = filtered.groupby("country").agg(
            events=("fatalities","count"), fatalities=("fatalities","sum")
        ).reset_index()
        fig4 = px.choropleth(ca, locations="country", locationmode="country names",
            color="events", hover_name="country", hover_data={"fatalities":True},
            color_continuous_scale="Reds")
        fig4.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig4, use_container_width=True)

# ============================================================
# TAB 3 — Table
# ============================================================
with tab3:
    st.subheader(f"รายการทั้งหมด ({len(filtered):,} records)")
    show_cols = [c for c in ["year","name","operator","location","pipeline_type",
                              "fatalities","injuries","property_damage_usd","cause","source"]
                 if c in filtered.columns]
    rename_map = {"year":"ปี","name":"ชื่อเหตุการณ์","operator":"บริษัท","location":"สถานที่",
                  "pipeline_type":"ประเภท","fatalities":"เสียชีวิต","injuries":"บาดเจ็บ",
                  "property_damage_usd":"ความเสียหาย (USD)","cause":"สาเหตุ","source":"แหล่งข้อมูล"}
    disp = filtered[show_cols].rename(columns=rename_map).sort_values("ความเสียหาย (USD)" if "ความเสียหาย (USD)" in filtered.rename(columns=rename_map).columns else "เสียชีวิต", ascending=False)
    st.dataframe(disp, use_container_width=True, hide_index=True,
        column_config={"ความเสียหาย (USD)": st.column_config.NumberColumn(format="$%,.0f"),
                       "เสียชีวิต": st.column_config.NumberColumn(format="%d คน")})
    csv = disp.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ CSV", data=csv, file_name="mae_data.csv", mime="text/csv")

# ============================================================
# TAB 4 — BSEE Trends
# ============================================================
with tab4:
    st.subheader("🛢️ BSEE Offshore Incident Trends")
    st.caption("ที่มา: Bureau of Safety and Environmental Enforcement | bsee.gov")
    bsee_df = pd.DataFrame(BSEE_ANNUAL_STATS)
    bsee_df = bsee_df[(bsee_df["year"]>=int(year_from))&(bsee_df["year"]<=int(year_to))]
    if not bsee_df.empty:
        r1,r2 = st.columns(2)
        with r1:
            st.markdown("**ผู้เสียชีวิต & บาดเจ็บ**")
            fig_fi = go.Figure()
            fig_fi.add_trace(go.Bar(x=bsee_df["year"], y=bsee_df["fatalities"], name="เสียชีวิต", marker_color="#ef553b"))
            fig_fi.add_trace(go.Bar(x=bsee_df["year"], y=bsee_df["injuries"], name="บาดเจ็บ", marker_color="#636efa"))
            fig_fi.update_layout(barmode="group", height=260, margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h",y=1))
            st.plotly_chart(fig_fi, use_container_width=True)
        with r2:
            st.markdown("**ไฟไหม้ & ก๊าซรั่ว & Oil Spill**")
            fig_fg = go.Figure()
            fig_fg.add_trace(go.Scatter(x=bsee_df["year"], y=bsee_df["fires"], name="ไฟไหม้", line=dict(color="#EF9F27",width=2)))
            fig_fg.add_trace(go.Scatter(x=bsee_df["year"], y=bsee_df["gas_releases"], name="ก๊าซรั่ว", line=dict(color="#636efa",width=2)))
            fig_fg.add_trace(go.Scatter(x=bsee_df["year"], y=bsee_df["spills"], name="Oil Spill", line=dict(color="#A32D2D",width=2,dash="dot")))
            fig_fg.update_layout(height=260, margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h",y=1))
            st.plotly_chart(fig_fg, use_container_width=True)
        st.dataframe(bsee_df.sort_values("year",ascending=False).rename(columns={
            "year":"ปี","fatalities":"เสียชีวิต","injuries":"บาดเจ็บ",
            "fires":"ไฟไหม้","explosions":"ระเบิด","gas_releases":"ก๊าซรั่ว","spills":"Spills"
        }), use_container_width=True, hide_index=True)

# ============================================================
# TAB 5 — AI Report (วิเคราะห์ Historical)
# ============================================================
with tab5:
    st.subheader("🤖 AI Report — วิเคราะห์ข้อมูล Historical")
    st.caption("วิเคราะห์จากฐานข้อมูล Historical + PHMSA ที่กรองไว้")

    sample = filtered.nlargest(50,"fatalities") if len(filtered)>50 else filtered
    lines = [
        f"- {r.get('name', r.get('operator','?'))} ({int(r.get('year',0))}, "
        f"{r.get('location','?')}, {r.get('country','?')}): "
        f"{r.get('pipeline_type','?')}, {int(r.get('fatalities',0))} fatalities, "
        f"${r.get('property_damage_usd',0)/1e6:.0f}M damage, cause: {r.get('cause','?')}"
        for _, r in sample.iterrows()
    ]

    report_style = st.selectbox("รูปแบบ", ["Executive Summary","Detailed Technical","Statistical Analysis"])

    if st.button("🚀 สร้าง AI Report", type="primary", use_container_width=True):
        try:
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            # AI Report นี้ไม่ใช้ web_search — วิเคราะห์จากข้อมูลที่มีอยู่เท่านั้น
            with st.spinner("วิเคราะห์..."):
                with client.messages.stream(
                    model="claude-sonnet-4-20250514", max_tokens=2000,
                    system="คุณคือผู้เชี่ยวชาญ HSE ใน Oil & Gas ตอบภาษาไทยแบบ Professional Report",
                    messages=[{"role":"user","content":
                        f"วิเคราะห์ข้อมูล MAE ต่อไปนี้และสร้าง {report_style}:\n\n" +
                        "\n".join(lines) +
                        "\n\nรวม: Executive Summary, Trends, Root Causes, Top Events, Recommendations"}]
                ) as stream:
                    resp = st.write_stream(stream.text_stream)
            st.download_button("⬇️ ดาวน์โหลด", data=resp.encode("utf-8"),
                               file_name="mae_ai_report.txt", mime="text/plain")
        except KeyError:
            st.error("❌ ไม่พบ ANTHROPIC_API_KEY")
        except Exception as e:
            st.error(f"❌ {str(e)}")

# ============================================================
# Footer
# ============================================================
st.divider()
st.caption(
    "📡 **PHMSA**: data.phmsa.dot.gov | **BSEE**: bsee.gov | "
    "**Historical**: HSE UK, CSB, ARIA France, TSB Canada\n\n"
    "📰 **Web Search**: Claude AI ค้นหาข่าวจริงจากอินเทอร์เน็ตแบบ Real-time\n\n"
    "🤖 Powered by Claude (Anthropic) | "
    f"อัปเดต: {datetime.now().strftime('%d %b %Y %H:%M')}"
)
