"""
AgriChain – modules/explanation.py
Generates farmer-friendly harvest readiness explanations + harvest window advice.
"""


# ---------------------------------------------------------------------------
def _price_explanation(trend_percent: float) -> str:
    if trend_percent >= 10:
        return (
            "📈 Great news! Prices have gone UP strongly "
            f"({'+' if trend_percent >= 0 else ''}{trend_percent:.1f}%). "
            "This is a very good time to sell your produce."
        )
    elif trend_percent >= 5:
        return (
            "📈 Prices are going UP "
            f"({'+' if trend_percent >= 0 else ''}{trend_percent:.1f}%). "
            "Market conditions look good for selling."
        )
    elif trend_percent >= 0:
        return (
            "📊 Prices are steady or slightly up "
            f"({'+' if trend_percent >= 0 else ''}{trend_percent:.1f}%). "
            "You can sell now or wait a few days."
        )
    elif trend_percent >= -5:
        return (
            f"📉 Prices have dropped a little ({trend_percent:.1f}%). "
            "If you have good storage, you may want to wait for prices to recover."
        )
    else:
        return (
            f"📉 Prices have dropped significantly ({trend_percent:.1f}%). "
            "If your produce can be stored safely, consider waiting. "
            "But if it may spoil, it is better to sell now at a lower price than to lose it."
        )


def _weather_explanation(hot_days: int, rainy_days: int) -> str:
    parts = []

    if hot_days == 0 and rainy_days == 0:
        parts.append(
            "☀️ Weather looks clear for the next 5 days — "
            "good conditions for harvesting and transporting your crop to the mandi."
        )
    else:
        if hot_days > 0:
            parts.append(
                f"🔥 {hot_days} day(s) of extreme heat (above 35°C) ahead. "
                "Your crop may spoil faster in the heat. "
                "Try to transport early morning or late evening."
            )
        if rainy_days > 0:
            parts.append(
                f"🌧️ {rainy_days} day(s) of heavy rain expected. "
                "Roads may be difficult and produce can get damaged. "
                "If possible, avoid transport on rainy days."
            )
    return " ".join(parts)


def _storage_explanation(storage_type: str) -> str:
    key = storage_type.lower().strip()
    explanations = {
        "cold_storage": (
            "❄️ You have cold storage — excellent! "
            "Your produce will stay fresh for a long time. "
            "You can wait for better prices without worrying about spoilage."
        ),
        "warehouse": (
            "🏗️ Warehouse storage is good — it protects from rain and sun. "
            "Your produce should be safe for several days. "
            "You have some time to find the best market price."
        ),
        "covered_shed": (
            "🏚️ A covered shed gives basic protection from rain. "
            "But your produce may still lose quality in a few days. "
            "Try to sell within 3-5 days."
        ),
        "open_yard": (
            "🌿 Your produce is in the open — it is exposed to sun, rain and pests. "
            "Spoilage risk is HIGH. Try to sell as soon as possible — "
            "ideally within 1-2 days."
        ),
        "none": (
            "🚫 No storage means your produce is at very high risk. "
            "Sell immediately, even at a lower price. "
            "It is better to sell cheap than to lose everything."
        ),
    }
    return explanations.get(key, f"Storage: {storage_type}. Take care to protect your produce.")


def _transport_explanation(distance_km: float) -> str:
    if distance_km < 50:
        return (
            f"🚛 The mandi is only {distance_km:.0f} km away — very close! "
            "Transport will be quick and cheap."
        )
    elif distance_km <= 150:
        return (
            f"🚛 The mandi is {distance_km:.0f} km away — a moderate distance. "
            "Plan your journey early to avoid delays and extra fuel costs."
        )
    elif distance_km <= 300:
        return (
            f"🚛 The mandi is {distance_km:.0f} km away — quite far. "
            "Consider if the higher price at this mandi is worth the extra transport cost. "
            "Check if a closer mandi offers a reasonable price."
        )
    else:
        return (
            f"🚛 The mandi is {distance_km:.0f} km away — very far. "
            "Transport will be expensive and your produce may spoil on the way. "
            "Strongly consider selling at a nearer mandi."
        )


