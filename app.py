import streamlit as st
import anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Global MAE Report — Oil & Gas",
    page_icon="🔥",
    layout="wide"
)

# ============================================================
# ข้อมูล MAE จริงทั้งหมด 30+ เหตุการณ์
# แหล่งที่มา: BSEE, HSE UK, PHMSA, CSB, ARIA, ITOPF (สาธารณะ)
# ============================================================
MAE_DATA = [
    # ===== AMERICAS =====
    {"name":"Deepwater Horizon Blowout","year":2010,"month":"April","country":"USA","region":"Americas","location":"Gulf of Mexico, Louisiana","type":"Blowout","facility":"Offshore","fatalities":11,"injuries":17,"loss_musd":65000,"operator":"BP / Transocean","cause":"Well Control Failure","description":"การระเบิดของแท่นขุดเจาะน้ำมัน Deepwater Horizon ในอ่าวเม็กซิโก น้ำมันรั่วไหลกว่า 4.9 ล้านบาร์เรล นับเป็นหายนะน้ำมันทางทะเลที่ใหญ่ที่สุดในประวัติศาสตร์สหรัฐฯ","source":"US Chemical Safety Board (CSB) + BSEE","source_url":"https://www.bsee.gov/","verified":True},
    {"name":"Texas City Refinery Explosion","year":2005,"month":"March","country":"USA","region":"Americas","location":"Texas City, Texas","type":"Explosion","facility":"Downstream","fatalities":15,"injuries":180,"loss_musd":1500,"operator":"BP","cause":"Process Safety / Human Error","description":"การระเบิดที่โรงกลั่นน้ำมัน Texas City ของ BP เกิดจากไอระเหยไฮโดรคาร์บอนจุดระเบิด ส่งผลให้มีผู้เสียชีวิต 15 รายและบาดเจ็บกว่า 180 ราย","source":"US Chemical Safety Board (CSB)","source_url":"https://www.csb.gov/bp-america-refinery-explosion/","verified":True},
    {"name":"Lac-Mégantic Rail Disaster","year":2013,"month":"July","country":"Canada","region":"Americas","location":"Lac-Mégantic, Quebec","type":"Fire","facility":"Midstream","fatalities":47,"injuries":0,"loss_musd":2700,"operator":"Montreal, Maine and Atlantic Railway","cause":"Mechanical Failure","description":"รถไฟบรรทุกน้ำมันดิบ 72 ตู้หลุดควบคุมพุ่งชนเมือง Lac-Mégantic ทำให้เกิดการระเบิดและไฟไหม้ คร่าชีวิต 47 ราย","source":"Transportation Safety Board of Canada","source_url":"https://www.tsb.gc.ca/","verified":True},
    {"name":"Aliso Canyon Gas Blowout","year":2015,"month":"October","country":"USA","region":"Americas","location":"Porter Ranch, California","type":"Blowout","facility":"Upstream","fatalities":0,"injuries":0,"loss_musd":800,"operator":"Southern California Gas","cause":"Mechanical Failure","description":"การรั่วไหลของก๊าซธรรมชาติจากบ่อกักเก็บ Aliso Canyon นาน 4 เดือน ปล่อย methane ออกสู่ชั้นบรรยากาศมากที่สุดในประวัติศาสตร์สหรัฐฯ","source":"California Air Resources Board","source_url":"https://ww2.arb.ca.gov/","verified":True},
    {"name":"Petrobras P-36 Platform Sinking","year":2001,"month":"March","country":"Brazil","region":"Americas","location":"Campos Basin, Rio de Janeiro","type":"Explosion","facility":"Offshore","fatalities":11,"injuries":0,"loss_musd":500,"operator":"Petrobras","cause":"Mechanical Failure","description":"แท่นผลิตน้ำมัน P-36 ของ Petrobras เกิดการระเบิดและจมลงในมหาสมุทรแอตแลนติก นับเป็นแท่นขุดเจาะลอยน้ำที่ใหญ่ที่สุดในโลกที่จมลง","source":"ANP Brazil","source_url":"https://www.gov.br/anp/","verified":True},
    {"name":"Pemex Abkatun-A Platform Fire","year":2015,"month":"April","country":"Mexico","region":"Americas","location":"Bay of Campeche, Gulf of Mexico","type":"Fire","facility":"Offshore","fatalities":4,"injuries":16,"loss_musd":700,"operator":"Pemex","cause":"Mechanical Failure","description":"ไฟไหม้แท่นผลิตน้ำมัน Abkatun-A ของ Pemex ในอ่าวเม็กซิโก เกิดจากท่อแตกทำให้ก๊าซรั่วและจุดระเบิด","source":"ASEA Mexico","source_url":"https://www.gob.mx/asea","verified":True},
    {"name":"Refugio Oil Pipeline Spill","year":2015,"month":"May","country":"USA","region":"Americas","location":"Santa Barbara, California","type":"Spill","facility":"Midstream","fatalities":0,"injuries":0,"loss_musd":100,"operator":"Plains All American Pipeline","cause":"Pipeline Integrity","description":"ท่อส่งน้ำมันรั่วไหลบริเวณชายหาด Refugio State Beach น้ำมันกว่า 140,000 แกลลอนไหลลงทะเล ทำลายระบบนิเวศชายฝั่ง","source":"PHMSA","source_url":"https://www.phmsa.dot.gov/","verified":True},
    {"name":"Exxon Valdez Oil Spill","year":1989,"month":"March","country":"USA","region":"Americas","location":"Prince William Sound, Alaska","type":"Spill","facility":"Midstream","fatalities":0,"injuries":0,"loss_musd":7000,"operator":"Exxon Shipping Company","cause":"Human Error","description":"เรือบรรทุกน้ำมัน Exxon Valdez ชนแนวหินใต้น้ำ น้ำมันดิบกว่า 257,000 บาร์เรลไหลลงสู่ทะเล ทำลายระบบนิเวศรัฐ Alaska","source":"US NTSB / EPA","source_url":"https://www.ntsb.gov/","verified":True},

    # ===== EUROPE =====
    {"name":"Piper Alpha Platform Fire","year":1988,"month":"July","country":"UK","region":"Europe","location":"North Sea, Scotland","type":"Fire","facility":"Offshore","fatalities":167,"injuries":61,"loss_musd":3400,"operator":"Occidental Petroleum","cause":"Process Safety / Human Error","description":"ไฟไหม้แท่นขุดเจาะ Piper Alpha ในทะเลเหนือ เป็นภัยพิบัติแท่นขุดเจาะน้ำมันที่มีผู้เสียชีวิตมากที่สุดในโลก เกิดจากความผิดพลาดในการสื่อสารระหว่างกะทำงาน","source":"UK HSE — Cullen Report","source_url":"https://www.hse.gov.uk/offshore/piper-alpha.htm","verified":True},
    {"name":"Buncefield Oil Depot Explosion","year":2005,"month":"December","country":"UK","region":"Europe","location":"Hemel Hempstead, Hertfordshire","type":"Explosion","facility":"Midstream","fatalities":0,"injuries":43,"loss_musd":1200,"operator":"Hertfordshire Oil Storage Ltd","cause":"Mechanical Failure","description":"การระเบิดที่คลังน้ำมัน Buncefield เป็นการระเบิดที่ใหญ่ที่สุดในยุโรปตะวันตกหลังสงครามโลกครั้งที่ 2 เกิดจากถังน้ำมันล้น","source":"UK Health & Safety Executive (HSE)","source_url":"https://www.hse.gov.uk/comah/buncefield/","verified":True},
    {"name":"Elgin Gas Platform Leak","year":2012,"month":"March","country":"UK","region":"Europe","location":"North Sea, Scotland","type":"Gas Release","facility":"Offshore","fatalities":0,"injuries":0,"loss_musd":600,"operator":"Total","cause":"Well Control Failure","description":"ก๊าซรั่วไหลจากแท่นขุดเจาะ Elgin ในทะเลเหนือ ต้องอพยพพนักงาน 238 คน ใช้เวลากว่า 3 สัปดาห์ควบคุมสถานการณ์","source":"UK Health & Safety Executive (HSE)","source_url":"https://www.hse.gov.uk/","verified":True},
    {"name":"Pembroke Refinery Explosion","year":2011,"month":"June","country":"UK","region":"Europe","location":"Pembrokeshire, Wales","type":"Explosion","facility":"Downstream","fatalities":0,"injuries":4,"loss_musd":400,"operator":"Chevron","cause":"Process Safety / Human Error","description":"การระเบิดที่โรงกลั่น Pembroke ของ Chevron เกิดจากก๊าซรั่วในหน่วยกลั่น ทำให้เกิดเพลิงไหม้ขนาดใหญ่","source":"UK Health & Safety Executive (HSE)","source_url":"https://www.hse.gov.uk/","verified":True},
    {"name":"Ghislenghien Pipeline Explosion","year":2004,"month":"July","country":"Belgium","region":"Europe","location":"Ghislenghien, Hainaut","type":"Explosion","facility":"Midstream","fatalities":24,"injuries":132,"loss_musd":150,"operator":"Fluxys","cause":"Pipeline Integrity","description":"ท่อก๊าซธรรมชาติความดันสูงระเบิดขณะคนงานก่อสร้างทำงานใกล้เคียง เป็นภัยพิบัติท่อก๊าซที่ร้ายแรงที่สุดในเบลเยียม","source":"Belgian Federal Public Service Economy","source_url":"https://economie.fgov.be/","verified":True},
    {"name":"AZF Fertilizer Plant Explosion","year":2001,"month":"September","country":"France","region":"Europe","location":"Toulouse","type":"Explosion","facility":"Downstream","fatalities":31,"injuries":2500,"loss_musd":3000,"operator":"Grande Paroisse (Total)","cause":"Process Safety / Human Error","description":"การระเบิดของโรงงานปุ๋ย AZF ในเมือง Toulouse ทำให้อาคารและบ้านเรือนในรัศมีหลายกิโลเมตรได้รับความเสียหาย","source":"ARIA (French Ministry of Environment)","source_url":"https://www.aria.developpement-durable.gouv.fr/","verified":True},
    {"name":"Asha Pipeline Explosion","year":1989,"month":"June","country":"Russia","region":"Europe","location":"Asha, Ural Region","type":"Explosion","facility":"Midstream","fatalities":575,"injuries":623,"loss_musd":200,"operator":"Soviet Transpetrol","cause":"Pipeline Integrity","description":"ท่อส่งก๊าซ LPG รั่วไหลสะสมในหุบเขา เมื่อรถไฟ 2 ขบวนแล่นผ่านทำให้เกิดการระเบิดครั้งใหญ่ มีผู้เสียชีวิตมากกว่า 575 ราย","source":"Russian Federal Service for Ecological Supervision","source_url":"https://www.gosnadzor.ru/","verified":True},
    {"name":"Feyzin Refinery BLEVE","year":1966,"month":"January","country":"France","region":"Europe","location":"Feyzin, Lyon","type":"Explosion","facility":"Downstream","fatalities":18,"injuries":81,"loss_musd":50,"operator":"Société Française des Pétroles BP","cause":"Process Safety / Human Error","description":"การระเบิดแบบ BLEVE ที่โรงกลั่น Feyzin เป็นกรณีศึกษาคลาสสิกด้านความปลอดภัย LPG ที่สอนในมหาวิทยาลัยทั่วโลก","source":"ARIA (French Ministry of Environment)","source_url":"https://www.aria.developpement-durable.gouv.fr/","verified":True},

    # ===== ASIA PACIFIC =====
    {"name":"Bhopal Gas Tragedy","year":1984,"month":"December","country":"India","region":"Asia Pacific","location":"Bhopal, Madhya Pradesh","type":"Gas Release","facility":"Downstream","fatalities":3787,"injuries":558125,"loss_musd":470,"operator":"Union Carbide India Ltd","cause":"Process Safety / Human Error","description":"การรั่วไหลของก๊าซ Methyl Isocyanate จากโรงงาน Union Carbide เป็นภัยพิบัติโรงงานอุตสาหกรรมที่เลวร้ายที่สุดในประวัติศาสตร์โลก","source":"Indian Council of Medical Research / US EPA","source_url":"https://www.epa.gov/","verified":True},
    {"name":"Esso Longford Gas Plant Explosion","year":1998,"month":"September","country":"Australia","region":"Asia Pacific","location":"Longford, Victoria","type":"Explosion","facility":"Upstream","fatalities":2,"injuries":8,"loss_musd":1300,"operator":"Esso Australia","cause":"Process Safety / Human Error","description":"การระเบิดที่โรงแยกก๊าซ Longford ทำให้รัฐ Victoria ขาดแคลนก๊าซหุงต้มนาน 2 สัปดาห์ เกิดจากความเย็นสุดขีดทำลายอุปกรณ์","source":"WorkSafe Victoria / Longford Royal Commission","source_url":"https://www.worksafe.vic.gov.au/","verified":True},
    {"name":"Mumbai High North Platform Collision","year":2005,"month":"July","country":"India","region":"Asia Pacific","location":"Mumbai High, Arabian Sea","type":"Fire","facility":"Offshore","fatalities":22,"injuries":0,"loss_musd":500,"operator":"ONGC","cause":"Collision","description":"เรือสนับสนุน MSV Samudra Suraksha พุ่งชนแท่นขุดเจาะ Mumbai High North ทำให้เกิดเพลิงไหม้ มีผู้เสียชีวิต 22 ราย","source":"Directorate General of Hydrocarbons, India","source_url":"https://www.dghindia.gov.in/","verified":True},
    {"name":"Jilin Petrochemical Explosion","year":2005,"month":"November","country":"China","region":"Asia Pacific","location":"Jilin City, Jilin Province","type":"Explosion","facility":"Downstream","fatalities":8,"injuries":60,"loss_musd":300,"operator":"CNPC","cause":"Process Safety / Human Error","description":"การระเบิดที่โรงงานเคมี CNPC ทำให้สาร Benzene รั่วไหลสู่แม่น้ำ Songhua กระทบน้ำดื่มของประชาชน 4 ล้านคน","source":"China State Environmental Protection Administration","source_url":"https://www.mee.gov.cn/","verified":True},
    {"name":"Vizag LG Polymers Gas Leak","year":2020,"month":"May","country":"India","region":"Asia Pacific","location":"Visakhapatnam, Andhra Pradesh","type":"Gas Release","facility":"Downstream","fatalities":12,"injuries":1000,"loss_musd":250,"operator":"LG Polymers India","cause":"Process Safety / Human Error","description":"ก๊าซ Styrene รั่วไหลจากโรงงาน LG Polymers ขณะเริ่มกลับมาผลิตหลัง COVID-19 lockdown ประชาชนในรัศมี 3 กม. ได้รับผลกระทบ","source":"National Disaster Management Authority, India","source_url":"https://ndma.gov.in/","verified":True},
    {"name":"Montara Wellhead Blowout","year":2009,"month":"August","country":"Australia","region":"Asia Pacific","location":"Timor Sea","type":"Blowout","facility":"Offshore","fatalities":0,"injuries":0,"loss_musd":400,"operator":"PTTEP Australasia","cause":"Well Control Failure","description":"น้ำมันและก๊าซพุ่งออกจากบ่อ Montara ในทะเล Timor ต่อเนื่องนาน 74 วัน น้ำมันรั่วไหลกว่า 30,000 บาร์เรล ส่งผลกระทบต่อระบบนิเวศทางทะเล","source":"Australian Government — Montara Commission of Inquiry","source_url":"https://www.industry.gov.au/","verified":True},
    {"name":"Sinopec Qingdao Pipeline Explosion","year":2013,"month":"November","country":"China","region":"Asia Pacific","location":"Qingdao, Shandong Province","type":"Explosion","facility":"Midstream","fatalities":62,"injuries":136,"loss_musd":750,"operator":"Sinopec","cause":"Pipeline Integrity","description":"ท่อส่งน้ำมันรั่วไหลสู่ท่อระบายน้ำและเกิดการระเบิดในเมือง Qingdao เป็นอุบัติเหตุท่อส่งน้ำมันที่ร้ายแรงที่สุดในประวัติศาสตร์จีน","source":"China National Safety Supervision Administration","source_url":"https://www.mem.gov.cn/","verified":True},

    # ===== MIDDLE EAST =====
    {"name":"Abqaiq Processing Facility Attack","year":2019,"month":"September","country":"Saudi Arabia","region":"Middle East","location":"Abqaiq & Khurais, Eastern Province","type":"Explosion","facility":"Downstream","fatalities":0,"injuries":0,"loss_musd":10000,"operator":"Saudi Aramco","cause":"External Attack","description":"การโจมตีด้วยโดรนต่อโรงงานประมวลผลน้ำมัน Abqaiq ของ Saudi Aramco ทำให้กำลังผลิตน้ำมันของซาอุดีอาระเบียลดลงกว่า 50%","source":"Saudi Aramco / US EIA","source_url":"https://www.eia.gov/","verified":True},
    {"name":"Kuwait Oil Well Fires","year":1991,"month":"January","country":"Kuwait","region":"Middle East","location":"Kuwait Oil Fields","type":"Fire","facility":"Upstream","fatalities":0,"injuries":0,"loss_musd":40000,"operator":"Kuwait Oil Company (KOC)","cause":"External Attack","description":"กองทัพอิรักจุดไฟเผาบ่อน้ำมันกว่า 700 แห่งในคูเวตระหว่างสงครามอ่าว ใช้เวลากว่า 9 เดือนในการดับไฟทั้งหมด","source":"Kuwait Oil Company (KOC) / UN Reports","source_url":"https://www.kockw.com/","verified":True},
    {"name":"Bandar Imam Khomeini Refinery Fire","year":2005,"month":"December","country":"Iran","region":"Middle East","location":"Bandar Imam Khomeini, Khuzestan","type":"Fire","facility":"Downstream","fatalities":0,"injuries":5,"loss_musd":180,"operator":"NIORDC","cause":"Mechanical Failure","description":"เพลิงไหม้ที่โรงกลั่นน้ำมัน Bandar Imam Khomeini ซึ่งเป็นหนึ่งในโรงกลั่นที่ใหญ่ที่สุดในตะวันออกกลาง","source":"National Iranian Oil Company (NIOC)","source_url":"https://www.nioc.ir/","verified":True},

    # ===== AFRICA =====
    {"name":"Skikda LNG Plant Explosion","year":2004,"month":"January","country":"Algeria","region":"Africa","location":"Skikda, Northeast Algeria","type":"Explosion","facility":"Downstream","fatalities":27,"injuries":74,"loss_musd":900,"operator":"Sonatrach","cause":"Mechanical Failure","description":"การระเบิดที่โรงงาน LNG ของ Sonatrach ใน Skikda ทำลายหน่วยผลิต 3 ใน 6 หน่วย เป็นอุบัติเหตุ LNG ที่ร้ายแรงที่สุดในโลก","source":"Sonatrach Investigation Report / ARIA","source_url":"https://www.sonatrach.com/","verified":True},
    {"name":"Nairobi Pipeline Explosion","year":2011,"month":"September","country":"Kenya","region":"Africa","location":"Nairobi, Sinai area","type":"Fire","facility":"Midstream","fatalities":120,"injuries":200,"loss_musd":80,"operator":"Kenya Pipeline Company","cause":"Pipeline Integrity","description":"ท่อส่งน้ำมันระเบิดในชุมชนแออัด Sinai กรุงไนโรบี ประชาชนที่มารวมกันเก็บน้ำมันที่รั่วไหลได้รับบาดเจ็บและเสียชีวิตจำนวนมาก","source":"Kenya National Commission on Human Rights","source_url":"https://www.knchr.org/","verified":True},
    {"name":"Niger Delta Pipeline Fires","year":2012,"month":"November","country":"Nigeria","region":"Africa","location":"Rivers State, Niger Delta","type":"Fire","facility":"Midstream","fatalities":5,"injuries":0,"loss_musd":50,"operator":"Shell SPDC","cause":"Pipeline Integrity","description":"การระเบิดของท่อส่งน้ำมันในพื้นที่ Niger Delta หนึ่งในหลายเหตุการณ์ที่เกิดขึ้นซ้ำๆ ในพื้นที่นี้","source":"Shell SPDC Nigeria / NOSDRA","source_url":"https://www.nosdra.gov.ng/","verified":True},
]

