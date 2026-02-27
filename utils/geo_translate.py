"""
utils/geo_translate.py — Place name translation.
"""

_PLACE_HI = {
    "Pune": "पुणे", "Nashik": "नासिक", "Nagpur": "नागपुर",
    "Aurangabad": "औरंगाबाद", "Solapur": "सोलापुर",
    "Kolhapur": "कोल्हापुर", "Sangli": "सांगली",
}
_PLACE_MR = _PLACE_HI  # same for Marathi


def translate_place(place: str, lang_code: str = "en") -> str:
    if lang_code == "hi":
        return _PLACE_HI.get(place, place)
    if lang_code == "mr":
        return _PLACE_MR.get(place, place)
    return place
