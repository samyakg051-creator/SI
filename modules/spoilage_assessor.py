"""
modules/spoilage_assessor.py — Post-harvest spoilage risk assessment.
"""
from __future__ import annotations
import requests
import datetime
from utils.geo import DISTRICT_COORDS

STORAGE_PENALTY = {
    "Cold Storage": 0.05,
    "Warehouse": 0.15,
    "Covered Shed": 0.30,
    "Open Yard": 0.50,
    "None": 0.65,
}

# Crop perishability (higher = more perishable)
_CROP_PERISH = {
    "Tomato": 0.9, "Potato": 0.3, "Onion": 0.35,
    "Wheat": 0.1, "Corn": 0.15, "Soybean": 0.12, "Cotton": 0.08,
}


def _fetch_weather_3d(lat: float, lon: float) -> dict:
    """Fetch 3-day weather for spoilage analysis."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,"
        f"relative_humidity_2m_max,precipitation_sum"
        f"&timezone=Asia/Kolkata&forecast_days=3"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("daily", {})
    except Exception:
        return {
            "temperature_2m_max": [34, 33, 35],
            "temperature_2m_min": [24, 23, 25],
            "relative_humidity_2m_max": [70, 72, 68],
            "precipitation_sum": [2, 5, 0],
        }


def assess_spoilage(
    crop: str,
    district: str,
    quantity: float,
    storage_type: str,
    transit_hours: int,
) -> dict:
    """
    Assess post-harvest spoilage risk.
    Returns dict with risk_level, spoilage_probability, score, actions, etc.
    """
    coords = DISTRICT_COORDS.get(district, (19.75, 75.71))
    wx = _fetch_weather_3d(coords[0], coords[1])

    temps = wx.get("temperature_2m_max", [33, 33, 33])
    humidity = wx.get("relative_humidity_2m_max", [70, 70, 70])
    rain = wx.get("precipitation_sum", [0, 0, 0])

    avg_temp = sum(temps) / len(temps)
    avg_hum = sum(humidity) / len(humidity)
    total_rain = sum(rain)

    # Base perishability
    perish = _CROP_PERISH.get(crop, 0.3)

    # Storage factor
    storage_factor = STORAGE_PENALTY.get(storage_type, 0.30)

    # Transit factor (higher = worse)
    transit_factor = min(1.0, transit_hours / 48.0)

    # Weather factor
    weather_factor = 0.0
    if avg_temp > 38: weather_factor += 0.30
    elif avg_temp > 33: weather_factor += 0.15
    elif avg_temp > 28: weather_factor += 0.05
    if avg_hum > 85: weather_factor += 0.25
    elif avg_hum > 75: weather_factor += 0.10
    if total_rain > 20: weather_factor += 0.20
    elif total_rain > 5: weather_factor += 0.08

    # Final score (0..1, higher = more risky)
    score = (perish * 0.30 + storage_factor * 0.25 + transit_factor * 0.20 + weather_factor * 0.25)
    score = max(0, min(1, score))

    # Risk level
    if score >= 0.55:
        risk_level = "HIGH"
        risk_color = "🔴"
        prob = f"{int(score * 100)}%"
    elif score >= 0.35:
        risk_level = "MEDIUM"
        risk_color = "🟡"
        prob = f"{int(score * 100)}%"
    else:
        risk_level = "LOW"
        risk_color = "🟢"
        prob = f"{int(score * 100)}%"

    # Reason
    parts = []
    if perish > 0.5: parts.append(f"{crop} is highly perishable")
    if storage_factor > 0.3: parts.append(f"storage type ({storage_type}) offers limited protection")
    if transit_hours > 12: parts.append(f"long transit ({transit_hours}h) increases exposure")
    if avg_temp > 35: parts.append(f"high temperatures ({avg_temp:.0f}°C) accelerate spoilage")
    if avg_hum > 80: parts.append(f"high humidity ({avg_hum:.0f}%) promotes fungal growth")
    reason = "; ".join(parts) if parts else "Conditions are relatively favorable for storage"

    # Actions
    actions = _get_actions(crop, score, storage_type, transit_hours, avg_temp)

    return {
        "risk_level": risk_level,
        "risk_color": risk_color,
        "spoilage_probability": prob,
        "score": score,
        "reason": reason,
        "weather_summary": {
            "avg_temp": avg_temp,
            "avg_humidity": avg_hum,
            "total_rain": total_rain,
        },
        "actions": actions,
    }


def _get_actions(crop, score, storage, transit, temp):
    """Generate ranked preservation actions."""
    actions = []

    if score > 0.4:
        actions.append({
            "action": "Move to cold storage immediately to slow microbial growth",
            "cost": "₹200–400/qtl", "effectiveness": "High",
        })
    if transit > 8:
        actions.append({
            "action": f"Reduce transit time (currently {transit}h) — send to the nearest mandi instead",
            "cost": "Variable", "effectiveness": "High",
        })
    if temp > 33:
        actions.append({
            "action": "Cover produce with wet jute bags during transport to reduce heat damage",
            "cost": "₹20–50/qtl", "effectiveness": "Medium",
        })
    if storage in ("Open Yard", "None"):
        actions.append({
            "action": "Upgrade to at least a covered shed — open storage doubles spoilage rate",
            "cost": "₹100–200/qtl", "effectiveness": "High",
        })
    if crop in ("Tomato", "Potato", "Onion"):
        actions.append({
            "action": f"Sort and remove damaged {crop.lower()} before storage — one bad piece spoils the lot",
            "cost": "₹10–20/qtl (labor)", "effectiveness": "Medium",
        })

    actions.append({
        "action": "Sell within 24–48 hours if cold storage is not available",
        "cost": "Free", "effectiveness": "High" if score > 0.5 else "Medium",
    })

    return actions[:5]