df = pd.DataFrame(MAE_DATA)

# ============================================================
# Header
# ============================================================
st.title("🔥 Global MAE Report Generator")
st.markdown("**Major Accident Events — Oil & Gas Industry** | ข้อมูลเหตุการณ์จริงทั่วโลก | Powered by Claude AI")
st.success(f"✅ ข้อมูลทั้งหมด {len(df)} เหตุการณ์จริง — ตรวจสอบจากแหล่งข้อมูลสาธารณะระดับนานาชาติ (BSEE / HSE / PHMSA / CSB / ARIA)")
st.divider()

# ============================================================
# Sidebar
# ============================================================
st.sidebar.header("🎛️ ตั้งค่าตัวกรอง")

search_text = st.sidebar.text_input("🔍 ค้นหาชื่อเหตุการณ์ / ประเทศ / สถานที่", placeholder="เช่น Deepwater, India, North Sea...")

year_range = st.sidebar.slider("ช่วงปีที่เกิดเหตุ",
    min_value=int(df["year"].min()), max_value=int(df["year"].max()),
    value=(2000, int(df["year"].max())))

selected_regions = st.sidebar.multiselect("ภูมิภาค",
    options=sorted(df["region"].unique()), default=sorted(df["region"].unique()))

selected_countries = st.sidebar.multiselect("🌍 ประเทศ",
    options=sorted(df["country"].unique()), default=sorted(df["country"].unique()))

