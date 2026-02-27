"""
modules/data_loader.py
Central data loader for AgriChain — ALL pages import from here.

Uses pathlib so the CSV loads correctly regardless of which directory
Streamlit is launched from or which page is currently active.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st

# ── Absolute path to the data directory ──────────────────────────────────────
# __file__ = e:/rippl_effect/modules/data_loader.py
# .parent   = e:/rippl_effect/modules/
# .parent.parent = e:/rippl_effect/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data"
CSV_PATH     = DATA_DIR / "mandi_prices.csv"


# ── Cached dataframe loader ───────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def load_price_df() -> pd.DataFrame:
    """
    Load the full mandi_prices.csv into a DataFrame.
    Cached for 1 hour so repeated page loads don't re-read the 21k-row file.
    Returns an empty DataFrame on error.
    """
    try:
        df = pd.read_csv(CSV_PATH)
        df.columns = [c.strip() for c in df.columns]
        df["Crop"]  = df["Crop"].str.strip()
        df["Mandi"] = df["Mandi"].str.strip()
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
        df.dropna(subset=["Price"], inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Data file not found: {CSV_PATH}")
        return pd.DataFrame(columns=["Crop", "Mandi", "Price", "Date"])
    except Exception as e:
        st.error(f"Failed to load price data: {e}")
        return pd.DataFrame(columns=["Crop", "Mandi", "Price", "Date"])


@st.cache_data(show_spinner=False, ttl=3600)
def get_all_crops() -> list[str]:
    """Sorted list of all crops in the CSV."""
    df = load_price_df()
    return sorted(df["Crop"].dropna().unique().tolist())


@st.cache_data(show_spinner=False, ttl=3600)
def get_mandis_for_crop(crop: str) -> list[str]:
    """Sorted list of mandis that have data for the given crop."""
    df = load_price_df()
    return sorted(df[df["Crop"] == crop]["Mandi"].dropna().unique().tolist())


@st.cache_data(show_spinner=False, ttl=3600)
def get_avg_price(crop: str, mandi: str, days: int = 30) -> float:
    """Average price for a crop at a mandi over the most recent N rows."""
    df = load_price_df()
    sub = df[(df["Crop"] == crop) & (df["Mandi"] == mandi)]["Price"]
    if sub.empty:
        return 0.0
    return round(float(sub.tail(days).mean()), 2)


@st.cache_data(show_spinner=False, ttl=3600)
def get_latest_price(crop: str, mandi: str) -> float:
    """Most recent price for a crop at a mandi."""
    df = load_price_df()
    sub = df[(df["Crop"] == crop) & (df["Mandi"] == mandi)]["Price"]
    if sub.empty:
        return 0.0
    return round(float(sub.iloc[-1]), 2)


@st.cache_data(show_spinner=False, ttl=3600)
def get_top_mandis_for_crop(crop: str, n: int = 10) -> pd.DataFrame:
    """
    Returns a DataFrame of the top N mandis by average price for a given crop.
    Columns: Mandi, AvgPrice, LatestPrice
    """
    df = load_price_df()
    sub = df[df["Crop"] == crop]
    if sub.empty:
        return pd.DataFrame(columns=["Mandi", "AvgPrice", "LatestPrice"])

    agg = (
        sub.groupby("Mandi")["Price"]
        .agg(AvgPrice="mean", LatestPrice="last")
        .reset_index()
        .sort_values("LatestPrice", ascending=False)
        .head(n)
    )
    agg["AvgPrice"]    = agg["AvgPrice"].round(0).astype(int)
    agg["LatestPrice"] = agg["LatestPrice"].round(0).astype(int)
    return agg.reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def build_mandi_price_dict(crop: str) -> dict[str, int]:
    """
    Build {mandi_name: avg_price} for all mandis that have `crop` data.
    Used by map + spoilage pages as a live replacement for hardcoded prices.
    """
    df = load_price_df()
    sub = df[df["Crop"] == crop]
    if sub.empty:
        return {}
    return (
        sub.groupby("Mandi")["Price"]
           .mean()
           .round(0)
           .astype(int)
           .to_dict()
    )


# ── Mandi → (lat, lon) geocoding ─────────────────────────────────────────────
# Covers every mandi that appears in the CSV (Maharashtra).
# Coordinates are approximate city-centre values.
MANDI_COORDINATES: dict[str, tuple[float, float]] = {
    # ── Ahmednagar district ──
    "Ahmednagar":              (19.0948, 74.7480),
    "Kopargaon":               (19.8826, 74.4774),
    "Pathardi":                (19.1588, 75.1834),
    "Rahuri":                  (19.3927, 74.6483),
    "Rahata":                  (19.7137, 74.4784),
    "Sangamner":               (19.5669, 74.2132),
    "Shrirampur":              (19.6186, 74.6581),
    "Shrigonda":               (18.6154, 74.6976),
    # ── Nashik district ──
    "Lasalgaon(Niphad)":       (20.1457, 74.2282),
    "Lasalgaon(Vinchur)":      (20.1457, 74.2282),
    "Malegaon":                (20.5505, 74.5255),
    "Manmad":                  (20.2518, 74.4378),
    "Nandgaon":                (20.3069, 74.6567),
    "Nashik":                  (20.0113, 73.7903),
    "Pimpalgaon":              (20.1629, 73.8990),
    "Pimpalgaon Baswant(Saykheda)": (20.1629, 73.8990),
    "Satana":                  (20.5933, 74.2165),
    "Yeola":                   (20.0404, 74.4847),
    "Dindori":                 (20.2090, 73.8447),
    "Niphad":                  (20.0820, 74.1096),
    "Sinner":                  (19.8469, 73.9950),
    "Kalwan":                  (20.4927, 73.6965),
    "Chandwad":                (20.3210, 74.2428),
    # ── Pune district ──
    "Pune":                    (18.5204, 73.8567),
    "Pune(Pimpri)":            (18.6298, 73.7997),
    "Khed(Chakan)":            (18.7608, 73.8636),
    "Phaltan":                 (17.9828, 74.4345),
    "Baramati":                (18.1515, 74.5771),
    "Junnar":                  (19.2055, 73.8767),
    "Manchar":                 (19.0061, 73.9450),
    # ── Kolhapur district ──
    "Kolhapur":                (16.6910, 74.2430),
    # ── Sangli district ──
    "Sangli":                  (16.8524, 74.5815),
    "Vai":                     (17.0610, 73.9600),
    # ── Satara district ──
    "Satara":                  (17.6805, 74.0183),
    "Karad":                   (17.2862, 74.1832),
    "Patan":                   (17.3700, 73.8990),
    "Wai":                     (17.9521, 73.8914),
    # ── Solapur district ──
    "Solapur":                 (17.6599, 75.9064),
    "Pandharpur":              (17.6776, 75.3282),
    "Karmala":                 (18.4040, 75.1940),
    # ── Nanded district ──
    "Nanded":                  (19.1609, 77.3212),
    # ── Latur district ──
    "Latur":                   (18.4088, 76.5604),
    # ── Beed / Kille Dharur ──
    "Kille Dharur":            (18.0500, 76.5667),
    # ── Jalgaon district ──
    "Jalgaon":                 (21.0077, 75.5626),
    "Yawal":                   (21.1686, 75.6939),
    "Chopda":                  (21.2452, 75.2958),
    # ── Nagpur district ──
    "Nagpur":                  (21.1458, 79.0882),
    # ── Aurangabad / Chhatrapati Sambhajinagar ──
    "Aurangabad":              (19.8762, 75.3433),
    "Sillod":                  (20.2974, 75.6552),
    # ── Osmanabad / Dharashiv ──
    "Osmanabad":               (18.1863, 76.0356),
    # ── Palghar district ──
    "Palghar":                 (19.6969, 72.7650),
    "Vasai":                   (19.3919, 72.8397),
    # ── Thane district ──
    "Ulhasnagar":              (19.2183, 73.1558),
    "Panvel":                  (18.9894, 73.1175),
    "Vashi New Mumbai":        (19.0770, 72.9988),
    "Kalyan":                  (19.2437, 73.1355),
    # ── Raigad district ──
    "Pen":                     (18.7370, 73.0962),
    "Alibag":                  (18.6487, 72.8748),
    # ── Ratnagiri district ──
    "Ratnagiri":               (16.9902, 73.3120),
    # ── Dhule district ──
    "Dhule":                   (20.9042, 74.7749),
    # ── Amravati district ──
    "Amravati":                (20.9374, 77.7796),
    # ── Akola district ──
    "Akola":                   (20.7070, 77.0082),
    # ── Buldhana district ──
    "Buldhana":                (20.5292, 76.1842),
    # ── Parbhani district ──
    "Parbhani":                (19.2709, 76.7749),
    # ── Hingoli district ──
    "Hingoli":                 (19.7157, 77.1497),
    # ── Washim district ──
    "Washim":                  (20.1121, 77.1464),
    # ── Yavatmal district ──
    "Yavatmal":                (20.3888, 78.1204),
    # ── Wardha district ──
    "Wardha":                  (20.7453, 78.6022),
    # ── Chandrapur district ──
    "Chandrapur":              (19.9615, 79.2961),
    # ── Nandurbar district ──
    "Nandurbar":               (21.3690, 74.2429),
    # ── Misc ──
    "Pratap Nana Mahale Khajgi Bajar Samiti": (20.0113, 73.7903),  # Nashik area
}

# Maharashtra centre fallback
_MH_CENTER = (19.6633, 75.3003)


def get_mandi_coords(mandi: str) -> tuple[float, float]:
    """Return (lat, lon) for a mandi name. Falls back to Maharashtra centre."""
    return MANDI_COORDINATES.get(mandi, _MH_CENTER)
