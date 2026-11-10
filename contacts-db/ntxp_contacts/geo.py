"""Approximate city centroids (TX/OK + neighbours) for the proximity-in-miles
filter. The canonical DB stores addresses, not coordinates, so proximity is
resolved city -> centroid. Accuracy is city-level (a few miles), which is what
"contacts within N miles of Dallas" needs; unknown cities simply don't match a
proximity filter (they are never silently included).
"""
from __future__ import annotations

import math

# (city, state) -> (lat, lng)
CITIES: dict[tuple[str, str], tuple[float, float]] = {
    ("dallas", "TX"): (32.7767, -96.7970), ("fort worth", "TX"): (32.7555, -97.3308),
    ("plano", "TX"): (33.0198, -96.6989), ("frisco", "TX"): (33.1507, -96.8236),
    ("arlington", "TX"): (32.7357, -97.1081), ("irving", "TX"): (32.8140, -96.9489),
    ("garland", "TX"): (32.9126, -96.6389), ("richardson", "TX"): (32.9483, -96.7299),
    ("mckinney", "TX"): (33.1972, -96.6398), ("denton", "TX"): (33.2148, -97.1331),
    ("carrollton", "TX"): (32.9537, -96.8903), ("grand prairie", "TX"): (32.7460, -96.9978),
    ("mesquite", "TX"): (32.7668, -96.5992), ("lewisville", "TX"): (33.0462, -96.9942),
    ("allen", "TX"): (33.1032, -96.6706), ("flower mound", "TX"): (33.0146, -97.0970),
    ("rockwall", "TX"): (32.9312, -96.4597), ("rowlett", "TX"): (32.9029, -96.5639),
    ("desoto", "TX"): (32.5899, -96.8570), ("duncanville", "TX"): (32.6518, -96.9083),
    ("cedar hill", "TX"): (32.5885, -96.9561), ("lancaster", "TX"): (32.5921, -96.7561),
    ("coppell", "TX"): (32.9546, -97.0150), ("the colony", "TX"): (33.0890, -96.8864),
    ("little elm", "TX"): (33.1626, -96.9375), ("prosper", "TX"): (33.2362, -96.8011),
    ("wylie", "TX"): (33.0151, -96.5389), ("sherman", "TX"): (33.6357, -96.6089),
    ("burleson", "TX"): (32.5421, -97.3208), ("mansfield", "TX"): (32.5632, -97.1417),
    ("keller", "TX"): (32.9346, -97.2517), ("southlake", "TX"): (32.9412, -97.1342),
    ("euless", "TX"): (32.8371, -97.0820), ("bedford", "TX"): (32.8440, -97.1431),
    ("grapevine", "TX"): (32.9343, -97.0781), ("weatherford", "TX"): (32.7593, -97.7973),
    ("waco", "TX"): (31.5493, -97.1467), ("austin", "TX"): (30.2672, -97.7431),
    ("round rock", "TX"): (30.5083, -97.6789), ("georgetown", "TX"): (30.6333, -97.6780),
    ("san marcos", "TX"): (29.8833, -97.9414), ("san antonio", "TX"): (29.4241, -98.4936),
    ("new braunfels", "TX"): (29.7030, -98.1245), ("houston", "TX"): (29.7604, -95.3698),
    ("sugar land", "TX"): (29.5994, -95.6349), ("the woodlands", "TX"): (30.1658, -95.4613),
    ("katy", "TX"): (29.7858, -95.8245), ("pearland", "TX"): (29.5636, -95.2860),
    ("galveston", "TX"): (29.3013, -94.7977), ("beaumont", "TX"): (30.0802, -94.1266),
    ("tyler", "TX"): (32.3513, -95.3011), ("longview", "TX"): (32.5007, -94.7405),
    ("texarkana", "TX"): (33.4251, -94.0477), ("abilene", "TX"): (32.4487, -99.7331),
    ("wichita falls", "TX"): (33.9137, -98.4934), ("lubbock", "TX"): (33.5779, -101.8552),
    ("amarillo", "TX"): (35.2220, -101.8313), ("midland", "TX"): (31.9973, -102.0779),
    ("odessa", "TX"): (31.8457, -102.3676), ("el paso", "TX"): (31.7619, -106.4850),
    ("corpus christi", "TX"): (27.8006, -97.3964), ("laredo", "TX"): (27.5306, -99.4803),
    ("mcallen", "TX"): (26.2034, -98.2300), ("brownsville", "TX"): (25.9017, -97.4975),
    ("college station", "TX"): (30.6280, -96.3344), ("killeen", "TX"): (31.1171, -97.7278),
    ("temple", "TX"): (31.0982, -97.3428),
    ("oklahoma city", "OK"): (35.4676, -97.5164), ("tulsa", "OK"): (36.1540, -95.9928),
    ("norman", "OK"): (35.2226, -97.4395), ("edmond", "OK"): (35.6528, -97.4781),
    ("broken arrow", "OK"): (36.0609, -95.7975), ("lawton", "OK"): (34.6036, -98.3959),
    ("moore", "OK"): (35.3395, -97.4867), ("midwest city", "OK"): (35.4495, -97.3967),
    ("stillwater", "OK"): (36.1156, -97.0589), ("enid", "OK"): (36.3956, -97.8784),
    ("ardmore", "OK"): (34.1743, -97.1436), ("durant", "OK"): (33.9937, -96.3971),
    ("shawnee", "OK"): (35.3273, -96.9253), ("muskogee", "OK"): (35.7479, -95.3697),
    ("bartlesville", "OK"): (36.7473, -95.9808), ("owasso", "OK"): (36.2695, -95.8547),
    ("shreveport", "LA"): (32.5252, -93.7502), ("little rock", "AR"): (34.7465, -92.2896),
}

_EARTH_MI = 3958.8


def coords(city: str | None, state: str | None):
    if not city or not state:
        return None
    return CITIES.get((city.strip().lower(), state.strip().upper()))


def miles_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2)
    return 2 * _EARTH_MI * math.asin(math.sqrt(h))


def parse_place(text: str):
    """'Dallas, TX' or 'Dallas' -> (lat, lng) or None. A bare city resolves to
    its TX entry first, then any state."""
    if not text:
        return None
    parts = [p.strip() for p in text.split(",")]
    city = parts[0].lower()
    if len(parts) > 1 and parts[1]:
        return coords(city, parts[1])
    for st in ("TX", "OK"):
        if (city, st) in CITIES:
            return CITIES[(city, st)]
    for (c, _s), v in CITIES.items():
        if c == city:
            return v
    return None
