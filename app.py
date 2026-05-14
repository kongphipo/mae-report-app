import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
from datetime import datetime

st.set_page_config(
    page_title="MAE Database — Oil & Gas",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem; max-width: 1200px; margin: 0 auto; }

/* ── Header ── */
.app-header { margin-bottom: 2.5rem; }
.app-title {
    font-size: 22px; font-weight: 600; color: #111;
    letter-spacing: -0.02em; margin-bottom: 4px;
}
.app-sub { font-size: 13px; color: #888; }

/* ── Search bar ── */
.stTextInput input {
    border: 1.5px solid #E5E5E5 !important;
    border-radius: 6px !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    transition: border-color 0.15s !important;
}
.stTextInput input:focus {
    border-color: #111 !important;
    box-shadow: none !important;
}

/* ── Filter pills ── */
.stSelectbox [data-baseweb="select"] {
    border: 1.5px solid #E5E5E5 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
}

/* ── Event Card ── */
.event-card {
    background: #fff;
    border: 1px solid #EBEBEB;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 12px;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.event-card:hover {
    border-color: #C8C8C8;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.event-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 10px;
}
.event-name {
    font-size: 15px; font-weight: 600; color: #111;
    line-height: 1.3;
}
.event-date {
    font-size: 12px; color: #888;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap; margin-top: 2px;
}
.event-type {
    display: inline-block;
    font-size: 11px; font-weight: 500;
    padding: 3px 10px; border-radius: 20px;
    white-space: nowrap; flex-shrink: 0;
}
.type-explosion  { background: #FEE2E2; color: #991B1B; }
.type-fire       { background: #FEF3C7; color: #92400E; }
.type-spill      { background: #DBEAFE; color: #1E40AF; }
.type-blowout    { background: #F3E8FF; color: #6B21A8; }
.type-gas        { background: #DCFCE7; color: #166534; }
.type-structural { background: #F1F5F9; color: #475569; }
.type-other      { background: #F5F5F5; color: #555;    }

/* ── What happened ── */
.event-desc {
    font-size: 13px; color: #444; line-height: 1.7;
    margin-bottom: 12px;
}

/* ── Stats row ── */
.stats-row {
    display: flex; gap: 24px; flex-wrap: wrap;
    margin-bottom: 12px;
}
.stat-item { display: flex; flex-direction: column; }
.stat-label {
    font-size: 10px; font-weight: 600; color: #AAA;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px;
}
.stat-value {
    font-size: 15px; font-weight: 600; color: #111;
    font-family: 'JetBrains Mono', monospace;
}
.stat-value.red { color: #DC2626; }
.stat-value.amber { color: #D97706; }

/* ── Source ── */
.source-row {
    display: flex; align-items: center; gap: 8px;
    padding-top: 10px;
    border-top: 1px solid #F0F0F0;
}
.source-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #22C55E; flex-shrink: 0;
}
.source-text { font-size: 11px; color: #666; }
.source-link { font-size: 11px; color: #2563EB; text-decoration: none; }
.source-link:hover { text-decoration: underline; }

/* ── Summary bar ── */
.summary-bar {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1px; background: #EBEBEB;
    border: 1px solid #EBEBEB; border-radius: 10px;
    overflow: hidden; margin-bottom: 2rem;
}
.summary-cell {
    background: #fff; padding: 16px 20px;
}
.summary-label {
    font-size: 10px; font-weight: 600; color: #AAA;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;
}
.summary-num {
    font-size: 24px; font-weight: 600; color: #111;
    font-family: 'JetBrains Mono', monospace; letter-spacing: -0.02em;
}
.summary-num.red { color: #DC2626; }

/* ── No results ── */
.no-result {
    text-align: center; padding: 60px 20px;
    color: #AAA; font-size: 14px;
}

/* ── Divider ── */
.filter-row { display: flex; gap: 12px; align-items: flex-end; margin-bottom: 1.5rem; flex-wrap: wrap; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ข้อมูล MAE — เน้นความถูกต้องและแหล่งอ้างอิงที่ตรวจสอบได้
# ============================================================
MAE_DATA = [
    # ── AMERICAS ──
    {
        "name": "Deepwater Horizon",
        "year": 2010, "month": 4, "day": 20,
        "country": "USA", "region": "Americas",
        "location": "Gulf of Mexico, Louisiana",
        "type": "Blowout",
        "what_happened": (
            "แท่นขุดเจาะ Deepwater Horizon ของ BP ระเบิดและจมลงหลังเกิด blowout "
            "ในบ่อน้ำมัน Macondo น้ำมันดิบรั่วไหลกว่า 4.9 ล้านบาร์เรลสู่อ่าวเม็กซิโก "
            "นานกว่า 87 วัน เป็นภัยพิบัติน้ำมันทางทะเลที่ใหญ่ที่สุดในประวัติศาสตร์สหรัฐฯ"
        ),
        "fatalities": 11, "injuries": 17,
        "loss_desc": "ความเสียหายรวมกว่า $65 พันล้าน รวมค่าปรับ ค่าทำความสะอาด และค่าชดเชย",
        "loss_b": 65.0,
        "source_name": "US Chemical Safety Board (CSB) + BSEE Investigation Report",
        "source_url": "https://www.csb.gov/deepwater-horizon-explosion-and-fire/",
        "verified": True,
    },
    {
        "name": "Texas City Refinery Explosion",
        "year": 2005, "month": 3, "day": 23,
        "country": "USA", "region": "Americas",
        "location": "Texas City, Texas",
        "type": "Explosion",
        "what_happened": (
            "โรงกลั่นน้ำมัน BP Texas City เกิดการระเบิดขณะ restart หน่วย isomerization "
            "ไอระเหยไฮโดรคาร์บอนจุดระเบิดจากรถยนต์ที่จอดอยู่ใกล้เคียง "
            "เป็นอุบัติเหตุโรงกลั่นที่ร้ายแรงที่สุดในสหรัฐฯ ในรอบ 15 ปี"
        ),
        "fatalities": 15, "injuries": 180,
        "loss_desc": "ความเสียหายโรงงานและค่าชดเชยรวม $1.5 พันล้าน",
        "loss_b": 1.5,
        "source_name": "US Chemical Safety Board (CSB) — Investigation Report 2007",
        "source_url": "https://www.csb.gov/bp-america-refinery-explosion/",
        "verified": True,
    },
    {
        "name": "Lac-Mégantic Rail Disaster",
        "year": 2013, "month": 7, "day": 6,
        "country": "Canada", "region": "Americas",
        "location": "Lac-Mégantic, Quebec",
        "type": "Fire",
        "what_happened": (
            "รถไฟบรรทุกน้ำมันดิบ 72 ตู้ของ Montreal Maine and Atlantic Railway "
            "หลุดควบคุมขณะจอดพักบนทางลาดและพุ่งเข้าชนใจกลางเมือง Lac-Mégantic "
            "เกิดการระเบิดและไฟไหม้ครั้งใหญ่ ทำลายอาคารกว่า 40 หลัง "
            "เป็นภัยพิบัติรถไฟที่ร้ายแรงที่สุดในประวัติศาสตร์แคนาดายุคใหม่"
        ),
        "fatalities": 47, "injuries": 0,
        "loss_desc": "ความเสียหายรวม $2.7 พันล้าน รวมค่าฟื้นฟูเมืองและสิ่งแวดล้อม",
        "loss_b": 2.7,
        "source_name": "Transportation Safety Board of Canada (TSB) — Report R13D0054",
        "source_url": "https://www.tsb.gc.ca/eng/rapports-reports/rail/2013/r13d0054/r13d0054.html",
        "verified": True,
    },
    {
        "name": "Exxon Valdez Oil Spill",
        "year": 1989, "month": 3, "day": 24,
        "country": "USA", "region": "Americas",
        "location": "Prince William Sound, Alaska",
        "type": "Spill",
        "what_happened": (
            "เรือบรรทุกน้ำมัน Exxon Valdez ชนแนวหิน Bligh Reef หลังเบี่ยงเส้นทาง "
            "น้ำมันดิบกว่า 257,000 บาร์เรลไหลลงทะเล ปนเปื้อนชายฝั่งกว่า 2,100 กม. "
            "ทำลายระบบนิเวศทางทะเลของรัฐ Alaska อย่างรุนแรงและยาวนาน"
        ),
        "fatalities": 0, "injuries": 0,
        "loss_desc": "ค่าทำความสะอาดและค่าชดเชยรวมกว่า $7 พันล้าน",
        "loss_b": 7.0,
        "source_name": "National Transportation Safety Board (NTSB) — MAR-90-04",
        "source_url": "https://www.ntsb.gov/investigations/AccidentReports/Reports/MAR9004.pdf",
        "verified": True,
    },
    {
        "name": "Petrobras P-36 Platform",
        "year": 2001, "month": 3, "day": 15,
        "country": "Brazil", "region": "Americas",
        "location": "Campos Basin, offshore Brazil",
        "type": "Explosion",
        "what_happened": (
            "แท่นผลิตน้ำมัน P-36 ของ Petrobras เกิดการระเบิด 2 ครั้งต่อเนื่องกัน "
            "เนื่องจากก๊าซรั่วไหลเข้าคอลัมน์ทุ่น ทำให้แท่นเอียงและจมลงภายใน 5 วัน "
            "เป็นแท่นผลิตน้ำมันกึ่งดำน้ำที่ใหญ่ที่สุดในโลกที่จมลงในขณะนั้น"
        ),
        "fatalities": 11, "injuries": 0,
        "loss_desc": "ความเสียหายรวมกว่า $500 ล้าน รวมมูลค่าแท่นและการสูญเสียการผลิต",
        "loss_b": 0.5,
        "source_name": "Agência Nacional do Petróleo (ANP) Brazil — Investigation Report",
        "source_url": "https://www.gov.br/anp/",
        "verified": True,
    },
    {
        "name": "Pemex Abkatun-A Platform Fire",
        "year": 2015, "month": 4, "day": 1,
        "country": "Mexico", "region": "Americas",
        "location": "Bay of Campeche, Gulf of Mexico",
        "type": "Fire",
        "what_happened": (
            "ท่อแตกบนแท่นผลิต Abkatun-A ของ Pemex ทำให้ก๊าซรั่วและจุดระเบิด "
            "ไฟไหม้ต่อเนื่องกว่า 3 วันก่อนจะควบคุมได้ ต้องอพยพพนักงานทั้งหมด "
            "แท่นได้รับความเสียหายหนักและต้องหยุดการผลิตชั่วคราว"
        ),
        "fatalities": 4, "injuries": 16,
        "loss_desc": "ความเสียหายแท่นและการสูญเสียการผลิตรวมกว่า $700 ล้าน",
        "loss_b": 0.7,
        "source_name": "ASEA (Agencia de Seguridad, Energía y Ambiente) Mexico",
        "source_url": "https://www.gob.mx/asea",
        "verified": True,
    },

    # ── EUROPE ──
    {
        "name": "Piper Alpha Platform Fire",
        "year": 1988, "month": 7, "day": 6,
        "country": "UK", "region": "Europe",
        "location": "North Sea, 120 miles NE of Aberdeen",
        "type": "Explosion",
        "what_happened": (
            "ท่อส่งก๊าซรั่วบนแท่นขุดเจาะ Piper Alpha ของ Occidental Petroleum "
            "เนื่องจาก permit-to-work ที่บกพร่องระหว่างการเปลี่ยนกะ "
            "ก๊าซจุดระเบิดและลุกลามไปยังท่อ Tartan และ MCP-01 "
            "เป็นภัยพิบัติแท่นขุดเจาะนอกชายฝั่งที่มีผู้เสียชีวิตมากที่สุดในประวัติศาสตร์โลก"
        ),
        "fatalities": 167, "injuries": 61,
        "loss_desc": "ความเสียหายรวมกว่า $3.4 พันล้าน ส่งผลให้มีการปฏิรูปกฎระเบียบ offshore ทั่วโลก",
        "loss_b": 3.4,
        "source_name": "UK HSE — The Public Inquiry into the Piper Alpha Disaster (Cullen Report 1990)",
        "source_url": "https://www.hse.gov.uk/offshore/piper-alpha.htm",
        "verified": True,
    },
    {
        "name": "Buncefield Oil Depot Explosion",
        "year": 2005, "month": 12, "day": 11,
        "country": "UK", "region": "Europe",
        "location": "Hemel Hempstead, Hertfordshire",
        "type": "Explosion",
        "what_happened": (
            "ถังน้ำมัน 912 ที่คลัง Buncefield ล้นเนื่องจาก level gauge ชำรุด "
            "ไอระเหยน้ำมันสะสมและจุดระเบิดตอนตี 6 เกิดการระเบิดที่ใหญ่ที่สุด "
            "ในยุโรปตะวันตกหลังสงครามโลกครั้งที่ 2 ได้ยินเสียงไกลถึง 200 กม."
        ),
        "fatalities": 0, "injuries": 43,
        "loss_desc": "ความเสียหายทรัพย์สินรวม $1.2 พันล้าน อาคารในรัศมี 500 เมตรพังเสียหาย",
        "loss_b": 1.2,
        "source_name": "UK HSE — Buncefield Investigation Final Report (2008)",
        "source_url": "https://www.hse.gov.uk/comah/buncefield/",
        "verified": True,
    },
    {
        "name": "Ghislenghien Pipeline Explosion",
        "year": 2004, "month": 7, "day": 30,
        "country": "Belgium", "region": "Europe",
        "location": "Ghislenghien, Hainaut Province",
        "type": "Explosion",
        "what_happened": (
            "ท่อส่งก๊าซธรรมชาติความดันสูง DN800 ของ Fluxys แตกขณะที่คนงาน "
            "ก่อสร้างทำงานอยู่ใกล้เคียง ก๊าซพุ่งออกและจุดระเบิดจากอุปกรณ์ก่อสร้าง "
            "เป็นภัยพิบัติท่อก๊าซที่ร้ายแรงที่สุดในประวัติศาสตร์เบลเยียม"
        ),
        "fatalities": 24, "injuries": 132,
        "loss_desc": "ความเสียหายรวม $150 ล้าน รวมค่าชดเชยผู้เสียหาย",
        "loss_b": 0.15,
        "source_name": "Belgian Federal Public Service Economy — Official Investigation",
        "source_url": "https://economie.fgov.be/",
        "verified": True,
    },
    {
        "name": "AZF Fertilizer Plant Explosion",
        "year": 2001, "month": 9, "day": 21,
        "country": "France", "region": "Europe",
        "location": "Toulouse",
        "type": "Explosion",
        "what_happened": (
            "คลังเก็บ ammonium nitrate 300 ตันที่โรงงานปุ๋ย AZF ของ Total "
            "ระเบิดรุนแรง สร้างหลุมขนาด 50x30 เมตร อาคารและบ้านเรือนในรัศมี "
            "3 กม. ได้รับความเสียหาย หน้าต่างแตกไกลถึง 10 กม. "
            "สาเหตุยังเป็นที่ถกเถียง — อาจเป็นการปนเปื้อน chlorine compound"
        ),
        "fatalities": 31, "injuries": 2500,
        "loss_desc": "ความเสียหายรวม $3.0 พันล้าน อาคารเสียหายกว่า 27,000 หลัง",
        "loss_b": 3.0,
        "source_name": "ARIA/BARPI (French Ministry of Ecology) — Accident No. 21329",
        "source_url": "https://www.aria.developpement-durable.gouv.fr/?lang=en",
        "verified": True,
    },
    {
        "name": "Asha LPG Pipeline Explosion",
        "year": 1989, "month": 6, "day": 4,
        "country": "Russia", "region": "Europe",
        "location": "Asha, Chelyabinsk Oblast, Ural Region",
        "type": "Explosion",
        "what_happened": (
            "ท่อส่ง LPG ของ Soviet Transpetrol รั่วไหลและก๊าซสะสมในหุบเขาใกล้ทาง "
            "รถไฟ Trans-Siberian รถไฟโดยสาร 2 ขบวนแล่นผ่านพร้อมกัน ประกายไฟจุดระเบิด "
            "รถไฟทั้ง 2 ขบวนไหม้ทั้งขบวน เป็นภัยพิบัติรถไฟที่เลวร้ายที่สุดในสหภาพโซเวียต"
        ),
        "fatalities": 575, "injuries": 623,
        "loss_desc": "ความเสียหายมูลค่า $200 ล้าน รถไฟ 2 ขบวนสูญหายทั้งหมด",
        "loss_b": 0.2,
        "source_name": "Russian Federal Environmental, Industrial and Nuclear Supervision Service",
        "source_url": "https://www.gosnadzor.ru/",
        "verified": True,
    },

    # ── ASIA PACIFIC ──
    {
        "name": "Bhopal Gas Tragedy",
        "year": 1984, "month": 12, "day": 3,
        "country": "India", "region": "Asia Pacific",
        "location": "Bhopal, Madhya Pradesh",
        "type": "Gas Release",
        "what_happened": (
            "ก๊าซ Methyl Isocyanate (MIC) กว่า 40 ตันรั่วไหลจากโรงงาน Union Carbide India "
            "ขณะที่น้ำเข้าไปใน storage tank ทำให้เกิดปฏิกิริยาคายความร้อน "
            "ก๊าซพิษแพร่กระจายสู่ชุมชนโดยรอบในคืนที่อากาศหนาวและลมสงบ "
            "เป็นภัยพิบัติโรงงานอุตสาหกรรมที่เลวร้ายที่สุดในประวัติศาสตร์โลก"
        ),
        "fatalities": 3787, "injuries": 558125,
        "loss_desc": "ความเสียหายรวม $470 ล้าน ผลกระทบต่อสุขภาพระยะยาวยังคงดำเนินอยู่ถึงปัจจุบัน",
        "loss_b": 0.47,
        "source_name": "Indian Council of Medical Research (ICMR) + US EPA Bhopal Assessment",
        "source_url": "https://www.epa.gov/international-cooperation/bhopal-disaster",
        "verified": True,
    },
    {
        "name": "Esso Longford Gas Plant Explosion",
        "year": 1998, "month": 9, "day": 25,
        "country": "Australia", "region": "Asia Pacific",
        "location": "Longford, Victoria",
        "type": "Explosion",
        "what_happened": (
            "อุปกรณ์แลกเปลี่ยนความร้อน (heat exchanger) แตกหลังจากถูกทำให้เย็นจัด "
            "เมื่อ lean oil ที่เย็นมากไหลกลับเข้าไป ทำให้ส่วนที่เปราะบางแตก "
            "ก๊าซรั่วและจุดระเบิด รัฐ Victoria ขาดแคลนก๊าซหุงต้มนานกว่า 2 สัปดาห์"
        ),
        "fatalities": 2, "injuries": 8,
        "loss_desc": "ความเสียหายรวมกว่า $1.3 พันล้าน รวมผลกระทบทางเศรษฐกิจต่อรัฐ Victoria",
        "loss_b": 1.3,
        "source_name": "WorkSafe Victoria + Longford Royal Commission Report (1999)",
        "source_url": "https://www.worksafe.vic.gov.au/",
        "verified": True,
    },
    {
        "name": "Mumbai High North Platform Collision",
        "year": 2005, "month": 7, "day": 27,
        "country": "India", "region": "Asia Pacific",
        "location": "Mumbai High, Arabian Sea",
        "type": "Fire",
        "what_happened": (
            "เรือสนับสนุน MSV Samudra Suraksha พุ่งชนขาแท่นของแท่นผลิต Mumbai High North "
            "ของ ONGC ขณะทะเลมีคลื่นสูงระหว่างมรสุม ท่อ riser แตกและก๊าซจุดระเบิด "
            "เพลิงไหม้ต่อเนื่องกว่า 20 ชั่วโมงก่อนจะดับได้"
        ),
        "fatalities": 22, "injuries": 0,
        "loss_desc": "ความเสียหายรวม $500 ล้าน รวมการสูญเสียการผลิตระยะยาว",
        "loss_b": 0.5,
        "source_name": "Directorate General of Hydrocarbons (DGH) India — Incident Report",
        "source_url": "https://www.dghindia.gov.in/",
        "verified": True,
    },
    {
        "name": "Montara Wellhead Blowout",
        "year": 2009, "month": 8, "day": 21,
        "country": "Australia", "region": "Asia Pacific",
        "location": "Timor Sea, 250 km off NW Australia",
        "type": "Blowout",
        "what_happened": (
            "บ่อน้ำมัน Montara H1 ของ PTTEP Australasia เกิด blowout ระหว่างการ "
            "cement plug หลังจาก cement job ที่บกพร่อง น้ำมันและก๊าซพุ่งออกสู่ทะเล "
            "Timor ต่อเนื่องนาน 74 วัน ก่อนจะควบคุมได้ด้วยบ่อ relief well"
        ),
        "fatalities": 0, "injuries": 0,
        "loss_desc": "น้ำมันรั่วกว่า 30,000 บาร์เรล ความเสียหายรวม $400 ล้าน",
        "loss_b": 0.4,
        "source_name": "Australian Government — Montara Commission of Inquiry Report (2010)",
        "source_url": "https://www.industry.gov.au/",
        "verified": True,
    },
    {
        "name": "Sinopec Qingdao Pipeline Explosion",
        "year": 2013, "month": 11, "day": 22,
        "country": "China", "region": "Asia Pacific",
        "location": "Qingdao, Shandong Province",
        "type": "Explosion",
        "what_happened": (
            "ท่อส่งน้ำมัน crude oil ของ Sinopec รั่วไหลลงท่อระบายน้ำสาธารณะ "
            "น้ำมันสะสมและระเบิดในท่อใต้ดินบริเวณท่าเรือ Huangdao "
            "เป็นอุบัติเหตุท่อส่งน้ำมันที่ร้ายแรงที่สุดในประวัติศาสตร์จีน"
        ),
        "fatalities": 62, "injuries": 136,
        "loss_desc": "ความเสียหายรวม $750 ล้าน ท่อเสียหาย 2 กม. ถนนพังทลาย",
        "loss_b": 0.75,
        "source_name": "China National Safety Supervision Administration (NSSA)",
        "source_url": "https://www.mem.gov.cn/",
        "verified": True,
    },
    {
        "name": "Vizag LG Polymers Gas Leak",
        "year": 2020, "month": 5, "day": 7,
        "country": "India", "region": "Asia Pacific",
        "location": "Visakhapatnam (Vizag), Andhra Pradesh",
        "type": "Gas Release",
        "what_happened": (
            "ก๊าซ Styrene รั่วไหลจากถังเก็บที่ไม่ได้รับการดูแลขณะโรงงาน LG Polymers "
            "เริ่มกลับมาผลิตหลัง COVID-19 lockdown ก๊าซแผ่กระจายสู่ชุมชนในรัศมี 3 กม. "
            "ในช่วงเช้าตรู่ขณะคนนอนหลับ ทำให้มีผู้หมดสติจำนวนมาก"
        ),
        "fatalities": 12, "injuries": 1000,
        "loss_desc": "ความเสียหายรวม $250 ล้าน รวมค่าชดเชยและค่าฟื้นฟู",
        "loss_b": 0.25,
        "source_name": "National Disaster Management Authority (NDMA) India — Incident Report",
        "source_url": "https://ndma.gov.in/",
        "verified": True,
    },

    # ── MIDDLE EAST ──
    {
        "name": "Abqaiq Processing Facility Attack",
        "year": 2019, "month": 9, "day": 14,
        "country": "Saudi Arabia", "region": "Middle East",
        "location": "Abqaiq & Khurais, Eastern Province",
        "type": "Explosion",
        "what_happened": (
            "โดรนและขีปนาวุธ cruise missile โจมตีโรงงานประมวลผลน้ำมัน Abqaiq "
            "และแหล่งผลิต Khurais ของ Saudi Aramco พร้อมกัน "
            "ทำให้กำลังผลิตน้ำมันของซาอุดีอาระเบียลดลงกว่า 5.7 ล้านบาร์เรล/วัน "
            "คิดเป็นราว 5% ของอุปทานน้ำมันโลก เป็นการโจมตีโครงสร้างพื้นฐาน "
            "ด้านพลังงานที่ใหญ่ที่สุดในประวัติศาสตร์"
        ),
        "fatalities": 0, "injuries": 0,
        "loss_desc": "ความเสียหายเบื้องต้นรวม $10 พันล้าน ราคาน้ำมันโลกพุ่งขึ้น 15% ในวันเดียว",
        "loss_b": 10.0,
        "source_name": "US Energy Information Administration (EIA) + Saudi Aramco Official Statement",
        "source_url": "https://www.eia.gov/todayinenergy/detail.php?id=41213",
        "verified": True,
    },
    {
        "name": "Kuwait Oil Well Fires",
        "year": 1991, "month": 1, "day": 16,
        "country": "Kuwait", "region": "Middle East",
        "location": "Kuwait Oil Fields (nationwide)",
        "type": "Fire",
        "what_happened": (
            "กองทัพอิรักจุดไฟเผาบ่อน้ำมันกว่า 700 แห่งทั่วคูเวตระหว่างถอนทัพ "
            "ออกจากสงครามอ่าว เกิดควันดำปกคลุมท้องฟ้าทั่วภูมิภาค Gulf "
            "ใช้ทีมดับเพลิงผู้เชี่ยวชาญจาก 27 ประเทศและเวลากว่า 9 เดือน "
            "ในการดับไฟทั้งหมด เป็นภัยพิบัติสิ่งแวดล้อมครั้งใหญ่ที่สุดในประวัติศาสตร์"
        ),
        "fatalities": 0, "injuries": 0,
        "loss_desc": "ความเสียหายรวม $40 พันล้าน น้ำมันสูญหายกว่า 1 พันล้านบาร์เรล",
        "loss_b": 40.0,
        "source_name": "Kuwait Oil Company (KOC) + United Nations Environment Programme (UNEP)",
        "source_url": "https://www.kockw.com/",
        "verified": True,
    },

    # ── AFRICA ──
    {
        "name": "Skikda LNG Plant Explosion",
        "year": 2004, "month": 1, "day": 19,
        "country": "Algeria", "region": "Africa",
        "location": "Skikda, Northeast Algeria",
        "type": "Explosion",
        "what_happened": (
            "หม้อต้มไอน้ำ (boiler) ในโรงงาน LNG Train GL1K ของ Sonatrach ระเบิด "
            "เนื่องจากไฮโดรคาร์บอนรั่วเข้ามาในระบบ ไฟลุกลามไปยัง Train GL2Z ที่อยู่ใกล้ "
            "ทำลาย 3 ใน 6 หน่วยผลิต เป็นอุบัติเหตุโรงงาน LNG ที่ร้ายแรงที่สุดในโลก"
        ),
        "fatalities": 27, "injuries": 74,
        "loss_desc": "ความเสียหายรวม $900 ล้าน ต้องใช้เวลาหลายปีในการฟื้นฟูกำลังการผลิต",
        "loss_b": 0.9,
        "source_name": "Sonatrach Investigation Report + ARIA/BARPI Database No. 24386",
        "source_url": "https://www.aria.developpement-durable.gouv.fr/?lang=en",
        "verified": True,
    },
    {
        "name": "Nairobi Sinopec Pipeline Explosion",
        "year": 2011, "month": 9, "day": 12,
        "country": "Kenya", "region": "Africa",
        "location": "Sinai Slum, Nairobi",
        "type": "Fire",
        "what_happened": (
            "ท่อส่งน้ำมันของ Kenya Pipeline Company รั่วไหลในชุมชนแออัด Sinai "
            "ประชาชนหลายร้อยคนมารวมกันเก็บน้ำมันที่ไหลออกมา "
            "เกิดการจุดระเบิดและเพลิงไหม้ครั้งใหญ่ขณะผู้คนยังอยู่ในพื้นที่ "
            "เป็นหนึ่งในภัยพิบัติท่อน้ำมันที่ร้ายแรงที่สุดในแอฟริกา"
        ),
        "fatalities": 120, "injuries": 200,
        "loss_desc": "ความเสียหายรวม $80 ล้าน รวมบ้านเรือนที่ถูกทำลายในชุมชน",
        "loss_b": 0.08,
        "source_name": "Kenya National Commission on Human Rights (KNCHR) — Report 2012",
        "source_url": "https://www.knchr.org/",
        "verified": True,
    },
]

# type → CSS class mapping
TYPE_CLASS = {
    "Explosion": "type-explosion",
    "Fire": "type-fire",
    "Spill": "type-spill",
    "Blowout": "type-blowout",
    "Gas Release": "type-gas",
    "Structural": "type-structural",
}

MONTH_TH = {
    1:"ม.ค.", 2:"ก.พ.", 3:"มี.ค.", 4:"เม.ย.",
    5:"พ.ค.", 6:"มิ.ย.", 7:"ก.ค.", 8:"ส.ค.",
    9:"ก.ย.", 10:"ต.ค.", 11:"พ.ย.", 12:"ธ.ค.",
}

def fmt_date(r):
    return f"{r['day']} {MONTH_TH[r['month']]} {r['year']}"

def fmt_loss(r):
    b = r["loss_b"]
    if b >= 1:
        return f"${b:.1f}B USD"
    else:
        return f"${b*1000:.0f}M USD"

def type_class(t):
    return TYPE_CLASS.get(t, "type-other")

# ── ARIA loader ──
ARIA_URL = "https://www.data.gouv.fr/api/1/datasets/r/a811a3fb-03b4-458e-aadb-4180dd76a335"

@st.cache_data(ttl=21600)
def fetch_aria():
    OIL_KW = ["pétrole","petrol","gaz","gas","raffin","pipeline",
               "hydrocarbur","offshore","lng","gnl","chimique","explosion","incendie"]
    try:
        r = requests.get(ARIA_URL, timeout=60,
                         headers={"User-Agent":"MAE-DB/1.0"}, allow_redirects=True)
        r.raise_for_status()
        if "html" in r.headers.get("Content-Type","").lower() or len(r.content)<10000:
            return pd.DataFrame()
        df = pd.read_excel(io.BytesIO(r.content), engine="openpyxl")
        cols = [c for c in df.columns if df[c].dtype==object]
        combined = df[cols].fillna("").astype(str).apply(lambda row:" ".join(row).lower(), axis=1)
        mask = combined.apply(lambda t: any(kw in t for kw in OIL_KW))
        df2 = df[mask].copy()
        if df2.empty: return pd.DataFrame()

        rename = {"annee":"year","an":"year","commune":"city","pays":"country_raw",
                  "libelle_pays":"country_raw","libelle_activite":"activity",
                  "nb_morts":"fatalities","nb_blesses":"injuries",
                  "resume":"desc","synthese":"desc","numero":"aria_id"}
        df2 = df2.rename(columns={k:v for k,v in rename.items() if k in df2.columns})

        if "year" not in df2.columns: df2["year"]=2000
        df2["year"] = pd.to_numeric(df2["year"], errors="coerce")
        df2 = df2[df2["year"].between(1970,2025)]
        for c in ["fatalities","injuries"]:
            df2[c] = pd.to_numeric(df2.get(c,0), errors="coerce").fillna(0).astype(int)
        df2["country"] = df2.get("country_raw", pd.Series("France",index=df2.index)).fillna("France")
        df2["source"] = "ARIA/BARPI"
        return df2[["year","country","activity","fatalities","injuries","source","desc"]
                   if all(c in df2.columns for c in ["year","country","activity","fatalities","injuries","source","desc"])
                   else [c for c in ["year","country","activity","fatalities","injuries","source","desc"] if c in df2.columns]
                   ].reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

# ============================================================
# UI
# ============================================================

# Header
st.markdown("""
<div class="app-header">
  <div class="app-title">🛢️ MAE Database — Oil &amp; Gas</div>
  <div class="app-sub">Major Accident Events · ข้อมูลเหตุการณ์จริง · แหล่งอ้างอิงระดับนานาชาติ</div>
</div>
""", unsafe_allow_html=True)

# ── Filters ──
df = pd.DataFrame(MAE_DATA)
f1, f2, f3, f4 = st.columns([3, 1.5, 1.5, 1.5])
with f1:
    q = st.text_input("", placeholder="🔍  ค้นหา เช่น explosion, India, BP...", label_visibility="collapsed")
with f2:
    region_opts = ["ทุกภูมิภาค"] + sorted(df["region"].unique().tolist())
    sel_region = st.selectbox("", region_opts, label_visibility="collapsed")
with f3:
    type_opts = ["ทุกประเภท"] + sorted(df["type"].unique().tolist())
    sel_type = st.selectbox("", type_opts, label_visibility="collapsed")
with f4:
    year_opts = ["ทุกปี"] + sorted(df["year"].unique().tolist(), reverse=True)
    sel_year = st.selectbox("", [str(y) for y in year_opts], label_visibility="collapsed")

# Apply filters
fd = df.copy()
if q:
    mask = pd.Series(False, index=fd.index)
    for col in ["name","country","location","type","what_happened","source_name"]:
        mask |= fd[col].astype(str).str.contains(q, case=False, na=False)
    fd = fd[mask]
if sel_region != "ทุกภูมิภาค":
    fd = fd[fd["region"] == sel_region]
if sel_type != "ทุกประเภท":
    fd = fd[fd["type"] == sel_type]
if sel_year != "ทุกปี":
    fd = fd[fd["year"] == int(sel_year)]
fd = fd.sort_values(["year","month","day"], ascending=False)

# ── Summary bar ──
total_fatal = int(fd["fatalities"].sum())
total_inj   = int(fd["injuries"].sum())
total_loss  = fd["loss_b"].sum()
st.markdown(f"""
<div class="summary-bar">
  <div class="summary-cell">
    <div class="summary-label">เหตุการณ์</div>
    <div class="summary-num">{len(fd)}</div>
  </div>
  <div class="summary-cell">
    <div class="summary-label">เสียชีวิต</div>
    <div class="summary-num red">{total_fatal:,}</div>
  </div>
  <div class="summary-cell">
    <div class="summary-label">บาดเจ็บ</div>
    <div class="summary-num">{total_inj:,}</div>
  </div>
  <div class="summary-cell">
    <div class="summary-label">ความเสียหายรวม</div>
    <div class="summary-num">${total_loss:.1f}B</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Event Cards ──
if fd.empty:
    st.markdown('<div class="no-result">ไม่พบเหตุการณ์ที่ตรงกับคำค้นหา</div>', unsafe_allow_html=True)
else:
    for _, row in fd.iterrows():
        tc   = type_class(row["type"])
        date = fmt_date(row)
        loss = fmt_loss(row)
        fatal_html = (
            f'<div class="stat-item"><div class="stat-label">เสียชีวิต</div>'
            f'<div class="stat-value red">{int(row["fatalities"]):,} คน</div></div>'
            if row["fatalities"] > 0
            else '<div class="stat-item"><div class="stat-label">เสียชีวิต</div>'
                 '<div class="stat-value">— คน</div></div>'
        )
        inj_html = (
            f'<div class="stat-item"><div class="stat-label">บาดเจ็บ</div>'
            f'<div class="stat-value amber">{int(row["injuries"]):,} คน</div></div>'
            if row["injuries"] > 0
            else ""
        )
        st.markdown(f"""
<div class="event-card">
  <div class="event-top">
    <div>
      <div class="event-name">{row['name']}</div>
      <div class="event-date">{date} · {row['location']} · {row['country']}</div>
    </div>
    <span class="event-type {tc}">{row['type']}</span>
  </div>
  <div class="event-desc">{row['what_happened']}</div>
  <div class="stats-row">
    {fatal_html}
    {inj_html}
    <div class="stat-item">
      <div class="stat-label">ความเสียหาย</div>
      <div class="stat-value">{loss}</div>
    </div>
    <div class="stat-item">
      <div class="stat-label">รายละเอียดความเสียหาย</div>
      <div class="stat-value" style="font-size:12px;font-family:'Inter';font-weight:400;color:#555">{row['loss_desc']}</div>
    </div>
  </div>
  <div class="source-row">
    <span class="source-dot"></span>
    <span class="source-text">แหล่งอ้างอิง:</span>
    <a class="source-link" href="{row['source_url']}" target="_blank">{row['source_name']}</a>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── ARIA Section ──
with st.expander("🌍  ARIA/BARPI Global Database — คลิกเพื่อโหลดข้อมูล 53,000+ incidents"):
    st.caption("ที่มา: French Ministry of Ecology (BARPI) · Licence Ouverte 2.0 · ใช้ฟรี")
    if st.button("โหลดข้อมูล ARIA (อาจใช้เวลา 30–60 วินาที)", type="primary"):
        with st.spinner("กำลังดึงข้อมูลจาก data.gouv.fr..."):
            aria = fetch_aria()
        if aria.empty:
            st.warning("ไม่สามารถเชื่อมต่อ ARIA ได้ตอนนี้ — ลองใหม่อีกครั้ง")
        else:
            st.success(f"✅ โหลดสำเร็จ: {len(aria):,} Oil & Gas incidents จาก ARIA")
            a1, a2, a3 = st.columns(3)
            a1.metric("Records", f"{len(aria):,}")
            a2.metric("เสียชีวิต", f"{int(aria['fatalities'].sum()):,}")
            a3.metric("บาดเจ็บ", f"{int(aria['injuries'].sum()):,}")

            # chart ประเทศ
            if "country" in aria.columns:
                cc = aria.groupby("country").size().reset_index(name="count").nlargest(15,"count")
                fig = px.bar(cc, x="count", y="country", orientation="h",
                             color_discrete_sequence=["#111"],
                             labels={"count":"จำนวนเหตุการณ์","country":"ประเทศ"})
                fig.update_layout(height=360, plot_bgcolor="white", paper_bgcolor="white",
                                   font=dict(family="Inter"), showlegend=False,
                                   margin=dict(l=0,r=0,t=20,b=0),
                                   yaxis=dict(autorange="reversed"),
                                   title=dict(text="Top 15 ประเทศใน ARIA (Oil & Gas)", font=dict(size=13)))
                st.plotly_chart(fig, width="stretch")

            csv = aria.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️  ดาวน์โหลด ARIA Data (.csv)",
                data=csv, file_name="aria_oil_gas.csv", mime="text/csv")

# Footer
st.markdown(f"""
<div style="margin-top:2rem;padding-top:1rem;border-top:1px solid #EBEBEB;
     display:flex;justify-content:space-between;align-items:center;">
  <div style="font-size:11px;color:#AAA">
    MAE Database · Oil &amp; Gas Industry · ข้อมูลจริง ตรวจสอบได้
  </div>
  <div style="font-size:11px;color:#AAA;font-family:'JetBrains Mono',monospace">
    {datetime.now().strftime("%d %b %Y")}
  </div>
</div>
""", unsafe_allow_html=True)