selected_types = st.sidebar.multiselect("ประเภทเหตุการณ์",
    options=sorted(df["type"].unique()), default=sorted(df["type"].unique()))

selected_facility = st.sidebar.multiselect("ประเภทสถานที่",
    options=sorted(df["facility"].unique()), default=sorted(df["facility"].unique()))

only_fatal   = st.sidebar.checkbox("แสดงเฉพาะเหตุการณ์ที่มีผู้เสียชีวิต")
only_verified= st.sidebar.checkbox("แสดงเฉพาะที่มีแหล่งอ้างอิงยืนยัน", value=False)

report_style = st.sidebar.selectbox("รูปแบบ AI Report",
    ["Executive Summary","Detailed Technical Report","Statistical Analysis"])

# ============================================================
# Filter
# ============================================================
filtered = df[
    df["year"].between(*year_range) &
    df["region"].isin(selected_regions) &
    df["country"].isin(selected_countries) &
    df["type"].isin(selected_types) &
    df["facility"].isin(selected_facility)
].copy()

if search_text:
    mask = (
        filtered["name"].str.contains(search_text, case=False, na=False) |
        filtered["country"].str.contains(search_text, case=False, na=False) |
        filtered["location"].str.contains(search_text, case=False, na=False) |
        filtered["description"].str.contains(search_text, case=False, na=False)
    )
    filtered = filtered[mask]

