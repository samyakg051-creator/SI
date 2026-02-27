import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime

from modules.harvest_engine import get_harvest_recommendation, CROP_MATURITY_DAYS
from utils.geo import DISTRICT_COORDS
from utils.translator import t
from utils.map_selector import render_district_selector
from utils.shared_state import init_shared, get_shared, sync_all
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Harvest Window — AgriChain", page_icon="🌾", layout="wide")

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
    background: linear-gradient(135deg, #2d6a4f 0%, #1a3d2e 100%);
    border-radius: 20px;
    padding: 32px 36px;
    margin-bottom: 28px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 4px 20px #2d6a4f22;
}
.page-header-icon { font-size: 3rem; flex-shrink: 0; }
.page-header h1   { font-size: 2.2rem; font-weight: 900; color: #fff; margin: 0; line-height: 1.1; }
.page-header p    { font-size: 0.95rem; color: #a8d5ba; margin: 6px 0 0; }

.input-section {
    background: #fff;
    border: 1px solid #d4e6c3;
    border-radius: 18px;
    padding: 28px 28px 20px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px #2d6a4f08;
}

.window-card {
    background: linear-gradient(135deg, #2d6a4f 0%, #1a3d2e 100%);
    border-radius: 20px;
    padding: 32px 36px;
    margin: 20px 0;
    position: relative; overflow: hidden;
    box-shadow: 0 4px 20px #2d6a4f22; color: #fff;
}
.window-card::after {
    content: '📅';
    position: absolute; right: 24px; top: 50%; transform: translateY(-50%);
    font-size: 5rem; opacity: 0.1;
}
.window-label { color: #a8d5ba; font-size: 0.82rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; }
.window-dates { font-size: 1.9rem; font-weight: 900; color: #6ee86e; margin: 8px 0 4px; }

.score-bar-wrap { background: #e8e8e0; border-radius: 10px; height: 10px; overflow: hidden; margin-top: 6px; }
.score-bar      { height: 100%; border-radius: 10px; background: linear-gradient(90deg, #2d7a4f, #52b788); transition: width 0.5s ease; }

.reason-card {
    background: #fff;
    border: 1px solid #d4e6c3;
    border-left: 4px solid #2d6a4f;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #333;
    font-size: 0.93rem;
    line-height: 1.6;
    box-shadow: 0 2px 8px #2d6a4f08;
}

[data-testid="metric-container"] { background:#fff !important; border:1px solid #d4e6c3 !important; border-radius:14px !important; padding:18px !important; }
[data-testid="metric-container"] label { color:#555 !important; font-size:0.82rem !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color:#1b1b1b !important; font-weight:800 !important; }
.stButton > button { background-color: #2d6a4f; color: #fff; font-weight: 700; border: none; border-radius: 8px; }
.stButton > button:hover { background-color: #1a3d2e; }
h1,h2,h3,h4 { color:#1b1b1b; }
p { color:#333; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
lang_code = render_sidebar(current_page="harvest")

# ─── Page Header ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div class="page-header-icon">🌾</div>
  <div>
    <h1 style="color:#fff !important">{t('Harvest Window', lang_code)}</h1>
    <p>Find the <strong>best 5-day window</strong> to harvest your crop using weather + market data.</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Inputs ───────────────────────────────────────────────────────────────────
init_shared()
crop_opts = list(CROP_MATURITY_DAYS.keys())

inp_col, map_col = st.columns([1, 1.7])

with inp_col:
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    _def_crop = get_shared("crop")
    crop = st.selectbox(t("Select Crop", lang_code), crop_opts,
                        index=crop_opts.index(_def_crop) if _def_crop in crop_opts else 0,
                        key="h_crop")
    maturity    = CROP_MATURITY_DAYS.get(crop, 100)
    _def_sow    = get_shared("sowing") or (datetime.date.today() - datetime.timedelta(days=int(maturity*0.85)))
    sowing_date = st.date_input(t("Sowing Date", lang_code), value=_def_sow,
                                max_value=datetime.date.today(), format="DD/MM/YYYY")
    run = st.button(f"🔍 {t('Get Recommendation', lang_code)}", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with map_col:
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    district = render_district_selector("harvest", lang_code, crop=crop)
    st.markdown('</div>', unsafe_allow_html=True)

sync_all(crop=crop, district=district, sowing=sowing_date)

# ─── Result ───────────────────────────────────────────────────────────────────
if run:
    with st.spinner("Analysing weather & price data..."):
        result = get_harvest_recommendation(crop, district, sowing_date)

    sc   = result["score_components"]
    conf = result["confidence"]

    conf_colors = {"High": "#2d6a4f", "Medium": "#e3a008", "Low": "#c0392b"}
    conf_color  = conf_colors.get(conf, "#2d6a4f")
    st.markdown(f"""
    <div class="window-card">
      <div class="window-label">✨ {t('Best Harvest Window', lang_code)}</div>
      <div class="window-dates">{result['recommended_window']['start']} → {result['recommended_window']['end']}</div>
      <div style="display:flex;gap:16px;margin-top:12px;flex-wrap:wrap;">
        <span style="background:#1a3d2e;color:#6ee86e;border-radius:20px;padding:5px 16px;font-weight:700;font-size:0.88rem;">
          📈 {result['expected_price_premium']} {t('Expected Price Premium', lang_code)}
        </span>
        <span style="background:#1a3d2e;color:{conf_color};border:1px solid {conf_color}33;border-radius:20px;padding:5px 16px;font-weight:700;font-size:0.88rem;">
          🎯 {t('Confidence', lang_code)}: {t(conf, lang_code)}
        </span>
        <span style="background:#1a3d2e;color:#a8d5ba;border-radius:20px;padding:5px 16px;font-size:0.88rem;">
          📊 Score: {int(result['score']*100)}%
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Score breakdown
    st.markdown(f"#### 📊 {t('Score Breakdown', lang_code)}")
    sb1, sb2, sb3 = st.columns(3)

    def score_metric(col, emoji, label, val):
        pct = int(val * 100)
        color = "#2d6a4f" if pct >= 60 else "#e3a008" if pct >= 40 else "#c0392b"
        col.markdown(f"""
        <div style="background:#fff;border:1px solid #d4e6c3;border-radius:14px;padding:18px;box-shadow:0 2px 8px #2d6a4f08;">
          <div style="color:#555;font-size:0.8rem;font-weight:600;letter-spacing:0.08em;">{emoji} {label}</div>
          <div style="font-size:1.7rem;font-weight:900;color:{color};margin:6px 0 10px;">{pct}%</div>
          <div class="score-bar-wrap"><div class="score-bar" style="width:{pct}%;background:linear-gradient(90deg,{'#2d7a4f,#52b788' if pct>=60 else '#b8860b,#e3a008' if pct>=40 else '#a02020,#c0392b'});"></div></div>
        </div>""", unsafe_allow_html=True)

    score_metric(sb1, "📈", t("Price Seasonality", lang_code), sc["price_seasonality"])
    score_metric(sb2, "🌤️", t("Weather Score", lang_code),     sc["weather"])
    score_metric(sb3, "🌱", t("Soil Readiness", lang_code),    sc["soil_readiness"])

    # Reasons
    st.markdown(f"#### 🤔 {t('Why this recommendation?', lang_code)}")
    for r in result["reasons"]:
        st.markdown(f'<div class="reason-card">✅ {r}</div>', unsafe_allow_html=True)

    # Price trend chart
    st.markdown(f"#### 📈 {t('14-Day Price Trend', lang_code)} — **{crop}** in **{district}**")
    chart_df = pd.DataFrame(result["chart_data"])
    fig = px.area(chart_df, x="Date", y="Price (₹/qtl)",
                  color_discrete_sequence=["#2d6a4f"], template="simple_white")
    fig.update_traces(fillcolor="rgba(45,106,79,0.12)", line=dict(width=2.5))
    fig.update_layout(
        paper_bgcolor="#fefae0", plot_bgcolor="#fefae0",
        font_color="#333", margin=dict(l=16, r=16, t=16, b=16),
        xaxis=dict(showgrid=False, color="#555", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#d4e6c3", color="#555", tickfont=dict(size=11)),
        height=280,
    )
    import pandas as _pd
    vline_x = _pd.Timestamp(result["recommended_window"]["start"])
    fig.add_vline(x=vline_x.timestamp() * 1000, line_dash="dash", line_color="#2d6a4f",
                  annotation_text="⬆ Best Window", annotation_font_color="#2d6a4f", annotation_font_size=12)
    st.plotly_chart(fig, use_container_width=True)

    # Weather table
    st.markdown(f"#### 🌡️ {t('Weather Forecast', lang_code)} — Next 7 Days")
    wx = result["weather"]
    wx_df = pd.DataFrame({
        "Date":           wx["time"][:7],
        "Max Temp (°C)":  wx["temperature_2m_max"][:7],
        "Min Temp (°C)":  wx["temperature_2m_min"][:7],
        "Rainfall (mm)":  wx["precipitation_sum"][:7],
        "Humidity (%)":   wx["relative_humidity_2m_max"][:7],
    })
    st.dataframe(wx_df, use_container_width=True, hide_index=True)
