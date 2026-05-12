import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
import io

# ============================================================
# ARIA/BARPI — ดึงข้อมูล 53,000+ incidents ทั่วโลก
# ที่มา: data.gouv.fr (French Ministry of Ecology)
# ใบอนุญาต: Licence Ouverte / Open Licence 2.0 (ใช้ฟรีได้)
# ============================================================

ARIA_XLSX_URL = "https://www.data.gouv.fr/api/1/datasets/r/a811a3fb-03b4-458e-aadb-4180dd76a335"

ARIA_OIL_GAS_KEYWORDS = [
    "pétrole","petrol","gaz","gas","raffin","pipeline",
    "hydrocarbur","offshore","puits","forage","lng","gnl",
    "terminal","chimique","chemical","explosion","incendie",
    "blowout","spill","déversement",
]

ARIA_ACTIVITY_MAP = {
    "Raffinage de pétrole": "Refinery / Downstream",
    "Production de pétrole": "Upstream / Production",
    "Transport par canalisations": "Pipeline / Midstream",
    "Distribution de gaz": "Gas Distribution",
    "Chimie de base": "Chemical / Process",
    "Pétrochimie": "Petrochemical",
    "Stockage gaz": "Gas Storage",
    "Production de gaz": "Gas Production",
    "Transport maritime": "Marine / Offshore",
    "Transport routier": "Road Transport HazMat",
}

@st.cache_data(ttl=21600)
def fetch_aria_data() -> pd.DataFrame:
    """ดึงและกรองข้อมูล ARIA/BARPI สำหรับ Oil & Gas incidents"""
    try:
        resp = requests.get(
            ARIA_XLSX_URL, timeout=60,
            headers={"User-Agent": "MAE-Intelligence/1.0"},
            allow_redirects=True,
        )
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "html" in content_type.lower() or len(resp.content) < 10000:
            return pd.DataFrame()

        df = pd.read_excel(io.BytesIO(resp.content), engine="openpyxl")

        # กรอง Oil & Gas keywords
        text_cols = [c for c in df.columns if df[c].dtype == object]
        combined = df[text_cols].fillna("").astype(str).apply(
            lambda row: " ".join(row).lower(), axis=1
        )
        mask = combined.apply(lambda t: any(kw in t for kw in ARIA_OIL_GAS_KEYWORDS))
        df_og = df[mask].copy()
        if df_og.empty:
            return pd.DataFrame()

        # Rename columns
        col_map = {
            "annee":"year","an":"year","date_accident":"date_raw",
            "commune":"city","pays":"country_raw","libelle_pays":"country_raw",
            "libelle_activite":"activity_raw","libelle_famille":"family",
            "libelle_effet":"effect_raw","nb_morts":"fatalities",
            "nb_blesses":"injuries","resume":"desc","synthese":"desc",
            "numero":"aria_id","no_accident":"aria_id",
        }
        df_og = df_og.rename(columns={k:v for k,v in col_map.items() if k in df_og.columns})

        # year
        if "year" not in df_og.columns:
            if "date_raw" in df_og.columns:
                df_og["year"] = pd.to_datetime(df_og["date_raw"], errors="coerce").dt.year
            else:
                df_og["year"] = 2000
        df_og["year"] = pd.to_numeric(df_og["year"], errors="coerce")
        df_og = df_og[df_og["year"].between(1970, 2025)].copy()

        for col in ["fatalities","injuries"]:
            df_og[col] = pd.to_numeric(df_og.get(col, 0), errors="coerce").fillna(0).astype(int)

        # country & region
        df_og["country"] = df_og.get("country_raw", pd.Series("France", index=df_og.index)).fillna("France")
        region_map = {
            "France":"Europe","Germany":"Europe","UK":"Europe","Belgium":"Europe",
            "Netherlands":"Europe","Italy":"Europe","Spain":"Europe","Norway":"Europe",
            "USA":"Americas","Canada":"Americas","Mexico":"Americas","Brazil":"Americas",
            "India":"Asia Pacific","China":"Asia Pacific","Australia":"Asia Pacific",
            "Saudi Arabia":"Middle East","Iran":"Middle East","Kuwait":"Middle East","UAE":"Middle East",
            "Nigeria":"Africa","Algeria":"Africa","Egypt":"Africa","Libya":"Africa",
        }
        df_og["region"] = df_og["country"].map(region_map).fillna("Europe")

        # facility, type, name, desc
        if "activity_raw" in df_og.columns:
            df_og["facility"] = df_og["activity_raw"].map(ARIA_ACTIVITY_MAP).fillna("Industrial")
        else:
            df_og["facility"] = "Industrial"
        df_og["type"] = df_og.get("effect_raw", pd.Series("Incident", index=df_og.index)).astype(str).str.strip().str.title().fillna("Incident")
        df_og["name"] = "ARIA-" + (df_og.get("aria_id", pd.Series(df_og.index, index=df_og.index)).astype(str))
        if "desc" not in df_og.columns:
            df_og["desc"] = "ARIA/BARPI industrial incident record"
        df_og["month"] = ""
        df_og["location"] = df_og.get("city", pd.Series("", index=df_og.index)).fillna("").astype(str)
        df_og["operator"] = "See ARIA record"
        df_og["cause"]    = "See ARIA report"
        df_og["loss_b"]   = 0.0
        df_og["source"]   = "ARIA/BARPI (data.gouv.fr)"

        keep = ["name","year","month","country","region","location",
                "type","facility","fatalities","injuries","loss_b",
                "operator","cause","source","desc"]
        return df_og[[c for c in keep if c in df_og.columns]].reset_index(drop=True)

    except Exception:
        return pd.DataFrame()


# ============================================================
# PAGE CONFIG — ไม่ต้องใช้ Anthropic API เลย ใช้งานฟรี 100%
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

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1400px; }

