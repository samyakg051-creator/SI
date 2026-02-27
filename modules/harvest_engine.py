"""
modules/harvest_engine.py — Harvest window recommendation engine.
Uses weather data + price trends to recommend optimal harvest timing.
"""
from __future__ import annotations
import datetime
import requests
from utils.geo import DISTRICT_COORDS

CROP_MATURITY_DAYS = {
    "Wheat": 120, "Tomato": 75, "Onion": 90,
    "Potato": 90, "Corn": 100, "Soybean": 100, "Cotton": 180,
}

# Seasonal price index per month (1=Jan..12=Dec) — rough multiplier
_SEASONAL = {
    "Wheat":   {1: 1.0, 2: 1.05, 3: 1.10, 4: 1.15, 5: 1.02, 6: 0.95, 7: 0.90, 8: 0.88, 9: 0.92, 10: 0.95, 11: 0.98, 12: 1.0},
    "Tomato":  {1: 1.15, 2: 1.20, 3: 1.10, 4: 0.90, 5: 0.80, 6: 0.75, 7: 0.85, 8: 0.90, 9: 1.0, 10: 1.05, 11: 1.10, 12: 1.12},
    "Onion":   {1: 0.85, 2: 0.80, 3: 0.75, 4: 0.80, 5: 0.95, 6: 1.05, 7: 1.15, 8: 1.20, 9: 1.18, 10: 1.10, 11: 1.0, 12: 0.90},
    "Potato":  {1: 0.95, 2: 0.90, 3: 0.88, 4: 0.92, 5: 1.0, 6: 1.05, 7: 1.10, 8: 1.12, 9: 1.08, 10: 1.0, 11: 0.95, 12: 0.93},
    "Corn":    {1: 1.0, 2: 1.02, 3: 1.05, 4: 1.08, 5: 0.98, 6: 0.92, 7: 0.90, 8: 0.95, 9: 1.0, 10: 1.05, 11: 1.08, 12: 1.02},
    "Soybean": {1: 1.02, 2: 1.05, 3: 1.08, 4: 1.04, 5: 0.95, 6: 0.90, 7: 0.92, 8: 0.98, 9: 1.05, 10: 1.10, 11: 1.08, 12: 1.04},
    "Cotton":  {1: 0.95, 2: 0.92, 3: 0.90, 4: 0.88, 5: 0.92, 6: 0.98, 7: 1.05, 8: 1.10, 9: 1.15, 10: 1.12, 11: 1.08, 12: 1.0},
}


