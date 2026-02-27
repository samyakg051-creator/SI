"""
AgriChain – modules/weather.py
Fetches detailed 5-day forecast + current conditions + AQI from Open-Meteo.
"""

import requests
from dataclasses import dataclass, field
from datetime import datetime


# ── Constants ─────────────────────────────────────────────────────────────────
FORECAST_URL     = "https://api.open-meteo.com/v1/forecast"
AQI_URL          = "https://air-quality-api.open-meteo.com/v1/air-quality"
FORECAST_DAYS    = 5
TEMP_THRESHOLD   = 35.0   # °C
RAIN_THRESHOLD   = 60.0   # %
PENALTY_HOT      = 3
PENALTY_RAIN     = 3
MAX_SCORE        = 30


# ── Data classes ──────────────────────────────────────────────────────────────
@dataclass
class DayForecast:
    date:          str
    temp_max:      float
    temp_min:      float
    precip_prob:   float   # %
    wind_max:      float   # km/h
    humidity_mean: float   # %
    uv_index:      float
    condition:     str     # emoji label


@dataclass
class WeatherResult:
    weather_score:    float
    hot_days_count:   int
    rainy_days_count: int
    # Current / today
    current_temp:     float = 0.0
    current_humidity: float = 0.0
    current_wind:     float = 0.0       # km/h
    current_precip:   float = 0.0       # mm
    current_uv:       float = 0.0
    # AQI
    aqi:              int   = 0
    aqi_label:        str   = "Unknown"
    pm25:             float = 0.0
    pm10:             float = 0.0
    # Daily breakdown
    days:             list[DayForecast] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _condition_emoji(temp: float, precip: float, uv: float) -> str:
    if precip > 70: return "🌧️ Heavy Rain"
    if precip > 40: return "🌦️ Light Rain"
    if temp > 38:   return "🔥 Scorching"
    if temp > 33:   return "☀️ Hot"
    if temp > 25:   return "🌤️ Warm"
    if temp > 18:   return "⛅ Mild"
    return "🌬️ Cool"

def _aqi_label(aqi: int) -> str:
    if aqi <= 50:  return "Good"
    if aqi <= 100: return "Moderate"
    if aqi <= 150: return "Unhealthy (Sensitive)"
    if aqi <= 200: return "Unhealthy"
    if aqi <= 300: return "Very Unhealthy"
    return "Hazardous"


# ── API calls ─────────────────────────────────────────────────────────────────
def _fetch_forecast(lat: float, lon: float) -> dict:
    params = {
        "latitude":    lat,
        "longitude":   lon,
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "windspeed_10m_max",
            "relative_humidity_2m_mean",
            "uv_index_max",
        ]),
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "windspeed_10m",
            "precipitation",
            "uv_index",
        ]),
        "forecast_days": FORECAST_DAYS,
        "timezone":    "auto",
        "wind_speed_unit": "kmh",
    }
    r = requests.get(FORECAST_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def _fetch_aqi(lat: float, lon: float) -> dict | None:
    try:
        params = {
            "latitude":  lat,
            "longitude": lon,
            "current":   "us_aqi,pm2_5,pm10",
            "timezone":  "auto",
        }
        r = requests.get(AQI_URL, params=params, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# ── Main function ─────────────────────────────────────────────────────────────
def get_weather_score(latitude: float, longitude: float) -> WeatherResult:
    """
    Fetch detailed 5-day weather forecast + AQI and compute harvest-readiness score.
    Returns WeatherResult with daily breakdown, current conditions, and AQI.
    """
    raw = _fetch_forecast(latitude, longitude)
    daily   = raw.get("daily", {})
    current = raw.get("current", {})

    dates        = daily.get("time", [])
    temp_max     = daily.get("temperature_2m_max", [])
    temp_min     = daily.get("temperature_2m_min", [])
    precip       = daily.get("precipitation_probability_max", [])
    wind         = daily.get("windspeed_10m_max", [])
    humidity     = daily.get("relative_humidity_2m_mean", [])
    uv           = daily.get("uv_index_max", [])

    # Score calculation
    score      = float(MAX_SCORE)
    hot_days   = 0
    rainy_days = 0
    day_list: list[DayForecast] = []

    for i in range(len(dates)):
        t  = temp_max[i] if i < len(temp_max)  and temp_max[i]  is not None else 0.0
        tm = temp_min[i] if i < len(temp_min)  and temp_min[i]  is not None else 0.0
        p  = precip[i]   if i < len(precip)    and precip[i]    is not None else 0.0
        w  = wind[i]     if i < len(wind)       and wind[i]      is not None else 0.0
        h  = humidity[i] if i < len(humidity)   and humidity[i]  is not None else 0.0
        u  = uv[i]       if i < len(uv)         and uv[i]        is not None else 0.0
        d  = dates[i]    if i < len(dates) else ""

        if t > TEMP_THRESHOLD:
            score -= PENALTY_HOT; hot_days += 1
        if p > RAIN_THRESHOLD:
            score -= PENALTY_RAIN; rainy_days += 1

        # Format date nicely
        try:
            d_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%a, %b %d")
        except Exception:
            d_fmt = d

        day_list.append(DayForecast(
            date=d_fmt, temp_max=round(t,1), temp_min=round(tm,1),
            precip_prob=round(p,1), wind_max=round(w,1),
            humidity_mean=round(h,1), uv_index=round(u,1),
            condition=_condition_emoji(t, p, u),
        ))

    final_score = round(min(max(score, 0.0), float(MAX_SCORE)), 4)

    # Current conditions
    c_temp  = current.get("temperature_2m", 0.0) or 0.0
    c_hum   = current.get("relative_humidity_2m", 0.0) or 0.0
    c_wind  = current.get("windspeed_10m", 0.0) or 0.0
    c_prec  = current.get("precipitation", 0.0) or 0.0
    c_uv    = current.get("uv_index", 0.0) or 0.0

    # AQI
    aqi_val, aqi_lbl, pm25_val, pm10_val = 0, "Unknown", 0.0, 0.0
    aqi_data = _fetch_aqi(latitude, longitude)
    if aqi_data:
        aqi_cur  = aqi_data.get("current", {})
        aqi_val  = int(aqi_cur.get("us_aqi", 0) or 0)
        pm25_val = float(aqi_cur.get("pm2_5", 0.0) or 0.0)
        pm10_val = float(aqi_cur.get("pm10",  0.0) or 0.0)
        aqi_lbl  = _aqi_label(aqi_val)

    return WeatherResult(
        weather_score=final_score,
        hot_days_count=hot_days,
        rainy_days_count=rainy_days,
        current_temp=round(c_temp, 1),
        current_humidity=round(c_hum, 1),
        current_wind=round(c_wind, 1),
        current_precip=round(c_prec, 1),
        current_uv=round(c_uv, 1),
        aqi=aqi_val,
        aqi_label=aqi_lbl,
        pm25=round(pm25_val, 1),
        pm10=round(pm10_val, 1),
        days=day_list,
    )


if __name__ == "__main__":
    result = get_weather_score(latitude=16.8524, longitude=74.5815)  # Sangli
    print(result)
