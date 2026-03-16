# Placeholder for utils/geo_utils.py
"""
Geolocation Utilities
Lightweight, offline-friendly geo classification
"""

# Offline static mapping (extendable)
KNOWN_REGIONS = {
    "8.8.8.8": "US",
    "8.8.4.4": "US",
    "1.1.1.1": "US"
}


def get_country(ip: str) -> str:
    """
    Returns country code for known IPs
    Offline-safe placeholder for geo correlation
    """
    return KNOWN_REGIONS.get(ip, "UNKNOWN")