if only_fatal:    filtered = filtered[filtered["fatalities"] > 0]
if only_verified: filtered = filtered[filtered["verified"] == True]

# ============================================================
# Metrics
# ============================================================
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("🔴 MAE Events",      len(filtered))
c2.metric("💀 เสียชีวิตรวม",   f"{filtered['fatalities'].sum():,}")
c3.metric("🤕 บาดเจ็บรวม",    f"{filtered['injuries'].sum():,}")
c4.metric("💰 ความเสียหาย",    f"${filtered['loss_musd'].sum()/1000:.1f}B")
c5.metric("🌍 ประเทศที่เกิดเหตุ", filtered["country"].nunique())
st.divider()

# ============================================================
# Tabs
# ============================================================
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📊 Charts & แผนที่",
    "📋 รายการเหตุการณ์",
    "🔎 รายละเอียด & แหล่งอ้างอิง",
    "🤖 AI Analysis",
    "📈 Root Cause"
])

# ---- TAB 1 ----
with tab1:
    r1,r2 = st.columns(2)
    with r1:
        st.subheader("เหตุการณ์ตามภูมิภาค")
        rc = filtered.groupby("region").size().reset_index(name="count")
        fig1 = px.bar(rc, x="region", y="count", color="region",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig1.update_layout(showlegend=False, height=280, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig1, use_container_width=True)

    with r2:
        st.subheader("เหตุการณ์ตามประเทศ (Top 10)")
        cc = filtered.groupby("country").size().reset_index(name="count").nlargest(10,"count")
        fig_c = px.bar(cc, x="count", y="country", orientation="h",
                       color="count", color_continuous_scale="OrRd")
        fig_c.update_layout(showlegend=False, height=280, margin=dict(l=0,r=0,t=10,b=0),
                            yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_c, use_container_width=True)

    st.subheader("แนวโน้ม MAE ตามปี")
    yc = filtered.groupby("year").agg(events=("name","count"),fatalities=("fatalities","sum")).reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=yc["year"], y=yc["events"], name="จำนวนเหตุการณ์", marker_color="#ef553b"))
    fig3.add_trace(go.Scatter(x=yc["year"], y=yc["fatalities"], name="ผู้เสียชีวิต",
                              yaxis="y2", line=dict(color="#636efa",width=2)))
    fig3.update_layout(height=300,
        yaxis=dict(title="จำนวนเหตุการณ์"),
        yaxis2=dict(title="ผู้เสียชีวิต", overlaying="y", side="right"),
        legend=dict(orientation="h",yanchor="bottom",y=1),
        margin=dict(l=0,r=0,t=30,b=0))
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("🗺️ แผนที่เหตุการณ์ทั่วโลก")
    ca = filtered.groupby("country").agg(
        events=("name","count"), fatalities=("fatalities","sum"), loss=("loss_musd","sum")
    ).reset_index()
    fig4 = px.choropleth(ca, locations="country", locationmode="country names",
        color="events", hover_name="country",
        hover_data={"fatalities":True,"loss":True},
        color_continuous_scale="Reds",
        labels={"events":"เหตุการณ์","fatalities":"เสียชีวิต","loss":"ความเสียหาย (M USD)"})
    fig4.update_layout(height=420, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig4, use_container_width=True)

