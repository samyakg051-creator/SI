"""
pages/4_Map_Explorer.py  (ASCII-safe version —  emoji in page display name is set via st.set_page_config)
AgriChain — Interactive India / Maharashtra Agricultural Map Explorer.
"""

import streamlit as st
from streamlit_folium import st_folium
from datetime import date, timedelta
import pandas as pd
import folium
import math

from modules.agri_data import (
    DISTRICT_CENTROIDS, MANDI_DATA, CROP_EMOJI, DEFAULT_EMOJI, CROP_DURATION, t,
)
from modules.data_loader import build_mandi_price_dict, get_top_mandis_for_crop, get_mandi_coords
from modules.map_utils import (
    build_base_map, add_india_layer, add_mh_district_layer,
    add_district_marker, add_mandi_markers,
    load_india_geojson, load_mh_districts_geojson,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgriChain — Map Explorer",
    page_icon="🗺️",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #fefae0 !important;
    color: #1b1b1b !important;
}
.stApp { background-color: #fefae0 !important; }
.main, .main > div, .block-container { background-color: #fefae0 !important; }
[data-testid="stAppViewContainer"] { background-color: #fefae0 !important; }
[data-testid="stHeader"] {
    background-color: #fefae0 !important;
    border-bottom: 1px solid #d4e6c3 !important;
}
section[data-testid="stSidebar"] { background-color: #1a3d2e !important; }
section[data-testid="stSidebar"] > div { padding: 1.2rem 1rem; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div { color: #d4f0c0 !important; }

.info-card {
    background: #fff; border: 1px solid #d4e6c3;
    border-radius: 14px; padding: 1.2rem 1.4rem;
    margin-bottom: 1rem; box-shadow: 0 2px 8px #2d6a4f15;
}
.info-card-title {
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #2d6a4f; margin-bottom: 0.8rem;
}
.summary-row {
    display: flex; justify-content: space-between;
    font-size: 0.88rem; padding: 4px 0; border-bottom: 1px solid #f0ebd0;
}
.summary-row:last-child { border-bottom: none; }
.summary-key { color: #888; }
.summary-val { font-weight: 600; color: #1b1b1b; }
.district-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: #2d6a4f; color: #fff; border-radius: 20px;
    padding: 0.35rem 1rem; font-size: 0.88rem; font-weight: 600;
}
.pill { display: inline-block; padding: 0.25rem 0.8rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
.pill-green  { background: #d4edda; color: #155724; }
.pill-yellow { background: #fff3cd; color: #856404; }
.pill-red    { background: #f8d7da; color: #721c24; }
.map-wrapper { border: 2px solid #52b788; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 16px #2d6a4f22; }
.section-heading { font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 800; color: #2d6a4f; margin-bottom: 0.3rem; }
.stButton > button {
    background: #2d6a4f; color: #fff; border: none; border-radius: 8px;
    padding: 0.5rem 1.4rem; font-weight: 600; width: 100%; cursor: pointer; transition: background 0.2s;
}
.stButton > button:hover { background: #1a3d2e; }
footer { visibility: hidden; }
.nav-card {
    background: #fff; border: 2px solid #52b788; border-radius: 14px;
    padding: 1.2rem 1.4rem; margin-bottom: 1rem; box-shadow: 0 4px 16px #2d6a4f22;
}
.nav-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #2d6a4f; margin-bottom: 0.8rem; }
.nav-btn {
    display: inline-block; background: #2d6a4f; color: #fff !important;
    padding: 0.5rem 1.2rem; border-radius: 8px; font-weight: 600;
    text-decoration: none; font-size: 0.88rem; transition: background 0.2s;
}
.nav-btn:hover { background: #1a3d2e; }
.mandi-nav-card {
    background: #f0f9f0; border: 1px solid #d4e6c3; border-radius: 12px;
    padding: 1rem; text-align: center; cursor: pointer; transition: all 0.2s;
}
.mandi-nav-card:hover { border-color: #52b788; box-shadow: 0 2px 8px #2d6a4f15; }
.route-line { stroke: #2d6a4f; stroke-width: 3; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
CROPS      = list(CROP_EMOJI.keys())
STORAGE_OPTIONS = ["cold_storage", "warehouse", "covered_shed", "open_yard", "none"]
DISTRICTS  = sorted(DISTRICT_CENTROIDS.keys())

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "crop":         CROPS[0],
    "district":     "Pune",
    "sowing_date":  date.today(),
    "quantity":     10,
    "storage_type": "warehouse",
    "language":     "en",
    "show_mandis":  True,
    "show_marker":  True,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

lang = st.session_state.get("language", "en")

# ── Shared sidebar + map-specific controls ────────────────────────────────────
from utils.sidebar import render_sidebar
lang = render_sidebar(current_page="map")

# Sync language from shared sidebar into the map's own state
st.session_state.language = st.session_state.get("app_language", "en")
lang = st.session_state.language

with st.sidebar:
    st.markdown('<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#6ee86e;margin-bottom:6px">🗺️ Map Controls</div>',
                unsafe_allow_html=True)

    crop = st.selectbox(
        f"&#127807; {t('crop', lang)}",
        CROPS,
        index=CROPS.index(st.session_state.crop) if st.session_state.crop in CROPS else 0,
    )
    st.session_state.crop = crop

    storage = st.selectbox(
        f"&#127968; {t('storage', lang)}",
        STORAGE_OPTIONS,
        index=STORAGE_OPTIONS.index(st.session_state.storage_type)
              if st.session_state.storage_type in STORAGE_OPTIONS else 1,
        format_func=lambda x: x.replace("_", " ").title(),
    )
    st.session_state.storage_type = storage

    qty = st.number_input(
        f"&#128230; {t('quantity', lang)}",
        min_value=1, max_value=10000,
        value=int(st.session_state.quantity), step=1,
    )
    st.session_state.quantity = qty

    st.markdown("---")

    st.markdown("<div style='font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#6ee86e;margin-bottom:0.5rem'>Map Options</div>",
                unsafe_allow_html=True)
    show_mandis = st.toggle(t("mandi_markers", lang), value=bool(st.session_state.show_mandis))
    st.session_state.show_mandis = show_mandis
    show_marker = st.toggle(t("crop_marker", lang), value=bool(st.session_state.show_marker))
    st.session_state.show_marker = show_marker

    st.markdown("---")

    emoji = CROP_EMOJI.get(crop, DEFAULT_EMOJI)
    sowing = st.session_state.sowing_date
    sd_str = sowing.strftime("%b %d") if hasattr(sowing, "strftime") else "—"
    st.markdown(f"""
    <div style="background:#1a3d2e;border-radius:10px;padding:0.9rem 1rem;font-size:0.85rem;color:#d4f0c0">
        <div style="color:#6ee86e;font-weight:700;margin-bottom:0.5rem">&#128203; Current Selection</div>
        <div>{emoji} {crop}</div>
        <div>&#128205; {st.session_state.district}</div>
        <div>&#128197; {sd_str}</div>
        <div>&#128230; {qty} qtl</div>
        <div>&#127968; {storage.replace('_',' ').title()}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Harvest Score"):
        st.switch_page("app.py")

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-heading">&#128506;&#65039; Maharashtra — Agricultural Map</div>', unsafe_allow_html=True)
st.markdown(f"<p style='color:#555;font-size:0.9rem;margin-top:-0.3rem'>{t('click_district', lang)}</p>",
            unsafe_allow_html=True)

# District dropdown (synced with map click)
col_drop, col_space = st.columns([2, 3])
with col_drop:
    district_idx = DISTRICTS.index(st.session_state.district) if st.session_state.district in DISTRICTS else 0
    selected_district = st.selectbox(
        f"&#128205; {t('select_district', lang)}",
        DISTRICTS,
        index=district_idx,
        key="district_dropdown",
    )
    if selected_district != st.session_state.district:
        st.session_state.district = selected_district
        st.rerun()

current_district = st.session_state.district

# ── Load GeoJSON ──────────────────────────────────────────────────────────────
with st.spinner("Loading map data..."):
    india_geojson = load_india_geojson()
    mh_geojson    = load_mh_districts_geojson()

# ── Build Folium map ──────────────────────────────────────────────────────────
center = DISTRICT_CENTROIDS.get(current_district, (19.7515, 75.7139))
m = build_base_map(center=center, zoom_start=8)

if india_geojson:
    m = add_india_layer(m, india_geojson)

if mh_geojson:
    m = add_mh_district_layer(m, mh_geojson, selected_district=current_district)

if show_marker and current_district:
    m = add_district_marker(m, current_district, crop, sd_str)

if show_mandis:
    m = add_mandi_markers(m, crop, selected_mandi="")

# ── Draw route to best mandi ──────────────────────────────────────────────────
def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

_top_for_nav = get_top_mandis_for_crop(crop, n=3)
_origin = DISTRICT_CENTROIDS.get(current_district, (19.75, 75.71))
_best_mandi_name = _top_for_nav.iloc[0]["Mandi"] if not _top_for_nav.empty else None
_best_coords = None
_best_dist_km = 0

if _best_mandi_name:
    _best_coords = get_mandi_coords(_best_mandi_name)
    _best_dist_km = round(_haversine(_origin[0], _origin[1], _best_coords[0], _best_coords[1]), 1)

    # Route line
    folium.PolyLine(
        [_origin, _best_coords],
        color="#2d6a4f", weight=4, opacity=0.8,
        dash_array="10 6",
        tooltip=f"Route to {_best_mandi_name} ({_best_dist_km} km)",
    ).add_to(m)

    # Star marker at destination
    folium.Marker(
        _best_coords,
        icon=folium.DivIcon(html=f'<div style="font-size:24px;text-shadow:0 2px 4px rgba(0,0,0,0.3)">⭐</div>'),
        tooltip=f"Best Mandi: {_best_mandi_name}",
    ).add_to(m)

# ── Render map ────────────────────────────────────────────────────────────────
st.markdown('<div class="map-wrapper">', unsafe_allow_html=True)
map_output = st_folium(m, key="agrichain_map", width="100%", height=520,
                       returned_objects=["last_object_clicked_tooltip", "last_clicked"])
st.markdown('</div>', unsafe_allow_html=True)

# ── Handle map click → update selected district ───────────────────────────────
if map_output:
    tooltip_val = map_output.get("last_object_clicked_tooltip")
    if tooltip_val and isinstance(tooltip_val, str):
        clicked = tooltip_val.strip().title()
        for d in DISTRICTS:
            if d.lower() in clicked.lower() or clicked.lower() in d.lower():
                if d != st.session_state.district:
                    st.session_state.district = d
                    st.rerun()
                break

# ── Info panels ───────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown('<div class="info-card-title">&#128205; Selected District</div>', unsafe_allow_html=True)
    coords = DISTRICT_CENTROIDS.get(current_district, (0, 0))
    st.markdown(f"""
    <div class="district-badge">{CROP_EMOJI.get(crop, DEFAULT_EMOJI)} {current_district}</div>
    <div style="font-size:0.82rem;color:#555;margin-top:0.6rem">
        <div>Lat: {coords[0]:.4f} &nbsp;|&nbsp; Lon: {coords[1]:.4f}</div>
        <div style="margin-top:4px">Crop: <b>{crop}</b></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    top_mandis = get_top_mandis_for_crop(crop, n=4)
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown('<div class="info-card-title">&#127978; Top Mandi Prices</div>', unsafe_allow_html=True)
    if top_mandis.empty:
        st.markdown('<div style="color:#888;font-size:0.85rem">No data</div>', unsafe_allow_html=True)
    else:
        for _, row in top_mandis.iterrows():
            st.markdown(f"""
            <div class="summary-row">
                <span class="summary-key">{row['Mandi']}</span>
                <span class="summary-val">&#8377;{row['LatestPrice']:,}</span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    duration = CROP_DURATION.get(crop, 90)
    sowing   = st.session_state.sowing_date
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown('<div class="info-card-title">&#127807; Crop Summary</div>', unsafe_allow_html=True)
    if hasattr(sowing, "strftime"):
        harvest_date = sowing + timedelta(days=duration)
        days_left    = (harvest_date - date.today()).days
        harvest_str  = harvest_date.strftime("%b %d, %Y")
        if days_left > 30:  risk_cls, risk_lbl = "pill-green",  "Early"
        elif days_left > 7: risk_cls, risk_lbl = "pill-yellow", "Soon"
        elif days_left > 0: risk_cls, risk_lbl = "pill-red",    "Ready!"
        else:               risk_cls, risk_lbl = "pill-red",    "Overdue"
    else:
        harvest_str  = "—"
        risk_cls, risk_lbl = "pill-green", "—"
    best_mandi  = top_mandis.iloc[0]["Mandi"] if not top_mandis.empty else "—"
    best_price  = int(top_mandis.iloc[0]["LatestPrice"]) if not top_mandis.empty else 0
    st.markdown(f"""
    <div class="summary-row"><span class="summary-key">&#8987; Duration</span><span class="summary-val">{duration} days</span></div>
    <div class="summary-row"><span class="summary-key">&#128197; Est. Harvest</span><span class="summary-val">{harvest_str}</span></div>
    <div class="summary-row"><span class="summary-key">&#9203; Status</span><span class="summary-val"><span class="pill {risk_cls}">{risk_lbl}</span></span></div>
    <div class="summary-row"><span class="summary-key">&#128176; Best Price</span><span class="summary-val">&#8377;{best_price:,} ({best_mandi})</span></div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── 🧭 Navigate to Best Mandi ────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-heading">&#128507;&#65039; Navigate to Best Mandi</div>', unsafe_allow_html=True)

if _best_mandi_name and _best_coords:
    gmaps_url = f"https://www.google.com/maps/dir/{_origin[0]},{_origin[1]}/{_best_coords[0]},{_best_coords[1]}"
    _best_price = int(_top_for_nav.iloc[0]["LatestPrice"]) if not _top_for_nav.empty else 0

    st.markdown(f"""
    <div class="nav-card">
        <div class="nav-title">&#11088; Recommended: {_best_mandi_name}</div>
        <div style="display:flex;gap:2rem;align-items:center;flex-wrap:wrap">
            <div>
                <div style="font-size:0.82rem;color:#555">Latest Price</div>
                <div style="font-size:1.4rem;font-weight:700;color:#2d6a4f">&#8377;{_best_price:,}/qtl</div>
            </div>
            <div>
                <div style="font-size:0.82rem;color:#555">Distance</div>
                <div style="font-size:1.4rem;font-weight:700;color:#1b1b1b">{_best_dist_km} km</div>
            </div>
            <div>
                <div style="font-size:0.82rem;color:#555">From</div>
                <div style="font-size:1rem;font-weight:600;color:#1b1b1b">{current_district}</div>
            </div>
            <a href="{gmaps_url}" target="_blank" class="nav-btn">
                &#128506;&#65039; Open in Google Maps
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show top 3 mandis with individual navigation
    if len(_top_for_nav) > 1:
        nav_cols = st.columns(min(len(_top_for_nav), 3))
        for idx, (_, row) in enumerate(_top_for_nav.iterrows()):
            if idx >= 3:
                break
            m_name = row["Mandi"]
            m_price = int(row["LatestPrice"])
            m_coords = get_mandi_coords(m_name)
            m_dist = round(_haversine(_origin[0], _origin[1], m_coords[0], m_coords[1]), 1)
            m_gmaps = f"https://www.google.com/maps/dir/{_origin[0]},{_origin[1]}/{m_coords[0]},{m_coords[1]}"
            rank_badge = "&#129351;" if idx == 0 else ("&#129352;" if idx == 1 else "&#129353;")

            with nav_cols[idx]:
                st.markdown(f"""
                <div class="mandi-nav-card">
                    <div style="font-size:1.2rem">{rank_badge}</div>
                    <div style="font-weight:700;color:#2d6a4f;font-size:0.95rem">{m_name}</div>
                    <div style="font-size:1.1rem;font-weight:700;margin:4px 0">&#8377;{m_price:,}/qtl</div>
                    <div style="font-size:0.78rem;color:#888">{m_dist} km away</div>
                    <a href="{m_gmaps}" target="_blank" style="display:inline-block;margin-top:8px;
                        background:#2d6a4f;color:#fff;padding:0.3rem 0.8rem;border-radius:6px;
                        font-size:0.78rem;font-weight:600;text-decoration:none">
                        Navigate &#8594;
                    </a>
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("No mandi data available for navigation.")
if show_mandis:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="info-card-title">&#127978; All Mandi Prices — {crop}</div>', unsafe_allow_html=True)
    all_mandis_df = get_top_mandis_for_crop(crop, n=50)
    if all_mandis_df.empty:
        st.info("No mandi price data available for this crop.")
    else:
        all_mandis_df = all_mandis_df.rename(columns={"AvgPrice": "Avg (Rs/qtl)", "LatestPrice": "Latest (Rs/qtl)"})
        st.dataframe(all_mandis_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;color:#aaa;font-size:0.76rem;margin-top:1rem">
    Map: CartoDB Positron &middot; GeoJSON: Survey of India composite &middot; Prices: AgriChain data
</div>
""", unsafe_allow_html=True)