def _fetch_weather_14d(lat: float, lon: float) -> dict:
    """Fetch 14-day weather forecast from Open-Meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        f"relative_humidity_2m_max,windspeed_10m_max"
        f"&timezone=Asia/Kolkata&forecast_days=14"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json().get("daily", {})
        return data
    except Exception:
        # Return synthetic data if API fails
        today = datetime.date.today()
        return {
            "time": [(today + datetime.timedelta(days=i)).isoformat() for i in range(14)],
            "temperature_2m_max": [32 + (i % 3) for i in range(14)],
            "temperature_2m_min": [22 + (i % 3) for i in range(14)],
            "precipitation_sum": [max(0, 5 - i) for i in range(14)],
            "relative_humidity_2m_max": [65 + (i % 10) for i in range(14)],
            "windspeed_10m_max": [12 + (i % 5) for i in range(14)],
        }


def _weather_score(wx: dict) -> float:
    """0..1 weather suitability score (higher = better harvesting weather)."""
    temps = wx.get("temperature_2m_max", [30]*7)[:7]
    rain = wx.get("precipitation_sum", [0]*7)[:7]
    humidity = wx.get("relative_humidity_2m_max", [60]*7)[:7]

    avg_temp = sum(temps) / len(temps) if temps else 30
    total_rain = sum(rain) if rain else 0
    avg_hum = sum(humidity) / len(humidity) if humidity else 60

    score = 1.0
    if avg_temp > 40: score -= 0.25
    elif avg_temp > 36: score -= 0.10
    if avg_temp < 15: score -= 0.15
    if total_rain > 50: score -= 0.35
    elif total_rain > 20: score -= 0.20
    elif total_rain > 5: score -= 0.10
    if avg_hum > 85: score -= 0.15
    elif avg_hum > 75: score -= 0.05

    return max(0.1, min(1.0, score))


def _price_seasonality_score(crop: str, harvest_date: datetime.date) -> float:
    """0..1 based on seasonal price multiplier for the harvest month."""
    month_idx = harvest_date.month
    seasonal = _SEASONAL.get(crop, {})
    mult = seasonal.get(month_idx, 1.0)
    # Normalize: 0.75 -> 0, 1.20 -> 1
    return max(0.0, min(1.0, (mult - 0.75) / 0.45))


def _soil_readiness_score(
    crop: str,
    sowing_date: datetime.date,
    harvest_date: datetime.date,
) -> float:
    """0..1 based on whether the crop has had enough growing days."""
    maturity = CROP_MATURITY_DAYS.get(crop, 100)
    actual_days = (harvest_date - sowing_date).days
    ratio = actual_days / maturity
    if ratio < 0.8:
        return max(0.2, ratio)
    elif ratio > 1.3:
        return max(0.4, 1.3 - (ratio - 1.3))
    else:
        return min(1.0, 0.5 + ratio * 0.4)


def get_harvest_recommendation(
    crop: str,
    district: str,
    sowing_date: datetime.date,
) -> dict:
    """
    Returns a comprehensive harvest recommendation dict.
    """
    maturity = CROP_MATURITY_DAYS.get(crop, 100)
    ideal_harvest = sowing_date + datetime.timedelta(days=maturity)
    today = datetime.date.today()

    # Best window is centered around ideal_harvest or today+3, whichever is later
    window_start = max(today + datetime.timedelta(days=2), ideal_harvest - datetime.timedelta(days=2))
    window_end = window_start + datetime.timedelta(days=5)

    coords = DISTRICT_COORDS.get(district, (19.75, 75.71))
    wx = _fetch_weather_14d(coords[0], coords[1])

    ws = _weather_score(wx)
    ps = _price_seasonality_score(crop, window_start)
    sr = _soil_readiness_score(crop, sowing_date, window_start)

    final_score = ws * 0.35 + ps * 0.35 + sr * 0.30

    # Confidence
    if final_score >= 0.7:
        confidence = "High"
    elif final_score >= 0.45:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Expected price premium
    seasonal = _SEASONAL.get(crop, {})
    mult = seasonal.get(window_start.month, 1.0)
    premium = f"{int((mult - 1) * 100):+d}%" if mult != 1.0 else "+0%"

    # Reasons
    reasons = []
    if ws > 0.7:
        reasons.append(f"Weather is favorable — low rainfall expected, moderate temperatures around {sum(wx.get('temperature_2m_max',[30]*7)[:7])//7}°C")
    elif ws > 0.4:
        reasons.append("Weather is acceptable but watch for rain; consider covering produce during transit")
    else:
        reasons.append("Poor weather expected — consider delaying harvest if storage allows")

    if ps > 0.6:
        reasons.append(f"Seasonal prices for {crop} are historically strong in {window_start.strftime('%B')}")
    elif ps > 0.3:
        reasons.append(f"Prices for {crop} are moderate this month — not the peak season")
    else:
        reasons.append(f"Prices tend to be lower in {window_start.strftime('%B')} — consider cold storage if possible")

    if sr > 0.7:
        reasons.append("Crop has had sufficient growing time — maturity indicators are positive")
    elif sr > 0.4:
        reasons.append("Crop is approaching maturity — a few more days could improve quality")
    else:
        reasons.append("Crop may not have reached full maturity — early harvest may reduce yield")

    # Chart data — 14-day synthetic price trend
    import random
    random.seed(hash(f"{crop}{district}"))
    base_price = {"Wheat": 2300, "Tomato": 1500, "Onion": 1800, "Potato": 1200, "Corn": 1700, "Soybean": 4200, "Cotton": 6500}.get(crop, 2000)
    chart_data = []
    for i in range(14):
        dt = today + datetime.timedelta(days=i)
        noise = random.uniform(-80, 80)
        seasonal_adj = seasonal.get(dt.month, 1.0)
        chart_data.append({
            "Date": dt.isoformat(),
            "Price (₹/qtl)": round(base_price * seasonal_adj + noise),
        })

    return {
        "recommended_window": {
            "start": window_start.strftime("%d %b %Y"),
            "end": window_end.strftime("%d %b %Y"),
        },
        "score": round(final_score, 3),
        "score_components": {
            "weather": round(ws, 3),
            "price_seasonality": round(ps, 3),
            "soil_readiness": round(sr, 3),
        },
        "confidence": confidence,
        "expected_price_premium": premium,
        "reasons": reasons,
        "chart_data": chart_data,
        "weather": wx,
    }