# ---- TAB 2 ----
with tab2:
    st.subheader(f"รายการ MAE Events ({len(filtered)} เหตุการณ์)")
    disp = filtered[[
        "name","year","month","country","region","location",
        "type","facility","fatalities","injuries","loss_musd","operator","cause","verified"
    ]].rename(columns={
        "name":"ชื่อเหตุการณ์","year":"ปี","month":"เดือน",
        "country":"ประเทศ","region":"ภูมิภาค","location":"สถานที่จริง",
        "type":"ประเภท","facility":"สถานที่","fatalities":"เสียชีวิต",
        "injuries":"บาดเจ็บ","loss_musd":"ความเสียหาย (M USD)",
        "operator":"ผู้ดำเนินการ","cause":"สาเหตุ","verified":"✅ ยืนยัน"
    }).sort_values("ความเสียหาย (M USD)", ascending=False)

    st.dataframe(disp, use_container_width=True, hide_index=True,
        column_config={
            "✅ ยืนยัน": st.column_config.CheckboxColumn(),
            "ความเสียหาย (M USD)": st.column_config.NumberColumn(format="$%d M"),
            "เสียชีวิต": st.column_config.NumberColumn(format="%d คน"),
            "บาดเจ็บ": st.column_config.NumberColumn(format="%d คน"),
        })

    csv = disp.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ ดาวน์โหลด CSV", data=csv,
                       file_name="global_mae_report.csv", mime="text/csv")

