import streamlit as st
import json
import re
import io
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Global MAE Monitoring System",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TRUSTED_SOURCES = {
    "Reuters": "https://www.reuters.com/business/energy/",
    "PSA Norway": "https://www.ptil.no/en/",
    "HSE UK": "https://www.hse.gov.uk/offshore/",
    "PHMSA": "https://www.phmsa.dot.gov/",
    "Offshore Technology": "https://www.offshore-technology.com/",
    "BSEE": "https://www.bsee.gov/",
    "CSB": "https://www.csb.gov/",
    "ARIA/BARPI": "https://www.aria.developpement-durable.gouv.fr/?lang=en",
    "Energy Voice": "https://www.energyvoice.com/",
    "Oil & Gas Journal": "https://www.ogj.com/",
}

SEVERITY = {
    "High":   {"color": "#EF4444", "bg": "#450A0A", "label_th": "รุนแรงสูง",   "label_en": "High Severity"},
    "Medium": {"color": "#F59E0B", "bg": "#451A03", "label_th": "รุนแรงปานกลาง","label_en": "Medium Severity"},
    "Low":    {"color": "#22C55E", "bg": "#052E16", "label_th": "รุนแรงต่ำ",    "label_en": "Low Severity"},
}

TYPE_ICONS = {
    "Explosion": "💥", "Fire": "🔥", "Gas Release": "☁️",
    "Oil Spill": "🌊", "Blowout": "⛽", "Structural": "🏗️",
    "Chemical": "⚗️", "Other": "⚠️",
}

COORDS = {
    "USA": (37.09, -95.71), "UK": (55.37, -3.43), "Norway": (60.47, 8.46),
    "Canada": (56.13, -106.34), "Australia": (25.27, 133.77), "Brazil": (14.23, -51.92),
    "India": (20.59, 78.96), "China": (35.86, 104.19), "Saudi Arabia": (23.88, 45.07),
    "Kuwait": (29.31, 47.48), "Algeria": (28.03, 1.65), "Nigeria": (9.08, 8.67),
    "Kenya": (0.02, 37.90), "Mexico": (23.63, -102.55), "France": (46.22, 2.21),
    "Belgium": (50.50, 4.46), "Russia": (61.52, 105.31), "UAE": (23.42, 53.84),
    "Iran": (32.42, 53.68), "Qatar": (25.35, 51.18), "Indonesia": (-0.78, 113.92),
    "Malaysia": (4.21, 108.01), "Thailand": (15.87, 100.99), "Japan": (36.20, 138.25),
    "Germany": (51.16, 10.45), "Netherlands": (52.13, 5.29), "Italy": (41.87, 12.56),
}

# ─────────────────────────────────────────────
# CSS — Industrial Dark
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@400;600;700&display=swap');

