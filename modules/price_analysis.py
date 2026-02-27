"""
AgriChain – modules/price_analysis.py
Loads mandi price CSV data and computes price trend score.
"""

import pandas as pd
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
@dataclass
class PriceAnalysisResult:
    last_7_avg:    float   # Average price over the last 7 days of available data
    last_30_avg:   float   # Average price over the last 30 days of available data
    trend_percent: float   # % change: (last_7_avg - last_30_avg) / last_30_avg * 100
    price_score:   float   # 0–30 score derived from trend

# ---------------------------------------------------------------------------
_CSV_PATH = Path(__file__).parent.parent / "data" / "mandi_prices.csv"

# ---------------------------------------------------------------------------
def _load_data() -> pd.DataFrame:
    """Load and parse the mandi prices CSV."""
    df = pd.read_csv(_CSV_PATH)
    df["Crop"]  = df["Crop"].str.strip()
    df["Mandi"] = df["Mandi"].str.strip()
    df["Date"]  = pd.to_datetime(df["Date"], dayfirst=True)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df.dropna(subset=["Price", "Date"])
    return df


def filter_by_crop_mandi(df: pd.DataFrame, crop: str, mandi: str) -> pd.DataFrame:
    """Filter dataframe by crop and mandi (case-insensitive)."""
    mask = (
        df["Crop"].str.strip().str.lower() == crop.strip().lower()
    ) & (
        df["Mandi"].str.strip().str.lower() == mandi.strip().lower()
    )
    filtered = df[mask].copy()
    if filtered.empty:
        raise ValueError(
            f"No data found for Crop='{crop}' and Mandi='{mandi}'"
        )
    return filtered


def _compute_price_score(trend_percent: float) -> float:
    """
    Convert a price trend percentage into a score out of 30.

    Scoring logic
    -------------
    trend >= +10%  → 30   (strong upward momentum)
    trend >= +5%   → 25
    trend >= 0%    → 20   (stable / slight upward)
    trend >= -5%   → 15
    trend >= -10%  → 10
    trend < -10%   →  5   (significant downward trend)
    """
    if trend_percent >= 10:
        return 30.0
    elif trend_percent >= 5:
        return 25.0
    elif trend_percent >= 0:
        return 20.0
    elif trend_percent >= -5:
        return 15.0
    elif trend_percent >= -10:
        return 10.0
    else:
        return 5.0

# ---------------------------------------------------------------------------
def analyse_prices(crop: str, mandi: str) -> PriceAnalysisResult:
    """
    Analyse price trends for a given crop and mandi.

    Parameters
    ----------
    crop  : str – crop name (e.g. 'Wheat')
    mandi : str – mandi name (e.g. 'Sangli')

    Returns
    -------
    PriceAnalysisResult with last_7_avg, last_30_avg, trend_percent, price_score.

    Raises
    ------
    ValueError – if no data exists for the given crop/mandi combination.
    FileNotFoundError – if the CSV file is missing.
    """
    df       = _load_data()
    filtered = filter_by_crop_mandi(df, crop, mandi)

    # Sort chronologically and use all available data
    filtered  = filtered.sort_values("Date")
    prices    = filtered["Price"].tolist()

    # Use last 7 records as proxy for "last 7 days" and all as "last 30 days"
    last_7    = prices[-7:]  if len(prices) >= 7  else prices
    last_30   = prices[-30:] if len(prices) >= 30 else prices

    last_7_avg  = round(sum(last_7)  / len(last_7),  2)
    last_30_avg = round(sum(last_30) / len(last_30), 2)

    if last_30_avg == 0:
        trend_percent = 0.0
    else:
        trend_percent = round(((last_7_avg - last_30_avg) / last_30_avg) * 100, 2)

    price_score = _compute_price_score(trend_percent)

    return PriceAnalysisResult(
        last_7_avg=last_7_avg,
        last_30_avg=last_30_avg,
        trend_percent=trend_percent,
        price_score=price_score,
    )

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = analyse_prices(crop="Wheat", mandi="Sangli")
    print(result)