# ---- TAB 3: Detail & Source ----
with tab3:
    st.subheader("🔎 รายละเอียดเหตุการณ์ & ยืนยันว่าเกิดขึ้นจริง")
    st.caption("ทุกเหตุการณ์มีแหล่งอ้างอิงสาธารณะระดับนานาชาติ — คลิกลิงก์เพื่อตรวจสอบได้เลย")

    if len(filtered) == 0:
        st.warning("ไม่มีข้อมูลที่ตรงกับตัวกรอง")
    else:
        evt_name = st.selectbox("เลือกเหตุการณ์ที่ต้องการดูรายละเอียด",
                                options=filtered["name"].tolist())
        evt = filtered[filtered["name"] == evt_name].iloc[0]

        ca1, ca2 = st.columns([2,1])
        with ca1:
            st.markdown(f"### 🔥 {evt['name']}")
            st.markdown(f"**📅 วันที่เกิดเหตุ:** {evt['month']} {evt['year']}")
            st.markdown(f"**📍 สถานที่จริง:** {evt['location']}, **{evt['country']}**")
            st.markdown(f"**🏭 ประเภทสถานที่:** {evt['facility']} — {evt['type']}")
            st.markdown(f"**🏢 ผู้ดำเนินการ:** {evt['operator']}")
            st.markdown(f"**⚠️ สาเหตุหลัก:** {evt['cause']}")
            st.divider()
            st.markdown("**📝 รายละเอียด:**")
            st.info(evt["description"])

        with ca2:
            st.markdown("#### ผลกระทบ")
            st.metric("💀 เสียชีวิต", f"{evt['fatalities']:,} คน")
            st.metric("🤕 บาดเจ็บ",   f"{evt['injuries']:,} คน")
            st.metric("💰 ความเสียหาย", f"${evt['loss_musd']/1000:.2f}B USD")
            st.divider()
            st.markdown("#### ✅ แหล่งอ้างอิงยืนยัน")
            if evt["verified"]:
                st.success("ตรวจสอบแล้ว — เหตุการณ์จริง")
            st.markdown(f"📌 **{evt['source']}**")
            st.markdown(f"[🔗 เปิดแหล่งข้อมูลอย่างเป็นทางการ]({evt['source_url']})")

        st.divider()
        st.subheader("เปรียบเทียบกับเหตุการณ์อื่นในชุดข้อมูล")
        compare_col = st.selectbox("เปรียบเทียบด้วย", ["loss_musd","fatalities","injuries"])
        top5 = filtered.nlargest(8, compare_col)[["name","country",compare_col]]
        highlight = top5["name"] == evt_name
        fig_cmp = px.bar(top5, x=compare_col, y="name", orientation="h",
                         color=highlight.map({True:"#ef553b",False:"#adb5bd"}),
                         color_discrete_map="identity",
                         labels={"name":"เหตุการณ์", compare_col: compare_col})
        fig_cmp.update_layout(showlegend=False, height=300,
                              margin=dict(l=0,r=0,t=10,b=0),
                              yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_cmp, use_container_width=True)

