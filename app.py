"""
AgriChain – app.py  (Harvest Readiness Score dashboard)
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from modules.data_loader import load_price_df, get_all_crops, get_mandis_for_crop, get_mandi_coords

load_dotenv()

st.set_page_config(
    page_title="AgriChain – Harvest Readiness Intelligence",
    page_icon="🌾",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fefae0 !important; color: #1b1b1b !important; }
.stApp { background-color: #fefae0 !important; }
.main, .main > div, .block-container { background-color: #fefae0 !important; }
[data-testid="stAppViewContainer"] { background-color: #fefae0 !important; }
[data-testid="stHeader"] { background-color: #fefae0 !important; border-bottom: 1px solid #d4e6c3 !important; }
.main > div { padding-top: 1rem !important; }
section[data-testid="stSidebar"] { background-color: #1a3d2e !important; border-right: 1px solid #2d6a4f; }
section[data-testid="stSidebar"] > div { padding: 1.2rem 1rem; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div { color: #d4f0c0 !important; }
.aqi-badge { display:inline-block; padding:0.3rem 1rem; border-radius:20px; font-weight:700; font-size:0.88rem; margin-bottom:0.5rem; }
.aqi-good       { background:#d4edda; border:1px solid #4caf50; color:#155724; }
.aqi-moderate   { background:#fff3cd; border:1px solid #ffc107; color:#856404; }
.aqi-unhealthy  { background:#f8d7da; border:1px solid #f44336; color:#721c24; }
.aqi-hazardous  { background:#e8d5f5; border:1px solid #9c27b0; color:#6a0080; }
.curr-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:0.6rem; margin-bottom:1rem; }
.curr-cell { background:#fff; border:1px solid #d4e6c3; border-radius:10px; padding:0.7rem 0.8rem; text-align:center; box-shadow:0 2px 8px #2d6a4f08; }
.curr-icon { font-size:1.3rem; }
.curr-lbl  { font-size:0.65rem; color:#555; text-transform:uppercase; letter-spacing:0.06em; margin:2px 0; }
.curr-val  { font-size:1.05rem; font-weight:700; color:#1b1b1b; }
.day-cards { display:flex; gap:0.6rem; flex-wrap:wrap; margin-top:0.5rem; }
.day-card  { background:#fff; border:1px solid #d4e6c3; border-radius:12px; padding:0.8rem 0.7rem; flex:1; min-width:110px; text-align:center; box-shadow:0 2px 8px #2d6a4f08; }
.day-date  { font-size:0.68rem; color:#555; margin-bottom:4px; }
.day-cond  { font-size:1rem; margin:4px 0; }
.day-temp  { font-size:0.88rem; font-weight:700; color:#1b1b1b; }
.day-sub   { font-size:0.72rem; color:#555; margin-top:2px; }
.sidebar-brand { display: flex; align-items: center; gap: 10px; margin-bottom: 0.2rem; }
.sidebar-brand-name { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 800; color: #6ee86e; }
.sidebar-subtitle { font-size: 0.78rem; color: #4a7a4a; font-weight: 500; margin-bottom: 1.5rem; }
.sidebar-divider { border: none; border-top: 1px solid #1e3a1e; margin: 1.2rem 0; }
div[data-testid="stSelectbox"] > div > div { background-color: #0e2a1c !important; border: 1px solid #2d6a4f !important; border-radius: 8px !important; color: #d4f0c0 !important; }
.stButton > button { background-color: #2d6a4f; color: #fff; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.95rem; border: none; border-radius: 8px; padding: 0.55rem 1.5rem; width: 100%; cursor: pointer; transition: background 0.2s; }
.stButton > button:hover { background-color: #1a3d2e; }
.hero-card { background: linear-gradient(135deg, #2d6a4f, #1a3d2e); border-radius: 18px; padding: 1.5rem 2rem; display: flex; align-items: center; gap: 16px; margin-bottom: 1rem; box-shadow: 0 4px 20px #2d6a4f22; }
.hero-logo { font-size: 2.4rem; }
.hero-title { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800; color: #fff; margin: 0; }
.hero-subtitle { color: #a8d5ba; font-size: 0.85rem; margin-top: 2px; }
.score-card { background: linear-gradient(135deg, #2d6a4f, #1a3d2e); border-radius: 16px; padding: 1rem 1.5rem; text-align: center; margin-bottom: 1rem; color: #fff; box-shadow: 0 4px 20px #2d6a4f22; display: flex; align-items: center; justify-content: center; gap: 2rem; flex-wrap: wrap; }
.score-left { display: flex; flex-direction: column; align-items: center; }
.score-number { font-family: 'Syne', sans-serif; font-size: 3.2rem; font-weight: 800; line-height: 1; color: #6ee86e; }
.score-denom { font-size: 0.9rem; color: #a8d5ba; margin-top: 2px; }
.score-badge { display: inline-flex; align-items: center; gap: 6px; padding: 0.25rem 0.8rem; border-radius: 20px; font-size: 0.76rem; font-weight: 600; margin: 0.4rem auto 0.2rem auto; }
.badge-green  { background: #d4edda; color: #155724; }
.badge-yellow { background: #fff3cd; color: #856404; }
.badge-red    { background: #f8d7da; color: #721c24; }
.score-tagline { font-size: 0.72rem; color: #a8d5ba; margin-top: 2px; }
.component-scores { display: flex; justify-content: center; gap: 0.6rem; flex-wrap: wrap; }
.comp-item { text-align: center; background: #1a3d2e; border-radius: 8px; padding: 0.4rem 0.8rem; }
.comp-label { font-size: 0.65rem; color: #a8d5ba; text-transform: uppercase; letter-spacing: 0.06em; }
.comp-value { font-size: 0.88rem; font-weight: 700; color: #fff; }
.comp-value span { font-size: 0.7rem; color: #a8d5ba; }
.section-card { background: #fff; border: 1px solid #d4e6c3; border-radius: 14px; padding: 1.4rem 1.6rem; margin-bottom: 1rem; box-shadow: 0 2px 8px #2d6a4f08; }
.section-title { font-size: 0.78rem; font-weight: 700; color: #2d6a4f; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1rem; }
.metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
.metric-box { background: #f0f9f0; border: 1px solid #d4e6c3; border-radius: 10px; padding: 0.9rem 1rem; }
.metric-lbl { font-size: 0.72rem; color: #555; text-transform: uppercase; letter-spacing: 0.06em; }
.metric-val { font-size: 1.3rem; font-weight: 700; color: #1b1b1b; margin-top: 2px; }
.metric-val.positive { color: #2d6a4f; }
.metric-val.negative { color: #c0392b; }
.explanation-text { font-size: 0.88rem; line-height: 1.7; color: #555; white-space: pre-wrap; }
.chat-card { background: #fff; border: 1px solid #d4e6c3; border-radius: 14px; padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
.chat-title { font-size: 0.78rem; font-weight: 700; color: #2d6a4f; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1rem; }
.chat-msg-user { background: #2d6a4f; border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.6rem; font-size: 0.88rem; color: #fff; text-align: right; }
.chat-msg-ai { background: #f0f9f0; border: 1px solid #d4e6c3; border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.6rem; font-size: 0.88rem; color: #333; line-height: 1.6; }
.info-box { background: #f0f9f0; border: 1px solid #d4e6c3; border-radius: 10px; padding: 1.2rem 1.4rem; color: #555; font-size: 0.88rem; text-align: center; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Additional CSS for forecast section ───────────────────────────────────────
st.markdown("""
<style>
.forecast-card { background: #fff; border: 1px solid #d4e6c3; border-radius: 14px; padding: 1.4rem 1.6rem; margin-bottom: 1rem; box-shadow: 0 2px 8px #2d6a4f08; }
.forecast-title { font-size: 0.78rem; font-weight: 700; color: #2d6a4f; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1rem; }
.pred-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; margin-bottom: 1rem; }
.pred-cell { background: #f0f9f0; border: 1px solid #d4e6c3; border-radius: 10px; padding: 0.9rem 1rem; text-align: center; }
.pred-lbl { font-size: 0.68rem; color: #555; text-transform: uppercase; letter-spacing: 0.06em; }
.pred-val { font-size: 1.3rem; font-weight: 700; margin-top: 4px; }
.pred-change { font-size: 0.76rem; margin-top: 2px; }
.chart-row { display: flex; align-items: flex-end; gap: 2px; height: 60px; margin: 0.8rem 0; }
.chart-bar { flex: 1; border-radius: 3px 3px 0 0; min-width: 3px; transition: height 0.3s; }
</style>
""", unsafe_allow_html=True)

STORAGE_ICONS = {"cold_storage":"❄️","warehouse":"🏗️","covered_shed":"🏚️","open_yard":"🌿","none":"🚫"}

from utils.translator import t
from modules.price_analysis import analyse_prices
from modules.scoring import generate_score
from modules.weather import get_weather_score
from modules.explanation import generate_explanation, generate_harvest_window, generate_farmer_summary
from modules.ai_assistant import get_ai_response, build_context
from modules.price_predictor import predict_future_prices

# Load data — uses absolute pathlib path from data_loader, safe from any CWD
try:
    price_df  = load_price_df()
    all_crops = get_all_crops()
    if price_df.empty:
        st.stop()
except Exception as e:
    st.error(f"Failed to load price data: {e}")
    st.stop()

for k, v in [("chat_history",[]),("ai_context",""),("analysis_done",False),
             ("score_result",None),("price_result",None),("weather_result",None),
             ("explanation_text",""),("selected_crop",""),("selected_mandi",""),
             ("crop",""),("district","Pune"),("storage_type","warehouse"),
             ("quantity",10),("sowing_date",None),("language","en")]:
    if k not in st.session_state: st.session_state[k] = v

STORAGE = ["cold_storage","warehouse","covered_shed","open_yard","none"]

from utils.sidebar import render_sidebar
lang = render_sidebar(current_page="home")

with st.sidebar:
    st.markdown(f'<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#6ee86e;margin-bottom:6px">🌾 {t("Farm Parameters", lang)}</div>',
                unsafe_allow_html=True)
    crop = st.selectbox(f"🌱  {t('Crop', lang)}", all_crops, index=0)
    mandis_for_crop = get_mandis_for_crop(crop)
    mandi = st.selectbox(f"🏪  {t('Mandi Market', lang)}", mandis_for_crop, index=0)
    storage_type = st.selectbox(f"🏚️  {t('Storage Type', lang)}", STORAGE,
        index=STORAGE.index(st.session_state.storage_type) if st.session_state.storage_type in STORAGE else 0,
        format_func=lambda x: f"{STORAGE_ICONS.get(x,'')}  {x.replace('_',' ').title()}")
    distance_km = st.slider(f"🚛  {t('Distance to Mandi (km)', lang)}", 0, 500, 100, 10)
    run_button = st.button(f"📊  {t('Calculate Score', lang)}", type="primary")

groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()

st.markdown(f"""
<div class="hero-card">
    <div class="hero-logo">🌾</div>
    <div>
        <div class="hero-title">AgriChain</div>
        <div class="hero-subtitle">{t('Harvest Readiness Intelligence', lang)} · {crop} · {mandi}</div>
    </div>
</div>
""", unsafe_allow_html=True)

if run_button:
    try:
        lat, lon = get_mandi_coords(mandi)
        with st.spinner("Analysing price trends..."):
            price_result = analyse_prices(crop=crop, mandi=mandi)
        with st.spinner(f"Fetching live weather for {mandi}..."):
            weather_result = get_weather_score(latitude=lat, longitude=lon)
        score_result = generate_score(price_score=price_result.price_score,
            weather_score=weather_result.weather_score, storage_type=storage_type,
            distance_km=float(distance_km))
        explanation_text = generate_explanation(price_result=price_result,
            weather_result=weather_result, storage_type=storage_type, distance_km=distance_km)

        st.session_state.update(dict(analysis_done=True, score_result=score_result,
            price_result=price_result, weather_result=weather_result,
            explanation_text=explanation_text, selected_crop=crop, selected_mandi=mandi,
            chat_history=[], crop=crop, storage_type=storage_type,
            ai_context=build_context(crop=crop, mandi=mandi, price_result=price_result,
                weather_result=weather_result, score_result=score_result,
                storage_type=storage_type, distance_km=distance_km)))
    except FileNotFoundError as e: st.error(f"Data file not found: {e}")
    except ValueError as e: st.error(f"Data error: {e}")
    except Exception as e: st.error(f"Unexpected error: {e}")

if st.session_state.analysis_done:
    sr = st.session_state.score_result
    pr = st.session_state.price_result
    wr = st.session_state.weather_result
    et = st.session_state.explanation_text
    tl = sr.traffic_light
    bc = {"Green":"badge-green","Yellow":"badge-yellow","Red":"badge-red"}.get(tl,"badge-green")
    bd = {"Green":"🟢","Yellow":"🟡","Red":"🔴"}.get(tl,"🟢")
    bt = {"Green":"Good Time to Sell","Yellow":"Monitor Conditions","Red":"Hold — Wait for Better Prices"}.get(tl,"")
    tg = {"Green":"Conditions are favourable — sell now","Yellow":"Mixed signals — proceed with caution","Red":"Market conditions are unfavourable"}.get(tl,"")

    # ── 🌾 Farmer Summary (plain language) ────────────────────────────────
    farmer_summary = generate_farmer_summary(
        crop=st.session_state.selected_crop,
        mandi=st.session_state.selected_mandi,
        final_score=sr.final_score,
        traffic_light=tl,
        price_trend=pr.trend_percent,
        hot_days=wr.hot_days_count,
        rainy_days=wr.rainy_days_count,
        storage_type=st.session_state.storage_type,
        distance_km=float(distance_km),
    )
    summary_border = {"Green":"#4caf50","Yellow":"#ffc107","Red":"#f44336"}.get(tl,"#4caf50")
    st.markdown(f"""
    <div style="background:#fff;border:2px solid {summary_border};
        border-radius:16px;padding:1.4rem 1.6rem;margin-bottom:1rem;box-shadow:0 2px 8px #2d6a4f08;">
        <div style="font-size:0.72rem;font-weight:600;color:{summary_border};text-transform:uppercase;
            letter-spacing:0.08em;margin-bottom:0.6rem">🌾 {t('Your Harvest Summary', lang)}</div>
        <div style="font-size:1rem;line-height:1.7;color:#333">{farmer_summary}</div>
    </div>""", unsafe_allow_html=True)

    # ── ⏰ Harvest Window Recommendation ──────────────────────────────────
    window_text, urgency_level, urgency_color = generate_harvest_window(
        price_trend=pr.trend_percent,
        hot_days=wr.hot_days_count,
        rainy_days=wr.rainy_days_count,
        storage_type=st.session_state.storage_type,
    )
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #d4e6c3;border-radius:14px;
        padding:1.2rem 1.4rem;margin-bottom:1rem;box-shadow:0 2px 8px #2d6a4f08;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.6rem">
            <span style="font-size:0.72rem;font-weight:600;color:#2d6a4f;text-transform:uppercase;
                letter-spacing:0.08em">⏰ {t('When to Sell', lang)}</span>
            <span style="background:{urgency_color}22;border:1px solid {urgency_color};color:{urgency_color};
                padding:0.2rem 0.8rem;border-radius:20px;font-size:0.78rem;font-weight:700">{urgency_level}</span>
        </div>
        <div style="font-size:0.92rem;line-height:1.6;color:#333">{window_text}</div>
    </div>""", unsafe_allow_html=True)

    # ── Score Card ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="score-card">
        <div class="score-left">
            <div class="score-number">{int(sr.final_score)}</div>
            <div class="score-denom">/ 100</div>
            <div><span class="score-badge {bc}">{bd} {bt}</span></div>
            <div class="score-tagline">{tg}</div>
        </div>
        <div class="component-scores">
            <div class="comp-item"><div class="comp-label">{t('Price', lang)}</div><div class="comp-value">{pr.price_score:.1f}<span>/30</span></div></div>
            <div class="comp-item"><div class="comp-label">{t('Weather', lang)}</div><div class="comp-value">{sr.weather_score:.1f}<span>/30</span></div></div>
            <div class="comp-item"><div class="comp-label">{t('Storage', lang)}</div><div class="comp-value">{sr.storage_score:.1f}<span>/20</span></div></div>
            <div class="comp-item"><div class="comp-label">{t('Transport', lang)}</div><div class="comp-value">{sr.transport_score:.1f}<span>/20</span></div></div>
        </div>
    </div>""", unsafe_allow_html=True)

    cl, cr = st.columns(2)
    with cl:
        ts = "+" if pr.trend_percent >= 0 else ""
        tc = "positive" if pr.trend_percent >= 0 else "negative"
        trend_icon = "&#8593;" if pr.trend_percent >= 5 else ("&#8595;" if pr.trend_percent < -5 else "&#8596;")
        trend_col = "#4caf50" if pr.trend_percent >= 0 else "#f44336"

        st.markdown(f"""<div class="section-card"><div class="section-title">📈 {t('Price Analysis', lang)} — {st.session_state.selected_mandi}</div>
        <div class="metric-grid">
        <div class="metric-box"><div class="metric-lbl">{t('7-Day Avg', lang)}</div><div class="metric-val">₹{pr.last_7_avg:,.0f}</div></div>
        <div class="metric-box"><div class="metric-lbl">{t('30-Day Avg', lang)}</div><div class="metric-val">₹{pr.last_30_avg:,.0f}</div></div>
        <div class="metric-box"><div class="metric-lbl">{t('Price Trend', lang)}</div><div class="metric-val" style="color:{trend_col}">{trend_icon} {ts}{pr.trend_percent:.2f}%</div></div>
        <div class="metric-box"><div class="metric-lbl">{t('Price Score', lang)}</div><div class="metric-val">{pr.price_score:.1f}<span style="font-size:0.82rem;color:#888"> /30</span></div></div>
        </div>""", unsafe_allow_html=True)

        # Price comparison with top mandis
        from modules.data_loader import get_top_mandis_for_crop
        top_m = get_top_mandis_for_crop(st.session_state.selected_crop, n=5)
        if not top_m.empty:
            st.markdown(f'<div style="font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:0.08em;margin:0.8rem 0 0.4rem">{t("Top Mandis Comparison", lang)}</div>', unsafe_allow_html=True)
            for _, row in top_m.iterrows():
                m_name = row["Mandi"]
                m_price = int(row["LatestPrice"])
                m_avg = int(row["AvgPrice"])
                is_current = m_name.lower() == st.session_state.selected_mandi.lower()
                bar_w = min(100, max(20, int(m_price / (top_m["LatestPrice"].max() or 1) * 100)))
                bar_col = "#2d6a4f" if is_current else "#d4e6c3"
                bdr = "border:1px solid #2d6a4f;" if is_current else ""
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;padding:4px 6px;border-radius:6px;{bdr}">
                    <div style="font-size:0.76rem;color:#1b1b1b;min-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{m_name}">
                        {"&#11088; " if is_current else ""}{m_name[:18]}
                    </div>
                    <div style="flex:1;height:14px;background:#e8e8e0;border-radius:4px;overflow:hidden">
                        <div style="width:{bar_w}%;height:100%;background:{bar_col};border-radius:4px"></div>
                    </div>
                    <div style="font-size:0.78rem;font-weight:700;color:#1b1b1b;min-width:60px;text-align:right">₹{m_price:,}</div>
                </div>""", unsafe_allow_html=True)

        # Price insight
        if pr.trend_percent >= 5:
            insight = "&#128994; Prices rising strongly — favorable for selling"
        elif pr.trend_percent >= 0:
            insight = "&#128992; Prices stable or slightly up — reasonable to sell"
        elif pr.trend_percent >= -5:
            insight = "&#128993; Slight price dip — consider waiting if storage allows"
        else:
            insight = "&#128308; Prices dropping — sell if spoilage risk is high, else wait"

        st.markdown(f"""
        <div style="background:#f0f9f0;border:1px solid #d4e6c3;border-radius:8px;padding:0.6rem 0.8rem;margin-top:0.8rem;font-size:0.82rem;color:#333">
            {insight}
        </div>
        </div>""", unsafe_allow_html=True)

    with cr:
        # ── AQI colour class ──────────────────────────────────────────────
        if wr.aqi <= 50:   aqi_cls = "aqi-good"
        elif wr.aqi <= 100: aqi_cls = "aqi-moderate"
        elif wr.aqi <= 200: aqi_cls = "aqi-unhealthy"
        else:               aqi_cls = "aqi-hazardous"

        # ── UV risk label ─────────────────────────────────────────────────
        uv = wr.current_uv
        uv_lbl = "Low" if uv<3 else ("Moderate" if uv<6 else ("High" if uv<8 else ("Very High" if uv<11 else "Extreme")))
        uv_col = "#4caf50" if uv<3 else ("#ffc107" if uv<6 else ("#ff9800" if uv<8 else "#f44336"))

        # ── Build 5-day cards HTML ────────────────────────────────────────
        day_html = ""
        for d in wr.days:
            hc2 = "#f44336" if d.temp_max > 35 else "#1b1b1b"
            day_html += f"""
            <div class="day-card">
                <div class="day-date">{d.date}</div>
                <div class="day-cond">{d.condition}</div>
                <div class="day-temp" style="color:{hc2}">&#8593;{d.temp_max}° &#8595;{d.temp_min}°</div>
                <div class="day-sub">&#127783; {d.precip_prob}%</div>
                <div class="day-sub">&#128168; {d.wind_max} km/h</div>
                <div class="day-sub">&#128167; {d.humidity_mean}%</div>
                <div class="day-sub">&#9728; UV {d.uv_index}</div>
            </div>"""

        mandi_name = st.session_state.selected_mandi
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">&#127774; {t('Weather at', lang)} {mandi_name}</div>
            <span class="aqi-badge {aqi_cls}">AQI {wr.aqi} — {wr.aqi_label}</span>
            <div class="curr-grid">
                <div class="curr-cell"><div class="curr-icon">&#127777;</div><div class="curr-lbl">{t('Temp', lang)}</div><div class="curr-val">{wr.current_temp}°C</div></div>
                <div class="curr-cell"><div class="curr-icon">&#128167;</div><div class="curr-lbl">{t('Humidity', lang)}</div><div class="curr-val">{wr.current_humidity}%</div></div>
                <div class="curr-cell"><div class="curr-icon">&#128168;</div><div class="curr-lbl">{t('Wind', lang)}</div><div class="curr-val">{wr.current_wind} km/h</div></div>
                <div class="curr-cell"><div class="curr-icon">&#127783;</div><div class="curr-lbl">{t('Precip', lang)}</div><div class="curr-val">{wr.current_precip} mm</div></div>
                <div class="curr-cell"><div class="curr-icon" style="color:{uv_col}">&#9728;</div><div class="curr-lbl">{t('UV Index', lang)}</div><div class="curr-val" style="color:{uv_col}">{uv} ({uv_lbl})</div></div>
                <div class="curr-cell"><div class="curr-icon">&#128066;</div><div class="curr-lbl">{t('PM2.5', lang)}</div><div class="curr-val">{wr.pm25} &#181;g</div></div>
            </div>
            <div style="font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem">{t('5-Day Forecast', lang)}</div>
            <div class="day-cards">{day_html}</div>
            <div style="display:flex;gap:1.5rem;margin-top:0.8rem;flex-wrap:wrap">
                <span style="font-size:0.78rem;color:#555">{t('Weather Score', lang)}: <b style="color:#1b1b1b">{wr.weather_score:.1f}/30</b></span>
                <span style="font-size:0.78rem;color:#555">&#127777; {t('Hot days', lang)} &gt;35°C: <b style="color:{'#c0392b' if wr.hot_days_count>0 else '#2d6a4f'}">{wr.hot_days_count}</b></span>
                <span style="font-size:0.78rem;color:#555">&#127783; {t('Rainy days', lang)} &gt;60%: <b style="color:{'#c0392b' if wr.rainy_days_count>0 else '#2d6a4f'}">{wr.rainy_days_count}</b></span>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── 🤖 ML Price Forecast ─────────────────────────────────────────────
    with st.spinner("Training ML model for price prediction..."):
        forecast = predict_future_prices(
            crop=st.session_state.selected_crop,
            mandi=st.session_state.selected_mandi,
            days_ahead=30,
        )

    if forecast:
        curr = forecast["current_price"]
        p7  = forecast["price_7d"]
        p14 = forecast["price_14d"]
        p30 = forecast["price_30d"]
        chg7  = ((p7  - curr) / curr * 100) if curr else 0
        chg14 = ((p14 - curr) / curr * 100) if curr else 0
        chg30 = ((p30 - curr) / curr * 100) if curr else 0

        def _arrow(chg):
            if chg > 2:   return "&#8593;", "#4caf50"
            elif chg < -2: return "&#8595;", "#f44336"
            else:          return "&#8596;", "#ffc107"

        a7, c7   = _arrow(chg7)
        a14, c14 = _arrow(chg14)
        a30, c30 = _arrow(chg30)

        trend_emoji = {"up": "📈", "down": "📉", "stable": "📊"}.get(forecast["trend_direction"], "📊")

        # Mini chart — last 15 history + 15 predictions
        chart_bars = ""
        hist = forecast["history"][-15:]
        preds = forecast["predictions"][:15]
        all_vals = [h["price"] for h in hist] + [p["price"] for p in preds]
        max_v = max(all_vals) if all_vals else 1
        min_v = min(all_vals) if all_vals else 0
        rng = max_v - min_v if max_v != min_v else 1

        for h in hist:
            ht = max(8, int((h["price"] - min_v) / rng * 80))
            chart_bars += f'<div class="chart-bar" style="height:{ht}px;background:#a8d5ba" title="{h["date"]}: ₹{h["price"]:,.0f}"></div>'
        for p in preds:
            ht = max(8, int((p["price"] - min_v) / rng * 80))
            chart_bars += f'<div class="chart-bar" style="height:{ht}px;background:#2d6a4f" title="{p["date"]}: ₹{p["price"]:,.0f}"></div>'

        # Farmer-friendly forecast message
        if chg7 > 5:
            farmer_msg = f"Good news! Prices are expected to increase to ₹{p7:,.0f} in the next week. You may want to wait a few days for better returns."
            msg_icon = "&#128994;"
        elif chg7 > 0:
            farmer_msg = f"Prices should stay around ₹{p7:,.0f} next week — a small increase. Selling this week or next looks fine."
            msg_icon = "&#128992;"
        elif chg7 > -5:
            farmer_msg = f"Prices may drop slightly to ₹{p7:,.0f}. If your crop can be stored, you can wait. Otherwise sell now."
            msg_icon = "&#128993;"
        else:
            farmer_msg = f"Prices may fall to ₹{p7:,.0f} — consider selling soon before they drop further."
            msg_icon = "&#128308;"

        # Build 7-day daily breakdown
        daily_rows = ""
        for day in forecast["predictions"][:7]:
            d_chg = ((day["price"] - curr) / curr * 100) if curr else 0
            d_col = "#4caf50" if d_chg >= 0 else "#f44336"
            d_sign = "+" if d_chg >= 0 else ""
            daily_rows += f"""
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #d4e6c3;font-size:0.8rem">
                <span style="color:#555">{day['date']}</span>
                <span style="font-weight:700;color:#1b1b1b">₹{day['price']:,.0f}</span>
                <span style="color:{d_col};min-width:50px;text-align:right">{d_sign}{d_chg:.1f}%</span>
                <span style="color:#555;font-size:0.72rem;min-width:100px;text-align:right">₹{day['low']:,.0f} – ₹{day['high']:,.0f}</span>
            </div>"""

        conf_col = "#4caf50" if forecast["confidence"] > 80 else ("#ffc107" if forecast["confidence"] > 65 else "#ff9800")
        data_pts = forecast.get("data_points", 0)

        st.markdown(f"""
        <div class="forecast-card">
            <div class="forecast-title">{trend_emoji} {t('ML Price Forecast', lang)} — {st.session_state.selected_crop} · {st.session_state.selected_mandi}</div>
            <div style="display:flex;gap:1.5rem;margin-bottom:0.8rem;flex-wrap:wrap;font-size:0.76rem;color:#555">
                <span>Model confidence: <b style="color:{conf_col}">{forecast['confidence']}%</b></span>
                <span>Current price: <b style="color:#1b1b1b">₹{curr:,.0f}/qtl</b></span>
                <span>Training data: <b style="color:#1b1b1b">{data_pts} records</b></span>
            </div>
            <div class="pred-grid">
                <div class="pred-cell">
                    <div class="pred-lbl">{t('In 7 Days', lang)}</div>
                    <div class="pred-val" style="color:{c7}">₹{p7:,.0f}</div>
                    <div class="pred-change" style="color:{c7}">{a7} {chg7:+.1f}%</div>
                </div>
                <div class="pred-cell">
                    <div class="pred-lbl">{t('In 14 Days', lang)}</div>
                    <div class="pred-val" style="color:{c14}">₹{p14:,.0f}</div>
                    <div class="pred-change" style="color:{c14}">{a14} {chg14:+.1f}%</div>
                </div>
                <div class="pred-cell">
                    <div class="pred-lbl">{t('In 30 Days', lang)}</div>
                    <div class="pred-val" style="color:{c30}">₹{p30:,.0f}</div>
                    <div class="pred-change" style="color:{c30}">{a30} {chg30:+.1f}%</div>
                </div>
            </div>
            <div style="font-size:0.68rem;color:#555;display:flex;justify-content:space-between;margin-bottom:2px">
                <span>◀ Past 15 records (₹{min_v:,.0f} – ₹{max_v:,.0f})</span><span>Next 15 days ▶</span>
            </div>
            <div class="chart-row" style="height:85px">{chart_bars}</div>
            <div style="display:flex;gap:1rem;margin-top:4px">
                <span style="font-size:0.7rem;color:#555">&#9632; <span style="color:#a8d5ba">{t('Historical', lang)}</span></span>
                <span style="font-size:0.7rem;color:#555">&#9632; <span style="color:#2d6a4f">{t('Predicted', lang)}</span></span>
            </div>
        </div>""", unsafe_allow_html=True)

        # 7-day breakdown as separate card
        st.markdown("""
        <div class="forecast-card" style="margin-top:-0.5rem;border-top:none;border-top-left-radius:0;border-top-right-radius:0">
            <div style="font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem">
                7-Day Price Breakdown (with confidence range)
            </div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #d4e6c3;font-size:0.68rem;color:#888;font-weight:700">
                <span>Date</span><span>Predicted</span><span>Change</span><span>Range (95%)</span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(daily_rows, unsafe_allow_html=True)

        st.markdown(f"""
            <div style="background:#f0f9f0;border:1px solid #d4e6c3;border-radius:10px;padding:0.8rem 1rem;margin-top:0.8rem;font-size:0.88rem;color:#333;line-height:1.6">
                {msg_icon} {farmer_msg}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="forecast-card" style="opacity:0.5">
            <div class="forecast-title">📈 Price Forecast</div>
            <div style="color:#555;font-size:0.88rem">
                Not enough historical data for this crop-mandi combination to train a prediction model.
                At least 30 price records are needed.
            </div>
        </div>""", unsafe_allow_html=True)

    # ── 📋 Why this recommendation? (VISIBLE by default) ──────────────────
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">📋 {t('Why This Recommendation?', lang)}</div>
        <div class="explanation-text">{et}</div>
    </div>""", unsafe_allow_html=True)


else:
    st.markdown(f"""
    <div class="score-card" style="opacity:0.6;">
        <div class="score-number" style="font-size:3rem;color:#a8d5ba;">—</div>
        <div class="score-denom">/ 100</div>
        <div class="score-tagline" style="margin-top:0.8rem;">
            {t('configure_msg', lang)} <strong style="color:#6ee86e">{t('Calculate Score', lang)}</strong>
        </div>
    </div>
    <div class="info-box">
        🌾 &nbsp; {t('configure_msg', lang)} <strong>{t('Calculate Score', lang)}</strong>.<br>
        {t('ai_help_msg', lang)}
    </div>
    """, unsafe_allow_html=True)

