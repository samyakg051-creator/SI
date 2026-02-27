"""
modules/agri_data.py
Central data store for AgriChain — district centroids, mandi data, crop info, translations.
"""

# ── Crop configuration ────────────────────────────────────────────────────────
CROP_EMOJI = {
    "Wheat":   "🌾",
    "Tomato":  "🍅",
    "Onion":   "🧅",
    "Potato":  "🥔",
    "Corn":    "🌽",
    "Soybean": "🫘",
    "Cotton":  "🌿",
}
DEFAULT_EMOJI = "🌱"

# Days from sowing to harvest
CROP_DURATION = {
    "Wheat":   120,
    "Tomato":  75,
    "Onion":   90,
    "Potato":  90,
    "Corn":    100,
    "Soybean": 100,
    "Cotton":  180,
}

# ── Maharashtra district centroids (lat, lon) ─────────────────────────────────
DISTRICT_CENTROIDS = {
    "Ahmednagar":       (19.0948, 74.7480),
    "Akola":            (20.7070, 77.0082),
    "Amravati":         (20.9374, 77.7796),
    "Aurangabad":       (19.8762, 75.3433),
    "Beed":             (18.9890, 75.7601),
    "Bhandara":         (21.1664, 79.6486),
    "Buldhana":         (20.5292, 76.1842),
    "Chandrapur":       (19.9615, 79.2961),
    "Dhule":            (20.9042, 74.7749),
    "Gadchiroli":       (20.1809, 80.0082),
    "Gondia":           (21.4607, 80.1969),
    "Hingoli":          (19.7157, 77.1497),
    "Jalgaon":          (21.0077, 75.5626),
    "Jalna":            (19.8347, 75.8816),
    "Kolhapur":         (16.6910, 74.2430),
    "Latur":            (18.4088, 76.5604),
    "Mumbai City":      (18.9388, 72.8354),
    "Mumbai Suburban":  (19.1136, 72.8697),
    "Nagpur":           (21.1458, 79.0882),
    "Nanded":           (19.1609, 77.3212),
    "Nandurbar":        (21.3690, 74.2429),
    "Nashik":           (20.0113, 73.7903),
    "Osmanabad":        (18.1863, 76.0356),
    "Palghar":          (19.6969, 72.7650),
    "Parbhani":         (19.2709, 76.7749),
    "Pune":             (18.5204, 73.8567),
    "Raigad":           (18.5158, 73.1780),
    "Ratnagiri":        (16.9902, 73.3120),
    "Sangli":           (16.8524, 74.5815),
    "Satara":           (17.6805, 74.0183),
    "Sindhudurg":       (16.3490, 73.7730),
    "Solapur":          (17.6599, 75.9064),
    "Thane":            (19.2183, 72.9781),
    "Wardha":           (20.7453, 78.6022),
    "Washim":           (20.1121, 77.1464),
    "Yavatmal":         (20.3888, 78.1204),
}

