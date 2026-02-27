"""
AgriChain – modules/scoring.py
Computes storage score, transport score, final weighted score, and traffic light.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
@dataclass
class ScoreResult:
    price_score: float        # 0–30  (supplied externally)
    weather_score: float      # 0–30  (supplied externally)
    storage_score: float      # 0–20  (computed here)
    transport_score: float    # 0–20  (computed here)
    final_score: float        # 0–100 (weighted composite)
    traffic_light: str        # "Green" | "Yellow" | "Red"

# Storage quality tiers → score out of 20
_STORAGE_TIERS: dict[str, int] = {
    "cold_storage":    20,   # refrigerated / controlled atmosphere
    "warehouse":       15,   # dry, covered warehouse
    "covered_shed":    10,   # basic covered shed
    "open_yard":        5,   # open-air storage
    "none":             0,   # no storage available
}


def compute_storage_score(storage_type: str) -> float:
    """
    Return a storage score out of 20 based on storage facility type.

    Parameters
    ----------
    storage_type : str
        One of: 'cold_storage', 'warehouse', 'covered_shed', 'open_yard', 'none'.
        Case-insensitive.  Unknown values default to 0.

    Returns
    -------
    float  – score in [0, 20]
    """
    return float(_STORAGE_TIERS.get(storage_type.lower().strip(), 0))

# Distance thresholds (km) → (base_score, penalty_per_km_beyond_threshold)
_TRANSPORT_BANDS = [
    (50,   20, 0.00),   # ≤  50 km → full score
    (150,  15, 0.05),   # 51–150 km → slight penalty
    (300,  10, 0.03),   # 151–300 km → moderate penalty
    (500,   5, 0.02),   # 301–500 km → high penalty
]
_TRANSPORT_MIN_SCORE = 0


def compute_transport_score(distance_km: float) -> float:
    """
    Return a transport score out of 20 based on distance to market (km).

    Shorter distance = higher score (less spoilage / cost risk).

    Parameters
    ----------
    distance_km : float  – road distance to the target mandi in kilometres.

    Returns
    -------
    float  – score in [0, 20]
    """
    if distance_km <= 0:
        return 20.0

    for threshold, base_score, _ in _TRANSPORT_BANDS:
        if distance_km <= threshold:
            return float(base_score)

    # Beyond 500 km → minimum score
    return float(_TRANSPORT_MIN_SCORE)

# ---------------------------------------------------------------------------
def compute_final_score(
    price_score: float,
    weather_score: float,
    storage_score: float,
    transport_score: float,
) -> float:
    """
    Weighted composite score (0–100).

    Weights
    -------
    Price   : 40 %
    Weather : 30 %
    Storage : 20 %
    Transport: 10 %

    Each component is normalised to a 0–100 scale before weighting:
        price_score   / 30 * 100
        weather_score / 30 * 100
        storage_score / 20 * 100
        transport_score / 20 * 100
    """
    normalised_price     = (price_score     / 30) * 100
    normalised_weather   = (weather_score   / 30) * 100
    normalised_storage   = (storage_score   / 20) * 100
    normalised_transport = (transport_score / 20) * 100

    final = (
        0.4 * normalised_price
        + 0.3 * normalised_weather
        + 0.2 * normalised_storage
        + 0.1 * normalised_transport
    )
    return round(min(max(final, 0.0), 100.0), 2)


def get_traffic_light(final_score: float) -> str:
    """
    Convert a final score to a traffic-light colour.

    Green  : >= 70
    Yellow : 40 – 69
    Red    : <  40
    """
    if final_score >= 70:
        return "Green"
    elif final_score >= 40:
        return "Yellow"
    else:
        return "Red"


# ---------------------------------------------------------------------------
def generate_score(
    price_score: float,
    weather_score: float,
    storage_type: str,
    distance_km: float,
) -> ScoreResult:
    """
    Master function that assembles all sub-scores into a ScoreResult.

    Parameters
    ----------
    price_score   : float – price trend score from price_analysis module (0–30)
    weather_score : float – weather penalty score from weather module     (0–30)
    storage_type  : str   – storage facility type string
    distance_km   : float – road distance to target mandi in km

    Returns
    -------
    ScoreResult dataclass with all scores and traffic light label.
    """
    storage_score   = compute_storage_score(storage_type)
    transport_score = compute_transport_score(distance_km)
    final_score     = compute_final_score(price_score, weather_score,
                                          storage_score, transport_score)
    traffic_light   = get_traffic_light(final_score)

    return ScoreResult(
        price_score=price_score,
        weather_score=weather_score,
        storage_score=storage_score,
        transport_score=transport_score,
        final_score=final_score,
        traffic_light=traffic_light,
    )

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = generate_score(
        price_score=22.5,
        weather_score=24.0,
        storage_type="warehouse",
        distance_km=120,
    )
    print(result)
