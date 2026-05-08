import streamlit as st
import anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# ============================================================
# PAGE CONFIG + CUSTOM CSS — Clean Industrial Design
# ============================================================
st.set_page_config(
    page_title="MAE Intelligence — Oil & Gas",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D0D0D;
    border-right: 1px solid #1E1E1E;
}
[data-testid="stSidebar"] * { color: #E0E0E0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stCheckbox label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stTextInput label { color: #888 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #888 !important; font-size: 11px; }

/* ── Sidebar section headers ── */
.sidebar-section {
    color: #FF4B1F !important;
    font-size: 10px !important;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 12px 0 4px;
    border-top: 1px solid #1E1E1E;
    margin-top: 8px;
}

/* ── Page Header ── */
.page-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #E8E4DF;
}
.page-title {
    font-size: 28px;
    font-weight: 600;
    color: #0D0D0D;
    letter-spacing: -0.03em;
    line-height: 1;
}
.page-subtitle {
    font-size: 13px;
    color: #888;
    margin-top: 6px;
    font-weight: 400;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #FF4B1F;
    color: white;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    padding: 5px 12px;
    border-radius: 2px;
    text-transform: uppercase;
}
.live-dot {
    width: 6px; height: 6px;
    background: white;
    border-radius: 50%;
    animation: blink 1.2s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── Metric Cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: #E8E4DF;
    border: 1px solid #E8E4DF;
    margin-bottom: 2rem;
}
.metric-card {
    background: white;
    padding: 20px 24px;
}
.metric-label {
    font-size: 10px;
    font-weight: 600;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 32px;
    font-weight: 600;
    color: #0D0D0D;
    line-height: 1;
    font-family: 'DM Mono', monospace;
    letter-spacing: -0.02em;
}
.metric-value.danger { color: #CC2200; }
.metric-sub {
    font-size: 11px;
    color: #999;
    margin-top: 4px;
}

/* ── Section Headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 2rem 0 1rem;
}
.section-label {
    font-size: 10px;
    font-weight: 700;
    color: #FF4B1F;
    text-transform: uppercase;
    letter-spacing: 0.15em;
}
.section-title {
    font-size: 16px;
    font-weight: 600;
    color: #0D0D0D;
}
.section-line {
    flex: 1;
    height: 1px;
    background: #E8E4DF;
}

/* ── Tab Styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #E8E4DF;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-size: 12px;
    font-weight: 500;
    color: #999;
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
    letter-spacing: 0.02em;
}
.stTabs [aria-selected="true"] {
    color: #0D0D0D !important;
    border-bottom: 2px solid #0D0D0D !important;
    background: transparent !important;
}

/* ── News Search Box ── */
.search-panel {
    background: #F7F5F2;
    border: 1px solid #E8E4DF;
    padding: 24px;
    margin-bottom: 1.5rem;
}
.search-title {
    font-size: 12px;
    font-weight: 700;
    color: #FF4B1F;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 16px;
}

/* ── Buttons ── */
.stButton > button {
    background: #0D0D0D !important;
    color: white !important;
    border: none !important;
    border-radius: 2px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 24px !important;
    transition: background 0.15s !important;
}
.stButton > button:hover {
    background: #FF4B1F !important;
}
.stButton > button[kind="primary"] {
    background: #FF4B1F !important;
}
.stButton > button[kind="primary"]:hover {
    background: #CC3300 !important;
}

/* ── Result box ── */
.result-box {
    background: white;
    border: 1px solid #E8E4DF;
    border-left: 3px solid #FF4B1F;
    padding: 24px;
    font-size: 14px;
    line-height: 1.8;
    color: #1A1A1A;
}

/* ── Info / Alert boxes ── */
.stAlert { border-radius: 2px !important; }
div[data-testid="stAlert"] { border-radius: 2px !important; }

/* ── Status pills ── */
.status-ok  { display:inline-block; background:#EDFAF2; color:#1A7F42; font-size:11px; font-weight:600; padding:3px 10px; border-radius:2px; letter-spacing:0.04em; }
.status-warn{ display:inline-block; background:#FFF8E6; color:#946C00; font-size:11px; font-weight:600; padding:3px 10px; border-radius:2px; letter-spacing:0.04em; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #E8E4DF; }
.stDataFrame thead { background: #F7F5F2; }

/* ── Source tag ── */
.source-tag {
    display: inline-block;
    background: #F7F5F2;
    border: 1px solid #E8E4DF;
    color: #666;
    font-size: 10px;
    font-family: 'DM Mono', monospace;
    padding: 2px 8px;
    border-radius: 2px;
    margin-right: 4px;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA
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
    {"name":"Ghislenghien","year":2004,"country":"Belgium","region":"Europe","location":"Ghislenghien","pipeline_type":"Gas Transmission","fatalities":24,"injuries":132,"property_damage_usd":150000000,"operator":"Fluxys","cause":"Pipeline Integrity","source":"Belgian Gov"},
    {"name":"Bhopal Gas Tragedy","year":1984,"country":"India","region":"Asia Pacific","location":"Bhopal","pipeline_type":"Downstream","fatalities":3787,"injuries":558125,"property_damage_usd":470000000,"operator":"Union Carbide","cause":"Human Error","source":"EPA"},
    {"name":"Nairobi Pipeline","year":2011,"country":"Kenya","region":"Africa","location":"Nairobi","pipeline_type":"Pipeline","fatalities":120,"injuries":200,"property_damage_usd":80000000,"operator":"Kenya Pipeline Co.","cause":"Pipeline Integrity","source":"KNCHR"},
    {"name":"AZF Toulouse","year":2001,"country":"France","region":"Europe","location":"Toulouse","pipeline_type":"Downstream","fatalities":31,"injuries":2500,"property_damage_usd":3000000000,"operator":"Grande Paroisse","cause":"Human Error","source":"ARIA France"},
]

PHMSA_BASE = "https://data.phmsa.dot.gov/api/action/datastore_search_sql"
PHMSA_RESOURCES = {
    "Gas Transmission": "f58c2c46-2e33-4e75-b1df-ea98c582cb0d",
    "Hazardous Liquid":  "9f24e58c-1b76-4a82-a95e-7c7571e1f9b1",
}

@st.cache_data(ttl=3600)
def fetch_phmsa(rid, y0, y1, limit=200):
    sql = f'SELECT * FROM "{rid}" WHERE "IYEAR">={y0} AND "IYEAR"<={y1} ORDER BY "IYEAR" DESC LIMIT {limit}'
    try:
        r = requests.get(PHMSA_BASE, params={"sql":sql}, timeout=20)
        recs = r.json().get("result",{}).get("records",[])
        return pd.DataFrame(recs) if recs else pd.DataFrame()
    except: return pd.DataFrame()

def clean_phmsa(df, ptype):
    if df.empty: return df
    col_map = {"IYEAR":"year","OPERATOR_NAME":"operator","STATE":"state","CITY":"city",
                "FATAL":"fatalities","INJURE":"injuries","PRPTY":"property_damage_usd","CAUSE":"cause_code"}
    df = df.rename(columns={k:v for k,v in col_map.items() if k in df.columns})
    for c in ["fatalities","injuries","property_damage_usd","year"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["pipeline_type"] = ptype; df["country"] = "USA"; df["region"] = "Americas"; df["source"] = "PHMSA"
    cause_map = {"CORROSION":"Corrosion","EXCAVATION":"Excavation Damage",
                 "INCORRECT OPERATION":"Human Error","MATERIAL":"Material Failure",
                 "EQUIPMENT":"Equipment Failure","NATURAL FORCE":"Natural Force"}
    if "cause_code" in df.columns:
        df["cause"] = df["cause_code"].map(cause_map).fillna(df["cause_code"].fillna("Unknown"))
    if "city" in df.columns and "state" in df.columns:
        df["location"] = df["city"].fillna("")+", "+df["state"].fillna("")+" (USA)"
    return df

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🛢️ MAE Intelligence")
    st.markdown("---")

    st.markdown('<p class="sidebar-section">📅 ช่วงเวลา</p>', unsafe_allow_html=True)
    year_from = st.number_input("ปีเริ่มต้น", min_value=1984, max_value=2025, value=2010)
    year_to   = st.number_input("ปีสิ้นสุด",  min_value=1984, max_value=2025, value=2025)

    st.markdown('<p class="sidebar-section">🔍 กรองข้อมูล</p>', unsafe_allow_html=True)
    search_q   = st.text_input("ค้นหา", placeholder="เช่น explosion, BP...")
    only_fatal = st.checkbox("เฉพาะที่มีผู้เสียชีวิต")

    st.markdown('<p class="sidebar-section">📡 แหล่งข้อมูล</p>', unsafe_allow_html=True)
    use_phmsa = st.checkbox("PHMSA (USA Pipeline)", value=True)
    use_hist  = st.checkbox("Historical Global MAE", value=True)

    st.markdown("---")
    st.markdown(f'<span class="source-tag">BSEE</span><span class="source-tag">PHMSA</span><span class="source-tag">HSE UK</span><span class="source-tag">CSB</span>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:10px;color:#555;margin-top:8px;">อัปเดต {datetime.now().strftime("%d %b %Y")}</p>', unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================
frames = []
phmsa_status = ""

if use_hist:
    h = pd.DataFrame(HISTORICAL_MAE)
    frames.append(h[(h["year"]>=int(year_from))&(h["year"]<=int(year_to))])

if use_phmsa:
    pf = []
    for ptype, rid in PHMSA_RESOURCES.items():
        raw = fetch_phmsa(rid, int(year_from), int(year_to))
        if not raw.empty: pf.append(clean_phmsa(raw, ptype))
    if pf:
        phmsa_df = pd.concat(pf, ignore_index=True)
        frames.append(phmsa_df)
        phmsa_status = f"PHMSA {len(phmsa_df):,} records"

df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(HISTORICAL_MAE)
for c in ["fatalities","injuries","property_damage_usd","year"]:
    if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
df = df.drop_duplicates(subset=["year","operator","fatalities"], keep="first")

filtered = df.copy()
if search_q:
    mask = pd.Series(False, index=filtered.index)
    for col in ["operator","location","cause","pipeline_type","country","name"]:
        if col in filtered.columns:
            mask |= filtered[col].astype(str).str.contains(search_q, case=False, na=False)
    filtered = filtered[mask]
if only_fatal:
    filtered = filtered[filtered["fatalities"]>0]

# ============================================================
# PAGE HEADER
# ============================================================
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown("""
    <div class="page-title">MAE Intelligence Platform</div>
    <div class="page-subtitle">Major Accident Events — Oil &amp; Gas Industry · Global Database</div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown('<div style="text-align:right;padding-top:8px"><span class="live-badge"><span class="live-dot"></span>Live Data</span></div>', unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# METRIC CARDS
# ============================================================
dmg = filtered["property_damage_usd"].sum() if "property_damage_usd" in filtered.columns else 0
dmg_str = f"${dmg/1e9:.1f}B" if dmg>=1e9 else f"${dmg/1e6:.0f}M"
countries = filtered["country"].nunique() if "country" in filtered.columns else 0

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">MAE Events</div>
    <div class="metric-value danger">{len(filtered):,}</div>
    <div class="metric-sub">ปี {int(year_from)}–{int(year_to)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">ผู้เสียชีวิต</div>
    <div class="metric-value danger">{int(filtered['fatalities'].sum()):,}</div>
    <div class="metric-sub">รวมทุกเหตุการณ์</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">ความเสียหาย</div>
    <div class="metric-value">{dmg_str}</div>
    <div class="metric-sub">USD รวมทั้งหมด</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">ประเทศที่เกิดเหตุ</div>
    <div class="metric-value">{countries}</div>
    <div class="metric-sub">ทั่วโลก</div>
  </div>
</div>
""", unsafe_allow_html=True)

# source status
if phmsa_status:
    st.markdown(f'<span class="status-ok">✓ {phmsa_status}</span> <span class="status-ok">✓ Historical {len(pd.DataFrame(HISTORICAL_MAE))} records</span>', unsafe_allow_html=True)
    st.markdown("")

# ============================================================
# TABS
# ============================================================
tab_news, tab_chart, tab_table, tab_bsee, tab_ai = st.tabs([
    "📰  ข่าวล่าสุด",
    "📊  Charts",
    "📋  รายการ",
    "🛢️  BSEE Trends",
    "🤖  AI Report",
])

# ──────────────────────────────────────────────
# TAB 1 — ข่าวล่าสุด (Web Search)
# ──────────────────────────────────────────────
with tab_news:
    st.markdown("""
    <div class="section-header">
      <span class="section-label">Real-time</span>
      <span class="section-title">ค้นหาข่าว MAE ล่าสุด</span>
      <span class="section-line"></span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="search-panel">', unsafe_allow_html=True)
    st.markdown('<div class="search-title">🔎 ตั้งค่าการค้นหา</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        news_region = st.selectbox("ภูมิภาค", [
            "ทั่วโลก","Americas","Europe / North Sea",
            "Middle East","Asia Pacific","Africa"
        ], label_visibility="visible")
    with col2:
        news_type = st.selectbox("ประเภทเหตุการณ์", [
            "ทุกประเภท","Explosion","Fire","Oil Spill",
            "Blowout / Well Control","Gas Release","Pipeline Rupture"
        ])
    with col3:
        news_period = st.selectbox("ช่วงเวลา", [
            "ล่าสุด (2024–2025)","ปี 2024","ปี 2023","3 ปีล่าสุด"
        ])

    custom_q = st.text_input("เพิ่มคำค้นหา (ไม่บังคับ)", placeholder="เช่น offshore platform, refinery, LNG...")
    st.markdown('</div>', unsafe_allow_html=True)

    search_btn = st.button("🔍  ค้นหาข่าวล่าสุด", type="primary", use_container_width=True)

    if search_btn:
        st.markdown("---")
        status_ph = st.empty()
        result_ph = st.empty()

        # ตรวจสอบ API Key ก่อนเรียก
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except KeyError:
            st.error("❌ ไม่พบ ANTHROPIC_API_KEY — กรุณาเพิ่มใน Streamlit Secrets ก่อน")
            st.code('ANTHROPIC_API_KEY = "sk-ant-api03-xxxxxxxxxxxx"', language="toml")
            st.stop()

        if not api_key or not api_key.startswith("sk-ant"):
            st.error("❌ API Key ไม่ถูกต้อง — ต้องขึ้นต้นด้วย sk-ant-api03-...")
            st.stop()

        try:
            status_ph.info("🔍 Claude กำลังค้นหาข่าวจากอินเทอร์เน็ต...")

            client = anthropic.Anthropic(api_key=api_key)

            system_p = """คุณคือผู้เชี่ยวชาญด้าน HSE ในอุตสาหกรรม Oil & Gas
ค้นหาข่าว Major Accident Events (MAE) ล่าสุดจากแหล่งที่น่าเชื่อถือ:
- Offshore Technology, Oil & Gas Journal, Rigzone, Energy Voice
- BSEE.gov, HSE UK, CSB, PHMSA
- Reuters Energy, Bloomberg Energy

ตอบเป็นภาษาไทยในรูปแบบนี้:

## ข่าว MAE ที่พบ

### [ชื่อเหตุการณ์]
- **วันที่**: ...
- **สถานที่**: ...
- **ประเภท**: Fire / Explosion / Spill / Blowout
- **บริษัท**: ...
- **ผู้เสียชีวิต/บาดเจ็บ**: ...
- **สรุป**: อธิบาย 2-3 ประโยค
- **แหล่งข่าว**: ...

## สรุปภาพรวม
สรุปแนวโน้มที่พบ"""

            user_p = f"""ค้นหาข่าว MAE ในอุตสาหกรรม Oil & Gas:
- ภูมิภาค: {news_region}
- ประเภท: {news_type}
- ช่วงเวลา: {news_period}
- คำค้นเพิ่มเติม: {custom_q if custom_q else 'ไม่มี'}

ค้นหาและสรุปเหตุการณ์จริงที่พบ พร้อมแหล่งข่าว"""

            full_text = ""
            result_ph.markdown('<div class="result-box">กำลังดึงข้อมูล...</div>', unsafe_allow_html=True)

            # เรียก API พร้อม web_search tool
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system_p,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role":"user","content": user_p}]
            ) as stream:
                for event in stream:
                    etype = type(event).__name__
                    if etype == "ContentBlockStart":
                        blk = getattr(event, "content_block", None)
                        if blk and getattr(blk,"type","") == "tool_use" and getattr(blk,"name","") == "web_search":
                            status_ph.info("🌐 Claude กำลังค้นหาข่าวจากเว็บ...")
                    elif etype == "ContentBlockDelta":
                        d = getattr(event,"delta",None)
                        if d and hasattr(d,"text"):
                            full_text += d.text
                            result_ph.markdown(f'<div class="result-box">{full_text}▌</div>', unsafe_allow_html=True)

            status_ph.empty()
            result_ph.markdown(f'<div class="result-box">{full_text}</div>', unsafe_allow_html=True)

            if full_text:
                st.download_button(
                    "⬇️  บันทึกข่าว (.txt)",
                    data=full_text.encode("utf-8"),
                    file_name=f"mae_news_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )

        except anthropic.AuthenticationError:
            status_ph.empty()
            st.error("❌ API Key ไม่ถูกต้อง (AuthenticationError) — กรุณาตรวจสอบ Key ใน Streamlit Secrets")
            st.info("วิธีแก้: ไปที่ Streamlit Cloud → Settings → Secrets → ตรวจสอบ ANTHROPIC_API_KEY")
        except Exception as e:
            status_ph.empty()
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

    else:
        # แสดง tips
        st.markdown("""
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:8px">
        """, unsafe_allow_html=True)
        tips = [
            ("🔴","Offshore explosion 2025","ระเบิดแท่นขุดเจาะล่าสุด"),
            ("🌊","Oil spill global 2024","น้ำมันรั่วทั่วโลก"),
            ("💥","Refinery fire Asia","โรงกลั่น Asia"),
            ("⚡","Pipeline rupture Europe","ท่อแตก Europe"),
            ("🔥","LNG incident 2024","อุบัติเหตุ LNG"),
            ("🛢️","Well blowout offshore","Blowout offshore"),
        ]
        cols = st.columns(3)
        for i,(icon,eng,thai) in enumerate(tips):
            with cols[i%3]:
                st.markdown(f"""
                <div style="background:#F7F5F2;border:1px solid #E8E4DF;
                     padding:14px;margin-bottom:10px;">
                  <div style="font-size:20px;margin-bottom:6px">{icon}</div>
                  <div style="font-size:13px;font-weight:600;color:#0D0D0D">{thai}</div>
                  <div style="font-size:11px;color:#999;font-family:'DM Mono',monospace">{eng}</div>
                </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TAB 2 — Charts
# ──────────────────────────────────────────────
with tab_chart:
    st.markdown('<div class="section-header"><span class="section-label">Analytics</span><span class="section-title">ภาพรวมสถิติ MAE</span><span class="section-line"></span></div>', unsafe_allow_html=True)

    CHART_COLORS = ["#FF4B1F","#0D0D0D","#E8E4DF","#888","#CC2200"]

    if not filtered.empty:
        r1,r2 = st.columns(2)
        with r1:
            cc = filtered.groupby("country").size().reset_index(name="count").nlargest(10,"count")
            fig = px.bar(cc, x="count", y="country", orientation="h",
                         color_discrete_sequence=["#FF4B1F"])
            fig.update_layout(showlegend=False, height=300, plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(family="DM Sans"), margin=dict(l=0,r=0,t=20,b=0),
                              xaxis=dict(gridcolor="#F0EDE8"), yaxis=dict(autorange="reversed"),
                              title=dict(text="Top 10 ประเทศ",font=dict(size=13)))
            st.plotly_chart(fig, use_container_width=True)

        with r2:
            if "region" in filtered.columns:
                rc = filtered.groupby("region").size().reset_index(name="count")
                fig2 = px.pie(rc, values="count", names="region",
                              color_discrete_sequence=["#FF4B1F","#0D0D0D","#888","#E8E4DF","#CC2200"])
                fig2.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                                   font=dict(family="DM Sans"), margin=dict(l=0,r=0,t=20,b=0),
                                   title=dict(text="สัดส่วนตามภูมิภาค",font=dict(size=13)))
                fig2.update_traces(textinfo="percent+label")
                st.plotly_chart(fig2, use_container_width=True)

        yc = filtered.groupby("year").agg(events=("fatalities","count"),fatalities=("fatalities","sum")).reset_index()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=yc["year"], y=yc["events"], name="จำนวน Events",
                              marker_color="#E8E4DF", marker_line_color="#0D0D0D", marker_line_width=0.5))
        fig3.add_trace(go.Scatter(x=yc["year"], y=yc["fatalities"], name="ผู้เสียชีวิต",
                                  yaxis="y2", line=dict(color="#FF4B1F",width=2.5), mode="lines+markers",
                                  marker=dict(size=5,color="#FF4B1F")))
        fig3.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white",
                           font=dict(family="DM Sans"), margin=dict(l=0,r=0,t=30,b=0),
                           title=dict(text="แนวโน้มตามปี",font=dict(size=13)),
                           yaxis=dict(title="Events",gridcolor="#F0EDE8"),
                           yaxis2=dict(title="เสียชีวิต",overlaying="y",side="right"),
                           legend=dict(orientation="h",y=1.08),
                           xaxis=dict(gridcolor="#F0EDE8"))
        st.plotly_chart(fig3, use_container_width=True)

        ca = filtered.groupby("country").agg(events=("fatalities","count"),fatalities=("fatalities","sum")).reset_index()
        fig4 = px.choropleth(ca, locations="country", locationmode="country names",
            color="events", hover_name="country", hover_data={"fatalities":True},
            color_continuous_scale=["#F7F5F2","#FF9980","#FF4B1F","#CC2200","#800000"])
        fig4.update_layout(height=380, margin=dict(l=0,r=0,t=30,b=0),
                           paper_bgcolor="white", font=dict(family="DM Sans"),
                           title=dict(text="แผนที่ MAE ทั่วโลก",font=dict(size=13)),
                           geo=dict(bgcolor="white",lakecolor="#F7F5F2",landcolor="#F0EDE8",
                                    showframe=False,showcoastlines=True,coastlinecolor="#E8E4DF"))
        st.plotly_chart(fig4, use_container_width=True)

# ──────────────────────────────────────────────
# TAB 3 — รายการ
# ──────────────────────────────────────────────
with tab_table:
    st.markdown('<div class="section-header"><span class="section-label">Database</span><span class="section-title">รายการเหตุการณ์ทั้งหมด</span><span class="section-line"></span></div>', unsafe_allow_html=True)

    show = [c for c in ["year","name","operator","location","country","pipeline_type",
                          "fatalities","injuries","property_damage_usd","cause","source"]
            if c in filtered.columns]
    rnm = {"year":"ปี","name":"ชื่อเหตุการณ์","operator":"บริษัท","location":"สถานที่",
            "country":"ประเทศ","pipeline_type":"ประเภท","fatalities":"เสียชีวิต",
            "injuries":"บาดเจ็บ","property_damage_usd":"ความเสียหาย (USD)",
            "cause":"สาเหตุ","source":"แหล่งข้อมูล"}
    disp = filtered[show].rename(columns=rnm)
    sort_col = "ความเสียหาย (USD)" if "ความเสียหาย (USD)" in disp.columns else "เสียชีวิต"
    disp = disp.sort_values(sort_col, ascending=False)
    st.dataframe(disp, use_container_width=True, hide_index=True,
        column_config={
            "ความเสียหาย (USD)": st.column_config.NumberColumn(format="$%,.0f"),
            "เสียชีวิต": st.column_config.NumberColumn(format="%d คน"),
            "บาดเจ็บ": st.column_config.NumberColumn(format="%d คน"),
        })
    csv = disp.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️  ดาวน์โหลด CSV", data=csv, file_name="mae_data.csv", mime="text/csv")

# ──────────────────────────────────────────────
# TAB 4 — BSEE
# ──────────────────────────────────────────────
with tab_bsee:
    st.markdown('<div class="section-header"><span class="section-label">BSEE · bsee.gov</span><span class="section-title">Offshore Incident Trends — Gulf of Mexico</span><span class="section-line"></span></div>', unsafe_allow_html=True)

    bsee = pd.DataFrame(BSEE_ANNUAL_STATS)
    bsee = bsee[(bsee["year"]>=int(year_from))&(bsee["year"]<=int(year_to))]

    if not bsee.empty:
        r1,r2 = st.columns(2)
        with r1:
            fig_fi = go.Figure()
            fig_fi.add_trace(go.Bar(x=bsee["year"],y=bsee["fatalities"],name="เสียชีวิต",marker_color="#FF4B1F"))
            fig_fi.add_trace(go.Bar(x=bsee["year"],y=bsee["injuries"],name="บาดเจ็บ",marker_color="#E8E4DF",marker_line_color="#0D0D0D",marker_line_width=0.5))
            fig_fi.update_layout(barmode="group",height=260,plot_bgcolor="white",paper_bgcolor="white",
                                 font=dict(family="DM Sans"),margin=dict(l=0,r=0,t=30,b=0),
                                 title=dict(text="ผู้เสียชีวิต & บาดเจ็บ",font=dict(size=13)),
                                 legend=dict(orientation="h",y=1.1),xaxis=dict(gridcolor="#F0EDE8"),yaxis=dict(gridcolor="#F0EDE8"))
            st.plotly_chart(fig_fi, use_container_width=True)

        with r2:
            fig_fg = go.Figure()
            fig_fg.add_trace(go.Scatter(x=bsee["year"],y=bsee["fires"],name="ไฟไหม้",line=dict(color="#FF4B1F",width=2)))
            fig_fg.add_trace(go.Scatter(x=bsee["year"],y=bsee["gas_releases"],name="ก๊าซรั่ว",line=dict(color="#0D0D0D",width=2)))
            fig_fg.add_trace(go.Scatter(x=bsee["year"],y=bsee["spills"],name="Oil Spill",line=dict(color="#888",width=2,dash="dot")))
            fig_fg.update_layout(height=260,plot_bgcolor="white",paper_bgcolor="white",
                                 font=dict(family="DM Sans"),margin=dict(l=0,r=0,t=30,b=0),
                                 title=dict(text="ไฟ / ก๊าซรั่ว / Spill",font=dict(size=13)),
                                 legend=dict(orientation="h",y=1.1),xaxis=dict(gridcolor="#F0EDE8"),yaxis=dict(gridcolor="#F0EDE8"))
            st.plotly_chart(fig_fg, use_container_width=True)

        st.dataframe(bsee.sort_values("year",ascending=False).rename(columns={
            "year":"ปี","fatalities":"เสียชีวิต","injuries":"บาดเจ็บ",
            "fires":"ไฟไหม้","explosions":"ระเบิด","gas_releases":"ก๊าซรั่ว","spills":"Spills"
        }), use_container_width=True, hide_index=True)

        st.markdown('<a href="https://www.bsee.gov/stats-facts/offshore-incident-statistics" target="_blank" style="font-size:12px;color:#FF4B1F">🔗 ดูข้อมูลต้นฉบับ bsee.gov →</a>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TAB 5 — AI Report
# ──────────────────────────────────────────────
with tab_ai:
    st.markdown('<div class="section-header"><span class="section-label">AI Analysis</span><span class="section-title">Executive Report</span><span class="section-line"></span></div>', unsafe_allow_html=True)

    rstyle = st.selectbox("รูปแบบ Report", ["Executive Summary","Detailed Technical","Statistical Analysis"])

    sample = filtered.nlargest(50,"fatalities") if len(filtered)>50 else filtered
    lines = [
        f"- {r.get('name',r.get('operator','?'))} ({int(r.get('year',0))}, {r.get('location','?')}, {r.get('country','?')}): "
        f"{r.get('pipeline_type','?')}, {int(r.get('fatalities',0))} fatalities, "
        f"${r.get('property_damage_usd',0)/1e6:.0f}M damage, cause: {r.get('cause','?')}"
        for _,r in sample.iterrows()
    ]

    if st.button("🚀  สร้าง AI Report", type="primary", use_container_width=True):
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("AI กำลังวิเคราะห์..."):
                with client.messages.stream(
                    model="claude-sonnet-4-20250514", max_tokens=2000,
                    system="คุณคือผู้เชี่ยวชาญ HSE ใน Oil & Gas ตอบภาษาไทย แบบ Professional Report",
                    messages=[{"role":"user","content":
                        f"วิเคราะห์ข้อมูล MAE และสร้าง {rstyle}:\n\n"+"\n".join(lines)+
                        "\n\nรวม: Executive Summary, Key Trends, Root Causes, Worst Events, Recommendations"}]
                ) as stream:
                    resp = st.write_stream(stream.text_stream)
            st.download_button("⬇️  ดาวน์โหลด Report", data=resp.encode("utf-8"),
                               file_name="mae_ai_report.txt", mime="text/plain")
        except KeyError:
            st.error("❌ ไม่พบ ANTHROPIC_API_KEY ใน Secrets")
        except anthropic.AuthenticationError:
            st.error("❌ API Key ไม่ถูกต้อง — ตรวจสอบใน Streamlit Secrets")
        except Exception as e:
            st.error(f"❌ {str(e)}")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0">
  <div style="font-size:11px;color:#999;font-family:'DM Mono',monospace">
    MAE Intelligence Platform · Oil &amp; Gas HSE Analytics
  </div>
  <div>
    <span class="source-tag">BSEE</span>
    <span class="source-tag">PHMSA</span>
    <span class="source-tag">HSE UK</span>
    <span class="source-tag">CSB</span>
    <span class="source-tag">Claude AI</span>
  </div>
</div>
""", unsafe_allow_html=True)
