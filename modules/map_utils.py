"""
modules/map_utils.py
Shared Folium map-building utilities for AgriChain.
"""

import folium
import requests
import streamlit as st
from modules.agri_data import DISTRICT_CENTROIDS, MANDI_DATA, CROP_EMOJI, DEFAULT_EMOJI

# ── GeoJSON URLs ──────────────────────────────────────────────────────────────
INDIA_GEOJSON_URL = (
    "https://raw.githubusercontent.com/datameet/maps/master/Country/india-composite.geojson"
)
MH_DISTRICTS_URLS = [
    "https://raw.githubusercontent.com/datameet/maps/master/States/maharashtra.geojson",
    "https://raw.githubusercontent.com/geohacker/india/master/state/maharashtra.geojson",
    "https://raw.githubusercontent.com/answerquest/answerquest.github.io/master/data/Maharashtra_Districts.geojson",
]


@st.cache_data(show_spinner=False, ttl=86400)
def load_india_geojson() -> dict | None:
    """Load India composite GeoJSON (correct borders incl. PoK, Aksai Chin, Arunachal)."""
    try:
        r = requests.get(INDIA_GEOJSON_URL, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=86400)
def load_mh_districts_geojson() -> dict | None:
    """Load Maharashtra district GeoJSON, trying multiple fallback URLs."""
    for url in MH_DISTRICTS_URLS:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("features"):
                    return data
        except Exception:
            continue
    return None


def _get_name_from_feature(feature: dict) -> str:
    """Extract name from a GeoJSON feature, trying common property keys."""
    props = feature.get("properties", {})
    for key in ["dtname", "NAME_2", "DISTRICT", "district", "Name", "name", "ST_NM"]:
        val = props.get(key)
        if val:
            return str(val).strip().title()
    return ""


def _detect_field(geojson: dict, candidates: list[str]) -> str | None:
    """Return first property key found in the first feature of a GeoJSON."""
    features = geojson.get("features", [])
    if not features:
        return None
    props = features[0].get("properties", {})
    for k in candidates:
        if k in props:
            return k
    return None


def build_base_map(
    center: tuple[float, float] = (19.7515, 75.7139),
    zoom_start: int = 7,
) -> folium.Map:
    """Create a Folium map centred on Maharashtra."""
    return folium.Map(
        location=list(center),
        zoom_start=zoom_start,
        tiles="CartoDB positron",
        zoom_control=True,
        scrollWheelZoom=True,
        attributionControl=False,
    )


def add_india_layer(m: folium.Map, india_geojson: dict) -> folium.Map:
    """Overlay India state boundaries. Maharashtra highlighted in dark green."""
    def style_fn(feature):
        props = feature.get("properties", {})
        name  = ""
        for k in ["NAME_1", "ST_NM", "state", "State", "name"]:
            v = props.get(k, "")
            if v:
                name = str(v).lower()
                break
        is_mh = "maharashtra" in name
        return {
            "fillColor":   "#2d6a4f" if is_mh else "#f0e6d3",
            "color":       "#1a3d2e" if is_mh else "#ccc",
            "weight":       2 if is_mh else 0.6,
            "fillOpacity": 0.55 if is_mh else 0.65,
        }

    # Build tooltip kwargs only if a name field exists
    name_field = _detect_field(india_geojson, ["NAME_1", "ST_NM", "state", "State"])
    tooltip    = folium.GeoJsonTooltip([name_field], aliases=["State:"], sticky=False) \
                 if name_field else None

    folium.GeoJson(
        india_geojson,
        name="India States",
        style_function=style_fn,
        tooltip=tooltip,
    ).add_to(m)
    return m


def add_mh_district_layer(
    m: folium.Map,
    mh_geojson: dict,
    selected_district: str = "",
) -> folium.Map:
    """Overlay Maharashtra district polygons. Selected district highlighted in orange."""
    def style_fn(feature):
        name        = _get_name_from_feature(feature)
        is_selected = bool(selected_district and name.lower() == selected_district.lower())
        return {
            "fillColor":   "#f4a261" if is_selected else "#52b788",
            "color":       "#1a3d2e",
            "weight":       2 if is_selected else 0.8,
            "fillOpacity": 0.75 if is_selected else 0.2,
        }

    def highlight_fn(_feature):
        return {"fillColor": "#f4a261", "color": "#d4601a", "weight": 2, "fillOpacity": 0.6}

    dist_field = _detect_field(mh_geojson, ["dtname", "NAME_2", "DISTRICT", "district", "Name", "name"])
    tooltip    = folium.GeoJsonTooltip([dist_field], aliases=["District:"], sticky=False) \
                 if dist_field else None

    folium.GeoJson(
        mh_geojson,
        name="Maharashtra Districts",
        style_function=style_fn,
        highlight_function=highlight_fn,
        tooltip=tooltip,
    ).add_to(m)
    return m


def add_district_marker(
    m: folium.Map,
    district: str,
    crop: str,
    sowing_date: str = "",
) -> folium.Map:
    """Add a crop emoji marker at the district centroid."""
    coords = DISTRICT_CENTROIDS.get(district)
    if not coords:
        return m
    emoji = CROP_EMOJI.get(crop, DEFAULT_EMOJI)
    popup_html = (
        f'<div style="font-family:sans-serif;min-width:160px;padding:4px">'
        f'<b style="font-size:1.1rem">{emoji} {crop}</b><br>'
        f'&#128205; <b>{district}</b><br>'
        f'&#128197; Sowing: {sowing_date or "N/A"}'
        f'</div>'
    )
    folium.Marker(
        location=list(coords),
        popup=folium.Popup(popup_html, max_width=220),
        tooltip=f"{emoji} {district}",
        icon=folium.DivIcon(
            html=f'<div style="font-size:2rem;line-height:1;filter:drop-shadow(1px 1px 2px rgba(0,0,0,.35))">'
                 f'{emoji}</div>',
            icon_size=(40, 40),
            icon_anchor=(20, 20),
        ),
    ).add_to(m)
    return m


def add_mandi_markers(
    m: folium.Map,
    crop: str,
    selected_mandi: str = "",
) -> folium.Map:
    """Add mandi markers with price popups."""
    for mandi_name, data in MANDI_DATA.items():
        price       = data["prices"].get(crop, 0)
        is_selected = mandi_name == selected_mandi
        bg          = "#f4a261" if is_selected else "#2d6a4f"
        border      = "3px solid #d4601a" if is_selected else "2px solid #1a3d2e"

        popup_html = (
            f'<div style="font-family:sans-serif;min-width:180px;padding:6px">'
            f'<b>&#127978; {mandi_name} Mandi</b><br>'
            f'&#128205; {data["district"]} district<br>'
            f'<hr style="margin:4px 0">'
            f'<b style="color:#2d6a4f">&#8377; {price:,} / qtl</b>'
            f'<span style="color:#888;font-size:.85rem"> &mdash; {crop}</span>'
            f'</div>'
        )
        folium.Marker(
            location=[data["lat"], data["lon"]],
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"Mandi: {mandi_name}  Rs.{price:,}",
            icon=folium.DivIcon(
                html=(
                    f'<div style="background:{bg};border:{border};border-radius:50%;'
                    f'width:34px;height:34px;display:flex;align-items:center;'
                    f'justify-content:center;font-size:1.1rem;'
                    f'box-shadow:0 2px 6px rgba(0,0,0,.25);">&#127978;</div>'
                ),
                icon_size=(34, 34),
                icon_anchor=(17, 17),
            ),
        ).add_to(m)
    return m