html,body,[class*="css"]{font-family:'Barlow',sans-serif;background:#0A0A0F;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0 1.5rem 3rem;max-width:1400px;margin:0 auto;}

/* ── TOPBAR ── */
.topbar{
  background:linear-gradient(135deg,#0D1117 0%,#161B22 100%);
  border-bottom:1px solid #21262D;
  padding:14px 24px;
  display:flex;align-items:center;justify-content:space-between;
  margin:-1rem -1.5rem 2rem;
  position:sticky;top:0;z-index:100;
}
.topbar-left{display:flex;align-items:center;gap:12px;}
.topbar-logo{
  font-family:'Barlow Condensed',sans-serif;
  font-size:20px;font-weight:700;
  color:#F8FAFC;letter-spacing:0.05em;
}
.topbar-logo span{color:#EF4444;}
.topbar-sub{font-size:11px;color:#6B7280;font-family:'Share Tech Mono',monospace;margin-top:2px;}
.live-indicator{
  display:flex;align-items:center;gap:6px;
  background:#0F1C0F;border:1px solid #1A3A1A;
  padding:5px 12px;border-radius:4px;
  font-family:'Share Tech Mono',monospace;font-size:11px;color:#22C55E;
}
.live-dot{width:7px;height:7px;border-radius:50%;background:#22C55E;
  animation:pulse 1.4s ease-in-out infinite;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(.8);}}

/* ── METRICS ── */
.metric-strip{
  display:grid;grid-template-columns:repeat(5,1fr);gap:1px;
  background:#21262D;border:1px solid #21262D;border-radius:8px;
  overflow:hidden;margin-bottom:1.5rem;
}
.metric-cell{background:#0D1117;padding:14px 20px;}
.metric-lbl{
  font-family:'Share Tech Mono',monospace;font-size:9px;
  color:#6B7280;letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px;
}
.metric-val{
  font-family:'Barlow Condensed',sans-serif;font-size:28px;
  font-weight:700;color:#F8FAFC;line-height:1;
}
.metric-val.red{color:#EF4444;}
.metric-val.amber{color:#F59E0B;}
.metric-val.green{color:#22C55E;}
.metric-sub{font-size:10px;color:#4B5563;margin-top:3px;}

/* ── SECTION HEADERS ── */
.sec-hd{
  display:flex;align-items:center;gap:10px;
  margin:1.5rem 0 .75rem;
}
.sec-tag{
  font-family:'Share Tech Mono',monospace;font-size:9px;
  color:#EF4444;letter-spacing:.15em;text-transform:uppercase;
}
.sec-title{
  font-family:'Barlow Condensed',sans-serif;font-size:16px;
  font-weight:600;color:#F8FAFC;
}
.sec-line{flex:1;height:1px;background:#21262D;}

/* ── MAP ── */
.map-frame{
  background:#0D1117;border:1px solid #21262D;border-radius:8px;
  padding:16px;margin-bottom:1.5rem;overflow:hidden;
}

/* ── PROMPT BOX ── */
.prompt-panel{
  background:#0D1117;border:1px solid #21262D;border-radius:8px;
  padding:20px;margin-bottom:1.5rem;
}
.prompt-title{
  font-family:'Barlow Condensed',sans-serif;font-size:14px;
  font-weight:600;color:#F8FAFC;margin-bottom:12px;
  display:flex;align-items:center;gap:8px;
}
.prompt-box{
  background:#161B22;border:1px solid #30363D;border-radius:6px;
  padding:14px;font-family:'Share Tech Mono',monospace;
  font-size:12px;color:#8B949E;line-height:1.6;
  white-space:pre-wrap;max-height:200px;overflow-y:auto;
}
.prompt-steps{
  display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px;
}
.step-card{
  background:#161B22;border:1px solid #30363D;border-radius:6px;
  padding:10px;text-align:center;
}
.step-num{
  font-family:'Barlow Condensed',sans-serif;font-size:20px;
  font-weight:700;color:#EF4444;
}
.step-txt{font-size:11px;color:#8B949E;margin-top:2px;}

/* ── EVENT CARD ── */
.evt-card{
  background:#0D1117;border:1px solid #21262D;border-radius:8px;
  padding:18px 20px;margin-bottom:10px;
  transition:border-color .15s;
}
.evt-card:hover{border-color:#374151;}
.evt-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:10px;}
.evt-title{
  font-family:'Barlow Condensed',sans-serif;font-size:16px;
  font-weight:600;color:#F8FAFC;line-height:1.3;
}
.evt-meta{
  font-family:'Share Tech Mono',monospace;font-size:10px;
  color:#6B7280;margin-top:3px;
}
.badges{display:flex;gap:6px;flex-wrap:wrap;flex-shrink:0;}
.badge{
  font-size:10px;font-weight:600;padding:3px 8px;
  border-radius:3px;white-space:nowrap;
  font-family:'Barlow Condensed',sans-serif;letter-spacing:.04em;
}
.badge-sev-High  {background:#450A0A;color:#EF4444;border:1px solid #7F1D1D;}
.badge-sev-Medium{background:#451A03;color:#F59E0B;border:1px solid #78350F;}
.badge-sev-Low   {background:#052E16;color:#22C55E;border:1px solid #14532D;}
.badge-mae {background:#1E1B4B;color:#818CF8;border:1px solid #312E81;}
.badge-ver {background:#052E16;color:#22C55E;border:1px solid #14532D;}
.badge-unv {background:#1C1917;color:#78716C;border:1px solid #292524;}

.evt-desc{
  font-size:13px;color:#9CA3AF;line-height:1.65;
  margin-bottom:12px;padding-bottom:12px;
  border-bottom:1px solid #161B22;
}
.evt-stats{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:10px;}
.stat-blk{display:flex;flex-direction:column;}
.stat-lbl{font-family:'Share Tech Mono',monospace;font-size:9px;color:#4B5563;letter-spacing:.1em;text-transform:uppercase;margin-bottom:2px;}
.stat-val{font-family:'Barlow Condensed',sans-serif;font-size:17px;font-weight:700;color:#F8FAFC;}
.stat-val.red{color:#EF4444;}
.stat-val.amber{color:#F59E0B;}

.evt-footer{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.src-dot{width:5px;height:5px;border-radius:50%;background:#22C55E;flex-shrink:0;}
.src-lbl{font-size:10px;color:#4B5563;}
.src-link{font-size:10px;color:#60A5FA;text-decoration:none;}
.src-link:hover{text-decoration:underline;}
.ai-tag{font-size:9px;color:#374151;margin-left:auto;font-family:'Share Tech Mono',monospace;}

/* ── TIMELINE ── */
.timeline{border-left:2px solid #21262D;margin-left:10px;padding-left:20px;}
.tl-item{position:relative;margin-bottom:16px;}
.tl-dot{
  position:absolute;left:-27px;top:4px;
  width:10px;height:10px;border-radius:50%;
  border:2px solid #0D1117;
}
.tl-time{font-family:'Share Tech Mono',monospace;font-size:10px;color:#4B5563;margin-bottom:3px;}
.tl-name{font-size:13px;color:#D1D5DB;font-weight:500;}
.tl-country{font-size:11px;color:#6B7280;}

/* ── SEARCH / FILTER ── */
.stTextInput input{
  background:#161B22 !important;border:1px solid #30363D !important;
  color:#F8FAFC !important;border-radius:6px !important;
  font-family:'Barlow',sans-serif !important;font-size:13px !important;
}
.stTextInput input::placeholder{color:#4B5563 !important;}
.stTextInput input:focus{border-color:#EF4444 !important;box-shadow:none !important;}

.stSelectbox [data-baseweb="select"]>div{
  background:#161B22 !important;border:1px solid #30363D !important;
  color:#F8FAFC !important;border-radius:6px !important;
}

/* ── BUTTONS ── */
.stButton>button{
  background:#EF4444 !important;color:#fff !important;
  border:none !important;border-radius:6px !important;
  font-family:'Barlow Condensed',sans-serif !important;
  font-size:13px !important;font-weight:600 !important;
  letter-spacing:.04em !important;padding:9px 20px !important;
}
.stButton>button:hover{background:#DC2626 !important;}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{
  gap:0;border-bottom:1px solid #21262D;background:transparent;
}
.stTabs [data-baseweb="tab"]{
  font-family:'Barlow Condensed',sans-serif;font-size:13px;
  font-weight:600;color:#6B7280;padding:10px 18px;
  border-bottom:2px solid transparent;letter-spacing:.04em;
}
.stTabs [aria-selected="true"]{
  color:#EF4444 !important;border-bottom:2px solid #EF4444 !important;
}

/* ── DOWNLOAD BTN ── */
.stDownloadButton>button{
  background:#161B22 !important;color:#8B949E !important;
  border:1px solid #30363D !important;border-radius:6px !important;
  font-family:'Barlow Condensed',sans-serif !important;
  font-size:12px !important;padding:7px 16px !important;
}

/* ── MISC ── */
.divider{height:1px;background:#21262D;margin:1.5rem 0;}
.empty-state{
  text-align:center;padding:48px 20px;
  font-size:13px;color:#4B5563;
  font-family:'Share Tech Mono',monospace;
}
.lang-toggle{
  display:flex;gap:4px;background:#161B22;
  border:1px solid #30363D;border-radius:6px;padding:3px;
}
.lang-btn{
  font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:600;
  padding:4px 10px;border-radius:4px;cursor:pointer;
  color:#6B7280;border:none;background:transparent;
}
.lang-btn.active{background:#EF4444;color:#fff;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "events"   not in st.session_state: st.session_state.events   = []
if "lang"     not in st.session_state: st.session_state.lang     = "TH"
if "last_scan"not in st.session_state: st.session_state.last_scan = None
if "scan_count"not in st.session_state:st.session_state.scan_count= 0

L = st.session_state.lang
TH = L == "TH"

def t(th, en): return th if TH else en

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def severity_of(e):
    f = e.get("fatalities", 0)
    if f >= 3 or e.get("type") in ["Explosion","Blowout"]: return "High"
    if f >= 1 or e.get("type") in ["Fire","Gas Release","Oil Spill"]: return "Medium"
    return "Low"

def is_mae(e):
    f = e.get("fatalities", 0)
    return f >= 1 or e.get("type") in ["Explosion","Fire","Gas Release","Oil Spill","Blowout","Chemical"]

def is_verified(e):
    src = e.get("source_name", "")
    return any(ts.lower() in src.lower() for ts in TRUSTED_SOURCES)

def parse_ai_json(text: str) -> list:
    """แยก JSON array จาก text ที่ AI ส่งกลับมา"""
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except Exception:
        m = re.search(r"\[.*\]", text, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try: return [json.loads(m.group())]
            except: pass
        return []

def enrich(e: dict) -> dict:
    """เพิ่ม severity, mae_flag, verified"""
    e["severity"]  = severity_of(e)
    e["is_mae"]    = is_mae(e)
    e["verified"]  = is_verified(e)
    e["id"]        = e.get("id", f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(e.get('title',''))%10000:04d}")
    # ถ้าไม่มี coords ให้ดึงจาก country
    country = e.get("country","")
    if "lat" not in e or "lon" not in e:
        c = COORDS.get(country, (0, 0))
        e["lat"], e["lon"] = c
    return e

def add_events(new_list: list):
    existing_ids = {ev.get("title","")+"_"+str(ev.get("date","")) for ev in st.session_state.events}
    added = 0
    for e in new_list:
        key = e.get("title","") + "_" + str(e.get("date",""))
        if key not in existing_ids:
            st.session_state.events.insert(0, enrich(e))
            existing_ids.add(key)
            added += 1
    return added

def make_prompt(lang="TH") -> str:
    now = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d %b %Y %H:%M")
    src_list = ", ".join(TRUSTED_SOURCES.keys())
    return f"""You are an expert HSE analyst for the Oil & Gas industry.
Task: Search for Major Accident Events (MAE) that occurred RECENTLY (last 7 days as of {now}).

Search these credible sources: {src_list}

MAE criteria (must meet at least one):
- Fatalities ≥ 1
- Explosion, fire, oil spill, gas leak, blowout, or structural failure

For each event found, return a JSON array (ONLY JSON, no other text):
[
  {{
    "title": "Short descriptive title in {'Thai' if lang=='TH' else 'English'}",
    "title_en": "Short descriptive title in English",
    "date": "YYYY-MM-DD",
    "country": "Country name in English",
    "location": "Specific location",
    "type": "Explosion|Fire|Gas Release|Oil Spill|Blowout|Structural|Chemical|Other",
    "fatalities": 0,
    "injuries": 0,
    "summary_th": "สรุปเหตุการณ์ภาษาไทย 2-3 ประโยค",
    "summary_en": "2-3 sentence English summary",
    "source_name": "Source organization name (e.g. Reuters, PSA Norway)",
    "source_url": "https://actual-url-to-article-or-report"
  }}
]

If no MAE found in last 7 days, return: []
Return ONLY the JSON array."""

def build_map_html(events, lang="TH"):
    markers_js = ""
    for e in events:
        lat = e.get("lat", 0)
        lon = e.get("lon", 0)
        sev = e.get("severity", "Low")
        col = SEVERITY[sev]["color"]
        icon = TYPE_ICONS.get(e.get("type","Other"),"⚠️")
        title = e.get("title","") if lang=="TH" else e.get("title_en", e.get("title",""))
        fatal = e.get("fatalities",0)
        inj   = e.get("injuries",0)
        country = e.get("country","")
        date    = e.get("date","")
        popup = f"{icon} {title}<br><small>{date} · {country}</small><br>💀 {fatal} &nbsp; 🤕 {inj}"
        markers_js += f"""
L.circleMarker([{lat},{lon}],{{
  radius:{8 if sev=='High' else 6 if sev=='Medium' else 5},
  fillColor:"{col}",color:"#0D1117",weight:1.5,
  fillOpacity:.85
}}).bindPopup(`{popup}`).addTo(map);
"""
    return f"""<!DOCTYPE html><html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
  html,body{{margin:0;padding:0;height:100%;background:#0A0A0F;}}
  #map{{height:100%;}}
  .leaflet-container{{background:#0D1117;}}
  .leaflet-popup-content-wrapper{{background:#161B22;border:1px solid #30363D;color:#D1D5DB;border-radius:6px;}}
  .leaflet-popup-tip{{background:#161B22;}}
</style>
</head>
<body>
<div id="map"></div>
<script>
var map=L.map('map',{{center:[20,0],zoom:2,zoomControl:true}});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
  attribution:'©OpenStreetMap ©CartoDB',subdomains:'abcd',maxZoom:19
}}).addTo(map);
{markers_js}
</script>
</body></html>"""

def export_pdf_html(events, lang="TH") -> str:
    now = datetime.now().strftime("%d %b %Y %H:%M")
    rows = ""
    mae_events = [e for e in events if e.get("is_mae")]
    for e in mae_events:
        title = e.get("title","") if lang=="TH" else e.get("title_en", e.get("title",""))
        summary = e.get("summary_th","") if lang=="TH" else e.get("summary_en","")
        sev = e.get("severity","Low")
        col = SEVERITY[sev]["color"]
        rows += f"""
<tr>
  <td>{e.get('date','')}</td>
  <td><strong>{title}</strong><br><small style="color:#555">{e.get('location','')}, {e.get('country','')}</small></td>
  <td><span style="color:{col};font-weight:700">{sev}</span></td>
  <td>{e.get('type','')}</td>
  <td style="color:#DC2626;font-weight:700">{e.get('fatalities',0)}</td>
  <td>{e.get('injuries',0)}</td>
  <td style="font-size:11px">{summary}</td>
  <td style="font-size:10px"><a href="{e.get('source_url','#')}">{e.get('source_name','')}</a></td>
</tr>"""
    countries = len(set(e.get("country","") for e in mae_events))
    total_fatal = sum(e.get("fatalities",0) for e in mae_events)
    return f"""<!DOCTYPE html><html>
<head><meta charset="utf-8">
<style>
  body{{font-family:Arial,sans-serif;font-size:12px;color:#111;padding:24px;}}
  h1{{font-size:20px;color:#111;border-bottom:2px solid #EF4444;padding-bottom:8px;}}
  .meta{{color:#555;font-size:11px;margin-bottom:16px;}}
  .stats{{display:flex;gap:24px;margin-bottom:20px;}}
  .stat{{text-align:center;padding:10px 20px;border:1px solid #E5E5E5;border-radius:6px;}}
  .stat-n{{font-size:24px;font-weight:700;color:#EF4444;}}
  .stat-l{{font-size:10px;color:#555;text-transform:uppercase;}}
  table{{width:100%;border-collapse:collapse;font-size:11px;}}
  th{{background:#F3F4F6;padding:8px;text-align:left;border:1px solid #E5E5E5;}}
  td{{padding:7px 8px;border:1px solid #E5E5E5;vertical-align:top;}}
  tr:nth-child(even){{background:#FAFAFA;}}
</style>
</head>
<body>
<h1>🛢️ Global MAE Monitoring Report</h1>
<div class="meta">Generated: {now} | Oil & Gas Industry | AI-Powered MAE Detection</div>
<div class="stats">
  <div class="stat"><div class="stat-n">{len(mae_events)}</div><div class="stat-l">MAE Events</div></div>
  <div class="stat"><div class="stat-n">{total_fatal}</div><div class="stat-l">Fatalities</div></div>
  <div class="stat"><div class="stat-n">{countries}</div><div class="stat-l">Countries</div></div>
</div>
<table>
<tr><th>Date</th><th>Event</th><th>Severity</th><th>Type</th><th>Deaths</th><th>Injuries</th><th>Summary</th><th>Source</th></tr>
{rows}
</table>
<div style="margin-top:16px;font-size:10px;color:#999">
Sources: Reuters · PSA Norway · HSE UK · PHMSA · Offshore Technology · BSEE · CSB · ARIA/BARPI
</div>
</body></html>"""

# ─────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <div>
      <div class="topbar-logo">🛢️ GLOBAL <span>MAE</span> MONITORING SYSTEM</div>
      <div class="topbar-sub">OIL &amp; GAS INDUSTRY · AI-POWERED INCIDENT DETECTION</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <div class="live-indicator">
      <div class="live-dot"></div>
      {'กำลังติดตาม' if TH else 'MONITORING'}
    </div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#4B5563;">
      {datetime.now(ZoneInfo('Asia/Bangkok')).strftime('%d %b %Y %H:%M')} ICT
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LANG TOGGLE (ใน expander เล็กๆ ไม่รกหน้า)
# ─────────────────────────────────────────────
with st.expander("🌐 Language / ภาษา", expanded=False):
    col_l1, col_l2, *_ = st.columns([1,1,4])
    with col_l1:
        if st.button("🇹🇭 ไทย", key="btn_th"):
            st.session_state.lang = "TH"; st.rerun()
    with col_l2:
        if st.button("🇬🇧 EN", key="btn_en"):
            st.session_state.lang = "EN"; st.rerun()

# ─────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────
all_ev  = st.session_state.events
mae_ev  = [e for e in all_ev if e.get("is_mae")]
total_f = sum(e.get("fatalities",0) for e in mae_ev)
total_i = sum(e.get("injuries",0) for e in mae_ev)
countries_hit = len(set(e.get("country","") for e in mae_ev))
verified_n    = sum(1 for e in mae_ev if e.get("verified"))
next_scan = (
    (st.session_state.last_scan + timedelta(hours=1)).strftime("%H:%M")
    if st.session_state.last_scan else t("รอการสแกน","Awaiting scan")
)

st.markdown(f"""
<div class="metric-strip">
  <div class="metric-cell">
    <div class="metric-lbl">{t('MAE ทั้งหมด','Total MAE')}</div>
    <div class="metric-val red">{len(mae_ev)}</div>
    <div class="metric-sub">{t('เหตุการณ์','events')}</div>
  </div>
  <div class="metric-cell">
    <div class="metric-lbl">{t('ผู้เสียชีวิต','Fatalities')}</div>
    <div class="metric-val red">{total_f:,}</div>
    <div class="metric-sub">{t('รายรวม','total')}</div>
  </div>
  <div class="metric-cell">
    <div class="metric-lbl">{t('บาดเจ็บ','Injuries')}</div>
    <div class="metric-val amber">{total_i:,}</div>
    <div class="metric-sub">{t('รายรวม','total')}</div>
  </div>
  <div class="metric-cell">
    <div class="metric-lbl">{t('ประเทศที่ได้รับผล','Countries Affected')}</div>
    <div class="metric-val">{countries_hit}</div>
    <div class="metric-sub">{t('ประเทศ','countries')}</div>
  </div>
  <div class="metric-cell">
    <div class="metric-lbl">{t('ตรวจสอบแล้ว','Verified')}</div>
    <div class="metric-val green">{verified_n}</div>
    <div class="metric-sub">{t('แหล่งน่าเชื่อถือ','trusted sources')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────
tab_scan, tab_map, tab_events, tab_timeline, tab_report = st.tabs([
    t("🔍  สแกน MAE","🔍  Scan MAE"),
    t("🗺️  แผนที่โลก","🗺️  World Map"),
    t("📋  รายการเหตุการณ์","📋  Event List"),
    t("📅  Timeline","📅  Timeline"),
    t("📊  รายงาน","📊  Report"),
])

# ─────────────────────────────────────────────
# TAB 1: SCAN — AI Search Engine (copy-paste workflow)
# ─────────────────────────────────────────────
with tab_scan:
    st.markdown(f"""
    <div class="sec-hd">
      <span class="sec-tag">AI ENGINE</span>
      <span class="sec-title">{t('ระบบตรวจจับ MAE ด้วย AI','AI-Powered MAE Detection')}</span>
      <span class="sec-line"></span>
    </div>
    """, unsafe_allow_html=True)

    prompt_text = make_prompt(L)

    st.markdown(f"""
    <div class="prompt-panel">
      <div class="prompt-title">
        ⚡ {t('วิธีใช้งาน — ใช้ Claude.ai ฟรีเป็น AI Engine','How to use — Claude.ai as free AI Engine')}
      </div>
      <div class="prompt-steps">
        <div class="step-card">
          <div class="step-num">01</div>
          <div class="step-txt">{t('Copy prompt ด้านล่าง','Copy the prompt below')}</div>
        </div>
        <div class="step-card">
          <div class="step-num">02</div>
          <div class="step-txt">{t('วางใน Claude.ai แล้วส่ง','Paste in Claude.ai & send')}</div>
        </div>
        <div class="step-card">
          <div class="step-num">03</div>
          <div class="step-txt">{t('Copy JSON ผลลัพธ์ วางในช่องด้านล่าง','Copy JSON result & paste below')}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_p1, col_p2 = st.columns([4, 1])
    with col_p1:
        st.markdown(f"""
        <div class="prompt-box">{prompt_text}</div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.download_button(
            t("⬇️ ดาวน์โหลด Prompt","⬇️ Download Prompt"),
            data=prompt_text.encode(),
            file_name="mae_search_prompt.txt",
            mime="text/plain",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t("📋 เปิด Claude.ai","📋 Open Claude.ai"), key="open_claude"):
            st.markdown('<meta http-equiv="refresh" content="0;url=https://claude.ai">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sec-hd" style="margin-top:1.5rem;">
      <span class="sec-tag">INPUT</span>
      <span class="sec-title">{t('วาง JSON ผลลัพธ์จาก Claude.ai','Paste JSON result from Claude.ai')}</span>
      <span class="sec-line"></span>
    </div>
    """, unsafe_allow_html=True)

    json_input = st.text_area(
        "",
        height=200,
        placeholder=t(
            '[ { "title": "ก๊าซรั่วบนแท่นขุดเจาะ", "date": "2025-05-10", ... } ]',
            '[ { "title": "Gas leak on offshore platform", "date": "2025-05-10", ... } ]',
        ),
        label_visibility="collapsed",
    )

    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 4])
    with col_btn1:
        if st.button(t("✅ นำเข้าข้อมูล MAE","✅ Import MAE Data"), type="primary", key="import_btn"):
            if json_input.strip():
                parsed = parse_ai_json(json_input)
                if parsed:
                    added = add_events(parsed)
                    st.session_state.last_scan = datetime.now()
                    st.session_state.scan_count += 1
                    if added > 0:
                        st.success(t(f"✅ นำเข้าสำเร็จ {added} เหตุการณ์ใหม่",f"✅ Imported {added} new events"))
                    else:
                        st.info(t("ข้อมูลซ้ำกับที่มีอยู่แล้วทั้งหมด","All events already exist in database"))
                    st.rerun()
                else:
                    st.error(t("❌ ไม่พบ JSON ที่ถูกต้อง — ตรวจสอบรูปแบบอีกครั้ง","❌ No valid JSON found — please check the format"))
            else:
                st.warning(t("กรุณาวาง JSON ก่อนกดนำเข้า","Please paste JSON before importing"))

    with col_btn2:
        if st.button(t("🗑️ ล้างข้อมูลทั้งหมด","🗑️ Clear All Data"), key="clear_btn"):
            st.session_state.events = []
            st.session_state.last_scan = None
            st.success(t("ล้างข้อมูลแล้ว","Data cleared"))
            st.rerun()

    # ── ตัวอย่าง JSON ──
    with st.expander(t("📌 ดูตัวอย่าง JSON format","📌 View example JSON format")):
        example = [
            {
                "title": "ก๊าซรั่วบนแท่นผลิตนอกชายฝั่ง — Norway",
                "title_en": "Gas leak on offshore platform — North Sea Norway",
                "date": "2025-05-10",
                "country": "Norway",
                "location": "North Sea, Barents Sea",
                "type": "Gas Release",
                "fatalities": 0,
                "injuries": 1,
                "summary_th": "AI ตรวจพบก๊าซรั่วบนแท่นผลิต มีการหยุดการผลิตและมีพนักงานบาดเจ็บเล็กน้อย 1 ราย",
                "summary_en": "AI detected gas leak on production platform. Production halted, 1 minor injury reported.",
                "source_name": "PSA Norway",
                "source_url": "https://www.ptil.no/en/",
            }
        ]
        st.code(json.dumps(example, ensure_ascii=False, indent=2), language="json")

    # ── สถานะการสแกน ──
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric(
        t("สแกนล่าสุด","Last Scan"),
        st.session_state.last_scan.strftime("%d %b %Y %H:%M") if st.session_state.last_scan else t("ยังไม่ได้สแกน","Not yet"),
    )
    c2.metric(t("ครั้งที่สแกน","Scan Count"), st.session_state.scan_count)
    c3.metric(t("รอบถัดไป","Next Cycle"), next_scan)

# ─────────────────────────────────────────────
# TAB 2: MAP
# ─────────────────────────────────────────────
with tab_map:
    st.markdown(f"""
    <div class="sec-hd">
      <span class="sec-tag">WORLD MAP</span>
      <span class="sec-title">{t('แผนที่ MAE ทั่วโลก','Global MAE Incident Map')}</span>
      <span class="sec-line"></span>
    </div>
    """, unsafe_allow_html=True)

    if not mae_ev:
        st.markdown(f'<div class="empty-state">{t("ยังไม่มีข้อมูล MAE — กด Tab สแกน เพื่อเริ่มต้น","No MAE data yet — go to Scan tab to get started")}</div>', unsafe_allow_html=True)
    else:
        map_html = build_map_html(mae_ev, L)
        st.components.v1.html(map_html, height=460)
        # Legend
        st.markdown("""
        <div style="display:flex;gap:16px;margin-top:8px;padding:8px 4px;">
          <span style="font-size:11px;color:#6B7280;font-family:'Share Tech Mono',monospace">SEVERITY:</span>
          <span style="font-size:11px;color:#EF4444">● High</span>
          <span style="font-size:11px;color:#F59E0B">● Medium</span>
          <span style="font-size:11px;color:#22C55E">● Low</span>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 3: EVENT LIST
# ─────────────────────────────────────────────
with tab_events:
    st.markdown(f"""
    <div class="sec-hd">
      <span class="sec-tag">EVENTS</span>
      <span class="sec-title">{t('รายการเหตุการณ์ MAE','MAE Event List')}</span>
      <span class="sec-line"></span>
    </div>
    """, unsafe_allow_html=True)

    # ── Search & Filter ──
    sf1, sf2, sf3, sf4 = st.columns([3, 1.5, 1.5, 1.5])
    with sf1:
        q = st.text_input("", placeholder=t("🔍 ค้นหา เหตุการณ์ ประเทศ ประเภท...","🔍 Search events, country, type..."), label_visibility="collapsed")
    with sf2:
        country_opts = [t("ทุกประเทศ","All Countries")] + sorted(set(e.get("country","") for e in all_ev if e.get("country")))
        sel_country = st.selectbox("", country_opts, label_visibility="collapsed")
    with sf3:
        type_opts = [t("ทุกประเภท","All Types")] + sorted(set(e.get("type","") for e in all_ev if e.get("type")))
        sel_type = st.selectbox("", type_opts, label_visibility="collapsed", key="type_sel")
    with sf4:
        sev_opts = [t("ทุกระดับ","All Severity"), "High", "Medium", "Low"]
        sel_sev = st.selectbox("", sev_opts, label_visibility="collapsed", key="sev_sel")

    # apply filters
    display_ev = all_ev
    if q:
        ql = q.lower()
        display_ev = [e for e in display_ev if ql in (e.get("title","")+" "+e.get("title_en","")+" "+e.get("country","")+" "+e.get("type","")+" "+e.get("summary_th","")+" "+e.get("summary_en","")).lower()]
    if sel_country not in [t("ทุกประเทศ","All Countries")]:
        display_ev = [e for e in display_ev if e.get("country") == sel_country]
    if sel_type not in [t("ทุกประเภท","All Types")]:
        display_ev = [e for e in display_ev if e.get("type") == sel_type]
    if sel_sev not in [t("ทุกระดับ","All Severity")]:
        display_ev = [e for e in display_ev if e.get("severity") == sel_sev]

    mae_only = [e for e in display_ev if e.get("is_mae")]
    non_mae  = [e for e in display_ev if not e.get("is_mae")]

    st.markdown(f"<div style='font-size:11px;color:#4B5563;font-family:\"Share Tech Mono\",monospace;margin-bottom:12px;'>{t(f'แสดง {len(display_ev)} เหตุการณ์ · MAE {len(mae_only)} · ไม่ใช่ MAE {len(non_mae)}',f'Showing {len(display_ev)} events · MAE {len(mae_only)} · Non-MAE {len(non_mae)}')}</div>", unsafe_allow_html=True)

    if not display_ev:
        st.markdown(f'<div class="empty-state">{t("ไม่พบเหตุการณ์ที่ตรงกับเงื่อนไข","No events match your filters")}</div>', unsafe_allow_html=True)
    else:
        for e in display_ev:
            title    = e.get("title","") if TH else e.get("title_en", e.get("title",""))
            summary  = e.get("summary_th","") if TH else e.get("summary_en","")
            sev      = e.get("severity","Low")
            sev_info = SEVERITY[sev]
            icon     = TYPE_ICONS.get(e.get("type","Other"), "⚠️")
            fatal    = e.get("fatalities",0)
            inj      = e.get("injuries",0)
            mae_flag = e.get("is_mae",False)
            ver_flag = e.get("verified",False)
            conf     = e.get("confidence","—")
            src_name = e.get("source_name","")
            src_url  = e.get("source_url","#")
            country  = e.get("country","")
            date     = e.get("date","")
            loc      = e.get("location","")
            etype    = e.get("type","")

            fatal_html = f'<div class="stat-blk"><div class="stat-lbl">{t("เสียชีวิต","Fatalities")}</div><div class="stat-val {"red" if fatal>0 else ""}">{fatal:,}</div></div>' if fatal is not None else ""
            inj_html   = f'<div class="stat-blk"><div class="stat-lbl">{t("บาดเจ็บ","Injuries")}</div><div class="stat-val {"amber" if inj>0 else ""}">{inj:,}</div></div>' if inj is not None else ""

            mae_badge = f'<span class="badge badge-mae">✓ MAE</span>' if mae_flag else f'<span class="badge badge-unv">— {t("ไม่ใช่ MAE","Not MAE")}</span>'
            ver_badge = f'<span class="badge badge-ver">✔ {t("ตรวจสอบแล้ว","Verified")}</span>' if ver_flag else f'<span class="badge badge-unv">? {t("ยังไม่ตรวจสอบ","Unverified")}</span>'

            st.markdown(f"""
<div class="evt-card">
  <div class="evt-top">
    <div>
      <div class="evt-title">{icon} {title}</div>
      <div class="evt-meta">{date} &nbsp;·&nbsp; {loc}, {country} &nbsp;·&nbsp; {etype}</div>
    </div>
    <div class="badges">
      <span class="badge badge-sev-{sev}">{sev_info['label_th' if TH else 'label_en']}</span>
      {mae_badge}
      {ver_badge}
    </div>
  </div>
  <div class="evt-desc">{summary}</div>
  <div class="evt-stats">
    {fatal_html}
    {inj_html}
    <div class="stat-blk">
      <div class="stat-lbl">{t('ประเทศ','Country')}</div>
      <div class="stat-val" style="font-size:14px">{country}</div>
    </div>
    <div class="stat-blk">
      <div class="stat-lbl">{t('ประเภท','Type')}</div>
      <div class="stat-val" style="font-size:14px">{etype}</div>
    </div>
  </div>
  <div class="evt-footer">
    <span class="src-dot"></span>
    <span class="src-lbl">{t('แหล่งอ้างอิง','Source')}:</span>
    <a class="src-link" href="{src_url}" target="_blank">{src_name}</a>
    <span class="ai-tag">AI CLASSIFIED</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 4: TIMELINE
# ─────────────────────────────────────────────
with tab_timeline:
    st.markdown(f"""
    <div class="sec-hd">
      <span class="sec-tag">TIMELINE</span>
      <span class="sec-title">{t('ลำดับเหตุการณ์','Incident Timeline')}</span>
      <span class="sec-line"></span>
    </div>
    """, unsafe_allow_html=True)

    sorted_ev = sorted(mae_ev, key=lambda x: x.get("date",""), reverse=True)
    if not sorted_ev:
        st.markdown(f'<div class="empty-state">{t("ยังไม่มีข้อมูล MAE","No MAE events yet")}</div>', unsafe_allow_html=True)
    else:
        tl_html = '<div class="timeline">'
        for e in sorted_ev:
            sev = e.get("severity","Low")
            col = SEVERITY[sev]["color"]
            title = e.get("title","") if TH else e.get("title_en", e.get("title",""))
            icon  = TYPE_ICONS.get(e.get("type","Other"),"⚠️")
            tl_html += f"""
<div class="tl-item">
  <div class="tl-dot" style="background:{col}"></div>
  <div class="tl-time">{e.get('date','')}</div>
  <div class="tl-name">{icon} {title}</div>
  <div class="tl-country">{e.get('location','')}, {e.get('country','')} · 💀 {e.get('fatalities',0)} &nbsp; 🤕 {e.get('injuries',0)}</div>
</div>"""
        tl_html += "</div>"
        st.markdown(tl_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 5: REPORT
# ─────────────────────────────────────────────
with tab_report:
    st.markdown(f"""
    <div class="sec-hd">
      <span class="sec-tag">AUTO REPORT</span>
      <span class="sec-title">{t('รายงาน MAE อัตโนมัติ','Automatic MAE Report')}</span>
      <span class="sec-line"></span>
    </div>
    """, unsafe_allow_html=True)

    if not mae_ev:
        st.markdown(f'<div class="empty-state">{t("ยังไม่มีข้อมูล — นำเข้าข้อมูลจาก Tab สแกนก่อน","No data yet — import events from the Scan tab first")}</div>', unsafe_allow_html=True)
    else:
        # Summary
        r1,r2,r3,r4 = st.columns(4)
        r1.metric(t("MAE ทั้งหมด","Total MAE"),       len(mae_ev))
        r2.metric(t("ผู้เสียชีวิต","Total Fatalities"), f"{total_f:,}")
        r3.metric(t("บาดเจ็บ","Total Injuries"),        f"{total_i:,}")
        r4.metric(t("ประเทศที่ได้รับผล","Countries"),   countries_hit)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Country breakdown
        st.markdown(f"**{t('การกระจายตามประเทศ','Country Distribution')}**")
        country_count = {}
        for e in mae_ev:
            c = e.get("country","Unknown")
            country_count[c] = country_count.get(c,0)+1
        for country, count in sorted(country_count.items(), key=lambda x:-x[1]):
            pct = count/len(mae_ev)*100
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
  <span style="font-size:12px;color:#9CA3AF;width:140px;font-family:'Share Tech Mono',monospace">{country}</span>
  <div style="flex:1;height:6px;background:#161B22;border-radius:3px;overflow:hidden;">
    <div style="width:{pct}%;height:100%;background:#EF4444;border-radius:3px;"></div>
  </div>
  <span style="font-size:11px;color:#4B5563;width:30px;text-align:right">{count}</span>
</div>""", unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Type breakdown
        st.markdown(f"**{t('การกระจายตามประเภท','Event Type Distribution')}**")
        type_count = {}
        for e in mae_ev:
            tp = e.get("type","Other")
            type_count[tp] = type_count.get(tp,0)+1
        for tp, count in sorted(type_count.items(), key=lambda x:-x[1]):
            icon = TYPE_ICONS.get(tp,"⚠️")
            pct  = count/len(mae_ev)*100
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
  <span style="font-size:12px;color:#9CA3AF;width:140px;">{icon} {tp}</span>
  <div style="flex:1;height:6px;background:#161B22;border-radius:3px;overflow:hidden;">
    <div style="width:{pct}%;height:100%;background:#F59E0B;border-radius:3px;"></div>
  </div>
  <span style="font-size:11px;color:#4B5563;width:30px;text-align:right">{count}</span>
</div>""", unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Export
        st.markdown(f"**{t('ส่งออกรายงาน','Export Report')}**")
        ec1, ec2 = st.columns(2)
        with ec1:
            report_html = export_pdf_html(mae_ev, L)
            st.download_button(
                t("⬇️ ดาวน์โหลด HTML Report","⬇️ Download HTML Report"),
                data=report_html.encode("utf-8"),
                file_name=f"MAE_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html",
            )
        with ec2:
            report_json = json.dumps(mae_ev, ensure_ascii=False, indent=2)
            st.download_button(
                t("⬇️ ดาวน์โหลด JSON Data","⬇️ Download JSON Data"),
                data=report_json.encode("utf-8"),
                file_name=f"MAE_Data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
            )

        st.info(t(
            "💡 เปิด HTML ในเบราว์เซอร์ → Ctrl+P → Save as PDF เพื่อบันทึกเป็น PDF",
            "💡 Open HTML in browser → Ctrl+P → Save as PDF to export as PDF"
        ))

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="border-top:1px solid #21262D;margin-top:2rem;padding-top:1rem;
     display:flex;justify-content:space-between;align-items:center;">
  <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#374151;">
    GLOBAL MAE MONITORING SYSTEM · OIL &amp; GAS INDUSTRY
  </div>
  <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#374151;">
    SOURCES: REUTERS · PSA NORWAY · HSE UK · PHMSA · OFFSHORE TECHNOLOGY · BSEE · CSB · ARIA
  </div>
</div>
""", unsafe_allow_html=True)
