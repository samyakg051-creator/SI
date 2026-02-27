"""
AgriChain – modules/ai_assistant.py
Groq-powered AI assistant for farmer queries.
"""

from groq import Groq


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are AgriChain AI, a friendly and practical assistant for Indian farmers.
You help farmers make smart decisions about when to harvest and sell their crops.
Keep answers short, clear and actionable. Avoid jargon. Use simple language.
When relevant, refer to the farm analysis data provided in the context.
Always be encouraging and empathetic — farming is hard work.
Respond in the same language the farmer uses (Hindi or English)."""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_ai_response(
    api_key: str,
    user_message: str,
    context: str = "",
    chat_history: list[dict] | None = None,
) -> str:
    """
    Send a message to Groq and return the AI response.

    Parameters
    ----------
    api_key      : str  – Groq API key
    user_message : str  – The farmer's question
    context      : str  – Current analysis context (scores, weather, prices)
    chat_history : list – Previous messages for multi-turn conversation

    Returns
    -------
    str – AI assistant response text
    """
    client = Groq(api_key=api_key)

    system_content = _SYSTEM_PROMPT
    if context:
        system_content += f"\n\nCurrent Farm Analysis:\n{context}"

    messages = [{"role": "system", "content": system_content}]

    # Include previous turns for context
    if chat_history:
        messages.extend(chat_history[-6:])  # last 3 exchanges

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=400,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


def build_context(
    crop: str,
    mandi: str,
    price_result=None,
    weather_result=None,
    score_result=None,
    storage_type: str = "",
    distance_km: float = 0,
) -> str:
    """
    Build a plain-text context string from the current analysis results
    to pass to the AI assistant.
    """
    parts = [
        f"Crop: {crop}",
        f"Target Mandi: {mandi}",
        f"Storage Type: {storage_type}",
        f"Distance to Mandi: {distance_km} km",
    ]

    if price_result:
        parts += [
            f"Last 7-Day Avg Price: ₹{price_result.last_7_avg:,.2f}",
            f"Last 30-Day Avg Price: ₹{price_result.last_30_avg:,.2f}",
            f"Price Trend: {price_result.trend_percent:+.2f}%",
            f"Price Score: {price_result.price_score}/30",
        ]

    if weather_result:
        parts += [
            f"Weather Score: {weather_result.weather_score}/30",
            f"Hot Days Forecast (>35°C): {weather_result.hot_days_count}",
            f"Rainy Days Forecast (>60%): {weather_result.rainy_days_count}",
        ]

    if score_result:
        parts += [
            f"Storage Score: {score_result.storage_score}/20",
            f"Transport Score: {score_result.transport_score}/20",
            f"FINAL Harvest Readiness Score: {score_result.final_score}/100",
            f"Market Status: {score_result.traffic_light}",
        ]

    return "\n".join(parts)