# ---------------------------------------------------------------------------
def generate_harvest_window(
    price_trend: float,
    hot_days: int,
    rainy_days: int,
    storage_type: str,
) -> tuple[str, str, str]:
    """
    Returns (window_text, urgency_level, urgency_color).
    urgency_level: "Sell Now", "Sell in 1-2 Days", "Sell This Week", "Can Wait"
    """
    storage_days = {
        "cold_storage": 30, "warehouse": 14, "covered_shed": 5,
        "open_yard": 2, "none": 1,
    }
    max_wait = storage_days.get(storage_type.lower().strip(), 3)

    # Find first clear day (no rain, no extreme heat)
    clear_in = 0
    if rainy_days > 0 or hot_days > 0:
        clear_in = min(rainy_days + hot_days, 3)

    # Price going up → can wait if storage allows
    if price_trend >= 5 and max_wait >= 7:
        return (
            f"✅ Prices are rising and your storage is good. "
            f"You can wait up to {max_wait} days for even better prices. "
            f"Best window: next {min(max_wait, 7)} days.",
            "Can Wait", "#4caf50"
        )
    elif price_trend >= 0 and max_wait >= 3:
        if rainy_days > 0:
            return (
                f"☁️ Prices are stable but rain is expected. "
                f"Wait for clear weather (1-2 days), then sell. "
                f"Your storage can hold for {max_wait} days.",
                "Sell This Week", "#ffc107"
            )
        return (
            f"📊 Good conditions. Sell within the next 3-5 days "
            f"while prices are stable and weather is clear.",
            "Sell This Week", "#4caf50"
        )
    elif max_wait <= 2:
        return (
            f"⚠️ Your storage is limited — produce will last only {max_wait} day(s). "
            f"Sell TODAY or TOMORROW to avoid losses.",
            "Sell Now", "#f44336"
        )
    elif price_trend < -5:
        if max_wait >= 7:
            return (
                f"📉 Prices are dropping but your storage is good. "
                f"You can wait up to {max_wait} days for prices to recover.",
                "Can Wait", "#ffc107"
            )
        return (
            f"📉 Prices are dropping and storage is limited. "
            f"Sell within {min(max_wait, 3)} days before prices fall more.",
            "Sell in 1-2 Days", "#ff9800"
        )
    else:
        return (
            f"📋 Conditions are mixed. Sell within {min(max_wait, 5)} days. "
            f"Keep checking mandi prices daily.",
            "Sell This Week", "#ffc107"
        )


# ---------------------------------------------------------------------------
def generate_farmer_summary(
    crop: str,
    mandi: str,
    final_score: float,
    traffic_light: str,
    price_trend: float,
    hot_days: int,
    rainy_days: int,
    storage_type: str,
    distance_km: float,
) -> str:
    """One-paragraph plain language summary for the farmer."""
    # Simple verdict
    if traffic_light == "Green":
        verdict = f"It is a GOOD TIME to sell your {crop} at {mandi} mandi"
    elif traffic_light == "Yellow":
        verdict = f"Conditions for selling {crop} at {mandi} are OKAY but not perfect"
    else:
        verdict = f"It is NOT the best time to sell {crop} at {mandi} right now"

    # Price direction
    if price_trend >= 5:
        price_msg = "prices are going up"
    elif price_trend >= 0:
        price_msg = "prices are steady"
    else:
        price_msg = "prices have dropped"

    # Weather summary
    weather_parts = []
    if hot_days > 0:
        weather_parts.append(f"{hot_days} very hot day(s)")
    if rainy_days > 0:
        weather_parts.append(f"{rainy_days} rainy day(s)")
    if weather_parts:
        weather_msg = f"weather shows {' and '.join(weather_parts)} ahead"
    else:
        weather_msg = "weather looks clear"

    # Storage
    storage_nice = storage_type.replace("_", " ").title()

    return (
        f"🌾 {verdict}. Currently, {price_msg} and {weather_msg}. "
        f"Your storage ({storage_nice}) is noted and the mandi is {distance_km:.0f} km away. "
        f"Overall readiness score: {int(final_score)} out of 100."
    )


# ---------------------------------------------------------------------------
def generate_explanation(
    price_result,
    weather_result,
    storage_type: str,
    distance_km: float,
) -> str:
    """
    Generate a plain-text, farmer-friendly explanation of harvest readiness.
    """
    sections = [
        "📈 About the Market Price:\n" + _price_explanation(price_result.trend_percent),
        "🌤️ About the Weather:\n" + _weather_explanation(
            weather_result.hot_days_count,
            weather_result.rainy_days_count,
        ),
        "🏚️ About Your Storage:\n" + _storage_explanation(storage_type),
        "🚛 About Transport:\n" + _transport_explanation(distance_km),
    ]

    return "\n\n".join(sections)


if __name__ == "__main__":
    from types import SimpleNamespace

    mock_price   = SimpleNamespace(trend_percent=6.2,  last_7_avg=2150.0, last_30_avg=2025.0, price_score=22.5)
    mock_weather = SimpleNamespace(weather_score=21.0, hot_days_count=1,  rainy_days_count=2)

    print(generate_explanation(mock_price, mock_weather, "warehouse", 120))
    print()
    print(generate_farmer_summary("Wheat", "Sangli", 72, "Green", 6.2, 1, 2, "warehouse", 120))
    print()
    print(generate_harvest_window(6.2, 1, 2, "warehouse"))
