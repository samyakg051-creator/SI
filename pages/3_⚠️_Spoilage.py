import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from modules.spoilage_assessor import assess_spoilage, STORAGE_PENALTY
from modules.data_fetcher import CROPS
from utils.geo import DISTRICT_COORDS
from utils.translator import t
from utils.map_selector import render_district_selector
from utils.shared_state import init_shared, get_shared, sync_all
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Spoilage Assessor — AgriChain", page_icon="⚠️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Syne:wght@700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fefae0 !important; color: #1b1b1b !important; }
.stApp { background-color: #fefae0 !important; }
[data-testid="stAppViewContainer"] { background-color: #fefae0 !important; }
[data-testid="stHeader"] { background-color: #fefae0 !important; border-bottom: 1px solid #d4e6c3 !important; }
section[data-testid="stSidebar"] { background-color: #1a3d2e !important; border-right: 1px solid #2d6a4f; }
section[data-testid="stSidebar"] > div { padding: 1.2rem 1rem; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div { color: #d4f0c0 !important; }

.page-header {
    background: linear-gradient(135deg, #5c1a1a 0%, #3d1010 100%);
    border-radius: 20px;
    padding: 32px 36px;
    margin-bottom: 28px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 4px 20px #5c1a1a22;
}
.page-header-icon { font-size: 3rem; flex-shrink: 0; }
.page-header h1   { font-size: 2.2rem; font-weight: 900; color: #fff; margin: 0; line-height: 1.1; }
.page-header p    { font-size: 0.95rem; color: #f09090; margin: 6px 0 0; }

.input-section {
    background: #fff;
    border: 1px solid #d4e6c3;
    border-radius: 18px;
    padding: 28px 28px 20px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px #2d6a4f08;
}

.risk-banner {
    border-radius: 20px;
    padding: 30px 36px;
    margin: 20px 0;
    position: relative; overflow: hidden;
}
.risk-banner::after {
    position: absolute; right: 30px; top: 50%; transform: translateY(-50%);
    font-size: 7rem; opacity: 0.1; pointer-events: none;
}
.risk-high   { background: linear-gradient(135deg, #f8d7da, #f5c6cb); border: 1.5px solid #c0392b; }
.risk-high::after   { content: '🔴'; }
.risk-medium { background: linear-gradient(135deg, #fff3cd, #ffeeba); border: 1.5px solid #e3a008; }
.risk-medium::after { content: '🟡'; }
.risk-low    { background: linear-gradient(135deg, #d4edda, #c3e6cb); border: 1.5px solid #2d6a4f; }
.risk-low::after    { content: '🟢'; }

.risk-label-high   { font-size: 2.6rem; font-weight: 900; color: #c0392b; }
.risk-label-medium { font-size: 2.6rem; font-weight: 900; color: #856404; }
.risk-label-low    { font-size: 2.6rem; font-weight: 900; color: #2d6a4f; }

.risk-prob  { font-size: 1.05rem; color: #333; margin-top: 8px; }
.risk-why   { font-size: 0.9rem; color: #666; margin-top: 10px; font-style: italic; line-height: 1.6; }

.action-card {
    border-radius: 14px;
    padding: 16px 20px;
    margin: 10px 0;
    display: flex; align-items: flex-start;
    gap: 16px; border: 1px solid transparent;
    box-shadow: 0 2px 8px #2d6a4f08;
}
.action-high   { background: #fff; border-color: #f5c6cb; }
.action-medium { background: #fff; border-color: #ffeeba; }
.action-low    { background: #fff; border-color: #c3e6cb; }

.action-num  { font-size: 1.1rem; font-weight: 900; color: #888; flex-shrink: 0; width: 24px; }
.action-text { font-size: 0.93rem; font-weight: 600; color: #1b1b1b; line-height: 1.4; }
.action-meta { font-size: 0.82rem; color: #666; margin-top: 4px; }
.eff-high    { color: #2d6a4f !important; font-weight: 700; }
.eff-medium  { color: #856404 !important; font-weight: 700; }

[data-testid="metric-container"] { background:#fff !important; border:1px solid #d4e6c3 !important; border-radius:14px !important; padding:18px !important; }
[data-testid="metric-container"] label { color:#555 !important; font-size:0.82rem !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color:#1b1b1b !important; font-weight:800 !important; }
.stButton > button { background-color: #2d6a4f; color: #fff; font-weight: 700; border: none; border-radius: 8px; }
.stButton > button:hover { background-color: #1a3d2e; }
h1,h2,h3,h4 { color:#1b1b1b; } p { color:#333; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ───────────────────────────────────────────────────────────────────
lang_code = render_sidebar(current_page="spoilage")

# ─── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div class="page-header-icon">⚠️</div>
  <div>
    <h1 style="color:#fff !important">{t('Spoilage Assessor', lang_code)}</h1>
    <p>Know your <strong>post-harvest spoilage risk</strong> and get ranked actions to preserve your produce.</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Inputs ────────────────────────────────────────────────────────────────
init_shared()
storage_options = list(STORAGE_PENALTY.keys())

inp_col, map_col = st.columns([1, 1.7])

with inp_col:
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    _def_crop = get_shared("crop")
    crop      = st.selectbox(t("Select Crop", lang_code), CROPS,
                             index=CROPS.index(_def_crop) if _def_crop in CROPS else 0,
                             key="sp_crop")
    quantity      = st.number_input(t("Quantity (Quintals)", lang_code),
                                    min_value=1.0, max_value=5000.0,
                                    value=float(get_shared("quantity") or 20.0), step=5.0)
    _def_stor     = get_shared("storage")
    storage_type  = st.selectbox(t("Storage Type", lang_code), storage_options,
                                 index=storage_options.index(_def_stor) if _def_stor in storage_options else 0)
    transit_hours = st.slider(t("Transit Duration (Hours)", lang_code),
                              min_value=1, max_value=48,
                              value=int(get_shared("transit") or 8), step=1)
    run = st.button(f"🔍 {t('Assess Spoilage Risk', lang_code)}", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with map_col:
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    district = render_district_selector("spoilage", lang_code, crop=crop)
    st.markdown('</div>', unsafe_allow_html=True)

sync_all(crop=crop, district=district, quantity=quantity, storage=storage_type, transit=transit_hours)

# ─── Results ───────────────────────────────────────────────────────────────────
if run:
    with st.spinner("Calculating spoilage risk from weather + crop data..."):
        result = assess_spoilage(crop, district, quantity, storage_type, transit_hours)

    risk  = result["risk_level"]
    color = result["risk_color"]
    prob  = result["spoilage_probability"]
    wx    = result["weather_summary"]

    risk_class  = f"risk-{risk.lower()}"
    label_class = f"risk-label-{risk.lower()}"
    act_class   = f"action-{risk.lower()}"

    # Risk Banner
    st.markdown(f"""
    <div class="risk-banner {risk_class}">
      <div style="color:#555;font-size:0.78rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;">
        {t('Spoilage Risk', lang_code)}
      </div>
      <div class="{label_class}">{color} {t(risk, lang_code)}</div>
      <div class="risk-prob">
        🎯 {t('Spoilage Probability', lang_code)}: <strong style="font-size:1.2rem;">{prob}</strong>
      </div>
      <div class="risk-why">📋 {result['reason']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🌡️ Risk Score",          f"{int(result['score']*100)}%",     border=True)
    m2.metric("💧 Avg Humidity",         f"{wx['avg_humidity']:.0f}%",       border=True)
    m3.metric("🌡️ Avg Temp (3-day)",    f"{wx['avg_temp']:.1f} °C",         border=True)
    m4.metric("🚛 Transit",             f"{transit_hours} hrs",               border=True)

    # Gauge + Actions
    col_gauge, col_actions = st.columns([1, 1.6])
    with col_gauge:
        gauge_color = {"HIGH": "#c0392b", "MEDIUM": "#e3a008", "LOW": "#2d6a4f"}[risk]
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=int(result["score"] * 100),
            domain={"x": [0,1], "y": [0,1]},
            title={"text": "Risk Score", "font": {"color": "#555", "size": 14}},
            number={"suffix": "%", "font": {"color": gauge_color, "size": 46}},
            gauge={
                "axis":       {"range": [0,100], "tickcolor": "#888", "tickwidth": 1},
                "bar":        {"color": gauge_color, "thickness": 0.28},
                "bgcolor":    "#f5f5f0",
                "bordercolor":"#d4e6c3",
                "borderwidth": 2,
                "steps": [
                    {"range": [0, 35],  "color": "#d4edda"},
                    {"range": [35, 65], "color": "#fff3cd"},
                    {"range": [65, 100],"color": "#f8d7da"},
                ],
                "threshold": {"line": {"color": gauge_color, "width": 3}, "thickness": 0.8, "value": int(result["score"]*100)},
            },
        ))
        fig.update_layout(
            paper_bgcolor="#fefae0", font_color="#333",
            height=260, margin=dict(l=20, r=20, t=40, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_actions:
        st.markdown(f"### 🛡️ {t('Recommended Actions', lang_code)}")
        for i, action in enumerate(result["actions"]):
            eff_class = "eff-high" if action["effectiveness"] == "High" else "eff-medium"
            st.markdown(f"""
            <div class="action-card {act_class}">
              <div class="action-num">#{i+1}</div>
              <div>
                <div class="action-text">{action['action']}</div>
                <div class="action-meta">
                  💰 {t('Cost', lang_code)}: <strong>{action['cost']}</strong>
                  &nbsp;·&nbsp;
                  ⚡ {t('Effectiveness', lang_code)}: <span class="{eff_class}">{action['effectiveness']}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # Summary expander
    with st.expander(f"📋 {t('Full Input Summary', lang_code)}", expanded=False):
        summary_df = pd.DataFrame([{
            "Crop": crop, "District": district, "Quantity": f"{quantity:.0f} qtl",
            "Storage Type": storage_type, "Transit": f"{transit_hours} hrs",
            "Risk Level": risk, "Probability": prob,
        }])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