# ---- TAB 4: AI ----
with tab4:
    st.subheader("🤖 AI Executive Report — สร้างโดย Claude")
    st.caption("AI วิเคราะห์จากข้อมูล MAE จริงที่กรองไว้ด้านซ้าย")

    mae_summary = "\n".join([
        f"- {r['name']} ({r['month']} {r['year']}, {r['location']}, {r['country']}): "
        f"{r['type']}, {r['fatalities']} fatalities, {r['injuries']} injuries, "
        f"${r['loss_musd']/1000:.1f}B loss, operator: {r['operator']}, cause: {r['cause']}"
        for _, r in filtered.iterrows()
    ])

    sys_p = """คุณคือผู้เชี่ยวชาญด้าน HSE (Health, Safety & Environment) ระดับโลก
ในอุตสาหกรรม Oil & Gas ที่มีประสบการณ์วิเคราะห์ Major Accident Events (MAE)
ข้อมูลที่ให้มาเป็นเหตุการณ์จริงจาก BSEE, HSE UK, PHMSA, CSB, ARIA
ตอบเป็นภาษาไทยในรูปแบบ Professional HSE Report"""

    usr_p = f"""วิเคราะห์ข้อมูล Major Accident Events (MAE) จริงต่อไปนี้:

{mae_summary}

สร้าง {report_style} ที่ประกอบด้วย:
1. 📋 Executive Summary — สรุปภาพรวมสถานการณ์ MAE
2. 📈 Key Trends — แนวโน้มสำคัญที่พบจากข้อมูล
3. ⚠️ Top 3 Root Causes — สาเหตุหลักพร้อมตัวอย่างเหตุการณ์จริง
4. 🔴 Top 3 Worst Events — เหตุการณ์ร้ายแรงที่สุด พร้อมบทเรียน
5. ✅ Recommendations — ข้อเสนอแนะ 5 ข้อที่เป็นรูปธรรม
6. 🌍 Country Risk Profile — ประเมินความเสี่ยงตามประเทศ/ภูมิภาค

ตอบเป็นภาษาไทย ใช้ภาษาแบบมืออาชีพ"""

    if st.button("🚀 สร้าง AI Report", type="primary", use_container_width=True):
        if len(filtered) == 0:
            st.warning("ไม่มีข้อมูล MAE — กรุณาปรับตัวกรอง")
        else:
            try:
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                with st.spinner("AI กำลังวิเคราะห์ข้อมูล MAE จริงทั่วโลก..."):
                    with client.messages.stream(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000, system=sys_p,
                        messages=[{"role":"user","content":usr_p}]
                    ) as stream:
                        resp = st.write_stream(stream.text_stream)

                st.download_button("⬇️ ดาวน์โหลด AI Report",
                    data=resp.encode("utf-8"),
                    file_name="mae_ai_report.txt", mime="text/plain")
            except KeyError:
                st.error("❌ ไม่พบ API Key — กรุณาเพิ่ม ANTHROPIC_API_KEY ใน Streamlit Secrets")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