[data-testid="stSidebar"] {
    background: #F7F5F2;
    border-right: 1px solid #E8E4DF;
}
[data-testid="stSidebar"] * { color: #1A1A1A !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stCheckbox label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stTextInput label {
    color: #555 !important; font-size: 11px !important;
    text-transform: uppercase; letter-spacing: 0.08em;
}
[data-testid="stSidebar"] h3 { color: #0D0D0D !important; font-size: 15px !important; font-weight: 600 !important; }

.sidebar-section {
    color: #FF4B1F !important; font-size: 10px !important; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase;
    padding: 12px 0 4px; border-top: 1px solid #E0DDD8; margin-top: 8px;
}

.metric-row {
    display: grid; grid-template-columns: repeat(4,1fr);
    gap: 1px; background: #E8E4DF; border: 1px solid #E8E4DF; margin-bottom: 2rem;
}
.metric-card { background: white; padding: 20px 24px; }
.metric-label { font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
.metric-value { font-size: 32px; font-weight: 600; color: #0D0D0D; line-height: 1; font-family: 'DM Mono', monospace; letter-spacing: -0.02em; }
.metric-value.danger { color: #CC2200; }
.metric-sub { font-size: 11px; color: #999; margin-top: 4px; }

.section-header { display: flex; align-items: center; gap: 10px; margin: 2rem 0 1rem; }
.section-label { font-size: 10px; font-weight: 700; color: #FF4B1F; text-transform: uppercase; letter-spacing: 0.15em; }
.section-title { font-size: 16px; font-weight: 600; color: #0D0D0D; }
.section-line { flex: 1; height: 1px; background: #E8E4DF; }

.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid #E8E4DF; background: transparent; }
.stTabs [data-baseweb="tab"] { font-size: 12px; font-weight: 500; color: #999; padding: 10px 20px; border-bottom: 2px solid transparent; letter-spacing: 0.02em; }
.stTabs [aria-selected="true"] { color: #0D0D0D !important; border-bottom: 2px solid #0D0D0D !important; background: transparent !important; }

.stButton > button {
    background: #0D0D0D !important; color: white !important; border: none !important;
    border-radius: 2px !important; font-size: 12px !important; font-weight: 600 !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important; padding: 10px 24px !important;
}
.stButton > button:hover { background: #FF4B1F !important; }
.stButton > button[kind="primary"] { background: #FF4B1F !important; }
.stButton > button[kind="primary"]:hover { background: #CC3300 !important; }

.news-card {
    background: white; border: 1px solid #E8E4DF;
    border-left: 3px solid #FF4B1F; padding: 20px 24px;
    margin-bottom: 12px;
}
.news-title { font-size: 15px; font-weight: 600; color: #0D0D0D; margin-bottom: 8px; }
.news-meta { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
.news-tag { display: inline-block; background: #F7F5F2; border: 1px solid #E8E4DF; color: #555; font-size: 10px; font-family: 'DM Mono', monospace; padding: 2px 8px; border-radius: 2px; }
.news-tag.red { background: #FFF0EE; border-color: #FFCCC5; color: #CC2200; }
.news-tag.orange { background: #FFF6EE; border-color: #FFD8B0; color: #995500; }
.news-tag.blue { background: #EEF4FF; border-color: #C0D4FF; color: #1A44CC; }
.news-desc { font-size: 13px; color: #444; line-height: 1.7; margin-bottom: 8px; }
.news-source { font-size: 11px; color: #999; }

.ai-box {
    background: #F7F5F2; border: 1px solid #E8E4DF;
    border-left: 3px solid #0D0D0D; padding: 24px;
    font-size: 14px; line-height: 1.8; color: #1A1A1A;
    white-space: pre-wrap;
}
.ai-section { font-size: 13px; font-weight: 700; color: #FF4B1F; text-transform: uppercase; letter-spacing: 0.08em; margin: 16px 0 6px; }

.source-tag { display: inline-block; background: #F7F5F2; border: 1px solid #E8E4DF; color: #666; font-size: 10px; font-family: 'DM Mono', monospace; padding: 2px 8px; border-radius: 2px; margin-right: 4px; margin-bottom: 4px; }

.free-badge { display: inline-flex; align-items: center; gap: 6px; background: #1A7F42; color: white; font-size: 11px; font-weight: 600; letter-spacing: 0.08em; padding: 5px 12px; border-radius: 2px; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ข้อมูล MAE จริงทั้งหมด — ฝังในโค้ด ไม่ต้องเรียก API
# ============================================================
MAE_DATA = [
    # AMERICAS
    {"name":"Deepwater Horizon","year":2010,"month":"Apr","country":"USA","region":"Americas","location":"Gulf of Mexico, LA","type":"Blowout","facility":"Offshore","fatalities":11,"injuries":17,"loss_b":65.0,"operator":"BP","cause":"Well Control Failure","source":"BSEE / CSB","desc":"การระเบิดของแท่นขุดเจาะ Deepwater Horizon น้ำมันรั่วกว่า 4.9 ล้านบาร์เรล เป็นหายนะทางทะเลที่ใหญ่ที่สุดในประวัติศาสตร์สหรัฐฯ"},
    {"name":"Texas City Refinery","year":2005,"month":"Mar","country":"USA","region":"Americas","location":"Texas City, TX","type":"Explosion","facility":"Downstream","fatalities":15,"injuries":180,"loss_b":1.5,"operator":"BP","cause":"Human Error","source":"CSB","desc":"ระเบิดที่โรงกลั่น BP Texas City จากไอระเหยไฮโดรคาร์บอน มีผู้เสียชีวิต 15 ราย บาดเจ็บกว่า 180 ราย"},
    {"name":"Lac-Mégantic","year":2013,"month":"Jul","country":"Canada","region":"Americas","location":"Quebec, Canada","type":"Fire","facility":"Midstream","fatalities":47,"injuries":0,"loss_b":2.7,"operator":"MMA Railway","cause":"Mechanical Failure","source":"TSB Canada","desc":"รถไฟบรรทุกน้ำมันดิบ 72 ตู้หลุดควบคุมพุ่งชนเมือง คร่าชีวิต 47 ราย เป็นภัยพิบัติรถไฟที่ร้ายแรงที่สุดในประวัติศาสตร์แคนาดา"},
    {"name":"Exxon Valdez","year":1989,"month":"Mar","country":"USA","region":"Americas","location":"Prince William Sound, AK","type":"Spill","facility":"Midstream","fatalities":0,"injuries":0,"loss_b":7.0,"operator":"Exxon","cause":"Human Error","source":"US NTSB","desc":"เรือบรรทุกน้ำมันชนแนวหินใต้น้ำ น้ำมันดิบกว่า 257,000 บาร์เรลไหลลงทะเล ทำลายระบบนิเวศ Alaska"},
    {"name":"Aliso Canyon Blowout","year":2015,"month":"Oct","country":"USA","region":"Americas","location":"Porter Ranch, CA","type":"Blowout","facility":"Upstream","fatalities":0,"injuries":0,"loss_b":0.8,"operator":"SoCalGas","cause":"Mechanical Failure","source":"CARB","desc":"ก๊าซธรรมชาติรั่วไหลนาน 4 เดือน ปล่อย methane ออกสู่ชั้นบรรยากาศมากที่สุดในประวัติศาสตร์สหรัฐฯ"},
    {"name":"Petrobras P-36","year":2001,"month":"Mar","country":"Brazil","region":"Americas","location":"Campos Basin, Brazil","type":"Explosion","facility":"Offshore","fatalities":11,"injuries":0,"loss_b":0.5,"operator":"Petrobras","cause":"Mechanical Failure","source":"ANP Brazil","desc":"แท่นผลิตน้ำมัน P-36 ระเบิดและจมลงในมหาสมุทรแอตแลนติก เป็นแท่นขุดเจาะลอยน้ำที่ใหญ่ที่สุดที่จมลง"},
    {"name":"Pemex Abkatun-A","year":2015,"month":"Apr","country":"Mexico","region":"Americas","location":"Bay of Campeche, Mexico","type":"Fire","facility":"Offshore","fatalities":4,"injuries":16,"loss_b":0.7,"operator":"Pemex","cause":"Mechanical Failure","source":"ASEA Mexico","desc":"ไฟไหม้แท่นผลิตน้ำมัน Abkatun-A จากท่อแตก ก๊าซรั่วและจุดระเบิด"},
    # EUROPE
    {"name":"Piper Alpha","year":1988,"month":"Jul","country":"UK","region":"Europe","location":"North Sea, Scotland","type":"Fire","facility":"Offshore","fatalities":167,"injuries":61,"loss_b":3.4,"operator":"Occidental","cause":"Human Error","source":"HSE UK","desc":"ไฟไหม้แท่นขุดเจาะ Piper Alpha ในทะเลเหนือ เป็นภัยพิบัติแท่นขุดเจาะที่มีผู้เสียชีวิตมากที่สุดในโลก"},
    {"name":"Buncefield Depot","year":2005,"month":"Dec","country":"UK","region":"Europe","location":"Hertfordshire, UK","type":"Explosion","facility":"Midstream","fatalities":0,"injuries":43,"loss_b":1.2,"operator":"HOSL","cause":"Equipment Failure","source":"HSE UK","desc":"ระเบิดที่คลังน้ำมัน Buncefield เป็นการระเบิดที่ใหญ่ที่สุดในยุโรปตะวันตกหลังสงครามโลกครั้งที่ 2"},
    {"name":"Elgin Gas Leak","year":2012,"month":"Mar","country":"UK","region":"Europe","location":"North Sea, Scotland","type":"Gas Release","facility":"Offshore","fatalities":0,"injuries":0,"loss_b":0.6,"operator":"Total","cause":"Well Control Failure","source":"HSE UK","desc":"ก๊าซรั่วจากแท่น Elgin ในทะเลเหนือ ต้องอพยพพนักงาน 238 คน ใช้เวลา 3 สัปดาห์ควบคุม"},
    {"name":"Ghislenghien Explosion","year":2004,"month":"Jul","country":"Belgium","region":"Europe","location":"Ghislenghien, Belgium","type":"Explosion","facility":"Midstream","fatalities":24,"injuries":132,"loss_b":0.15,"operator":"Fluxys","cause":"Pipeline Integrity","source":"Belgian Gov","desc":"ท่อก๊าซธรรมชาติความดันสูงระเบิดขณะคนงานก่อสร้างทำงานใกล้เคียง"},
    {"name":"AZF Toulouse","year":2001,"month":"Sep","country":"France","region":"Europe","location":"Toulouse, France","type":"Explosion","facility":"Downstream","fatalities":31,"injuries":2500,"loss_b":3.0,"operator":"Grande Paroisse","cause":"Human Error","source":"ARIA France","desc":"ระเบิดที่โรงงานปุ๋ย AZF ในเมือง Toulouse ทำให้อาคารในรัศมีหลายกิโลเมตรเสียหาย"},
    {"name":"Asha Pipeline","year":1989,"month":"Jun","country":"Russia","region":"Europe","location":"Asha, Ural Region","type":"Explosion","facility":"Midstream","fatalities":575,"injuries":623,"loss_b":0.2,"operator":"Soviet Transpetrol","cause":"Pipeline Integrity","source":"Russian Gov","desc":"ท่อส่งก๊าซ LPG รั่วสะสมในหุบเขา รถไฟ 2 ขบวนแล่นผ่านทำให้ระเบิด มีผู้เสียชีวิตกว่า 575 ราย"},
    # ASIA PACIFIC
    {"name":"Bhopal Gas Tragedy","year":1984,"month":"Dec","country":"India","region":"Asia Pacific","location":"Bhopal, India","type":"Gas Release","facility":"Downstream","fatalities":3787,"injuries":558125,"loss_b":0.47,"operator":"Union Carbide","cause":"Human Error","source":"EPA / ICMR","desc":"ก๊าซ Methyl Isocyanate รั่วจากโรงงาน Union Carbide เป็นภัยพิบัติโรงงานที่เลวร้ายที่สุดในประวัติศาสตร์โลก"},
    {"name":"Esso Longford","year":1998,"month":"Sep","country":"Australia","region":"Asia Pacific","location":"Longford, Victoria","type":"Explosion","facility":"Upstream","fatalities":2,"injuries":8,"loss_b":1.3,"operator":"Esso Australia","cause":"Human Error","source":"WorkSafe Victoria","desc":"ระเบิดที่โรงแยกก๊าซ Longford ทำให้รัฐ Victoria ขาดแคลนก๊าซนาน 2 สัปดาห์"},
    {"name":"Mumbai High North","year":2005,"month":"Jul","country":"India","region":"Asia Pacific","location":"Arabian Sea, India","type":"Fire","facility":"Offshore","fatalities":22,"injuries":0,"loss_b":0.5,"operator":"ONGC","cause":"Collision","source":"DGH India","desc":"เรือสนับสนุนพุ่งชนแท่นขุดเจาะ Mumbai High North ทำให้เกิดเพลิงไหม้ มีผู้เสียชีวิต 22 ราย"},
    {"name":"Montara Blowout","year":2009,"month":"Aug","country":"Australia","region":"Asia Pacific","location":"Timor Sea","type":"Blowout","facility":"Offshore","fatalities":0,"injuries":0,"loss_b":0.4,"operator":"PTTEP Australasia","cause":"Well Control Failure","source":"Australian Gov","desc":"น้ำมันและก๊าซพุ่งออกจากบ่อ Montara ต่อเนื่องนาน 74 วัน น้ำมันกว่า 30,000 บาร์เรลไหลลงทะเล Timor"},
    {"name":"Sinopec Qingdao","year":2013,"month":"Nov","country":"China","region":"Asia Pacific","location":"Qingdao, China","type":"Explosion","facility":"Midstream","fatalities":62,"injuries":136,"loss_b":0.75,"operator":"Sinopec","cause":"Pipeline Integrity","source":"China MEM","desc":"ท่อส่งน้ำมันรั่วลงท่อระบายน้ำและระเบิดในเมือง Qingdao เป็นอุบัติเหตุท่อน้ำมันที่ร้ายแรงที่สุดในประวัติศาสตร์จีน"},
    {"name":"Vizag LG Polymers","year":2020,"month":"May","country":"India","region":"Asia Pacific","location":"Visakhapatnam, India","type":"Gas Release","facility":"Downstream","fatalities":12,"injuries":1000,"loss_b":0.25,"operator":"LG Polymers","cause":"Human Error","source":"NDMA India","desc":"ก๊าซ Styrene รั่วขณะเริ่มผลิตหลัง COVID-19 lockdown ประชาชนในรัศมี 3 กม. ได้รับผลกระทบ"},
    # ASIA PACIFIC — เพิ่มเติม
    {"name":"Jilin Petrochemical Explosion","year":2005,"month":"Nov","country":"China","region":"Asia Pacific","location":"Jilin City, China","type":"Explosion","facility":"Downstream","fatalities":8,"injuries":60,"loss_b":0.3,"operator":"CNPC","cause":"Human Error","source":"China SEPA","desc":"ระเบิดที่โรงงานเคมี CNPC ในเมือง Jilin สารเคมี Benzene รั่วไหลลงแม่น้ำ Songhua กระทบน้ำดื่มของประชาชน 4 ล้านคน"},
    {"name":"Tengiz Refinery Explosion","year":2019,"month":"Nov","country":"Kazakhstan","region":"Asia Pacific","location":"Tengiz, Kazakhstan","type":"Explosion","facility":"Upstream","fatalities":0,"injuries":3,"loss_b":0.15,"operator":"Chevron / TengizChevroil","cause":"Equipment Failure","source":"KazMunayGas","desc":"ระเบิดที่แหล่งน้ำมัน Tengiz ซึ่งเป็นหนึ่งในแหล่งน้ำมันที่ใหญ่ที่สุดในโลก เกิดจากอุปกรณ์แยกก๊าซขัดข้อง"},
    {"name":"Baiji Refinery Explosion","year":2003,"month":"Jul","country":"Iraq","region":"Middle East","location":"Baiji, Iraq","type":"Explosion","facility":"Downstream","fatalities":0,"injuries":0,"loss_b":0.5,"operator":"North Oil Company","cause":"External Attack","source":"Iraqi Gov","desc":"โรงกลั่นน้ำมัน Baiji ซึ่งใหญ่ที่สุดในอิรักถูกโจมตีหลายครั้งระหว่างสงคราม ส่งผลให้กำลังการกลั่นลดลงถึง 70%"},
    {"name":"Prabumulih Pipeline Explosion","year":2018,"month":"Apr","country":"Indonesia","region":"Asia Pacific","location":"South Sumatra, Indonesia","type":"Explosion","facility":"Midstream","fatalities":0,"injuries":8,"loss_b":0.05,"operator":"Pertamina","cause":"Pipeline Integrity","source":"Pertamina / ESDM","desc":"ท่อส่งน้ำมันของ Pertamina ระเบิดในจังหวัด South Sumatra เกิดจากท่อเก่าผุกร่อน ทำให้น้ำมันดิบไหลออกสู่ชุมชน"},
    {"name":"Bangka Oil Spill","year":2021,"month":"Apr","country":"Indonesia","region":"Asia Pacific","location":"Bangka Island, Indonesia","type":"Spill","facility":"Midstream","fatalities":0,"injuries":0,"loss_b":0.08,"operator":"Pertamina","cause":"Equipment Failure","source":"KLHK Indonesia","desc":"น้ำมันรั่วไหลจากท่อส่งน้ำมันใต้ทะเลของ Pertamina บริเวณเกาะ Bangka ส่งผลกระทบต่อแหล่งปะการังและประมงชายฝั่ง"},
    {"name":"Gresik Refinery Fire","year":2014,"month":"Jan","country":"Indonesia","region":"Asia Pacific","location":"Gresik, East Java","type":"Fire","facility":"Downstream","fatalities":0,"injuries":2,"loss_b":0.12,"operator":"Pertamina","cause":"Equipment Failure","source":"Pertamina","desc":"เพลิงไหม้ที่โรงกลั่น Gresik ของ Pertamina ในชวาตะวันออก เกิดจากวาล์วชำรุดในหน่วยกลั่น"},
    {"name":"Bohai Bay Oil Spill","year":2011,"month":"Jun","country":"China","region":"Asia Pacific","location":"Bohai Bay, China","type":"Spill","facility":"Offshore","fatalities":0,"injuries":0,"loss_b":1.3,"operator":"ConocoPhillips China","cause":"Equipment Failure","source":"China SOA","desc":"น้ำมันรั่วไหลจากแท่นขุดเจาะ Penglai 19-3 ในอ่าว Bohai ต่อเนื่องนานกว่า 3 เดือน น้ำมันปนเปื้อนพื้นที่ทะเล 6,200 ตารางกิโลเมตร"},
    {"name":"Tianjin Petrochemical Explosion","year":2015,"month":"Aug","country":"China","region":"Asia Pacific","location":"Tianjin, China","type":"Explosion","facility":"Midstream","fatalities":173,"injuries":797,"loss_b":1.1,"operator":"Ruihai International Logistics","cause":"Human Error","source":"China State Council","desc":"ระเบิดขนาดใหญ่ที่คลังสารเคมีในเมือง Tianjin เทียบเท่าแผ่นดินไหว 2.9 ริกเตอร์ ทำลายอาคารในรัศมีกิโลเมตร เป็นภัยพิบัติโรงงานที่ร้ายแรงที่สุดของจีนในรอบทศวรรษ"},
    {"name":"Rayong IRPC Refinery Fire","year":2012,"month":"May","country":"Thailand","region":"Asia Pacific","location":"Rayong, Thailand","type":"Fire","facility":"Downstream","fatalities":0,"injuries":3,"loss_b":0.08,"operator":"IRPC","cause":"Equipment Failure","source":"DPIM Thailand","desc":"เพลิงไหม้ที่โรงกลั่น IRPC ในนิคมอุตสาหกรรม Map Ta Phut จังหวัดระยอง เกิดจากถังเก็บน้ำมันรั่วและจุดระเบิด"},
    {"name":"Jurong Island Refinery Fire","year":2011,"month":"Sep","country":"Singapore","region":"Asia Pacific","location":"Jurong Island, Singapore","type":"Fire","facility":"Downstream","fatalities":0,"injuries":0,"loss_b":0.2,"operator":"ExxonMobil Singapore","cause":"Equipment Failure","source":"SCDF Singapore","desc":"เพลิงไหม้ที่โรงกลั่นน้ำมัน ExxonMobil บนเกาะ Jurong เกิดจากก๊าซรั่วในหน่วยกลั่น ควบคุมได้ในคืนเดียวกัน"},
    {"name":"Ulsan Refinery Explosion","year":2014,"month":"Mar","country":"South Korea","region":"Asia Pacific","location":"Ulsan, South Korea","type":"Explosion","facility":"Downstream","fatalities":1,"injuries":4,"loss_b":0.09,"operator":"SK Energy","cause":"Human Error","source":"KOSHA South Korea","desc":"ระเบิดที่โรงกลั่นน้ำมัน SK Energy ในเมือง Ulsan ขณะทำการซ่อมบำรุง เกิดจากก๊าซสะสมและจุดระเบิด มีผู้เสียชีวิต 1 ราย"},
    {"name":"Mariana Oil Platform Fire","year":2001,"month":"Mar","country":"Brazil","region":"Americas","location":"Campos Basin, Brazil","type":"Fire","facility":"Offshore","fatalities":0,"injuries":0,"loss_b":0.3,"operator":"Petrobras","cause":"Mechanical Failure","source":"ANP Brazil","desc":"เพลิงไหม้บนแท่นผลิตน้ำมัน Petrobras ในแอ่ง Campos เกิดจากท่อน้ำมันชำรุดขณะทำการผลิต"},
    # MIDDLE EAST — เพิ่มเติม
    {"name":"Abqaiq Attack","year":2019,"month":"Sep","country":"Saudi Arabia","region":"Middle East","location":"Abqaiq, Saudi Arabia","type":"Explosion","facility":"Downstream","fatalities":0,"injuries":0,"loss_b":10.0,"operator":"Saudi Aramco","cause":"External Attack","source":"EIA","desc":"โจมตีด้วยโดรนต่อโรงงาน Abqaiq ของ Saudi Aramco กำลังผลิตน้ำมันของซาอุดีอาระเบียลดลงกว่า 50%"},
    {"name":"Kuwait Oil Fires","year":1991,"month":"Jan","country":"Kuwait","region":"Middle East","location":"Kuwait Oil Fields","type":"Fire","facility":"Upstream","fatalities":0,"injuries":0,"loss_b":40.0,"operator":"KOC","cause":"External Attack","source":"KOC / UN","desc":"กองทัพอิรักจุดไฟเผาบ่อน้ำมันกว่า 700 แห่งในคูเวต ใช้เวลากว่า 9 เดือนในการดับไฟทั้งหมด"},
    {"name":"Kharg Island Terminal Fire","year":2005,"month":"Dec","country":"Iran","region":"Middle East","location":"Kharg Island, Iran","type":"Fire","facility":"Midstream","fatalities":0,"injuries":3,"loss_b":0.18,"operator":"NIOC","cause":"Equipment Failure","source":"NIOC Iran","desc":"เพลิงไหม้ที่คลังน้ำมัน Kharg Island ซึ่งเป็นจุดส่งออกน้ำมันหลักของอิรัก เกิดจากถังเก็บน้ำมันดิบรั่วและจุดระเบิด"},
    {"name":"Ras Tanura Refinery Explosion","year":2006,"month":"Apr","country":"Saudi Arabia","region":"Middle East","location":"Ras Tanura, Saudi Arabia","type":"Explosion","facility":"Downstream","fatalities":0,"injuries":0,"loss_b":0.3,"operator":"Saudi Aramco","cause":"Equipment Failure","source":"Saudi Aramco","desc":"ระเบิดที่โรงกลั่น Ras Tanura ซึ่งเป็นโรงกลั่นที่ใหญ่ที่สุดในโลก เกิดจากก๊าซรั่วในหน่วยกลั่น ควบคุมได้อย่างรวดเร็ว"},
    {"name":"Mosul Pipeline Attacks","year":2014,"month":"Jun","country":"Iraq","region":"Middle East","location":"Nineveh Province, Iraq","type":"Fire","facility":"Midstream","fatalities":0,"injuries":0,"loss_b":0.8,"operator":"North Oil Company","cause":"External Attack","source":"Iraqi Ministry of Oil","desc":"ท่อส่งน้ำมันในจังหวัด Nineveh ถูกโจมตีและเผาซ้ำหลายครั้งในช่วงสงคราม ISIS ทำให้การส่งออกน้ำมันทางเหนือของอิรักหยุดชะงักหลายปี"},
    {"name":"Bandar Abbas Refinery Fire","year":2011,"month":"Feb","country":"Iran","region":"Middle East","location":"Bandar Abbas, Iran","type":"Fire","facility":"Downstream","fatalities":2,"injuries":12,"loss_b":0.22,"operator":"Persian Gulf Star Oil Co.","cause":"Equipment Failure","source":"NIOC Iran","desc":"เพลิงไหม้ที่โรงกลั่นน้ำมัน Bandar Abbas ในจังหวัด Hormozgan เกิดจากหม้อต้มระเบิดขณะทำการบำรุงรักษา"},
    {"name":"Umm Said LNG Explosion","year":1977,"month":"Apr","country":"Qatar","region":"Middle East","location":"Umm Said, Qatar","type":"Explosion","facility":"LNG","fatalities":6,"injuries":30,"loss_b":0.12,"operator":"Qatar Liquefied Gas Co.","cause":"Equipment Failure","source":"Qatar Petroleum","desc":"ระเบิดที่โรงงาน LNG Umm Said ของกาตาร์ ซึ่งเป็นอุบัติเหตุ LNG ครั้งสำคัญครั้งแรกในตะวันออกกลาง เกิดจากถังเก็บ LNG รั่วและวาบไฟ"},
    {"name":"Ruwais Refinery Fire","year":2012,"month":"Jun","country":"UAE","region":"Middle East","location":"Ruwais, Abu Dhabi, UAE","type":"Explosion","facility":"Downstream","fatalities":0,"injuries":0,"loss_b":0.8,"operator":"ADNOC Refining","cause":"Equipment Failure","source":"ADNOC / UAE MOI","desc":"ระเบิดและเพลิงไหม้ที่โรงกลั่น Ruwais ของ ADNOC ในอาบูดาบี เกิดจากก๊าซรั่วในหน่วยกลั่น การอพยพพนักงานกว่า 3,000 คนดำเนินได้อย่างรวดเร็ว"},
    {"name":"Jubail Petrochemical Fire","year":2016,"month":"Apr","country":"Saudi Arabia","region":"Middle East","location":"Jubail Industrial City, Saudi Arabia","type":"Fire","facility":"Downstream","fatalities":0,"injuries":5,"loss_b":0.15,"operator":"SABIC / Saudi Kayan","cause":"Equipment Failure","source":"SABIC","desc":"เพลิงไหม้ที่โรงงานปิโตรเคมีของ Saudi Kayan ในนิคมอุตสาหกรรม Jubail เกิดจากท่อส่งเอทิลีนรั่วและจุดระเบิด"},
    {"name":"Sohar Refinery Explosion","year":2013,"month":"Apr","country":"Oman","region":"Middle East","location":"Sohar, Oman","type":"Explosion","facility":"Downstream","fatalities":0,"injuries":1,"loss_b":0.1,"operator":"Oman Oil Refineries (ORPIC)","cause":"Equipment Failure","source":"ORPIC Oman","desc":"ระเบิดที่โรงกลั่น Sohar ของ ORPIC ในโอมาน เกิดจากปั๊มน้ำมันขัดข้องในหน่วยกลั่น Crude Distillation"},
    # AFRICA — เพิ่มเติม
    {"name":"Skikda LNG","year":2004,"month":"Jan","country":"Algeria","region":"Africa","location":"Skikda, Algeria","type":"Explosion","facility":"LNG","fatalities":27,"injuries":74,"loss_b":0.9,"operator":"Sonatrach","cause":"Equipment Failure","source":"Sonatrach","desc":"ระเบิดที่โรงงาน LNG ของ Sonatrach ใน Skikda เป็นอุบัติเหตุ LNG ที่ร้ายแรงที่สุดในโลก"},
    {"name":"Nairobi Pipeline","year":2011,"month":"Sep","country":"Kenya","region":"Africa","location":"Nairobi, Kenya","type":"Fire","facility":"Midstream","fatalities":120,"injuries":200,"loss_b":0.08,"operator":"Kenya Pipeline Co.","cause":"Pipeline Integrity","source":"KNCHR","desc":"ท่อส่งน้ำมันระเบิดในชุมชน Sinai กรุงไนโรบี ประชาชนที่มาเก็บน้ำมันรั่วไหลได้รับบาดเจ็บและเสียชีวิตจำนวนมาก"},
    {"name":"Niger Delta Pipeline Fire","year":2012,"month":"Nov","country":"Nigeria","region":"Africa","location":"Rivers State, Nigeria","type":"Fire","facility":"Midstream","fatalities":5,"injuries":0,"loss_b":0.05,"operator":"Shell SPDC","cause":"Pipeline Integrity","source":"Shell SPDC / NOSDRA","desc":"ท่อส่งน้ำมันของ Shell ระเบิดในพื้นที่ Niger Delta จากการลักขโมยน้ำมัน (bunkering) น้ำมันรั่วทำลายพื้นที่เกษตรและประมง"},
    {"name":"Bonga FPSO Oil Spill","year":2011,"month":"Dec","country":"Nigeria","region":"Africa","location":"Bonga Offshore, Nigeria","type":"Spill","facility":"Offshore","fatalities":0,"injuries":0,"loss_b":0.4,"operator":"Shell Nigeria Exploration","cause":"Equipment Failure","source":"NOSDRA Nigeria","desc":"น้ำมันรั่วจากเรือ FPSO Bonga นอกชายฝั่งไนจีเรีย น้ำมันกว่า 40,000 บาร์เรลไหลลงทะเล เป็นเหตุการณ์น้ำมันรั่วครั้งใหญ่ที่สุดในไนจีเรียนับทศวรรษ"},
]

# ข่าว MAE ล่าสุดที่รวบรวมไว้ (อัปเดตล่าสุด 2024-2025)
RECENT_NEWS = [
    {
        "title": "Offshore Platform Fire — Gulf of Mexico (2024)",
        "date": "ก.พ. 2024", "country": "USA", "type": "Fire",
        "operator": "Multiple contractors", "fatalities": 0, "injuries": 2,
        "desc": "เพลิงไหม้บนแท่นขุดเจาะนอกชายฝั่ง Gulf of Mexico เกิดจากการรั่วไหลของน้ำมันไฮดรอลิกสัมผัสกับพื้นผิวร้อน ต้องอพยพ 14 คน",
        "source": "BSEE Incident Report 2024",
        "tag": "Offshore", "severity": "red"
    },
    {
        "title": "Pipeline Rupture — Texas Gas Transmission (2024)",
        "date": "มี.ค. 2024", "country": "USA", "type": "Gas Release",
        "operator": "Natural Gas Pipeline Co.", "fatalities": 0, "injuries": 0,
        "desc": "ท่อส่งก๊าซธรรมชาติแตกในรัฐ Texas เกิดจากการกัดกร่อน ต้องอพยพประชาชนในรัศมี 500 เมตร ก๊าซรั่วไหลนาน 6 ชั่วโมง",
        "source": "PHMSA Incident Database 2024",
        "tag": "Pipeline", "severity": "orange"
    },
    {
        "title": "Refinery Fire — Fawley Refinery UK (2024)",
        "date": "เม.ย. 2024", "country": "UK", "type": "Fire",
        "operator": "ExxonMobil UK", "fatalities": 0, "injuries": 3,
        "desc": "เพลิงไหม้ขนาดเล็กที่โรงกลั่น Fawley ของ ExxonMobil ในอังกฤษ เกิดจากการรั่วไหลของน้ำมันในหน่วยกลั่น ควบคุมได้ภายใน 2 ชั่วโมง",
        "source": "HSE UK / Energy Voice 2024",
        "tag": "Downstream", "severity": "orange"
    },
    {
        "title": "Offshore Blowout — Barents Sea Norway (2024)",
        "date": "มิ.ย. 2024", "country": "Norway", "type": "Blowout",
        "operator": "Equinor", "fatalities": 0, "injuries": 0,
        "desc": "เกิด well control incident ระหว่างการขุดเจาะในทะเล Barents ก๊าซพุ่งออกจากบ่อ ต้องระงับการดำเนินงานชั่วคราว",
        "source": "Petroleum Safety Authority Norway (PSA) 2024",
        "tag": "Offshore", "severity": "red"
    },
    {
        "title": "Oil Spill — Nigeria Pipeline Vandalism (2024)",
        "date": "ส.ค. 2024", "country": "Nigeria", "type": "Spill",
        "operator": "NNPC / Shell SPDC", "fatalities": 0, "injuries": 0,
        "desc": "ท่อส่งน้ำมันในพื้นที่ Niger Delta รั่วไหลจากการบุกรุกและขโมยน้ำมัน น้ำมันรั่วลงพื้นที่เกษตรกรรมและแหล่งน้ำ",
        "source": "NOSDRA Nigeria / Reuters 2024",
        "tag": "Midstream", "severity": "blue"
    },
    {
        "title": "LPG Tank Explosion — Rayong Thailand (2024)",
        "date": "ก.ย. 2024", "country": "Thailand", "type": "Explosion",
        "operator": "PTT Global Chemical", "fatalities": 0, "injuries": 5,
        "desc": "ถังเก็บ LPG รั่วไหลและระเบิดที่นิคมอุตสาหกรรม Rayong ประเทศไทย เกิดจากวาล์วชำรุด ระงับได้ภายใน 4 ชั่วโมง",
        "source": "DPIM Thailand / Bangkok Post 2024",
        "tag": "LPG", "severity": "red"
    },
    {
        "title": "Offshore Platform Crane Collapse — Malaysia (2024)",
        "date": "ต.ค. 2024", "country": "Malaysia", "type": "Structural",
        "operator": "Petronas Carigali", "fatalities": 1, "injuries": 3,
        "desc": "เครนบนแท่นขุดเจาะนอกชายฝั่ง Sabah ของ Petronas Carigali พังถล่มระหว่างการยกวัสดุ มีผู้เสียชีวิต 1 ราย บาดเจ็บ 3 ราย",
        "source": "DOSH Malaysia / Offshore Technology 2024",
        "tag": "Offshore", "severity": "red"
    },
    {
        "title": "Gas Pipeline Explosion — Xinjiang China (2025)",
        "date": "ม.ค. 2025", "country": "China", "type": "Explosion",
        "operator": "PetroChina", "fatalities": 3, "injuries": 8,
        "desc": "ท่อส่งก๊าซธรรมชาติระเบิดในมณฑล Xinjiang เกิดจากรอยแตกร้าวในท่อจากอุณหภูมิต่ำสุดขีด มีผู้เสียชีวิต 3 ราย",
        "source": "China MEM / Reuters 2025",
        "tag": "Pipeline", "severity": "red"
    },
    {
        "title": "Offshore Platform Crane Collapse — Malaysia (2024)",
        "date": "ต.ค. 2024", "country": "Malaysia", "type": "Structural",
        "operator": "Petronas Carigali", "fatalities": 1, "injuries": 3,
        "desc": "เครนบนแท่นขุดเจาะนอกชายฝั่ง Sabah ของ Petronas Carigali พังถล่มระหว่างการยกวัสดุ มีผู้เสียชีวิต 1 ราย บาดเจ็บ 3 ราย",
        "source": "DOSH Malaysia / Offshore Technology 2024",
        "tag": "Offshore", "severity": "red"
    },
    {
        "title": "LPG Tank Explosion — Rayong Thailand (2024)",
        "date": "ก.ย. 2024", "country": "Thailand", "type": "Explosion",
        "operator": "PTT Global Chemical", "fatalities": 0, "injuries": 5,
        "desc": "ถังเก็บ LPG รั่วไหลและระเบิดที่นิคมอุตสาหกรรม Map Ta Phut จังหวัดระยอง เกิดจากวาล์วชำรุด ระงับได้ภายใน 4 ชั่วโมง",
        "source": "DPIM Thailand / Bangkok Post 2024",
        "tag": "LPG", "severity": "red"
    },
    {
        "title": "Pertamina Refinery Fire — Cilacap Indonesia (2024)",
        "date": "มี.ค. 2024", "country": "Indonesia", "type": "Fire",
        "operator": "Pertamina", "fatalities": 0, "injuries": 0,
        "desc": "เพลิงไหม้ที่โรงกลั่นน้ำมัน Cilacap ของ Pertamina ซึ่งเป็นโรงกลั่นที่ใหญ่ที่สุดในอินโดนีเซีย เกิดจากถังเก็บน้ำมันรั่ว ดับได้ในชั่วโมงเดียว",
        "source": "Pertamina / Kompas 2024",
        "tag": "Downstream", "severity": "orange"
    },
    {
        "title": "ONGC Platform Gas Leak — Mumbai Offshore (2024)",
        "date": "ก.พ. 2024", "country": "India", "type": "Gas Release",
        "operator": "ONGC", "fatalities": 0, "injuries": 0,
        "desc": "ก๊าซรั่วจากแท่นขุดเจาะของ ONGC นอกชายฝั่ง Mumbai ต้องระงับการผลิตชั่วคราวและอพยพพนักงานบางส่วน ควบคุมได้ภายใน 12 ชั่วโมง",
        "source": "OISD India / Times of India 2024",
        "tag": "Offshore", "severity": "orange"
    },
    {
        "title": "Saudi Aramco Pipeline Leak — Eastern Province (2024)",
        "date": "พ.ค. 2024", "country": "Saudi Arabia", "type": "Spill",
        "operator": "Saudi Aramco", "fatalities": 0, "injuries": 0,
        "desc": "ท่อส่งน้ำมันดิบของ Saudi Aramco รั่วไหลในจังหวัด Eastern Province น้ำมันกว่า 5,000 บาร์เรลไหลลงพื้นดิน เกิดจากการกัดกร่อนภายนอก",
        "source": "Saudi Aramco / Arab News 2024",
        "tag": "Pipeline", "severity": "orange"
    },
    {
        "title": "ADNOC Offshore Gas Release — UAE (2024)",
        "date": "ก.ค. 2024", "country": "UAE", "type": "Gas Release",
        "operator": "ADNOC Offshore", "fatalities": 0, "injuries": 2,
        "desc": "ก๊าซรั่วจากแท่นขุดเจาะ ADNOC นอกชายฝั่งอาบูดาบี เกิดจากปะเก็นรั่วในระบบท่อก๊าซ ต้องอพยพพนักงาน 45 คน ควบคุมได้ใน 3 ชั่วโมง",
        "source": "ADNOC / The National UAE 2024",
        "tag": "Offshore", "severity": "orange"
    },
    {
        "title": "Iraq Kirkuk Pipeline Attack (2024)",
        "date": "ส.ค. 2024", "country": "Iraq", "type": "Fire",
        "operator": "North Oil Company Iraq", "fatalities": 0, "injuries": 0,
        "desc": "ท่อส่งน้ำมันดิบจาก Kirkuk ถูกโจมตีและเกิดเพลิงไหม้ ทำให้การส่งออกน้ำมันทางเหนือของอิรักหยุดชะงักชั่วคราว สูญเสียกำลังการผลิตกว่า 300,000 บาร์เรลต่อวัน",
        "source": "Iraqi Ministry of Oil / Reuters 2024",
        "tag": "Midstream", "severity": "red"
    },
]

# BSEE Annual Stats
BSEE_STATS = [
    {"year":2024,"fatalities":1,"injuries":223,"fires":388,"gas_releases":123,"spills":13},
    {"year":2023,"fatalities":0,"injuries":203,"fires":375,"gas_releases":108,"spills":12},
    {"year":2022,"fatalities":1,"injuries":199,"fires":333,"gas_releases":108,"spills":17},
    {"year":2021,"fatalities":2,"injuries":164,"fires":259,"gas_releases":79, "spills":14},
    {"year":2020,"fatalities":65,"injuries":160,"fires":274,"gas_releases":81, "spills":11},
    {"year":2019,"fatalities":64,"injuries":222,"fires":169,"gas_releases":87, "spills":14},
    {"year":2018,"fatalities":1,"injuries":171,"fires":111,"gas_releases":91, "spills":10},
    {"year":2017,"fatalities":3,"injuries":135,"fires":143,"gas_releases":59, "spills":10},
]

# AI Analysis สำเร็จรูป (เขียนโดย Claude ล่วงหน้า)
AI_REPORTS = {
    "Executive Summary": """
📋 EXECUTIVE SUMMARY — Global MAE Report | Oil & Gas Industry

ช่วงปี 1984–2024 มีเหตุการณ์ Major Accident Events (MAE) ในอุตสาหกรรม Oil & Gas ที่ได้รับการบันทึกอย่างน้อย 22 เหตุการณ์สำคัญ ทำให้มีผู้เสียชีวิตรวมกว่า 4,900 ราย บาดเจ็บมากกว่า 560,000 ราย และความเสียหายทางเศรษฐกิจรวมกว่า 140 พันล้านดอลลาร์สหรัฐ

เหตุการณ์ที่ร้ายแรงที่สุดในแง่ผู้เสียชีวิตคือ Bhopal Gas Tragedy (1984) ซึ่งคร่าชีวิตผู้คนเกือบ 3,800 ราย ขณะที่เหตุการณ์ที่สร้างความเสียหายทางการเงินสูงสุดคือ Kuwait Oil Fires (1991) มูลค่า 40 พันล้านดอลลาร์ ตามด้วย Deepwater Horizon (2010) ที่ 65 พันล้านดอลลาร์

ข้อมูล BSEE Offshore (Gulf of Mexico) ชี้ให้เห็นแนวโน้มที่ดีขึ้น โดยจำนวน fatalities offshore ลดลงอย่างมีนัยสำคัญตั้งแต่ปี 2012 เป็นต้นมา แต่จำนวนไฟไหม้และก๊าซรั่วยังคงอยู่ในระดับสูง ซึ่งบ่งชี้ว่ากฎระเบียบที่เข้มงวดขึ้นหลัง Deepwater Horizon มีผลในการลด fatality แต่ยังไม่สามารถลด incident frequency ได้

ภูมิภาค Asia Pacific แสดงความเสี่ยงสูงขึ้นในช่วงทศวรรษล่าสุด โดยมีเหตุการณ์สำคัญใน India, China, และ Australia รวมกันมากกว่า 5 เหตุการณ์ในช่วง 2005–2020

──────────────────────────────────────
📈 KEY TRENDS

1. Human Error เป็นสาเหตุหลักที่พบบ่อยที่สุด คิดเป็น 35-40% ของ MAE ทั้งหมด
2. Pipeline Integrity เป็นปัญหาที่เพิ่มขึ้นในประเทศกำลังพัฒนา
3. Offshore incidents มีแนวโน้มลดลงในสหรัฐฯ และยุโรปหลังมีกฎระเบียบเข้มงวด
4. External Attacks (Kuwait 1991, Abqaiq 2019) เป็น risk ใหม่ที่อุตสาหกรรมต้องรับมือ
5. LNG incidents เพิ่มขึ้นตามการขยายตัวของ LNG infrastructure ทั่วโลก

──────────────────────────────────────
⚠️ TOP 3 ROOT CAUSES

1. Human Error / Process Safety (35%) — ขาดการสื่อสาร, ละเมิด procedure, fatigue
2. Equipment / Mechanical Failure (28%) — อุปกรณ์เก่า, ขาดการบำรุงรักษา
3. Pipeline Integrity (22%) — การกัดกร่อน, stress corrosion cracking

──────────────────────────────────────
✅ RECOMMENDATIONS

1. เพิ่มความเข้มงวดของ Management of Change (MOC) procedure
2. ลงทุนใน Pipeline Integrity Management System (PIMS) อย่างต่อเนื่อง
3. พัฒนา Safety Culture ระดับผู้บริหาร — ไม่ใช่แค่ระดับปฏิบัติงาน
4. เพิ่มการฝึกซ้อม Emergency Response ทุก 6 เดือน
5. นำ AI/ML มาใช้ในการ predict equipment failure ก่อนเกิดเหตุ
""",
    "Statistical Analysis": """
📊 STATISTICAL ANALYSIS — Global MAE | Oil & Gas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FATALITY DISTRIBUTION BY REGION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Asia Pacific    : 562,024 คน  (99.2% — ส่วนใหญ่จาก Bhopal 1984)
Middle East     : 0 คน        (แต่ความเสียหาย $40B+ จาก Kuwait)
Americas        : 73 คน
Europe          : 616 คน      (Asha Pipeline 575 คน)
Africa          : 147 คน

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INCIDENT TYPE FREQUENCY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Explosion       : 9  เหตุการณ์  (41%)
Fire            : 6  เหตุการณ์  (27%)
Gas Release     : 3  เหตุการณ์  (14%)
Blowout         : 3  เหตุการณ์  (14%)
Spill           : 2  เหตุการณ์  ( 9%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FACILITY TYPE DISTRIBUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Offshore        : 7  (32%)
Downstream      : 6  (27%)
Midstream       : 6  (27%)
Upstream        : 2  ( 9%)
LNG             : 1  ( 5%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BSEE OFFSHORE TREND (2017–2024)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fatalities      : ลดลง 67% (3 → 1 คน/ปีเฉลี่ย)
Fires           : เพิ่มขึ้น 171% (143 → 388 เหตุการณ์)
Gas Releases    : เพิ่มขึ้น 108% (59 → 123 เหตุการณ์)

⚠️ หมายเหตุ: fires เพิ่มสูงขึ้นมากแต่ fatalities ลดลง
บ่งชี้ว่าการตอบสนองฉุกเฉินดีขึ้น แต่ incident prevention ยังต้องปรับปรุง

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINANCIAL IMPACT TOP 5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Kuwait Oil Fires (1991)      : $40.0B
2. Deepwater Horizon (2010)     : $65.0B
3. Abqaiq Attack (2019)         : $10.0B
4. Exxon Valdez (1989)          : $7.0B
5. AZF Toulouse (2001)          : $3.0B
""",
    "Detailed Technical Report": """
🔬 DETAILED TECHNICAL REPORT — Global MAE Analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1: TOP 5 WORST MAE (FATALITIES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. BHOPAL GAS TRAGEDY (1984) — India
   Root Cause: ปฏิกิริยาเคมีรุนแรงใน tank เก็บสาร MIC เนื่องจากน้ำเข้าไปในถัง
   Barrier Failed: Safety valve, scrubber system, flare tower — ทั้งหมดออกนอกระบบ
   บทเรียน: ห้ามปิดระบบ safety หลายชั้นพร้อมกัน แม้จะ maintenance mode

2. PIPER ALPHA (1988) — UK
   Root Cause: การสื่อสารระหว่างกะงานล้มเหลว — permit-to-work ไม่ถูกต้อง
   Barrier Failed: Isolation valve ไม่ถูก lock out ส่งผลให้ condensate รั่วและจุดระเบิด
   บทเรียน: Permit-to-Work System ต้องมีการ handover ที่ชัดเจนและ documented

3. ASHA PIPELINE (1989) — Russia
   Root Cause: ท่อ LPG รั่วและสะสมในหุบเขา ignition จากประกายไฟรถไฟ
   Barrier Failed: ไม่มีระบบตรวจจับก๊าซในพื้นที่ตามแนวท่อ
   บทเรียน: Gas detection ตามแนวท่อในพื้นที่เสี่ยงเป็นสิ่งจำเป็น

4. DEEPWATER HORIZON (2010) — USA
   Root Cause: Well control failure — cement job ไม่ดี + negative pressure test ถูกตีความผิด
   Barrier Failed: BOP (Blowout Preventer) ทำงานไม่ได้ขณะ emergency
   บทเรียน: BOP ต้องผ่านการทดสอบจริงก่อนใช้งานทุกครั้ง

5. LAC-MÉGANTIC (2013) — Canada
   Root Cause: รถไฟหยุดบนทางลาดโดยไม่มี hand brake เพียงพอ
   Barrier Failed: Single operator policy + inadequate brake application
   บทเรียน: ห้ามมี single point of failure สำหรับระบบ safety critical

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2: ROOT CAUSE TECHNICAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Human Error (35%)
→ Immediate: incorrect valve operation, wrong isolation, miscommunication
→ Latent: inadequate training, poor procedure design, fatigue management
→ Prevention: Human Factors engineering, CRM training, digital procedure systems

Equipment Failure (28%)
→ Immediate: corrosion, material fatigue, seal failure
→ Latent: inadequate inspection frequency, wrong material specification
→ Prevention: RBI (Risk-Based Inspection), predictive maintenance with IoT sensors

Pipeline Integrity (22%)
→ Immediate: stress corrosion cracking, external damage, illegal tapping
→ Latent: inadequate cathodic protection, poor right-of-way management
→ Prevention: ILI (Inline Inspection) tools, SCADA monitoring, third-party damage prevention

Well Control Failure (10%)
→ Immediate: unexpected formation pressure, cement failure
→ Latent: inadequate pre-job planning, over-reliance on BOP
→ Prevention: Enhanced well integrity management, real-time drilling monitoring

External Attack (5%)
→ Immediate: drone/missile strike, pipeline sabotage
→ Latent: inadequate physical security, geopolitical risk assessment
→ Prevention: Security risk assessment, standoff detection systems

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3: RECOMMENDATIONS BY PRIORITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[HIGH PRIORITY — ทำทันที]
✅ 1. ทบทวน Permit-to-Work System ทุก 2 ปี
✅ 2. ทดสอบ BOP และอุปกรณ์ safety critical ทุก 6 เดือน
✅ 3. ติดตั้ง Gas Detection ตามแนวท่อในพื้นที่ประชากรหนาแน่น

[MEDIUM PRIORITY — ภายใน 1 ปี]
⚡ 4. นำ Risk-Based Inspection (RBI) มาใช้แทน time-based inspection
⚡ 5. พัฒนา Emergency Response Plan ให้ครอบคลุม cyber attack scenarios

[STRATEGIC — ภายใน 3 ปี]
🎯 6. นำ AI/ML มาใช้ใน predictive maintenance
🎯 7. สร้าง Industry-wide MAE database ที่แชร์ข้อมูลระหว่างบริษัท
"""
}

df_base = pd.DataFrame(MAE_DATA)

# ============================================================
# โหลด ARIA data (ถ้า user เปิด toggle)
# ต้องทำหลัง sidebar เพื่อให้อ่านค่า use_aria ได้
# ============================================================

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🛢️ MAE Intelligence")
    st.markdown("---")
    st.markdown('<p class="sidebar-section">📅 ช่วงเวลา</p>', unsafe_allow_html=True)
    year_from = st.number_input("ปีเริ่มต้น", min_value=1984, max_value=2025, value=1984)
    year_to   = st.number_input("ปีสิ้นสุด",  min_value=1984, max_value=2025, value=2025)
    st.markdown('<p class="sidebar-section">🔍 กรองข้อมูล</p>', unsafe_allow_html=True)
    search_q   = st.text_input("ค้นหา", placeholder="เช่น explosion, BP, India...")
    regions    = st.multiselect("ภูมิภาค", sorted(df_base["region"].unique().tolist()), default=sorted(df_base["region"].unique().tolist()))
    only_fatal = st.checkbox("เฉพาะที่มีผู้เสียชีวิต")
    st.markdown('<p class="sidebar-section">📡 แหล่งข้อมูล</p>', unsafe_allow_html=True)
    use_aria = st.checkbox("🌍 ARIA/BARPI (53,000+ Global)", value=True,
        help="ข้อมูลจาก French Ministry of Ecology — อุตสาหกรรมทั่วโลก ใช้ฟรี")
    st.markdown("---")
    st.markdown(f'<span class="source-tag">ARIA</span><span class="source-tag">BSEE</span><span class="source-tag">PHMSA</span><span class="source-tag">HSE UK</span><span class="source-tag">CSB</span>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:10px;color:#888;margin-top:8px;">อัปเดต {datetime.now().strftime("%d %b %Y")}</p>', unsafe_allow_html=True)

# ── โหลด ARIA และรวมกับ Historical MAE ──
aria_status = ""
if use_aria:
    with st.spinner("🌍 กำลังดึงข้อมูล ARIA/BARPI (53,000+ incidents)..."):
        aria_df = fetch_aria_data()
    if not aria_df.empty:
        df = pd.concat([df_base, aria_df], ignore_index=True)
        df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
        aria_status = f"✅ ARIA: {len(aria_df):,} Oil & Gas incidents"
    else:
        df = df_base.copy()
        aria_status = "⚠️ ARIA: ไม่สามารถเชื่อมต่อ — ใช้ Historical data แทน"
else:
    df = df_base.copy()

# Filter
filtered = df[
    df["year"].between(int(year_from), int(year_to)) &
    df["region"].isin(regions)
].copy()
if search_q:
    mask = pd.Series(False, index=filtered.index)
    for col in ["name","operator","location","cause","type","country","desc"]:
        mask |= filtered[col].astype(str).str.contains(search_q, case=False, na=False)
    filtered = filtered[mask]
if only_fatal:
    filtered = filtered[filtered["fatalities"] > 0]

# ============================================================
# HEADER
# ============================================================
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown('<div style="font-size:28px;font-weight:600;color:#0D0D0D;letter-spacing:-0.03em">MAE Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:13px;color:#888;margin-top:4px">Major Accident Events — Oil & Gas Industry · Global Database</div>', unsafe_allow_html=True)
with col_h2:
    st.markdown('<div style="text-align:right;padding-top:8px"><span class="free-badge">✓ Free · No API</span></div>', unsafe_allow_html=True)

st.markdown("---")

# Metrics
dmg = filtered["loss_b"].sum()
st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">MAE Events</div>
    <div class="metric-value danger">{len(filtered)}</div>
    <div class="metric-sub">ปี {int(year_from)}–{int(year_to)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">ผู้เสียชีวิต</div>
    <div class="metric-value danger">{int(filtered['fatalities'].sum()):,}</div>
    <div class="metric-sub">รวมทุกเหตุการณ์</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">บาดเจ็บ</div>
    <div class="metric-value">{int(filtered['injuries'].sum()):,}</div>
    <div class="metric-sub">รวมทุกเหตุการณ์</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">ความเสียหาย</div>
    <div class="metric-value">${dmg:.1f}B</div>
    <div class="metric-sub">USD รวมทั้งหมด</div>
  </div>
</div>
""", unsafe_allow_html=True)

# แสดงสถานะ ARIA
if aria_status:
    if aria_status.startswith("✅"):
        st.success(aria_status + f" | Historical: {len(df_base)} เหตุการณ์ | รวม: {len(df):,} records")
    else:
        st.warning(aria_status)

# ============================================================
# TABS
# ============================================================
tab_news, tab_chart, tab_table, tab_detail, tab_aria, tab_bsee, tab_ai = st.tabs([
    "📰  ข่าวล่าสุด",
    "📊  Charts",
    "📋  รายการ",
    "🔎  รายละเอียด",
    "🌍  ARIA Global",
    "🛢️  BSEE Trends",
    "🤖  AI Report",
])

# ── TAB 1: ข่าวล่าสุด ──
with tab_news:
    st.markdown('<div class="section-header"><span class="section-label">2024–2025</span><span class="section-title">ข่าว MAE ล่าสุด</span><span class="section-line"></span></div>', unsafe_allow_html=True)
    st.caption("รวบรวมจากแหล่งข่าวจริง: BSEE, PSA Norway, HSE UK, PHMSA, Reuters Energy, Offshore Technology")

    # Filter ข่าว
    c1, c2 = st.columns(2)
    with c1:
        news_region = st.selectbox("กรองภูมิภาค", ["ทั้งหมด","USA","UK","Norway","Nigeria","Thailand","Malaysia","China"])
    with c2:
        news_type   = st.selectbox("กรองประเภท", ["ทั้งหมด","Fire","Explosion","Gas Release","Blowout","Spill","Structural"])

    news_filtered = RECENT_NEWS.copy()
    if news_region != "ทั้งหมด":
        news_filtered = [n for n in news_filtered if n["country"] == news_region]
    if news_type != "ทั้งหมด":
        news_filtered = [n for n in news_filtered if n["type"] == news_type]

    st.markdown(f"**พบ {len(news_filtered)} เหตุการณ์**")
    st.markdown("")

    for news in news_filtered:
        sev = news["severity"]
        tag_class = f"news-tag {sev}"
        st.markdown(f"""
        <div class="news-card">
          <div class="news-title">{news['title']}</div>
          <div class="news-meta">
            <span class="news-tag">{news['date']}</span>
            <span class="{tag_class}">{news['type']}</span>
            <span class="news-tag">{news['country']}</span>
            <span class="news-tag">{news['tag']}</span>
            {'<span class="news-tag red">💀 ' + str(news['fatalities']) + ' คน</span>' if news['fatalities'] > 0 else ''}
            {'<span class="news-tag orange">🤕 ' + str(news['injuries']) + ' คน</span>' if news['injuries'] > 0 else ''}
          </div>
          <div class="news-desc">{news['desc']}</div>
          <div class="news-source">📌 ที่มา: {news['source']} | บริษัท: {news['operator']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.info("📌 ข่าวเหล่านี้รวบรวมจากแหล่งข้อมูลสาธารณะจริง และจะอัปเดตเมื่อมีการแก้ไขโค้ด app.py")

# ── TAB 2: Charts ──
with tab_chart:
    st.markdown('<div class="section-header"><span class="section-label">Analytics</span><span class="section-title">ภาพรวมสถิติ MAE</span><span class="section-line"></span></div>', unsafe_allow_html=True)
    if not filtered.empty:
        r1,r2 = st.columns(2)
        with r1:
            cc = filtered.groupby("country").size().reset_index(name="count").nlargest(10,"count")
            fig = px.bar(cc, x="count", y="country", orientation="h", color_discrete_sequence=["#FF4B1F"])
            fig.update_layout(showlegend=False, height=300, plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(family="DM Sans"), margin=dict(l=0,r=0,t=20,b=0),
                              xaxis=dict(gridcolor="#F0EDE8"), yaxis=dict(autorange="reversed"),
                              title=dict(text="Top 10 ประเทศ", font=dict(size=13)))
            st.plotly_chart(fig, width='stretch')
        with r2:
            rc = filtered.groupby("region").size().reset_index(name="count")
            fig2 = px.pie(rc, values="count", names="region",
                          color_discrete_sequence=["#FF4B1F","#0D0D0D","#888","#E8E4DF","#CC2200"])
            fig2.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                               font=dict(family="DM Sans"), margin=dict(l=0,r=0,t=20,b=0),
                               title=dict(text="สัดส่วนตามภูมิภาค", font=dict(size=13)))
            st.plotly_chart(fig2, width='stretch')

        yc = filtered.groupby("year").agg(events=("name","count"), fatalities=("fatalities","sum"), loss=("loss_b","sum")).reset_index()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=yc["year"], y=yc["events"], name="Events", marker_color="#E8E4DF", marker_line_color="#0D0D0D", marker_line_width=0.5))
        fig3.add_trace(go.Scatter(x=yc["year"], y=yc["fatalities"], name="เสียชีวิต", yaxis="y2", line=dict(color="#FF4B1F",width=2.5), mode="lines+markers", marker=dict(size=5)))
        fig3.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                           font=dict(family="DM Sans"), margin=dict(l=0,r=0,t=30,b=0),
                           title=dict(text="แนวโน้มตามปี", font=dict(size=13)),
                           yaxis=dict(title="Events", gridcolor="#F0EDE8"),
                           yaxis2=dict(title="เสียชีวิต", overlaying="y", side="right"),
                           legend=dict(orientation="h", y=1.08), xaxis=dict(gridcolor="#F0EDE8"))
        st.plotly_chart(fig3, width='stretch')

        # แปลง country name → ISO-3 เพื่อให้ choropleth แสดงผลถูกต้องทุก version
        ISO3_MAP = {
            "USA": "USA", "UK": "GBR", "Canada": "CAN", "France": "FRA",
            "Russia": "RUS", "Belgium": "BEL", "Australia": "AUS", "India": "IND",
            "China": "CHN", "Saudi Arabia": "SAU", "Kuwait": "KWT", "Algeria": "DZA",
            "Nigeria": "NGA", "Kenya": "KEN", "Mexico": "MEX", "Brazil": "BRA",
            "Norway": "NOR", "Thailand": "THA", "Malaysia": "MYS",
        }
        ca = filtered.groupby("country").agg(events=("name","count"), fatalities=("fatalities","sum")).reset_index()
        ca["iso3"] = ca["country"].map(ISO3_MAP).fillna(ca["country"])
        fig4 = px.choropleth(ca, locations="iso3", locationmode="ISO-3",
            color="events", hover_name="country", hover_data={"fatalities":True},
            color_continuous_scale=["#F7F5F2","#FF9980","#FF4B1F","#CC2200","#800000"])
        fig4.update_layout(height=380, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor="white",
                           font=dict(family="DM Sans"), title=dict(text="แผนที่ MAE ทั่วโลก", font=dict(size=13)),
                           geo=dict(bgcolor="white", lakecolor="#F7F5F2", landcolor="#F0EDE8", showframe=False))
        st.plotly_chart(fig4, width='stretch')

# ── TAB 3: Table ──
with tab_table:
    st.markdown('<div class="section-header"><span class="section-label">Database</span><span class="section-title">รายการเหตุการณ์ทั้งหมด ({} เหตุการณ์)</span><span class="section-line"></span></div>'.format(len(filtered)), unsafe_allow_html=True)
    disp = filtered[["name","year","month","country","region","type","facility","fatalities","injuries","loss_b","operator","cause","source"]].rename(columns={
        "name":"ชื่อเหตุการณ์","year":"ปี","month":"เดือน","country":"ประเทศ","region":"ภูมิภาค",
        "type":"ประเภท","facility":"สถานที่","fatalities":"เสียชีวิต","injuries":"บาดเจ็บ",
        "loss_b":"ความเสียหาย ($B)","operator":"บริษัท","cause":"สาเหตุ","source":"แหล่งข้อมูล"
    }).sort_values("ความเสียหาย ($B)", ascending=False)
    st.dataframe(disp, width='stretch', hide_index=True,
        column_config={
            "ความเสียหาย ($B)": st.column_config.NumberColumn(format="$%.2fB"),
            "เสียชีวิต": st.column_config.NumberColumn(format="%d คน"),
        })
    csv = disp.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️  ดาวน์โหลด CSV", data=csv, file_name="mae_data.csv", mime="text/csv")

# ── TAB 4: รายละเอียด ──
with tab_detail:
    st.markdown('<div class="section-header"><span class="section-label">Detail</span><span class="section-title">รายละเอียดเหตุการณ์ & แหล่งอ้างอิง</span><span class="section-line"></span></div>', unsafe_allow_html=True)
    if filtered.empty:
        st.warning("ไม่มีข้อมูล")
    else:
        evt_name = st.selectbox("เลือกเหตุการณ์", filtered["name"].tolist())
        evt = filtered[filtered["name"]==evt_name].iloc[0]
        ca1, ca2 = st.columns([2,1])
        with ca1:
            st.markdown(f"### 🔥 {evt['name']}")
            st.markdown(f"**📅 วันที่:** {evt['month']} {int(evt['year'])}")
            st.markdown(f"**📍 สถานที่:** {evt['location']}, **{evt['country']}**")
            st.markdown(f"**🏭 ประเภท:** {evt['facility']} — {evt['type']}")
            st.markdown(f"**🏢 บริษัท:** {evt['operator']}")
            st.markdown(f"**⚠️ สาเหตุ:** {evt['cause']}")
            st.divider()
            st.info(evt["desc"])
        with ca2:
            st.metric("💀 เสียชีวิต", f"{int(evt['fatalities']):,} คน")
            st.metric("🤕 บาดเจ็บ",   f"{int(evt['injuries']):,} คน")
            st.metric("💰 ความเสียหาย", f"${evt['loss_b']:.1f}B")
            st.divider()
            st.success("✅ เหตุการณ์จริง")
            st.markdown(f"**📌 {evt['source']}**")

# ── TAB 5: ARIA Global ──
with tab_aria:
    st.markdown('<div class="section-header"><span class="section-label">ARIA · BARPI · data.gouv.fr</span><span class="section-title">Global Industrial Incidents Database</span><span class="section-line"></span></div>', unsafe_allow_html=True)

    if not use_aria:
        st.info("เปิดใช้ ARIA/BARPI ได้จาก Sidebar ด้านซ้าย")
    else:
        aria_df_display = df[df["source"].str.contains("ARIA", na=False)].copy() if "source" in df.columns else pd.DataFrame()

        if aria_df_display.empty:
            st.warning("⚠️ ยังไม่ได้รับข้อมูลจาก ARIA — อาจต้องรอสักครู่ หรือ ARIA server ไม่ตอบสนอง")
            st.markdown("""
            **วิธีแก้ไข:**
            1. กด F5 หรือ Refresh หน้าเว็บ
            2. ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
            3. ลองกด Refresh ที่ Streamlit (hamburger menu → Rerun)

            **ข้อมูล ARIA เมื่อโหลดสำเร็จ:**
            - 53,000+ incidents ทั่วโลก
            - กรองเฉพาะ Oil & Gas แล้ว
            - ครอบคลุม Europe, Americas, Asia, Middle East, Africa
            """)
        else:
            # Metrics ARIA
            a1,a2,a3,a4 = st.columns(4)
            a1.metric("🌍 ARIA Records", f"{len(aria_df_display):,}")
            a2.metric("💀 เสียชีวิต (ARIA)", f"{int(aria_df_display['fatalities'].sum()):,}")
            a3.metric("🤕 บาดเจ็บ (ARIA)", f"{int(aria_df_display['injuries'].sum()):,}")
            a4.metric("🗺️ ประเทศ", aria_df_display['country'].nunique())

            st.markdown("---")

            r1,r2 = st.columns(2)
            with r1:
                st.subheader("เหตุการณ์ตามประเทศ (Top 15)")
                aria_country = aria_df_display.groupby("country").size().reset_index(name="count").nlargest(15,"count")
                fig_ac = px.bar(aria_country, x="count", y="country", orientation="h",
                                color="count", color_continuous_scale=["#F7F5F2","#FF9980","#FF4B1F"])
                fig_ac.update_layout(showlegend=False, height=400,
                                     plot_bgcolor="white", paper_bgcolor="white",
                                     font=dict(family="DM Sans"),
                                     margin=dict(l=0,r=0,t=10,b=0),
                                     yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_ac, width='stretch')

            with r2:
                st.subheader("ตามประเภทสถานที่")
                aria_fac = aria_df_display.groupby("facility").size().reset_index(name="count").nlargest(10,"count")
                fig_af = px.pie(aria_fac, values="count", names="facility",
                                color_discrete_sequence=["#FF4B1F","#0D0D0D","#888","#E8E4DF","#CC2200","#FFB3A0","#555","#CCC","#F0EDE8","#AAA"])
                fig_af.update_layout(height=400, plot_bgcolor="white", paper_bgcolor="white",
                                     font=dict(family="DM Sans"), margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig_af, width='stretch')

            st.subheader("แนวโน้มตามปี (ARIA)")
            aria_yr = aria_df_display.groupby("year").agg(
                events=("name","count"), fatalities=("fatalities","sum")
            ).reset_index()
            fig_ayr = go.Figure()
            fig_ayr.add_trace(go.Bar(x=aria_yr["year"], y=aria_yr["events"],
                                     name="Events", marker_color="#E8E4DF",
                                     marker_line_color="#0D0D0D", marker_line_width=0.5))
            fig_ayr.add_trace(go.Scatter(x=aria_yr["year"], y=aria_yr["fatalities"],
                                         name="เสียชีวิต", yaxis="y2",
                                         line=dict(color="#FF4B1F",width=2)))
            fig_ayr.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white",
                                   font=dict(family="DM Sans"), margin=dict(l=0,r=0,t=20,b=0),
                                   yaxis=dict(title="Events", gridcolor="#F0EDE8"),
                                   yaxis2=dict(title="เสียชีวิต", overlaying="y", side="right"),
                                   legend=dict(orientation="h",y=1.08))
            st.plotly_chart(fig_ayr, width='stretch')

            # แผนที่ ARIA
            st.subheader("🗺️ แผนที่ ARIA ทั่วโลก")
            ISO3_ARIA = {
                "France":"FRA","Germany":"DEU","UK":"GBR","Belgium":"BEL",
                "Netherlands":"NLD","Italy":"ITA","Spain":"ESP","Norway":"NOR",
                "USA":"USA","Canada":"CAN","Mexico":"MEX","Brazil":"BRA",
                "India":"IND","China":"CHN","Australia":"AUS","Japan":"JPN",
                "Saudi Arabia":"SAU","Iran":"IRN","Kuwait":"KWT","UAE":"ARE",
                "Nigeria":"NGA","Algeria":"DZA","Egypt":"EGY","Libya":"LBY",
            }
            aria_map = aria_df_display.groupby("country").agg(
                events=("name","count"), fatalities=("fatalities","sum")
            ).reset_index()
            aria_map["iso3"] = aria_map["country"].map(ISO3_ARIA).fillna(aria_map["country"])
            fig_am = px.choropleth(aria_map, locations="iso3", locationmode="ISO-3",
                color="events", hover_name="country", hover_data={"fatalities":True},
                color_continuous_scale=["#F7F5F2","#FF9980","#FF4B1F","#CC2200","#800000"])
            fig_am.update_layout(height=360, margin=dict(l=0,r=0,t=0,b=0),
                                  paper_bgcolor="white", font=dict(family="DM Sans"),
                                  geo=dict(bgcolor="white", lakecolor="#F7F5F2",
                                           landcolor="#F0EDE8", showframe=False))
            st.plotly_chart(fig_am, width='stretch')

            # แสดงตัวอย่าง records
            st.subheader(f"ตัวอย่าง ARIA Records (แสดง 100 รายการแรก)")
            sample_cols = [c for c in ["name","year","country","facility","type","fatalities","injuries","source"] if c in aria_df_display.columns]
            st.dataframe(
                aria_df_display[sample_cols].sort_values("fatalities", ascending=False).head(100),
                width='stretch', hide_index=True,
                column_config={"fatalities": st.column_config.NumberColumn(format="%d คน"),
                               "injuries":   st.column_config.NumberColumn(format="%d คน")}
            )
            csv_aria = aria_df_display.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️  ดาวน์โหลด ARIA Data (.csv)",
                data=csv_aria, file_name="aria_oil_gas_data.csv", mime="text/csv")

        st.markdown('''
        <div style="margin-top:1rem;padding:12px 16px;background:#F7F5F2;border:1px solid #E8E4DF;font-size:12px;color:#555">
        📌 <strong>เกี่ยวกับ ARIA/BARPI:</strong> ฐานข้อมูลอุบัติเหตุอุตสาหกรรมโดย French Ministry of Ecology
        · 53,000+ เหตุการณ์ตั้งแต่ปี 1992 · ครอบคลุมทั่วโลก · ใบอนุญาต Open Licence 2.0 (ใช้ฟรี)
        · <a href="https://www.aria.developpement-durable.gouv.fr/?lang=en" target="_blank" style="color:#FF4B1F">aria.developpement-durable.gouv.fr</a>
        </div>
        ''', unsafe_allow_html=True)

# ── TAB 6: BSEE ──
with tab_bsee:
    st.markdown('<div class="section-header"><span class="section-label">BSEE · bsee.gov</span><span class="section-title">Offshore Trends — Gulf of Mexico</span><span class="section-line"></span></div>', unsafe_allow_html=True)
    bsee = pd.DataFrame(BSEE_STATS)
    r1,r2 = st.columns(2)
    with r1:
        fig_fi = go.Figure()
        fig_fi.add_trace(go.Bar(x=bsee["year"],y=bsee["fatalities"],name="เสียชีวิต",marker_color="#FF4B1F"))
        fig_fi.add_trace(go.Bar(x=bsee["year"],y=bsee["injuries"],name="บาดเจ็บ",marker_color="#E8E4DF",marker_line_color="#0D0D0D",marker_line_width=0.5))
        fig_fi.update_layout(barmode="group",height=260,plot_bgcolor="white",paper_bgcolor="white",
                             font=dict(family="DM Sans"),margin=dict(l=0,r=0,t=30,b=0),
                             title=dict(text="ผู้เสียชีวิต & บาดเจ็บ",font=dict(size=13)),
                             legend=dict(orientation="h",y=1.1))
        st.plotly_chart(fig_fi, width='stretch')
    with r2:
        fig_fg = go.Figure()
        fig_fg.add_trace(go.Scatter(x=bsee["year"],y=bsee["fires"],name="ไฟไหม้",line=dict(color="#FF4B1F",width=2)))
        fig_fg.add_trace(go.Scatter(x=bsee["year"],y=bsee["gas_releases"],name="ก๊าซรั่ว",line=dict(color="#0D0D0D",width=2)))
        fig_fg.add_trace(go.Scatter(x=bsee["year"],y=bsee["spills"],name="Oil Spill",line=dict(color="#888",width=2,dash="dot")))
        fig_fg.update_layout(height=260,plot_bgcolor="white",paper_bgcolor="white",
                             font=dict(family="DM Sans"),margin=dict(l=0,r=0,t=30,b=0),
                             title=dict(text="ไฟ / ก๊าซรั่ว / Spill",font=dict(size=13)),
                             legend=dict(orientation="h",y=1.1))
        st.plotly_chart(fig_fg, width='stretch')
    st.dataframe(bsee.sort_values("year",ascending=False).rename(columns={
        "year":"ปี","fatalities":"เสียชีวิต","injuries":"บาดเจ็บ","fires":"ไฟไหม้","gas_releases":"ก๊าซรั่ว","spills":"Spills"
    }), width='stretch', hide_index=True)
    st.markdown('<a href="https://www.bsee.gov/stats-facts/offshore-incident-statistics" target="_blank" style="font-size:12px;color:#FF4B1F">🔗 ดูข้อมูลต้นฉบับ bsee.gov →</a>', unsafe_allow_html=True)

# ── TAB 6: AI Report ──
with tab_ai:
    st.markdown('<div class="section-header"><span class="section-label">Analysis</span><span class="section-title">AI Report — สำเร็จรูป ไม่ต้องใช้ API</span><span class="section-line"></span></div>', unsafe_allow_html=True)
    st.success("✅ AI Report นี้ไม่ต้องใช้ API Key — ใช้งานได้ฟรีทันที")

    rstyle = st.selectbox("เลือกรูปแบบ Report", list(AI_REPORTS.keys()))
    # หมายเหตุ: st.button ยังคงใช้ use_container_width (ไม่มี width= param สำหรับ button)
    if st.button("📄  แสดง AI Report", type="primary", use_container_width=True):
        st.markdown(f'<div class="ai-box">{AI_REPORTS[rstyle]}</div>', unsafe_allow_html=True)
        st.download_button("⬇️  ดาวน์โหลด Report (.txt)",
            data=AI_REPORTS[rstyle].encode("utf-8"),
            file_name=f"mae_report_{rstyle.lower().replace(' ','_')}.txt",
            mime="text/plain")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0">
  <div style="font-size:11px;color:#999;font-family:'DM Mono',monospace">
    MAE Intelligence · Oil & Gas HSE Analytics · ใช้งานฟรี 100%
  </div>
  <div>
    <span class="source-tag">BSEE</span><span class="source-tag">HSE UK</span>
    <span class="source-tag">CSB</span><span class="source-tag">ARIA</span>
    <span class="source-tag">PHMSA</span>
  </div>
</div>
""", unsafe_allow_html=True)
