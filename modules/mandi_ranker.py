"""
modules/mandi_ranker.py — Rank mandis by net profit after transport cost.
"""
from __future__ import annotations
import math
from utils.geo import DISTRICT_COORDS
from modules.data_loader import get_top_mandis_for_crop, get_mandi_coords


TRANSPORT_RATE_PER_KM_QTL = 1.8  # ₹ per km per quintal


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def rank_mandis(
    crop: str,
    quantity: float,
    district: str,
    top_n: int = 3,
) -> list[dict]:
    """
    Return top_n mandis ranked by net profit per quintal after transport.
    
    Each dict contains:
        mandi, expected_price, distance_km, transport_cost_qtl,
        net_profit_per_qtl, total_transport, reason
    """
    origin = DISTRICT_COORDS.get(district, (19.75, 75.71))
    top_mandis = get_top_mandis_for_crop(crop, n=20)

    if top_mandis.empty:
        return []

    results = []
    for _, row in top_mandis.iterrows():
        mandi_name = row["Mandi"]
        price = float(row["LatestPrice"])
        coords = get_mandi_coords(mandi_name)
        dist_km = _haversine(origin[0], origin[1], coords[0], coords[1])

        transport_per_qtl = round(dist_km * TRANSPORT_RATE_PER_KM_QTL, 2)
        net_profit = round(price - transport_per_qtl, 2)
        total_transport = round(transport_per_qtl * quantity, 2)

        # Generate reason
        if dist_km < 30:
            reason = f"Very close ({dist_km:.0f} km) — minimal transport cost"
        elif net_profit > price * 0.9:
            reason = f"High price ₹{price:,.0f} more than offsets {dist_km:.0f} km distance"
        elif dist_km > 150:
            reason = f"Far ({dist_km:.0f} km) but strong price ₹{price:,.0f}/qtl"
        else:
            reason = f"Balanced: ₹{price:,.0f}/qtl with {dist_km:.0f} km transport"

        results.append({
            "mandi": mandi_name,
            "expected_price": price,
            "distance_km": dist_km,
            "transport_cost_qtl": transport_per_qtl,
            "net_profit_per_qtl": net_profit,
            "total_transport": total_transport,
            "reason": reason,
        })

    # Sort by net profit descending
    results.sort(key=lambda x: x["net_profit_per_qtl"], reverse=True)
    return results[:top_n]