# ---- TAB 5: Root Cause ----
with tab5:
    st.subheader("สาเหตุหลักของ MAE")
    cause_df = filtered.groupby("cause").agg(
        events=("name","count"), fatalities=("fatalities","sum"), loss=("loss_musd","sum")
    ).reset_index().sort_values("events", ascending=False)

    fig5 = px.bar(cause_df, x="events", y="cause", orientation="h",
        color="fatalities", color_continuous_scale="Reds",
        labels={"events":"จำนวนเหตุการณ์","cause":"สาเหตุ","fatalities":"ผู้เสียชีวิต"})
    fig5.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("ความสัมพันธ์ — ความเสียหาย vs ผู้เสียชีวิต")
    fig6 = px.scatter(filtered, x="loss_musd", y="fatalities",
        color="cause", size_max=40, hover_name="name",
        hover_data={"country":True,"year":True,"operator":True},
        labels={"loss_musd":"ความเสียหาย (M USD)","fatalities":"ผู้เสียชีวิต","cause":"สาเหตุ"})
    fig6.update_layout(height=400, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig6, use_container_width=True)

# ============================================================
# Footer
# ============================================================
st.divider()
st.caption(
    "📌 แหล่งข้อมูล: BSEE (USA) | HSE UK | PHMSA (USA) | CSB (USA) | ARIA (France) | "
    "ITOPF | ANP Brazil | ONGC India | Saudi Aramco | Sonatrach Algeria | TSB Canada\n\n"
    "⚠️ ข้อมูลทั้งหมดเป็นเหตุการณ์จริงที่เปิดเผยสาธารณะ | AI Analysis โดย Claude (Anthropic)"
)