# ── Mandi data: which mandis appear where ────────────────────────────────────
# Prices per quintal (₹)
MANDI_DATA = {
    "Sangli": {
        "lat": 16.8524, "lon": 74.5815,
        "district": "Sangli",
        "prices": {"Wheat": 3580, "Onion": 2200, "Tomato": 1600, "Potato": 1900, "Corn": 1750, "Soybean": 4500, "Cotton": 6800},
    },
    "Palghar": {
        "lat": 19.6969, "lon": 72.7650,
        "district": "Palghar",
        "prices": {"Wheat": 3200, "Onion": 1900, "Tomato": 1400, "Potato": 1700, "Corn": 1600, "Soybean": 4200, "Cotton": 6500},
    },
    "Ulhasnagar": {
        "lat": 19.2183, "lon": 73.1558,
        "district": "Thane",
        "prices": {"Wheat": 3400, "Onion": 2100, "Tomato": 1550, "Potato": 1850, "Corn": 1700, "Soybean": 4300, "Cotton": 6600},
    },
    "Pune": {
        "lat": 18.5204, "lon": 73.8567,
        "district": "Pune",
        "prices": {"Wheat": 3500, "Onion": 2250, "Tomato": 1700, "Potato": 2000, "Corn": 1800, "Soybean": 4600, "Cotton": 6900},
    },
    "Nashik": {
        "lat": 20.0113, "lon": 73.7903,
        "district": "Nashik",
        "prices": {"Wheat": 3450, "Onion": 2400, "Tomato": 1750, "Potato": 1950, "Corn": 1820, "Soybean": 4550, "Cotton": 6750},
    },
    "Nagpur": {
        "lat": 21.1458, "lon": 79.0882,
        "district": "Nagpur",
        "prices": {"Wheat": 3380, "Onion": 1980, "Tomato": 1480, "Potato": 1820, "Corn": 1680, "Soybean": 4400, "Cotton": 6700},
    },
    "Aurangabad": {
        "lat": 19.8762, "lon": 75.3433,
        "district": "Aurangabad",
        "prices": {"Wheat": 3420, "Onion": 2050, "Tomato": 1520, "Potato": 1860, "Corn": 1720, "Soybean": 4480, "Cotton": 6820},
    },
    "Solapur": {
        "lat": 17.6599, "lon": 75.9064,
        "district": "Solapur",
        "prices": {"Wheat": 3350, "Onion": 2150, "Tomato": 1600, "Potato": 1780, "Corn": 1640, "Soybean": 4350, "Cotton": 6640},
    },
    "Kolhapur": {
        "lat": 16.6910, "lon": 74.2430,
        "district": "Kolhapur",
        "prices": {"Wheat": 3300, "Onion": 2100, "Tomato": 1580, "Potato": 1820, "Corn": 1660, "Soybean": 4320, "Cotton": 6580},
    },
    "Vasai": {
        "lat": 19.3919, "lon": 72.8397,
        "district": "Palghar",
        "prices": {"Wheat": 3380, "Onion": 2000, "Tomato": 1500, "Potato": 1800, "Corn": 1650, "Soybean": 4250, "Cotton": 6550},
    },
    "Kille Dharur": {
        "lat": 18.0500, "lon": 76.5667,
        "district": "Beed",
        "prices": {"Wheat": 3100, "Onion": 1850, "Tomato": 1350, "Potato": 1650, "Corn": 1580, "Soybean": 4100, "Cotton": 6400},
    },
}

# ── Language strings ──────────────────────────────────────────────────────────
T = {
    "en": {
        "app_title": "AgriChain",
        "app_subtitle": "Harvest Readiness Intelligence",
        "map_page": "🗺️ Map Explorer",
        "crop": "Crop",
        "district": "District",
        "sowing_date": "Sowing Date",
        "quantity": "Quantity (qtl)",
        "storage": "Storage Type",
        "language": "Language",
        "select_district": "Select a district",
        "map_title": "Maharashtra — Agricultural Map",
        "mandi_markers": "Show Mandi Markers",
        "crop_marker": "Show Crop Marker",
        "click_district": "Click a district on the map or select below",
        "session_card": "📋 Current Selection",
        "harvest_page": "Harvest Score",
    },
    "hi": {
        "app_title": "एग्रीचेन",
        "app_subtitle": "फसल तत्परता बुद्धिमत्ता",
        "map_page": "🗺️ नक्शा",
        "crop": "फसल",
        "district": "जिला",
        "sowing_date": "बुवाई की तारीख",
        "quantity": "मात्रा (क्विंटल)",
        "storage": "भंडारण प्रकार",
        "language": "भाषा",
        "select_district": "जिला चुनें",
        "map_title": "महाराष्ट्र — कृषि मानचित्र",
        "mandi_markers": "मंडी मार्कर दिखाएं",
        "crop_marker": "फसल मार्कर दिखाएं",
        "click_district": "नक्शे पर जिला क्लिक करें या नीचे से चुनें",
        "session_card": "📋 वर्तमान चयन",
        "harvest_page": "फसल स्कोर",
    },
    "mr": {
        "app_title": "ॲग्रीचेन",
        "app_subtitle": "कापणी तयारी बुद्धिमत्ता",
        "map_page": "🗺️ नकाशा",
        "crop": "पीक",
        "district": "जिल्हा",
        "sowing_date": "पेरणी तारीख",
        "quantity": "मात्रा (क्विं)",
        "storage": "साठवण प्रकार",
        "language": "भाषा",
        "select_district": "जिल्हा निवडा",
        "map_title": "महाराष्ट्र — कृषी नकाशा",
        "mandi_markers": "बाजार ठिकाणे दर्शवा",
        "crop_marker": "पीक ठिकाण दर्शवा",
        "click_district": "नकाशावर जिल्हा क्लिक करा किंवा खाली निवडा",
        "session_card": "📋 सध्याची निवड",
        "harvest_page": "कापणी स्कोर",
    },
}

def t(key: str, lang: str = "en") -> str:
    """Get translated string."""
    return T.get(lang, T["en"]).get(key, key)
